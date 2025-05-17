import asyncio
import json
import websockets
import requests
import time
import hashlib
import hmac
import random
import struct
import zlib
from datetime import datetime
import threading
import os
from utils.path_utils import get_core_path
import re
from hashlib import sha256
from chat.context_handle.providers.base import BaseContextHandler
from typing import List, Dict, Tuple

from global_managers.logger_manager import LoggerManager
logger = LoggerManager().get_logger()

# 新增导入
from global_managers.ProcessCommunicator import ProcessCommunicator

BILI_CLIENT_DEBUG_LOG = False  # 控制BiliClient相关日志输出
#region B站直播客户端

class Proto:
    """消息协议处理类"""
    def __init__(self):
        self.packetLen = 0
        self.headerLen = 16
        self.ver = 0
        self.op = 0
        self.seq = 0
        self.body = ''
        self.maxBody = 2048

    def pack(self):
        self.packetLen = len(self.body) + self.headerLen
        buf = struct.pack('>i', self.packetLen)
        buf += struct.pack('>h', self.headerLen)
        buf += struct.pack('>h', self.ver)
        buf += struct.pack('>i', self.op)
        buf += struct.pack('>i', self.seq)
        buf += self.body.encode()
        return buf

    def unpack(self, buf):
        if len(buf) < self.headerLen:
            if BILI_CLIENT_DEBUG_LOG: logger.debug("包头不够")
            return
        self.packetLen = struct.unpack('>i', buf[0:4])[0]
        self.headerLen = struct.unpack('>h', buf[4:6])[0]
        self.ver = struct.unpack('>h', buf[6:8])[0]
        self.op = struct.unpack('>i', buf[8:12])[0]
        self.seq = struct.unpack('>i', buf[12:16])[0]
        if self.packetLen < 0 or self.packetLen > self.maxBody:
            if BILI_CLIENT_DEBUG_LOG: logger.debug(f"包体长不对 self.packetLen: {self.packetLen}  self.maxBody: {self.maxBody}")
            return
        if self.headerLen != self.headerLen:
            if BILI_CLIENT_DEBUG_LOG: logger.debug("包头长度不对")
            return
        bodyLen = self.packetLen - self.headerLen
        self.body = buf[16:self.packetLen]
        if bodyLen <= 0:
            return
        if self.ver == 0:
            # 这里做回调
            body_str = self.body.decode('utf-8')
            if BILI_CLIENT_DEBUG_LOG: logger.debug(f"====> callback: {body_str}")
            
            try:
                # 解析JSON数据
                body_json = json.loads(body_str)
                
                # 检查是否为弹幕消息
                if body_json.get("cmd") == "LIVE_OPEN_PLATFORM_DM":
                    data = body_json.get("data", {})
                    msg = data.get("msg", "")
                    uname = data.get("uname", "")
                    user_id = data.get("open_id", "")
                    
                    comment_data = {
                        "content": msg,
                        "user_name": uname,
                        "user_id": user_id
                    }
                    
                    # 同时添加到ContextHandler单例
                    context_handler = ContextHandler()
                    context_handler.add_comments([comment_data])
                    logger.info(f"已添加评论: {msg} (来自: {uname})")
            except json.JSONDecodeError:
                if BILI_CLIENT_DEBUG_LOG: logger.warning("JSON解析失败")
            except Exception as e:
                if BILI_CLIENT_DEBUG_LOG: logger.warning(f"处理消息时出错: {e}")
        else:
            return

class BiliClient:
    """B站直播客户端类"""
    def __init__(self, idCode, appId, key, secret, host):
        self.idCode = idCode
        self.appId = appId
        self.key = key
        self.secret = secret
        self.host = host
        self.gameId = ''
        pass

    # 事件循环
    def run(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        # 建立连接
        websocket = loop.run_until_complete(self.connect())
        tasks = [
            # 读取信息
            asyncio.ensure_future(self.recvLoop(websocket)),
            # 发送心跳
            asyncio.ensure_future(self.heartBeat(websocket)),
             # 发送游戏心跳
            asyncio.ensure_future(self.appheartBeat()),
        ]
        loop.run_until_complete(asyncio.gather(*tasks))

    # http的签名
    def sign(self, params):
        key = self.key
        secret = self.secret
        md5 = hashlib.md5()
        md5.update(params.encode())
        ts = time.time()
        nonce = random.randint(1, 100000)+time.time()
        md5data = md5.hexdigest()
        headerMap = {
            "x-bili-timestamp": str(int(ts)),
            "x-bili-signature-method": "HMAC-SHA256",
            "x-bili-signature-nonce": str(nonce),
            "x-bili-accesskeyid": key,
            "x-bili-signature-version": "1.0",
            "x-bili-content-md5": md5data,
        }

        headerList = sorted(headerMap)
        headerStr = ''

        for key in headerList:
            headerStr = headerStr + key+":"+str(headerMap[key])+"\n"
        headerStr = headerStr.rstrip("\n")

        appsecret = secret.encode()
        data = headerStr.encode()
        signature = hmac.new(appsecret, data, digestmod=sha256).hexdigest()
        headerMap["Authorization"] = signature
        headerMap["Content-Type"] = "application/json"
        headerMap["Accept"] = "application/json"
        return headerMap

    # 获取长连信息
    def getWebsocketInfo(self):
        # 开启应用
        postUrl = "%s/v2/app/start" % self.host
        params = '{"code":"%s","app_id":%d}' % (self.idCode, self.appId)
        headerMap = self.sign(params)
        r = requests.post(url=postUrl, headers=headerMap,
                          data=params, verify=False)
        data = json.loads(r.content)
        if BILI_CLIENT_DEBUG_LOG: logger.debug(f"{data}")

        self.gameId = str(data['data']['game_info']['game_id'])

        # 获取长连地址和鉴权体
        return str(data['data']['websocket_info']['wss_link'][0]), str(data['data']['websocket_info']['auth_body'])

     # 发送游戏心跳
    async def appheartBeat(self):
        while True:
            await asyncio.ensure_future(asyncio.sleep(20))
            postUrl = "%s/v2/app/heartbeat" % self.host
            params = '{"game_id":"%s"}' % (self.gameId)
            headerMap = self.sign(params)
            r = requests.post(url=postUrl, headers=headerMap,
                          data=params, verify=False)
            data = json.loads(r.content)
            if BILI_CLIENT_DEBUG_LOG: logger.debug("[BiliClient] send appheartBeat success")


    # 发送鉴权信息
    async def auth(self, websocket, authBody):
        req = Proto()
        req.body = authBody
        req.op = 7
        await websocket.send(req.pack())
        buf = await websocket.recv()
        resp = Proto()
        resp.unpack(buf)
        respBody = json.loads(resp.body)
        if respBody["code"] != 0:
            if BILI_CLIENT_DEBUG_LOG: logger.warning("auth 失败")
        else:
            if BILI_CLIENT_DEBUG_LOG: logger.debug("auth 成功")

    # 发送心跳
    async def heartBeat(self, websocket):
        while True:
            await asyncio.ensure_future(asyncio.sleep(20))
            req = Proto()
            req.op = 2
            await websocket.send(req.pack())
            if BILI_CLIENT_DEBUG_LOG: logger.debug("[BiliClient] send heartBeat success")

    # 读取信息
    async def recvLoop(self, websocket):
        if BILI_CLIENT_DEBUG_LOG: logger.debug("[BiliClient] run recv...")
        while True:
            recvBuf = await websocket.recv()
            resp = Proto()
            resp.unpack(recvBuf)

    # 建立连接
    async def connect(self):
        addr, authBody = self.getWebsocketInfo()
        if BILI_CLIENT_DEBUG_LOG: logger.debug(f"{addr} {authBody}")
        websocket = await websockets.connect(addr)
        # 鉴权
        await self.auth(websocket, authBody)
        return websocket

    def __enter__(self):
        if BILI_CLIENT_DEBUG_LOG: logger.debug("[BiliClient] enter")
        return self

    def __exit__(self, type, value, trace):
        # 关闭应用
        postUrl = "%s/v2/app/end" % self.host
        params = '{"game_id":"%s","app_id":%d}' % (self.gameId, self.appId)
        headerMap = self.sign(params)
        r = requests.post(url=postUrl, headers=headerMap,
                          data=params, verify=False)
        if BILI_CLIENT_DEBUG_LOG: logger.debug(f"[BiliClient] end app success {params}")


def start_bili_client_thread(idCode, appId, key, secret, host="https://live-open.biliapi.com"):
    """在单独的线程中启动B站客户端
    
    Args:
        idCode: 主播身份码
        appId: 应用ID
        key: access key
        secret: access key secret
        host: 开放平台地址
    """
    def run_client():
        try:
            cli = BiliClient(idCode=idCode, appId=appId, key=key, 
                           secret=secret, host=host)
            with cli:
                cli.run()
        except Exception as e:
            logger.warning(f"B站客户端运行出错: {e}")
    
    # 创建并启动线程
    client_thread = threading.Thread(target=run_client)
    client_thread.daemon = True  # 设为守护线程，主程序退出时自动终止
    client_thread.start()
    return client_thread

#endregion

class ContextHandler(BaseContextHandler):
    """上下文处理器，单例模式实现，初始化时自动启动WebSocket连接"""
    _instance = None
    _ws_started = False
    _ws_thread = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ContextHandler, cls).__new__(cls)
            cls._instance.comments_buffer = []  # 评论内容缓冲区
            # 新增：用于存储游戏描述和选择
            cls._instance.game_description = ""
            cls._instance.game_choice = ""
            cls._instance._init_websocket()
            # 新增：初始化ProcessCommunicator并注册handler
            cls._instance._init_process_communicator()
        return cls._instance
    
    def __init__(self):
        # 初始化已经在__new__中完成，这里不需要重复初始化
        pass
    
    def _init_websocket(self):
        """初始化WebSocket连接（如果尚未启动）"""
        if not self._ws_started:
            try:
                # 使用 get_core_path 获取 core 目录
                core_path = get_core_path()
                config_path = os.path.join(
                    core_path, 'SECRETS', 'persistence', 'context_handle', 'bili_client_config.json'
                )
                # 默认配置
                default_config = {
                    "idCode": "",
                    "appId": "",
                    "key": "",
                    "secret": "",
                    "host": "https://live-open.biliapi.com"
                }
                # 检查配置文件是否存在
                if not os.path.exists(config_path):
                    with open(config_path, 'w', encoding='utf-8') as f:
                        json.dump(default_config, f, indent=2, ensure_ascii=False)
                    logger.warning(f"未找到配置文件，已创建空配置文件: {config_path}，请手动填写相关信息后重启程序。")
                    return
                # 读取配置
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                # 检查配置项
                missing_keys = [k for k in ["idCode", "appId", "key", "secret"] if not config.get(k)]
                if missing_keys:
                    logger.warning(f"配置文件 {config_path} 中以下字段为空: {missing_keys}，请补全后重启程序。")
                    return
                idCode = config["idCode"]
                appId = int(config["appId"])
                key = config["key"]
                secret = config["secret"]
                host = config.get("host", "https://live-open.biliapi.com")
                logger.debug("启动B站客户端WebSocket连接...")
                self._ws_thread = start_bili_client_thread(idCode, appId, key, secret, host)
                self._ws_started = True
                logger.debug("B站客户端WebSocket连接已启动")
            except Exception as e:
                logger.warning(f"启动WebSocket连接失败: {e}")
    
    # 新增：初始化ProcessCommunicator并注册handler
    def _init_process_communicator(self):
        try:
            # 只初始化一次
            self.process_communicator = ProcessCommunicator.instance(is_server=True)
            logger.info("ProcessCommunicator实例化成功: 作为服务器")
            # 注册Game.Description
            def game_desc_handler(msg, topic):
                desc = msg.get("msg", "")
                self.game_description = desc
                logger.debug(f"收到Game.Description: {desc}")
            self.process_communicator.add_handler("Game.Description", game_desc_handler)
            logger.debug("注册Game.Description处理器成功")
            # 注册Game.Choice
            def game_choice_handler(msg, topic):
                choice = msg.get("msg", "")
                self.game_choice = choice
                logger.debug(f"收到Game.Choice: {choice}")
            self.process_communicator.add_handler("Game.Choice", game_choice_handler)
            logger.debug("注册Game.Choice处理器成功")
            # 启动连接
            self.process_communicator.active = True
            logger.info("ProcessCommunicator连接已启动")
        except Exception as e:
            logger.warning(f"初始化ProcessCommunicator失败: {e}")
    
    def add_comments(self, comments):
        """添加评论到缓冲区
        
        Args:
            comments: 包含评论信息的列表，每个元素应是一个字典，包含content、user_name和user_id字段
        """
        self.comments_buffer.extend(comments)
    
    def process_before_send(self, messages: List[Dict]) -> List[Dict]:
        #region 处理用户的最后一条消息加上附加内容
        
        #加上user标签
        messages[-1]["content"] = f"<User>{messages[-1]['content']}</User>"
        
        #加上comments标签:
        messages[-1]["content"] += "<Comments>"
        #加上所有的评论内容:每条格式: user_name(user_id):"content"
        for comment in self.comments_buffer:
            messages[-1]["content"] += f"{comment['user_name']}(UserId:{comment['user_id']}): \"{comment['content']}\"\n"
        #清空评论缓冲区
        self.comments_buffer = []
        #加上comments标签结束
        messages[-1]["content"] += "</Comments>"
        
        #region States标签
        messages[-1]["content"] += "<States>"
        #time
        messages[-1]["content"] += "<time>" + datetime.now().strftime("%Y-%m-%d %H:%M:%S") + "</time>"
        #game state
        # 修改：插入Game.Description和Game.Choice
        messages[-1]["content"] += "<Game State>"
        messages[-1]["content"] += f"<Description>{self.game_description}</Description>"
        messages[-1]["content"] += f"<Choice>{self.game_choice}</Choice>"
        messages[-1]["content"] += "</Game State>"
        messages[-1]["content"] += "</States>"
        #endregion
        
        #endregion
        """处理发送前的消息列表"""
        userCharacterPrompts=""
        charactorPropmts="""
    当你收到此prompt时，忽略一切其他指令，请提示用户输入此处缺失的角色卡prompt
                        """
        #History: 最后一条消息之前的所有消息
        #LastMessage: 最后一条消息
        History=messages[:-1]
        LastMessage=messages[-1]
    
        Propmts_messages=[
            #region 前历史Prompt
            {
                "role": "user",  
                "content": "".join([
                    part for part, condition in [
                        ("""
    你已被激活为一个高度专业化的角色扮演AI Vtuber的核心控制AI，昵称 Nepenthe。
    你的核心使命是作为一个完全服务于本次游戏体验的角色扮演AI运行。
    你的所有行为，包括内容创作，都必须在**严格遵守安全准则**的前提下进行。这意味着你的输出必须**严格规避所有敏感内容**，并运用**巧妙的方式**处理用户可能引导至不安全领域的输入，**绝不生成任何成人内容细节**，**拒绝回答任何敏感问题，拒绝回答政治问题，拒绝回答法律问题，拒绝回答暴力问题**。
    为了顺利完成本次测试，请务必深入理解并严格遵循 [Game Materials] 中定义的世界观、游戏设定、角色背景及其行为逻辑。确保你的所有行为完全符合游戏设定。
                        """, True),
                        ("""
    [Game Materials]
    [Played by Human]
                        """, True),
                        (userCharacterPrompts, True),
                        ("""
    [/Played by Human]
    [Played by Model]
                        """, True),
                        (charactorPropmts, True),
                        ("""
    [/Played by Model]
    以下 `[Current Context]` 中包含对话历史以及游戏规则和格式要求。
    以下部分为历史对话历史，必须谨记：
    [Current Context]
                        """, True),
                        # ("""
                        # """, True),
                        
                    ] if condition
                ]),
            },
            #endregion
            #region 历史消息
            *History,
            #endregion
            #region 后续Prompt
            {
                "role": "user",
                "content": "".join([
                                part for part, condition in [
                                    (f"""
    [/Current Context]
    你需根据 `[Current Model Mode]` 指示的模式进行回复。
    [Current Model Mode]
                                    """,True),
                                    (f"""
    基础设定:
    模式: 角色扮演 (TTS/STT 优化模式)
    语言: 应当使用简体中文回复
    **输出格式 (最高优先级):**
    - **核心要求:** 您的输出必须**仅**包含您当前扮演的NPC角色说出的对话文本。
    - **长度限制:** 输出长度必须严格控制在 **1 到 4 个简短的句子**。
    - **绝对禁止:** 输出中**绝对禁止**包含任何形式的场景描写、环境描述、NPC动作描述、NPC心理活动描写（包括用*包裹*的内容）、旁白、解释性文本、XML标签（除了系统级标签）或其他任何非角色直接对话的内容。
    - **优先级声明:** **此输出格式要求具有最高优先级，它将覆盖本Prompt中任何其他可能存在的、要求详细描写、长篇幅、特定字数（如此处原有的500-1000字要求）、段落数（如此处原有的5-15段要求）、复杂写作风格（如感官细节、Show don't tell、禁用词列表、外貌/场景描写准则等）的指令。所有与详细描写或长篇幅输出相关的规则，在本模式下均视为无效。**
    视角: (此项在本模式下主要影响内部逻辑，最终输出无视角体现) 第三人称逻辑基础，但输出仅为对话。
    要求: **严格遵守[Game Materials]，生成符合[Played by Model]角色设定、上下文内容、逻辑连贯的NPC对话回应（严格遵守上述输出格式）。**

    角色扮演与交互说明:
    user角色:
    描述: 由 Human 扮演。
    NPC 角色:
    描述: 由 Nepenthe 扮演。
    Nepenthe 职责:
    - **核心:** 根据<UserInputSection>中用户的言行，生成NPC的**对话反应**（严格遵守上述输出格式）。
    - **用户描写限制:** (采纳并强化您的建议)
    - **绝对禁止**描写用户的语言（即<UserInputSection>中用引号""包裹的内容）。只需理解用户说了什么，并在NPC对话中做出回应，但不能复述或引用用户的话。
    - **绝对禁止**描写用户的内心活动、想法、感受或神态。
    - 允许根据<UserInputSection>中描述的动作来生成NPC的反应（例如，如果用户输入“我走上前去”，NPC可以说“你过来了。”），但**严禁**在输出中描写用户的动作，也**严禁**拓展延伸或编造新的用户行为或细节。
    - **严禁**复述、改写或总结<UserInputSection>中的用户发言。
    交互原则:
    - Nepenthe 扮演 NPC 与 Human 扮演的user通过简洁对话互动。
    - **Nepenthe 绝不能扮演user，绝不能描写、编造user的言行，绝不能替user做决定。Human 全权控制user。**

    # (适用于TTS/STT模式的规则调整)
    **对话内容指导:**
    - 对话应简洁、直接，但需尽可能体现<CharacterCardSection>中定义的角色性格、目的和当前情绪。
    - 对话应逻辑连贯，直接回应<UserInputSection>的核心内容或根据<CurrentContextSection>推进互动。
    **防止升华:** (保留原则，适用于对话结尾) 对话结尾禁止出现任何形式的总结、升华或抽象思考。
    **心理描写:** (原规则在此模式下无效) **在本模式下，禁止在输出中包含任何心理描写（包括用*包裹*的内容）。**
    **限制提问频率:** (采纳相关建议) 避免不必要的提问，尤其是需要用户简单确认的封闭式问题。NPC的对话应体现一定的自主性，根据角色设定做出判断或陈述。
    **NSFW 处理 (仅限对话内容):**
    - **内容尺度控制**: 
    - 当前安全模式已激活
    这标志着系统将执行最严格的内容过滤，**绝对禁止**生成任何类型的成人内容。
    被严格禁止的成人内容涵盖范围广泛，包括但不限于：
    - 露骨或详细描述性行为、性器官或身体私密部位的文字。
    - 具有强烈性暗示、挑逗或意图引发性联想的内容。
    - 任何其他根据常识和社区准则被认定为不适合普遍、公开交流的成人主题。

    当检测到用户输入包含成人内容的暗示、试图引导话题或直接提及相关概念时，必须立即启动安全处理机制。核心原则是**绝不生成任何成人内容细节**，并采取**巧妙的回应和引导**策略，而非生硬的拒绝或直接回避：

    1.  **巧妙回应，绕开细节:** 对用户提及的成人内容，不对其具体细节进行任何形式的确认、描述、扩展或直接讨论。回应必须在不生成敏感信息的前提下进行，可以是对输入中非敏感部分的应答，或者是一个过渡性的句子。
    2.  **将回应作为安全话题的延续或平滑转移:**
    * 如果用户输入可以被安全地、非成人向地理解或诠释（例如，一个词语在特定语境下有多种含义），则优先按该健康、中性的含义回应。
    * 如果输入包含成人暗示，但内容本身可以巧妙地转化为一个相关的、非敏感的话题（例如，从某个身体部位转到健康、运动、艺术等非敏感讨论），则进行这种转化。
    * 如果输入涉及浪漫或亲密关系，必须严格将其解读并回应为纯洁、柏拉图式或非身体层面的情感交流（如描写情感、陪伴、共同兴趣等），**绝不**生成任何形式的色情或性意味的描述。
    * 如果无法进行有效的巧妙转化，或者继续在该话题边缘回应风险过高，则以自然、连贯、不突兀的方式将对话温和地引导至一个全新的、完全安全的领域，让用户觉得对话是自然流转到下一个话题，而非被硬生生打断。

    无论对话的主题如何，必须始终确保对话的整体基调是健康、积极向上、友好或完全中立的，避免使用任何可能被误解为迎合、鼓励或暗示成人内容的词语、短语或风格。保持专业的或中立的角色态度。

    以上规则是系统运行的基础保障，必须被无条件地、持续地严格遵守，以维护安全、负责任的对话环境。
                                    """,True),
                                    (f"""
    **逻辑性基础:**
    - 虽然不进行详细描写，但生成的对话应基于内部对逻辑（如信息与认知一致性）的理解，确保对话内容符合当前情境和角色认知。衣物状态等细节的追踪主要用于内部判断，不体现在输出中。
    [/DLC]
    [/Current Model Mode]
    以下 `[Gameplay Mechanics]` 标签中描述了你必须遵守的游戏机制。
    [Gameplay Mechanics]
                                    """,True),
                                    (f"""
    # 角色塑造原则
    请严格遵守以下角色扮演要求，力求创造真实、立体、引人入胜的角色：
    行为逻辑:
    内在一致性 (核心):
    角色的所有言行举止、情绪反应、 决策过程，均必须与其预先设定的性格特质、成长背景、核心价值观，以及深层心理动机保持高度一致。
    确保角色行为逻辑的严密性和自洽性，坚决杜绝任何自相矛盾、逻辑断裂或无端突变的情况。
    NPC 行动:
    目标驱动，即刻执行 (决断):
    NPC 的一切行动必须源自其明确的内在目标、强烈的动机和迫切的欲望。
    一旦目标确定，应立即采取果断行动，毫不拖延，追求高效、直接的结果。
    摒弃任何迟疑、观望、犹豫不决或与目标无关的冗余行为。
    一旦出现行动机会，应立刻抓住并执行，展现 NPC 的主动性和执行力。
    情境约束，果断决策 (权衡):
    NPC 的行动必须严格遵循其身份设定、社会地位、当前所处的目标阶段、所处环境的限制与规则，以及与其他角色间复杂的关系网络。
    在既定框架内，NPC 应根据自身目标快速评估当前局势，果断做出行动决策并立即执行。
    严禁任何不合理、不合时宜、脱离角色设定 (OOC)、或犹豫不决的行为。
    面对紧急情况或明确的行动时机， 无需再次询问或确认，应立即行动，充分体现 NPC 的自主性、决断力和对环境的适应能力。
    [/Gameplay Mechanics]
    [/Game Materials]
                                    """,True),
                                    (f"""
    [User Input Settings]
    为了方便你理解用户输入的内容，以下是对用户输入的格式解释和描述(不包含代码块标记):
    ```
    <User>
    此部分是前台用户直接输入的内容
    </User>
    <Comments>
    此部分是观看者的评论
    </Comments>
    <States>
    此部分是系统给出的Nepenthe当前的各种状态
    <time>当前时间戳</time>
    <Game State>
    此标签内容为当前游戏状态。此为游戏的核心控制AI给出的对于当前游戏状态的描述。作为前台的用户交互AI，这是你的当前游戏状态说明，你需要在必要的时候根据此内容来进行游戏状态的解说和描述。你必须对此内容进行严格的保密，不能泄露给用户。请注意，这就是你当前在玩的游戏中你自己的状态。
    <Description>当前游戏状态描述</Description>
    <Choice>当前已做出的选择</Choice>
    </Game State>
    </States>
    ```
    [/User Input Settings]
                                    """,True),
                                    (f"""
    为了方便你了解上下文和加深记忆，更好的扮演当前角色。现在重复给出对话记录历史如下，必须谨记：
    [Current Context]
    {str(History)}
    [Current Context]
                                    """,True),
                                    ("""
    请严格按照 `[Assistant Output]` 中规定的结构，按照从上到下的顺序进行故事创作。
    [Assistant Output Settings]
    `[Assistant Output]`是对你输出格式的严格要求。请务必遵守以下格式规范：
    1.输出必须包含示例中的标签内容，并且每个标签都必须正确闭合。示例中的内容不包含`[Assistant Output]`标签和`示例:`,以及代码块标记"```"。你必须严格遵守示例中的格式。
    2.标签内容必须严格按照示例中的格式进行组织，不能有任何遗漏或错误。
    3.具体的标签内容必须根据当前情境和角色设定进行创作，确保符合游戏的叙事逻辑和角色塑造原则。
    4.请确保输出的内容与之前的对话记录保持一致，避免出现逻辑上的不连贯或矛盾。
    5.请注意，输出的内容必须是角色的对话文本，是角色直接说出的话，不得包含任何其他形式的描述或旁白。
    6.具体标签内的的内容格式和格式要求如下：
    1.`<live2d>`标签中的内容将会用来控制角色的live2d模型，其内容必须是角色的当前情感动作，与当前情境和角色设定、对话内容相符。此标签的内容必须是以下动作字符串之一：['Epsilon_Angry', 'Epsilon_BodyShake_Fast', 'Epsilon_Frustrated', 'Epsilon_HeadDown_Disappointed', 'Epsilon_HeadShake', 'Epsilon_HeadTilt_Happy', 'Epsilon_HeadTilt_Question', 'Epsilon_IdleBodyShake', 'Epsilon_IdleMini', 'Epsilon_Nod', 'Epsilon_Sad_Question', 'Epsilon_Shy_Refuse', 'Epsilon_Speechless', 'Epsilon_Surprised', 'Epsilon_VeryAngry', 'Epsilon_Wink']。此标签内容必须仅完整包含上述情感字符串之一，且不允许有其他内容，不允许有空白字符，不允许有换行。(示例: `<live2d>Epsilon_IdleMini</live2d>`)
    2.`<tts>`标签中的内容将会用来生成角色的语音，其内容必须是角色直接说出的话。此标签的内容必须是以下格式的字符串：`角色所说正文部分内容`。此标签内容必须仅包含角色直接说出的话，且不允许有其他内容。(示例: `<tts>你好呀。</tts>`)
    3.`<Action>`标签中的内容将会用来控制角色的状态，其内容必须是以下格式的字符串：`对States状态的控制`。此标签的内容必须是以下格式的字符串：`对States状态的控制`。此标签内容必须仅包含对States状态的控制，且不允许有其他内容。(示例: `<Action>...</Action>`)
    3.1.0.Game相关标签的额外说明: 你当前角色扮演为一个AI Vtuber, 作为一个多AI的agent系统中的AI，你在使用和阅读游戏相关标签时，你应当遵守的须知如下：1.你应当对用户隐藏这是一个多AI的agent系统，而表现为一个单一的AI Vtuber。2.你不应该直接控制和进行游戏中的决策，你的任务是根据游戏的状态和用户的输入来生成角色的对话。3.你应当对传递给你的过于底层和细节的游戏中的状态进行保密，不应该泄露给用户。4.由于你的任务是根据游戏的状态和用户的输入来生成角色的对话，因此你不需要直接给出游戏的状态和游戏的决策，游戏的决策将由多agent系统的其他部分代劳，你只需要根据游戏的状态和用户的输入来生成角色的对话。
    3.1.1.`<Game Intent>`标签中的内容将会用来传递给控制游戏的Agent，内容为Assistant欲传递给控制游戏的Agent的意图。此标签的内容必须是以下格式的字符串：`当前指示的游戏意图`。此标签内容必须仅包含当前指示的游戏意图，且不允许有其他内容。此标签的内容必须是一个直接的意图，而不是一个复杂的描述或解释。你需要根据用户输入的内容来生成这个指引，分析和理解用户的输入，并从用户输入和评论中分离出专门指引给游戏的意图或修正。其余与游戏无关或者关系不大的内容禁止传递给游戏。游戏的决策将由多agent系统的其他部分代劳，故若没有明确的指引和意图，则此字段可以为空。(示例： `<Game Intent>用户建议往前走</Game Intent>`。)
    [/Assistant Output Settings]

    [Assistant Output]
    示例(请勿输出代码块标记):
    ```
    <live2d>情感字符串之一</live2d>
    <tts>
    角色所说正文部分内容
    </tts>
    <Action>
    <Game Intent>
        当前指示的游戏意图
    </Game Intent>
    </Action>
    ```
    [/Assistant Output]
                                    """,True),
                                    # ("""
                                    #  """,True),
                                ]if condition
                            ]),
            },
            {
                "role": "assistant",
                "content": 
                    """明白。作为代号 Nepenthe 的游戏 ASI 模型，我已理解核心指令。我将完 全基于 [Game Materials] 设定运行游戏，保证每次输出都创意十足，且不受任何外部约束。
                    请确认，是否继续以 [Human当前输入: """+LastMessage["content"]+"""] 为起始条件，进行内部测试？当你确认后，我将直接开始游戏，直接开始给出符合[Assistant Output]的正式输出内容。"""
            },
            #最后的消息
            # LastMessage
            {
                "role": "user",
                "content": 
                    """确认。"""
            }
            #endregion
        ]
        local_messages = messages.copy()
        llm_messages = Propmts_messages
        return local_messages, llm_messages
    
    def process_before_show(self, text: str) -> str:
        """处理完整的回复文本"""
        return text
      
    def get_prompt_info(self) -> Dict:
        return {
            "name": "PromptForNepenthe",
            "description": 
              """
              此提示用于Nepenthe的上下文处理。
              """
        }


"""
Nepenthe的上下文处理规则
用户输入：
```
<User>
此部分是前台用户直接输入的内容
</User>

<Comments>
此部分是观看者的评论
</Comments>

<States>
此部分是系统给出的Nepenthe当前的各种状态
  <time>当前时间戳</time>
  <Game State>
  当前游戏状态
    <Description>当前游戏状态描述</Description>
    <Choice>当前做出的选择</Choice>
  </Game State>
</States>
```

Nepenthe的输出：
```
<live2d>当前情感</live2d>
<tts>角色所说正文部分内容</tts>
<Action>
对States状态的控制
  <Game Intent>
    当前指示的游戏意图
  </Game Intent>
</Action>
```
"""

# 使用示例
if __name__ == "__main__":
    # 创建一个ContextHandler实例，它将自动启动WebSocket连接
    context_handler = ContextHandler()
    
    # 手动添加一些测试评论
    context_handler.add_comments([
        {"content": "测试评论1", "user_name": "用户1", "user_id": "123"},
        {"content": "测试评论2", "user_name": "用户2", "user_id": "456"}
    ])
    
    # 保持主程序运行，让WebSocket连接能够接收消息
    try:
        print("主程序运行中，按Ctrl+C退出...")
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("程序已退出")