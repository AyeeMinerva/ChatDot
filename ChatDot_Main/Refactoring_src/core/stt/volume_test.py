"""
音量监测测试工具
用于测试麦克风音量和设置适当的阈值

使用方法:
1. 运行此脚本
2. 使用上下箭头键调整阈值
3. 说话，观察音量曲线
4. 找到合适的阈值后记下即可用于STT设置

按 'q' 退出
"""

import pyaudio
import numpy as np
import time
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
import matplotlib as mpl

# 设置中文字体为宋体
plt.rcParams['font.family'] = ['SimSun']  # 宋体
plt.rcParams['font.sans-serif'] = ['SimSun']  # 设置宋体优先
plt.rcParams['axes.unicode_minus'] = False  # 解决负号显示问题

def get_audio_volume(audio_data):
    """计算音频音量RMS值"""
    try:
        audio_array = np.frombuffer(audio_data, dtype=np.int16)
        if len(audio_array) == 0:
            return 0.0
        square_sum = np.mean(np.square(audio_array.astype(np.float64)))
        if square_sum <= 0:
            return 0.0
        return np.sqrt(square_sum)
    except Exception as e:
        print(f"计算音量出错: {e}")
        return 0.0

class VolumeMeter:
    """实时音量监测器"""
    
    def __init__(self, threshold=300, window_size=100):
        self.threshold = threshold
        self.window_size = window_size
        self.volumes = [0] * window_size
        self.times = list(range(window_size))
        self.above_threshold = [False] * window_size
        
        # 麦克风设置
        self.FORMAT = pyaudio.paInt16
        self.CHANNELS = 1
        self.RATE = 16000
        self.CHUNK = int(self.RATE / 10)  # 每100ms采样一次
        
        # PyAudio 对象
        self.p = pyaudio.PyAudio()
        self.stream = self.p.open(
            format=self.FORMAT,
            channels=self.CHANNELS,
            rate=self.RATE,
            input=True,
            frames_per_buffer=self.CHUNK
        )
        
        # 图表设置
        self.fig, self.ax = plt.subplots(figsize=(10, 6))
        self.line, = self.ax.plot(self.times, self.volumes, label='音量')
        self.threshold_line = self.ax.axhline(y=self.threshold, color='r', linestyle='-', label=f'阈值 ({self.threshold})')
        
        # 图表样式设置 - 使用宋体
        self.ax.set_title('实时音量监测', fontfamily='SimSun', fontsize=14)
        self.ax.set_xlabel('时间', fontfamily='SimSun', fontsize=12)
        self.ax.set_ylabel('音量', fontfamily='SimSun', fontsize=12)
        self.ax.set_ylim(0, 5000)
        self.ax.grid(True)
        self.ax.legend(loc='upper left', prop={'family': 'SimSun'})
        
        # 设置刻度标签字体
        for label in self.ax.get_xticklabels() + self.ax.get_yticklabels():
            label.set_fontfamily('SimSun')
        
        # 添加说明文本
        self.text = self.ax.text(0.02, 0.95, '', transform=self.ax.transAxes, 
                               verticalalignment='top', bbox=dict(boxstyle='round', alpha=0.2),
                               fontfamily='SimSun')
    
    def update_plot(self, frame):
        """更新图表"""
        # 读取音频数据
        data = self.stream.read(self.CHUNK, exception_on_overflow=False)
        
        # 计算音量
        volume = get_audio_volume(data)
        
        # 检查是否超过阈值
        is_above = volume > self.threshold
        
        # 更新数据
        self.volumes.pop(0)
        self.volumes.append(volume)
        self.above_threshold.pop(0)
        self.above_threshold.append(is_above)
        
        # 更新状态文本
        status = "检测到语音" if is_above else "静音"
        self.text.set_text(f"当前音量: {volume:.1f}\n状态: {status}")
        
        # 更新图表
        self.line.set_ydata(self.volumes)
        
        return self.line, self.threshold_line, self.text
    
    def set_threshold(self, threshold):
        """设置阈值"""
        self.threshold = threshold
        
        # 移除旧的阈值线并创建新的
        self.threshold_line.remove()
        self.threshold_line = self.ax.axhline(y=self.threshold, color='r', linestyle='-', 
                                            label=f'阈值 ({self.threshold})')
        
        # 更新图例
        self.ax.legend(loc='upper left', prop={'family': 'SimSun'})
    
    def run(self):
        """运行音量计"""
        print("\n=== 音量监测工具 ===")
        print("使用上下箭头键调整阈值，按 'q' 退出")
        print("建议在正常说话时，音量应该超过阈值，而在不说话时，音量应低于阈值")
        
        # 设置键盘事件
        def on_key(event):
            if event.key == 'up':
                self.set_threshold(self.threshold + 100)
                print(f"阈值增加到: {self.threshold}")
            elif event.key == 'down':
                self.set_threshold(max(100, self.threshold - 100))
                print(f"阈值减少到: {self.threshold}")
            elif event.key == 'q':
                plt.close()
                
        self.fig.canvas.mpl_connect('key_press_event', on_key)
        
        # 底部提示文本 - 使用宋体
        plt.figtext(0.5, 0.01, "按上下箭头调整阈值，按 'q' 退出", 
                   ha='center', fontsize=10, family='SimSun',
                   bbox=dict(boxstyle='round', alpha=0.1))
        
        # 创建动画
        ani = FuncAnimation(
            self.fig, self.update_plot, interval=100, 
            blit=False,  # 修改为False，因为我们动态更改图形元素
            save_count=self.window_size
        )
        
        plt.tight_layout()
        plt.show()
        
        print(f"\n最终选择的阈值: {self.threshold}")
        print("请将此阈值设置到STT模块中")
    
    def close(self):
        """关闭资源"""
        if hasattr(self, 'stream') and self.stream:
            self.stream.stop_stream()
            self.stream.close()
        if hasattr(self, 'p') and self.p:
            self.p.terminate()

def main():
    """主函数"""
    meter = None
    try:
        # 默认阈值
        threshold = 300
        
        # 允许用户输入初始阈值
        try:
            user_threshold = input("请输入初始阈值 (默认300): ")
            if user_threshold.strip():
                threshold = int(user_threshold)
        except:
            pass
            
        meter = VolumeMeter(threshold=threshold)
        meter.run()
    except KeyboardInterrupt:
        print("\n程序已退出")
    except Exception as e:
        print(f"发生错误: {e}")
        import traceback
        traceback.print_exc()  # 打印详细错误信息
    finally:
        if meter:
            meter.close()

if __name__ == "__main__":
    main()