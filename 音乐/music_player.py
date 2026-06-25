
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
import os
from tkinter import filedialog, messagebox
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"
import pygame
import time
from threading import Thread

play_info_frame = None
PlayerApp = None
ost_name = ""

from 日志.advanced_logger import AdvancedLogger
logger = AdvancedLogger.get_logger(__name__)

music_dir = {
    "OST1": "HEAVEN_BURNS_RED_Original_Sound_Track_Vol1",
    "OST2": "HEAVEN_BURNS_RED_Original_Sound_Track_Vol2",
    "Love_Song_from_the_Water":"Love_Song_from_the_Water",
    "麻枝准_やなぎなぎ":"麻枝准_やなぎなぎ",
    "麻枝准_rionos":"麻枝准_rionos",
    "佐々木恵梨":"佐々木恵梨",
    "She_is_Legend":"She_is_Legend",
    "Stargazer":"Stargazer",
    "Summer_Pockets_Original_Sound_Track":"Summer_Pockets_Original_Sound_Track",
    "Summer_Pockets_REFLECTION_BLUE_Original_SoundTrack":"Summer_Pockets_REFLECTION_BLUE_Original_SoundTrack",
    "CLANNAD_Original_Sound_Track":"CLANNAD_Original_Sound_Track",
    "Rewrite_Original_Sound_Track":"Rewrite_Original_Sound_Track",
    "Inst_Test_Examples":"Inst_Test_Examples"
}


class FLACPlayerApp:
    def __init__(self, parent_frame, row, column):
        # 创建主框架
        self.frame = ttk.Frame(parent_frame)
        self.frame.grid(row=row, column=column, padx=10, pady=10, sticky="nsew")
        self.frame.grid_rowconfigure(0, weight=1)
        self.frame.grid_columnconfigure(0, weight=1)

        # 初始化音频系统
        pygame.mixer.init()

        self.current_file = None
        self.paused = False
        self.playing = False
        self.volume = 0.5
        self.duration = 0
        self.seeking = False  # 是否正在拖动进度条
        self.current_position = 0  # 当前播放位置
        self.seek_position = 0  # 寻找的位置
        self.seek_time = 0  # 寻找的时间点
        self.position_selected = False  # 标记是否通过进度条选择了位置

        self.loop_enabled = False

        # 创建UI
        self.create_widgets()

        # 进度更新线程
        self.update_thread = None
        self.running = True

        self.volume_thread = None

        # 窗口关闭时清理资源
        # self.frame.protocol("WM_DELETE_WINDOW", self.on_close)

    # 创建界面控件
    def create_widgets(self):

        file_frame = ttk.Frame(self.frame)
        file_frame.pack(pady=(0, 5), fill='x')
        self.file_label = ttk.Label(file_frame, text="未选择文件", width=50, anchor='w')
        self.file_label.pack(side="left", padx=5)

        # 进度条 - 使用Canvas实现更精确的点击跳转
        self.progress_frame = ttk.Frame(self.frame)
        self.progress_frame.pack(pady=10, fill='x', padx=20)

        # 实际进度显示
        self.progress_canvas = ttk.Canvas(self.progress_frame, height=20)
        self.progress_canvas.pack(fill='x')
        self.progress_canvas.update()
        width = self.progress_canvas.winfo_width()

        # 进度条背景
        self.progress_bg = self.progress_canvas.create_rectangle(0, 0, width, 20, fill='lightgray', outline='lightgray')
        # 进度条前景
        # self.progress_fg = self.progress_canvas.create_rectangle(0, 0, 0, 20, fill='blue', outline='blue')
        self.progress_fg = self.progress_canvas.create_rectangle(0, 0, 0, 20, fill='#858585', outline='#858585')
        
        # 绑定点击事件
        self.progress_canvas.bind("<Button-1>", self.on_progress_click)
        self.progress_canvas.bind("<B1-Motion>", self.on_progress_drag)
        self.progress_canvas.bind("<ButtonRelease-1>", self.on_progress_release)

        # 时间显示
        self.time_var = ttk.StringVar()
        self.time_var.set("00:00 / 00:00")
        time_label = ttk.Label(self.frame, textvariable=self.time_var)
        time_label.pack()

        # 控制按钮
        control_frame = ttk.Frame(self.frame)
        control_frame.pack(pady=10)

        self.play_btn = ttk.Button(control_frame, text="播放▶", command=self.play, state='disabled')
        self.play_btn.pack(side="left", padx=5)

        self.pause_btn = ttk.Button(control_frame, text="暂停⏸︎", command=self.pause, state='disabled')
        self.pause_btn.pack(side="left", padx=5)

        self.stop_btn = ttk.Button(control_frame, text="停止⏹︎", command=self.stop, state='disabled')
        self.stop_btn.pack(side="left", padx=5)

        #添加循环按钮
        self.loop_btn = ttk.Button(control_frame, text="循环◻", command=self.toggle_loop, state='disabled')
        self.loop_btn.pack(side="left", padx=5)

        # 音量控制
        volume_frame = ttk.Frame(self.frame)
        volume_frame.pack()
        ttk.Label(volume_frame, text="音量🔉").pack(side="left")
        self.volume_scale = ttk.Scale(volume_frame, from_=0, to=100, orient='horizontal',
                                     command=self.set_volume)
        self.volume_scale.set(50)  # 默认音量设为50%
        self.volume_scale.pack(side="left")

    # 选择音频文件
    def select_file(self):
        file_path = filedialog.askopenfilename(
            title="选择音频文件",
            filetypes=[("flac文件", "*.flac"), ("mp3文件", "*.mp3"), ("所有文件", "*.*")]
        )

        if file_path:
            self.load_file(file_path)

    # 加载音频文件
    def load_file(self, file_path):
        # print(f"加载{file_path}")
        try:
            pygame.mixer.music.load(file_path)
            self.current_file = file_path
            self.file_label.config(text=os.path.basename(file_path))
            # self.play_btn.config(state='normal')
            # self.loop_btn.config(state='normal')

            # 获取音频长度
            sound = pygame.mixer.Sound(file_path)
            self.duration = sound.get_length()
            self.current_position = 0
            self.seek_position = 0
            self.position_selected = False

            # 重置进度条和时间
            self.frame.after(0, lambda: (
                self.update_progress_display(0),
                self.update_time_display(0, self.duration),
                self.play_btn.config(state='normal'),
                self.loop_btn.config(state='normal')
            ))

            self.frame.update_idletasks()  # 强制更新UI

        except Exception as e:
            logger.error(f"无法加载文件: {e}")
            messagebox.showerror("错误", f"无法加载文件: {e}")


    # 循环切换方法
    def toggle_loop(self):
        self.loop_enabled = not self.loop_enabled
        self.loop_btn.config(text="循环🔁" if self.loop_enabled else "循环◻")

    # 播放音频
    def play(self):
        if self.current_file:
            self.start_progress_volume("up")
            time.sleep(0.5)
            # 循环播放时强制重置起点（针对单曲循环场景）
            if self.loop_enabled and self.current_position >= self.duration:
                self.current_position = 0  # 重置播放位置
                self.seek_time = time.time()  # 重置时间基准

            if self.paused:
                # 从暂停状态恢复播放
                pygame.mixer.music.unpause()
                self.paused = False
                self.seek_time = time.time()  # 更新seek_time
                # 如果有选定位置，从该位置开始播放
                if self.position_selected:
                    pygame.mixer.music.set_pos(self.seek_position)
                    self.current_position = self.seek_position
                    self.position_selected = False  # 重置位置选择标记
                # 精确同步进度条和时间显示
                self.sync_progress_and_time()
            else:
                # 停止当前播放
                pygame.mixer.music.stop()
                # 确定开始播放位置
                start_position = self.seek_position if self.position_selected else 0
                pygame.mixer.music.play()

                # 如果有选定位置，从该位置开始播放
                if self.position_selected:
                    pygame.mixer.music.set_pos(start_position)
                    self.current_position = start_position
                else:
                    self.current_position = 0

                self.seek_time = time.time()  # 记录开始时间点
                self.position_selected = False  # 重置位置选择标记
                self.seeking = False

                self.playing = True
                self.start_progress_update()

            # 使用 after(0) 确保 UI 更新在主线程执行
            self.frame.after(0, lambda: (
                self.play_btn.config(state='disabled'),
                self.pause_btn.config(state='normal'),
                self.stop_btn.config(state='normal')
            ))


    # 精确同步进度条和时间显示
    def sync_progress_and_time(self):
        current_pos = self.get_current_pos()
        progress_percent = (current_pos / self.duration) * 100
        self.update_progress_display(progress_percent)
        self.update_time_display(current_pos, self.duration)

    # 暂停播放
    def pause(self):
        if self.playing and not self.paused:
            self.start_progress_volume("down")
            time.sleep(0.5)
            pygame.mixer.music.pause()
            self.paused = True
            # 保存当前位置
            self.current_position = self.get_current_pos()
            self.seek_time = time.time()  # 更新seek_time
            self.play_btn.config(state='normal')
            self.pause_btn.config(state='disabled')

    # 停止播放
    def stop(self):
        self.running = False
        self.start_progress_volume("down")
        time.sleep(0.5)
        pygame.mixer.music.stop()
        # time.sleep(0.2)
        self.playing = False
        self.paused = False
        self.current_position = 0
        self.seek_position = 0
        self.position_selected = False

        # 使用 after(0) 确保 UI 更新在主线程执行
        self.frame.after(0, lambda: (
            self.update_progress_display(0),
            self.update_time_display(0, self.duration),
            self.play_btn.config(state='normal'),
            self.pause_btn.config(state='disabled'),
            self.stop_btn.config(state='disabled')
        ))

    # 设置音量
    def set_volume(self, val):
        self.volume = int(float(val)) / 100
        pygame.mixer.music.set_volume(self.volume)

    # 启动进度更新线程
    def start_progress_update(self):
        if self.update_thread and self.update_thread.is_alive():
            return

        self.running = True
        self.update_thread = Thread(target=self.update_progress, daemon=True)
        self.update_thread.start()

    # 获取当前实际播放位置，考虑到寻找操作
    def get_current_pos(self):
        if not self.playing or self.seeking:
            return self.current_position

        # 循环时强制以最新seek_time计算（修复时间累加错误）
        if self.loop_enabled and self.current_position >= self.duration:
            self.current_position = 0
            self.seek_time = time.time()

        elapsed_since_seek = time.time() - self.seek_time
        return min(self.current_position + elapsed_since_seek, self.duration)


    # 更新进度条和时间显示
    def update_progress(self):
        while self.playing and self.running:
            if not self.seeking and not self.paused:  # 只有在非拖动和非暂停状态下更新
                current_pos = self.get_current_pos()

                # 播放结束处理（区分循环/非循环）
                if current_pos >= self.duration - 0.5:  # 允许0.5秒误差
                    if self.loop_enabled:
                        # 重置播放起点并重启进度线程
                        self.frame.after(0, lambda: (
                            self.stop(),
                            self.current_position,  # 强制刷新变量
                            self.play(),  # 调用play触发重置
                            self.start_progress_update()  # 重启进度更新线程
                        ))
                    else:
                        self.frame.after(0, self.stop)
                    return  # 退出当前线程，避免重复计算

                progress_percent = (current_pos / self.duration) * 100
                progress_percent = max(0, min(100, progress_percent))

                if self.running:
                    # 使用after确保在主线程中更新UI
                    self.frame.after(0, lambda p=progress_percent, pos=current_pos: (
                        self.update_progress_display(p),
                        self.update_time_display(pos, self.duration)
                    ))

            time.sleep(0.1)

    # 更新进度条显示
    def update_progress_display(self, percent):
        canvas_width = self.progress_canvas.winfo_width()
        if canvas_width <= 1:  # 避免窗口初始化时的异常情况
            canvas_width = 420
        progress_width = (percent / 100) * canvas_width
        self.progress_canvas.coords(self.progress_fg, 0, 0, progress_width, 20)

    # 更新时间显示
    def update_time_display(self, current, total):
        current_m, current_s = divmod(int(current), 60)
        total_m, total_s = divmod(int(total), 60)
        self.time_var.set(f"{current_m:02d}:{current_s:02d} / {total_m:02d}:{total_s:02d}")

    # 点击进度条跳转
    def on_progress_click(self, event):
        if self.duration > 0 and self.current_file:
            # 计算点击位置对应的百分比和时间
            click_percent = (event.x / self.progress_canvas.winfo_width()) * 100
            click_percent = max(0, min(100, click_percent))
            self.seek_position = (click_percent / 100) * self.duration
            self.position_selected = True  # 标记用户选择了位置

            # 立即更新显示
            self.update_progress_display(click_percent)
            self.update_time_display(self.seek_position, self.duration)

            if self.playing and not self.paused:
                # 如果正在播放，则从新位置开始播放
                pygame.mixer.music.stop()
                pygame.mixer.music.play()
                pygame.mixer.music.set_pos(self.seek_position)
                self.current_position = self.seek_position
                self.seek_time = time.time()
            elif self.paused:
                # 如果是暂停状态，更新当前位置
                self.current_position = self.seek_position

    # 拖动进度条
    def on_progress_drag(self, event):
        if self.duration > 0 and self.current_file:
            self.seeking = True
            seek_percent = (event.x / self.progress_canvas.winfo_width()) * 100
            seek_percent = max(0, min(100, seek_percent))  # 限制在0-100之间
            self.seek_position = (seek_percent / 100) * self.duration
            self.position_selected = True  # 标记用户选择了位置

            # 更新显示但不实际跳转
            self.update_progress_display(seek_percent)
            self.update_time_display(self.seek_position, self.duration)

    # 进度条释放事件
    def on_progress_release(self, event):
        if self.duration > 0 and self.seeking and self.current_file:
            seek_percent = (event.x / self.progress_canvas.winfo_width()) * 100
            seek_percent = max(0, min(100, seek_percent))
            self.seek_position = (seek_percent / 100) * self.duration
            self.position_selected = True  # 标记用户选择了位置

            if self.playing and not self.paused:
                pygame.mixer.music.stop()
                pygame.mixer.music.play()
                pygame.mixer.music.set_pos(self.seek_position)
                self.current_position = self.seek_position
                self.seek_time = time.time()
            elif self.paused:
                # 如果是暂停状态，更新当前位置
                self.current_position = self.seek_position

            self.seeking = False

    # 窗口关闭时清理资源
    def on_close(self):
        self.running = False
        pygame.mixer.music.stop()
        pygame.mixer.quit()
        self.frame.destroy()

    # 清理资源
    def on_clean(self):
        self.running = False
        pygame.mixer.music.stop()
        pygame.mixer.quit()

    def gradient_volume_up(self):
        val = 0
        step = 10
        for i in range(5):
            val += step
            pygame.mixer.music.set_volume(val/100)
            time.sleep(0.1)
    def gradient_volume_down(self):
        val = 50
        step = 10
        for i in range(5):
            val -= step
            pygame.mixer.music.set_volume(val/100)
            time.sleep(0.1)
    # 启动音量更新线程
    def start_progress_volume(self, operate):
        if operate == "up":
            self.volume_thread = Thread(target=self.gradient_volume_up, daemon=True)
        else:
            self.volume_thread = Thread(target=self.gradient_volume_down, daemon=True)
        self.volume_thread.start()

