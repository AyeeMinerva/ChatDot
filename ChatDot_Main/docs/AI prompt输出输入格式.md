# ChatDot-core AI格式控制

## 聊天及前台控制AI:
### 输入:
```
<user>
用户直接输入(或使用</stt>)
</user>

<comment>
外部弹幕/评论
</comment>

<States>
当前各种需要控制的状态
    <time>当前时间戳</time>
    <Game States>
        <Description>
        当前游戏具体状况的描述
        </Description>
        <Choice>
        当前做出的选择
        </Choice>
    </Game States>
</States>
```
### 输出:
```
<live2d>
情感字符串之一
</live2d>
<tts>
角色所说正文部分内容
</tts>
<Action>
    <Game Intent>
    游戏意图(尽可能为空)
    </Game Intent>
</Action>
```

## 游戏控制AI:
### 输出
```
<choice>
所选择的行动
</choice>
<Game Description Summary>
对当前游戏状态的总结和选择行动的简要说明
</Game Description Summary>
```