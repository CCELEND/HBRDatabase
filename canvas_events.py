
import tkinter as tk
from PIL import Image, ImageTk
from functools import partial
import cv2
import threading
import queue
import time
import platform

# 定义鼠标进入 Canvas 时的事件处理函数
def mouse_on_enter(event):
    # 获取触发事件的控件 设置光标为手型
    event.widget.config(cursor="hand2")  

# 定义鼠标离开 Canvas 时的事件处理函数
def mouse_on_leave(event):
    # 获取触发事件的控件 恢复默认光标
    event.widget.config(cursor="")

# 绑定鼠标进入和离开事件到 Canvas
def mouse_bind_canvas_events(canvas):
    canvas.bind("<Enter>", mouse_on_enter)
    canvas.bind("<Leave>", mouse_on_leave) 

# 显示边框
def mouse_on_enter_frame(event):
    event.widget.config(highlightbackground="blue", highlightthickness=2)  # 鼠标进入时显示边框

def mouse_on_leave_frame(event):
    event.widget.config(highlightbackground="SystemButtonFace", highlightthickness=0)   # 鼠标离开时隐藏边框gray

# 绑定鼠标进入和离开事件到 Canvas
def mouse_frame_bind_canvas_events(canvas):
    canvas.bind("<Enter>", mouse_on_enter_frame)
    canvas.bind("<Leave>", mouse_on_leave_frame) 

# 右键绑定 动态调整被绑定函数参数并传入
def right_click_bind_canvas_events(canvas, right_click_handler=None, **kwargs):
    # 为 Canvas 绑定事件
    if right_click_handler:
        # 使用 partial 来预填充所有额外的参数
        wrapped_handler = partial(right_click_handler, **kwargs)
        canvas.bind("<Button-3>", wrapped_handler)


# 单击绑定 动态调整被绑定函数参数并传入
def bind_canvas_events(canvas, click_handler=None, **kwargs):
    # 为 Canvas 绑定事件
    if click_handler:
        # 使用 partial 来预填充所有额外的参数
        wrapped_handler = partial(click_handler, **kwargs)
        canvas.bind("<Button-1>", wrapped_handler)


# 双击绑定 动态调整被绑定函数参数并传入
def double_click_bind_canvas_events(canvas, double_click_handler=None, **kwargs):
    # 为 Canvas 绑定事件
    if double_click_handler:
        # 使用 partial 来预填充所有额外的参数
        wrapped_handler = partial(double_click_handler, **kwargs)
        canvas.bind("<Double-Button-1>", wrapped_handler)


# 三击绑定 动态调整被绑定函数参数并传入
def triple_click_bind_canvas_events(canvas, triple_click_handler=None, **kwargs):
    # 为 Canvas 绑定事件
    if triple_click_handler:
        # 使用 partial 来预填充所有额外的参数
        wrapped_handler = partial(triple_click_handler, **kwargs)
        canvas.bind("<Triple-Button-1>", wrapped_handler)

# 获取图片对象
image_refs = {}
def get_photo(img_path, img_resize):
    # 创建唯一的键，由图片路径和加载大小决定
    unique_key = f"{img_path}_{img_resize}"

    # 如果图片已经被加载，则重用，否则加载新图片
    if unique_key in image_refs:
        photo = image_refs[unique_key]
        # print(f"复用：{img_path}")
    else:
        # print(img_path)
        image = Image.open(img_path)
        # 调整图片大小
        image = image.resize(img_resize, Image.LANCZOS)
        
        photo = ImageTk.PhotoImage(image)
        # 存储图片引用，防止被垃圾回收
        image_refs[unique_key] = photo

    return photo

# 创建图片 canvas
def create_canvas_with_image(parent_frame, 
    photo,
    canvas_width, canvas_height, 
    create_image_x, create_image_y, 
    row, column, rowspan=1, columnspan=1, padx=5, pady=5):

    # 创建 Canvas 并显示图片
    canvas = tk.Canvas(parent_frame, width=canvas_width, height=canvas_height)
    canvas.create_image(create_image_x, create_image_y, anchor="nw", image=photo)
    canvas.grid(
        row=row, column=column, 
        rowspan=rowspan, columnspan=columnspan, 
        sticky="nsew", 
        padx=padx, pady=pady)

    return canvas

# 图片填满窗口，不保持宽高比
class AutoResizeBackgroundNOAspectRatio:
    def __init__(self, parent_frame, image_path):
        self.root = parent_frame
        self.image_path = image_path

        # 加载原始图片
        self.original_image = Image.open(self.image_path)
        self.image_tk = ImageTk.PhotoImage(self.original_image)

        # 创建 Canvas 作为背景容器
        self.canvas = tk.Canvas(parent_frame)
        self.canvas.grid(row=0, column=0, columnspan=2, sticky="nsew")

        # 在 Canvas 上显示图片
        self.bg_image = self.canvas.create_image(0, 0, anchor="nw", image=self.image_tk)

        # 绑定窗口大小变化事件
        self.canvas.bind("<Configure>", self.resize_background)

    # 调整背景图片大小以完全填满窗口
    def resize_background(self, event):
        # 获取窗口的新大小
        new_width = event.width
        new_height = event.height

        # 直接调整图片大小以适应窗口
        resized_image = self.original_image.resize((new_width, new_height), Image.LANCZOS)
        self.image_tk = ImageTk.PhotoImage(resized_image)

        # 更新 Canvas 上的图片
        self.canvas.itemconfig(self.bg_image, image=self.image_tk)

        # 调整 Canvas 的大小以适应窗口
        self.canvas.config(width=new_width, height=new_height)


# 限定高度，保持宽高比不变，默认留白70
class ArtworkDisplayerHeight:
    def __init__(self, parent_frame, artwork_path, target_height, padding=70, opacity="100%"):
        self.padding = padding  # 留白大小
        self.parent_frame = parent_frame
        self.artwork_path = artwork_path
        self.target_height = target_height  # 传入的目标高度

        # 将透明度百分比转换为灰度值（0-255）
        opacity_percentage = int(opacity.strip('%')) / 100
        self.gray_value = int(opacity_percentage * 255)

        # 加载图片并调整大小
        self.load_and_resize_image()

        # 计算 Canvas 的宽度（图片宽度 + 左右留白）
        self.canvas_width = self.target_width + 2 * self.padding  # 左右各加 70 像素

        # 创建 Canvas 用于显示图片
        self.canvas = tk.Canvas(parent_frame, width=self.canvas_width, height=self.target_height)
        self.canvas.pack()

        # 在 Canvas 上显示图片
        self.display_image()

    # 加载图片并调整大小，保持宽高比
    def load_and_resize_image(self):
        # 打开图片
        self.original_image = Image.open(self.artwork_path)

        # 获取原始图片的宽度和高度
        original_width, original_height = self.original_image.size

        # 计算调整后的宽度，保持宽高比
        self.target_width = int(original_width * (self.target_height / original_height))

        # 调整图片大小
        self.resized_image = self.original_image.resize(
            (self.target_width, self.target_height), Image.LANCZOS
        )

        if self.gray_value != 255:
            # 生成一个透明度遮罩层
            mask = Image.new('L', self.resized_image.size, self.gray_value)  # 'L' 表示灰度图
            self.resized_image.putalpha(mask)

        # 将图片转换为 Tkinter 可用的格式
        self.tk_image = ImageTk.PhotoImage(self.resized_image)

    # 在 Canvas 上显示图片
    def display_image(self):
        # 计算图片的水平偏移量（居中显示）
        x_offset = (self.canvas_width - self.target_width) // 2
        # y_offset = (self.canvas_height - self.target_height) // 2

        # 在 Canvas 上显示图片
        self.canvas.create_image(x_offset, 0, anchor=tk.NW, image=self.tk_image)
        self.canvas.image = self.tk_image  # 保持引用，避免被垃圾回收

    def destroy(self):
        # 销毁 Canvas
        self.canvas.destroy()
        # 释放图片资源
        self.tk_image = None
        # 如果需要，也可以关闭原始图片
        self.original_image.close()


# webp 静态图显示
class ArtworkDisplayer:
    def __init__(self, parent_frame, artwork_path):
        self.parent_frame = parent_frame
        self.artwork_path = artwork_path

        # 目标分辨率
        self.target_width = 1366
        self.target_height = 768

        # 加载图片并调整大小
        self.load_and_resize_image()

        # 创建 Canvas 用于显示图片
        self.canvas = tk.Canvas(parent_frame, width=self.target_width, height=self.target_height)
        self.canvas.pack()

        # 在 Canvas 上显示图片
        self.display_image()

    # 加载图片并调整大小为 1366x768
    def load_and_resize_image(self):
        # 打开图片
        self.original_image = Image.open(self.artwork_path)

        # 调整图片大小
        self.resized_image = self.original_image.resize(
            (self.target_width, self.target_height), Image.LANCZOS
        )

        # 将图片转换为 Tkinter 可用的格式
        self.tk_image = ImageTk.PhotoImage(self.resized_image)

    # 在 Canvas 上显示图片
    def display_image(self):
        self.canvas.create_image(0, 0, anchor=tk.NW, image=self.tk_image)
        self.canvas.image = self.tk_image

# webm 动画显示
class VideoPlayer:
    def __init__(self, parent_frame, video_path):
        self.root = parent_frame
        self.video_path = video_path

        # 打开视频文件
        self.cap = cv2.VideoCapture(video_path)
        if not self.cap.isOpened():
            raise ValueError("无法打开视频文件")

        # 目标分辨率
        self.target_width = 1366
        self.target_height = 768

        # 创建 Canvas 用于显示视频
        self.canvas = tk.Canvas(parent_frame, width=self.target_width, height=self.target_height)
        self.canvas.pack()

        # 初始化视频帧
        self.update_frame()

    def update_frame(self):
        # 读取视频帧
        ret, frame = self.cap.read()
        if ret:
            # 将帧从 BGR 转换为 RGB
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

            # 调整帧的大小为目标分辨率
            frame = cv2.resize(frame, (self.target_width, self.target_height))

            # 将帧转换为 PIL 图像
            self.photo = ImageTk.PhotoImage(image=Image.fromarray(frame))

            # 在 Canvas 上显示帧
            self.canvas.create_image(0, 0, anchor=tk.NW, image=self.photo)

            # 每隔 25 毫秒更新一帧（约 40 FPS）
            self.root.after(25, self.update_frame)
        else:
            # 如果视频播放完毕，重置到开头并重新播放
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            self.update_frame()

    def release(self):
        # 释放视频资源
        self.cap.release()


class ThreadVideoPlayer:
    def __init__(self, parent_frame, video_path):
        self.root = parent_frame
        self.video_path = video_path

        # 打开视频文件
        self.cap = cv2.VideoCapture(video_path)
        if not self.cap.isOpened():
            raise ValueError("无法打开视频文件")

        # 目标分辨率
        self.target_width = 1366
        self.target_height = 768

        # 创建 Label 用于显示视频
        self.label = tk.Label(parent_frame)
        self.label.pack()

        # 初始化视频帧
        self.update_frame()

    def update_frame(self):
        def frame_loop():
            while True:
                ret, frame = self.cap.read()
                if ret:
                    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    frame = cv2.resize(frame, (self.target_width, self.target_height))
                    photo = ImageTk.PhotoImage(image=Image.fromarray(frame))
                    frame_queue.put(photo)  # 将帧放入队列
                else:
                    self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                time.sleep(0.04)  # 控制帧率

        def update_gui():
            try:
                photo = frame_queue.get_nowait()
                self.label.config(image=photo)
                self.label.image = photo  # 保持引用
            except queue.Empty:
                pass
            self.root.after(10, update_gui)  # 每 10 毫秒检查一次队列

        # 启动线程
        frame_queue = queue.Queue()
        threading.Thread(target=frame_loop, daemon=True).start()
        self.root.after(10, update_gui)  # 启动 GUI 更新循环

    def release(self):
        # 释放视频资源
        self.cap.release()


class GPUVideoPlayer:
    def __init__(self, parent_frame, video_path):
        self.root = parent_frame
        self.video_path = video_path

        # 打开视频文件
        self.cap = cv2.VideoCapture(video_path)
        if not self.cap.isOpened():
            raise ValueError("无法打开视频文件")

        # 目标分辨率
        self.target_width = 1366
        self.target_height = 768

        # 创建 Label 用于显示视频
        self.label = tk.Label(parent_frame)
        self.label.pack()

        # 初始化视频帧
        self.update_frame()

    def update_frame(self):
        def frame_loop():
            # 创建 CUDA 加速的帧处理管道
            gpu_frame = cv2.cuda_GpuMat()  # 创建 GPU 矩阵

            while True:
                ret, frame = self.cap.read()
                if ret:
                    # 将帧上传到 GPU
                    gpu_frame.upload(frame)

                    # 在 GPU 上进行颜色空间转换
                    gpu_frame = cv2.cuda.cvtColor(gpu_frame, cv2.COLOR_BGR2RGB)

                    # 在 GPU 上调整帧大小
                    gpu_frame = cv2.cuda.resize(gpu_frame, (self.target_width, self.target_height))

                    # 将帧下载回 CPU
                    frame = gpu_frame.download()

                    # 将帧转换为 Tkinter 可用的格式
                    photo = ImageTk.PhotoImage(image=Image.fromarray(frame))
                    frame_queue.put(photo)  # 将帧放入队列
                else:
                    self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                time.sleep(0.04)  # 控制帧率

        def update_gui():
            try:
                photo = frame_queue.get_nowait()
                self.label.config(image=photo)
                self.label.image = photo  # 保持引用
            except queue.Empty:
                pass
            self.root.after(10, update_gui)  # 每 10 毫秒检查一次队列

        # 启动线程
        frame_queue = queue.Queue()
        threading.Thread(target=frame_loop, daemon=True).start()
        self.root.after(10, update_gui)  # 启动 GUI 更新循环

    def release(self):
        # 释放视频资源
        self.cap.release()

# 限定高度，保持宽高比不变，默认留白70
class ArtworkDisplayerHeight2:
    def __init__(self, parent_frame, artwork_path, target_height, padding=70):
        self.padding = padding  # 留白大小
        self.parent_frame = parent_frame
        self.artwork_path = artwork_path
        self.target_height = target_height  # 传入的目标高度

        # 加载图片并调整大小
        self.load_and_resize_image()

        # 计算 Canvas 的宽度（图片宽度 + 左右留白）
        self.canvas_width = self.target_width + 2 * self.padding
        self.canvas_height = self.target_height + 2 * self.padding

        # 创建 Canvas 用于显示图片
        self.canvas = tk.Canvas(parent_frame, width=self.canvas_width, height=self.canvas_height)
        self.canvas.pack()

        # 在 Canvas 上显示图片
        self.display_image()

    # 加载图片并调整大小，保持宽高比
    def load_and_resize_image(self):
        # 打开图片
        self.original_image = Image.open(self.artwork_path)

        # 获取原始图片的宽度和高度
        original_width, original_height = self.original_image.size

        # 计算调整后的宽度，保持宽高比
        self.target_width = int(original_width * (self.target_height / original_height))

        # 调整图片大小
        self.resized_image = self.original_image.resize(
            (self.target_width, self.target_height), Image.LANCZOS
        )

        # 将图片转换为 Tkinter 可用的格式
        self.tk_image = ImageTk.PhotoImage(self.resized_image)

    # 在 Canvas 上显示图片
    def display_image(self):
        # 计算图片的水平偏移量（居中显示）
        x_offset = (self.canvas_width - self.target_width) // 2
        y_offset = (self.canvas_height - self.target_height) // 2

        # 在 Canvas 上显示图片
        self.canvas.create_image(x_offset, y_offset, anchor=tk.NW, image=self.tk_image)
        self.canvas.image = self.tk_image  # 保持引用，避免被垃圾回收


# 显示图片，根据宽度调整，加入滚动条
class ImageViewerWithScrollbar:
    def __init__(self, parent_frame, parent_width, parent_height, image_path):
        # 初始化
        self.parent_frame = parent_frame
        self.parent_width = parent_width
        self.parent_height = parent_height
        self.image_path = image_path

        # 打开图片
        self.image = Image.open(self.image_path)
        self.original_width, self.original_height = self.image.size

        # 将图片转换为 Tkinter 可用的格式
        self.tk_image = ImageTk.PhotoImage(self.image)

        # 创建 Canvas
        self.canvas = tk.Canvas(self.parent_frame, width=self.parent_width, height=self.parent_height)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # 在 Canvas 上显示图片
        self.image_id = self.canvas.create_image(0, 0, anchor=tk.NW, image=self.tk_image)

        # 设置 Canvas 的滚动区域
        self.canvas.config(scrollregion=(0, 0, self.original_width, self.original_height))

        # 创建垂直滚动条
        self.v_scrollbar = tk.Scrollbar(self.parent_frame, orient=tk.VERTICAL, command=self.canvas.yview)
        self.v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # 绑定 Canvas 和滚动条
        self.canvas.config(yscrollcommand=self.v_scrollbar.set)

        # 保持图片引用，避免被垃圾回收
        self.canvas.image = self.tk_image

        # 记录上一次的窗口大小
        self.last_width = parent_width
        self.last_height = parent_height

        # 绑定窗口大小变化事件（防抖处理）
        self.resize_timeout = None
        self.parent_frame.bind("<Configure>", self.on_resize)

        # 绑定鼠标滚轮事件
        self.bind_mouse_wheel_events()

        # 初始化大小
        self.resize_image()

    # 防抖处理窗口大小变化事件
    def on_resize(self, event):
        # 过滤异常值（例如窗口最小化时的宽度和高度）
        if event.width < 50 or event.height < 50:
            return

        # 检查窗口大小是否真的发生了变化
        if event.width != self.last_width or event.height != self.last_height:
            self.last_width = event.width
            self.last_height = event.height

            # 防抖处理
            if self.resize_timeout:
                self.parent_frame.after_cancel(self.resize_timeout)
            self.resize_timeout = self.parent_frame.after(200, self.resize_image)

    # 调整图片大小以适应父窗口宽度，并保持宽高比
    def resize_image(self):
        # 获取当前父容器的宽度（减去滚动条的宽度）
        scrollbar_width = self.v_scrollbar.winfo_width()
        new_width = self.parent_frame.winfo_width() - scrollbar_width

        # 如果滚动条未显示，宽度不需要减去滚动条宽度
        if not self.v_scrollbar.winfo_ismapped():
            new_width = self.parent_frame.winfo_width()

        # 计算新的高度，保持宽高比
        new_height = int(self.original_height * (new_width / self.original_width))

        # 调整图片大小
        resized_image = self.image.resize((new_width, new_height), Image.LANCZOS)
        self.resized_tk_image = ImageTk.PhotoImage(resized_image)

        # 更新 Canvas 上的图片
        self.canvas.itemconfig(self.image_id, image=self.resized_tk_image)
        self.canvas.image = self.resized_tk_image  # 保持引用，避免被垃圾回收

        # 设置 Canvas 的滚动区域
        self.canvas.config(scrollregion=(0, 0, new_width, new_height))

    # 处理鼠标滚轮事件
    def on_mouse_wheel(self, event):
        if platform.system() == "Windows":
            self.canvas.yview_scroll(-1 * (event.delta // 120), "units")  # Windows 的滚轮事件
        elif platform.system() == "Darwin":  # macOS
            self.canvas.yview_scroll(-1 * event.delta, "units")
        else:  # Linux
            if event.num == 4:
                self.canvas.yview_scroll(-1, "units")
            elif event.num == 5:
                self.canvas.yview_scroll(1, "units")

    # 绑定鼠标滚轮事件到 Canvas
    def bind_mouse_wheel_events(self):
        if platform.system() == "Windows":
            self.canvas.bind("<MouseWheel>", self.on_mouse_wheel)
        elif platform.system() == "Darwin":  # macOS
            self.canvas.bind("<MouseWheel>", self.on_mouse_wheel)
        else:  # Linux
            self.canvas.bind("<Button-4>", self.on_mouse_wheel)
            self.canvas.bind("<Button-5>", self.on_mouse_wheel)

    # 手动释放资源
    def destroy(self):
        self.canvas.delete("all")  # 删除 Canvas 上的所有内容
        self.canvas.image = None  # 释放图片引用
        self.canvas.destroy()  # 销毁 Canvas
        self.v_scrollbar.destroy()  # 销毁滚动条


# 显示动图，根据宽度调整，加入滚动条
class VideoPlayerWithScrollbar:
    def __init__(self, parent_frame, parent_width, parent_height, video_path):
        self.parent_frame = parent_frame
        self.parent_width = parent_width
        self.parent_height = parent_height
        self.video_path = video_path

        # 打开视频文件
        self.cap = cv2.VideoCapture(video_path)
        if not self.cap.isOpened():
            raise ValueError("无法打开视频文件")

        # 获取视频的原始宽度和高度
        self.original_width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.original_height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

        # 创建 Canvas
        self.canvas = tk.Canvas(self.parent_frame, width=self.parent_width, height=self.parent_height)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # 创建垂直滚动条
        self.v_scrollbar = tk.Scrollbar(self.parent_frame, orient=tk.VERTICAL, command=self.canvas.yview)
        self.v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # 绑定 Canvas 和滚动条
        self.canvas.config(yscrollcommand=self.v_scrollbar.set)

        # 记录上一次的窗口大小
        self.last_width = parent_width
        self.last_height = parent_height

        # 绑定窗口大小变化事件（防抖处理）
        self.resize_timeout = None
        self.parent_frame.bind("<Configure>", self.on_resize)

        # 绑定鼠标滚轮事件
        self.bind_mouse_wheel_events()

        # 初始化视频帧
        self.is_paused = False  # 是否暂停播放
        self.timer = None  # 定时器
        # self.fps = self.cap.get(cv2.CAP_PROP_FPS)  # 获取视频的帧率
        self.frame_delay = 25 #int(1000 / self.fps)  # 每帧的延迟时间（毫秒）

        # 开始播放
        self.start_playback()

    # 防抖处理窗口大小变化事件
    def on_resize(self, event):
        # 过滤异常值（例如窗口最小化时的宽度和高度）
        if event.width < 50 or event.height < 50:
            return

        # 检查窗口大小是否真的发生了变化
        if event.width != self.last_width or event.height != self.last_height:
            self.last_width = event.width
            self.last_height = event.height

            # 暂停播放
            self.pause_playback()

            # 防抖处理
            if self.resize_timeout:
                self.parent_frame.after_cancel(self.resize_timeout)
            self.resize_timeout = self.parent_frame.after(200, self.on_resize_complete)

    # 窗口大小调整完成后继续播放
    def on_resize_complete(self):
        # 继续播放
        self.resume_playback()

    # 开始播放
    def start_playback(self):
        self.is_paused = False
        self.update_frame()

    # 暂停播放
    def pause_playback(self):
        self.is_paused = True
        if self.timer:
            self.parent_frame.after_cancel(self.timer)
            self.timer = None

    # 继续播放
    def resume_playback(self):
        if self.is_paused:
            self.is_paused = False
            self.update_frame()

    # 更新视频帧
    def update_frame(self):
        if self.is_paused:
            return  # 如果暂停播放，直接返回

        # 读取视频帧
        ret, frame = self.cap.read()
        if ret:
            # 将帧从 BGR 转换为 RGB
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

            # 获取当前父容器的宽度（减去滚动条的宽度）
            scrollbar_width = self.v_scrollbar.winfo_width()
            new_width = self.parent_frame.winfo_width() - scrollbar_width

            # 如果滚动条未显示，宽度不需要减去滚动条宽度
            if not self.v_scrollbar.winfo_ismapped():
                new_width = self.parent_frame.winfo_width()

            # 计算新的高度，保持视频的宽高比
            new_height = int(self.original_height * (new_width / self.original_width))

            # 调整帧的大小
            frame = cv2.resize(frame, (new_width, new_height))

            # 将帧转换为 PIL 图像
            self.photo = ImageTk.PhotoImage(image=Image.fromarray(frame))

            # 在 Canvas 上显示帧
            self.canvas.create_image(0, 0, anchor=tk.NW, image=self.photo)

            # 设置 Canvas 的滚动区域
            self.canvas.config(scrollregion=(0, 0, new_width, new_height))

            # 设置定时器，更新下一帧
            self.timer = self.parent_frame.after(self.frame_delay, self.update_frame)
        else:
            # 如果视频播放完毕，重置到开头并重新播放
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            self.update_frame()

    # 处理鼠标滚轮事件
    def on_mouse_wheel(self, event):
        if platform.system() == "Windows":
            self.canvas.yview_scroll(-1 * (event.delta // 120), "units")  # Windows 的滚轮事件
        elif platform.system() == "Darwin":  # macOS
            self.canvas.yview_scroll(-1 * event.delta, "units")
        else:  # Linux
            if event.num == 4:
                self.canvas.yview_scroll(-1, "units")
            elif event.num == 5:
                self.canvas.yview_scroll(1, "units")

    # 绑定鼠标滚轮事件到 Canvas
    def bind_mouse_wheel_events(self):
        if platform.system() == "Windows":
            self.canvas.bind("<MouseWheel>", self.on_mouse_wheel)
        elif platform.system() == "Darwin":  # macOS
            self.canvas.bind("<MouseWheel>", self.on_mouse_wheel)
        else:  # Linux
            self.canvas.bind("<Button-4>", self.on_mouse_wheel)
            self.canvas.bind("<Button-5>", self.on_mouse_wheel)

    def destroy(self):
        self.pause_playback()  # 暂停播放
        self.canvas.delete("all")  # 删除 Canvas 上的所有内容
        self.canvas.image = None  # 释放图片引用
        self.canvas.destroy()  # 销毁 Canvas
        self.v_scrollbar.destroy()  # 销毁滚动条
        # 释放视频资源
        self.cap.release()


# 显示图片，根据宽度调整，加入滚动条，可调节透明
class ImageViewerWithScrollbarOpacity:
    def __init__(self, parent_frame, parent_width, parent_height, image_path, opacity):
        # 初始化
        self.parent_frame = parent_frame
        self.parent_width = parent_width
        self.parent_height = parent_height
        self.image_path = image_path

        # 将透明度百分比转换为灰度值（0-255）
        opacity_percentage = int(opacity.strip('%')) / 100
        self.gray_value = int(opacity_percentage * 255)

        # 打开图片
        self.image = Image.open(self.image_path)
        self.original_width, self.original_height = self.image.size

        # 将图片转换为 Tkinter 可用的格式
        self.tk_image = ImageTk.PhotoImage(self.image)

        # 创建 Canvas
        self.canvas = tk.Canvas(self.parent_frame, width=self.parent_width, height=self.parent_height)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # 在 Canvas 上显示图片
        self.image_id = self.canvas.create_image(0, 0, anchor=tk.NW, image=self.tk_image)

        # 设置 Canvas 的滚动区域
        self.canvas.config(scrollregion=(0, 0, self.original_width, self.original_height))

        # 创建垂直滚动条
        self.v_scrollbar = tk.Scrollbar(self.parent_frame, orient=tk.VERTICAL, command=self.canvas.yview)
        self.v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # 绑定 Canvas 和滚动条
        self.canvas.config(yscrollcommand=self.v_scrollbar.set)

        # 保持图片引用，避免被垃圾回收
        self.canvas.image = self.tk_image

        # 记录上一次的窗口大小
        self.last_width = parent_width
        self.last_height = parent_height

        # 绑定窗口大小变化事件（防抖处理）
        self.resize_timeout = None
        self.parent_frame.bind("<Configure>", self.on_resize)

        # 绑定鼠标滚轮事件
        self.bind_mouse_wheel_events()

        # 初始化大小
        self.resize_image()

    # 防抖处理窗口大小变化事件
    def on_resize(self, event):
        # 过滤异常值（例如窗口最小化时的宽度和高度）
        if event.width < 50 or event.height < 50:
            return

        # 检查窗口大小是否真的发生了变化
        if event.width != self.last_width or event.height != self.last_height:
            self.last_width = event.width
            self.last_height = event.height

            # 防抖处理
            if self.resize_timeout:
                self.parent_frame.after_cancel(self.resize_timeout)
            self.resize_timeout = self.parent_frame.after(200, self.resize_image)

    # 调整图片大小以适应父窗口宽度，并保持宽高比
    def resize_image(self):
        # 获取当前父容器的宽度（减去滚动条的宽度）
        scrollbar_width = self.v_scrollbar.winfo_width()
        new_width = self.parent_frame.winfo_width() - scrollbar_width

        # 如果滚动条未显示，宽度不需要减去滚动条宽度
        if not self.v_scrollbar.winfo_ismapped():
            new_width = self.parent_frame.winfo_width()

        # 计算新的高度，保持宽高比
        new_height = int(self.original_height * (new_width / self.original_width))

        # 调整图片大小
        resized_image = self.image.resize((new_width, new_height), Image.LANCZOS)

        # 生成一个透明度遮罩层
        mask = Image.new('L', resized_image.size, self.gray_value)  # 'L' 表示灰度图
        resized_image.putalpha(mask)

        self.resized_tk_image = ImageTk.PhotoImage(resized_image)

        # 更新 Canvas 上的图片
        self.canvas.itemconfig(self.image_id, image=self.resized_tk_image)
        self.canvas.image = self.resized_tk_image  # 保持引用，避免被垃圾回收

        # 设置 Canvas 的滚动区域
        self.canvas.config(scrollregion=(0, 0, new_width, new_height))

    # 处理鼠标滚轮事件
    def on_mouse_wheel(self, event):
        if platform.system() == "Windows":
            self.canvas.yview_scroll(-1 * (event.delta // 120), "units")  # Windows 的滚轮事件
        elif platform.system() == "Darwin":  # macOS
            self.canvas.yview_scroll(-1 * event.delta, "units")
        else:  # Linux
            if event.num == 4:
                self.canvas.yview_scroll(-1, "units")
            elif event.num == 5:
                self.canvas.yview_scroll(1, "units")

    # 绑定鼠标滚轮事件到 Canvas
    def bind_mouse_wheel_events(self):
        if platform.system() == "Windows":
            self.canvas.bind("<MouseWheel>", self.on_mouse_wheel)
        elif platform.system() == "Darwin":  # macOS
            self.canvas.bind("<MouseWheel>", self.on_mouse_wheel)
        else:  # Linux
            self.canvas.bind("<Button-4>", self.on_mouse_wheel)
            self.canvas.bind("<Button-5>", self.on_mouse_wheel)

    # 手动释放资源
    def destroy(self):
        self.canvas.delete("all")  # 删除 Canvas 上的所有内容
        self.canvas.image = None  # 释放图片引用
        self.canvas.destroy()  # 销毁 Canvas
        self.v_scrollbar.destroy()  # 销毁滚动条