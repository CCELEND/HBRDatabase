import cv2
import numpy as np
import tkinter as tk
from tkinter import filedialog, messagebox
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from PIL import Image, ImageTk
import platform
import tempfile
import os

# 创建一个新窗口（子窗口），使用 geometry 设置大小和位置
def creat_Toplevel(title: str, width=1366, height=769, x=300, y=120) -> ttk.Toplevel:
    if not isinstance(title, str):
        raise TypeError("title参数必须是字符串类型")
    for param, name in [(width, "width"), (height, "height"), (x, "x"), (y, "y")]:
        if param is not None and not isinstance(param, int):
            raise TypeError(f"{name}参数必须是整数类型或None")

    new_window = ttk.Toplevel(title=title)
    # 设置大小和位置
    if width is not None and height is not None:
        new_window.geometry(f"{width}x{height}+{x}+{y}")
    elif width is not None:
        # 只设置宽度，高度保持默认
        new_window.geometry(f"{width}x{new_window.winfo_reqheight()}+{x}+{y}")
    elif height is not None:
        new_window.geometry(f"{new_window.winfo_reqwidth()}x{height}+{x}+{y}")
    return new_window

# 显示图片，根据宽度调整，加入滚动条
class ImageViewerWithScrollbar:
    def __init__(self, parent_frame, parent_width=1000, parent_height=565, image_path=None):
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
        # self.canvas = tk.Canvas(self.parent_frame)
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
        self.last_width = parent_frame.winfo_width()
        self.last_height = parent_frame.winfo_height()

        # 绑定窗口大小变化事件（防抖处理）
        self.resize_timeout = None
        self.parent_frame.bind("<Configure>", self.on_resize)

        # 绑定鼠标滚轮事件
        self.bind_mouse_wheel_events()

        # 初始化大小
        self.resize_image()

    def on_resize(self, event):
        if event.widget != self.parent_frame:
            return
        # 过滤异常值
        if event.width < 50 or event.height < 50:
            return

        if event.width != self.last_width or event.height != self.last_height:
            self.last_width = event.width
            self.last_height = event.height

            if self.resize_timeout:
                self.parent_frame.after_cancel(self.resize_timeout)
            self.resize_timeout = self.parent_frame.after(200, self.resize_image)

    def resize_image(self):
        # 获取当前父容器的宽度（减去滚动条的宽度，如果滚动条可见）
        scrollbar_width = self.v_scrollbar.winfo_width() if self.v_scrollbar.winfo_ismapped() else 0
        new_width = self.parent_frame.winfo_width() - scrollbar_width
        new_width = max(1, new_width)  # 确保宽度至少为1

        new_height = int(self.original_height * (new_width / self.original_width))
        new_height = max(1, new_height)

        resized_image = self.image.resize((new_width, new_height), Image.LANCZOS)
        self.resized_tk_image = ImageTk.PhotoImage(resized_image)

        self.canvas.itemconfig(self.image_id, image=self.resized_tk_image)
        self.canvas.image = self.resized_tk_image
        self.canvas.config(scrollregion=(0, 0, new_width, new_height))

    def on_mouse_wheel(self, event):
        if platform.system() == "Windows":
            self.canvas.yview_scroll(-1 * (event.delta // 120), "units")
        elif platform.system() == "Darwin":
            self.canvas.yview_scroll(-1 * event.delta, "units")
        else:  # Linux
            if event.num == 4:
                self.canvas.yview_scroll(-1, "units")
            elif event.num == 5:
                self.canvas.yview_scroll(1, "units")

    def bind_mouse_wheel_events(self):
        if platform.system() == "Windows":
            self.canvas.bind("<MouseWheel>", self.on_mouse_wheel)
        elif platform.system() == "Darwin":
            self.canvas.bind("<MouseWheel>", self.on_mouse_wheel)
        else:
            self.canvas.bind("<Button-4>", self.on_mouse_wheel)
            self.canvas.bind("<Button-5>", self.on_mouse_wheel)

    def destroy(self):
        self.canvas.delete("all")
        self.canvas.image = None
        self.canvas.destroy()
        self.v_scrollbar.destroy()


class ToolTip:
    def __init__(self, widget, text=''):
        self.widget = widget
        self.text = text
        self.tipwindow = None
        self.id = None
        self.x = self.y = 0
        widget.bind("<Enter>", self.enter)
        widget.bind("<Leave>", self.leave)
        widget.bind("<ButtonPress>", self.leave)

    def enter(self, event=None):
        self.schedule()

    def leave(self, event=None):
        self.unschedule()
        self.hidetip()

    def schedule(self):
        self.unschedule()
        self.id = self.widget.after(300, self.showtip)

    def unschedule(self):
        id = self.id
        self.id = None
        if id:
            self.widget.after_cancel(id)

    def showtip(self):
        if self.tipwindow:
            return
        x, y, _, _ = self.widget.bbox("insert")
        x += self.widget.winfo_rootx() + 25
        y += self.widget.winfo_rooty() + 25
        self.tipwindow = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry("+%d+%d" % (x, y))
        label = tk.Label(tw, text=self.text, justify=tk.LEFT,
                         background="#ffffff", relief=tk.SOLID, borderwidth=1,
                         font=("Microsoft YaHei", 9))
        label.pack(ipadx=4, ipady=2)

    def hidetip(self):
        tw = self.tipwindow
        self.tipwindow = None
        if tw:
            tw.destroy()


class LineArtGUI2:
    def __init__(self, root):
        self.root = root
        self.input_path = tk.StringVar(value="未选择图片")
        self.min_radius = tk.IntVar(value=2)
        self.brightness_offset = tk.IntVar(value=50)
        self.enhance_mode = tk.StringVar(value="无")

        self.preview_window = None          # 保存预览窗口引用
        self.temp_preview_path = None       # 临时文件路径

        self.create_widgets()

    def create_widgets(self):
        file_frame = ttk.Frame(self.root, padding=10)
        file_frame.pack(fill=X, anchor=W)

        ttk.Label(file_frame, text="输入图片：").pack(side=LEFT, padx=5)

        self.path_entry = ttk.Entry(file_frame, textvariable=self.input_path, width=40, state=READONLY)
        self.path_entry.pack(side=LEFT, padx=5)
        self.path_tooltip = ToolTip(self.path_entry, text=self.input_path.get())
        self.input_path.trace_add("write", self.update_tooltip)

        ttk.Button(file_frame, text="打开文件", command=self.open_file, bootstyle=PRIMARY).pack(side=LEFT, padx=5)

        param_frame = ttk.LabelFrame(self.root, text="参数设置（调节线条粗细、明暗及清晰度）", padding=12)
        param_frame.pack(fill=BOTH, expand=YES, padx=10, pady=5)

        ttk.Label(param_frame, text="最小值半径（1~10）").grid(row=0, column=0, sticky=W, padx=5, pady=6)
        radius_cb = ttk.Combobox(param_frame, textvariable=self.min_radius,
                                 values=list(range(1, 11)), width=10, state=READONLY)
        radius_cb.grid(row=0, column=1, padx=5, pady=6)

        ttk.Label(param_frame, text="亮度补偿（0~100）").grid(row=0, column=2, sticky=W, padx=5, pady=6)
        bright_cb = ttk.Combobox(param_frame, textvariable=self.brightness_offset,
                                 values=list(range(0, 101, 5)), width=10, state=READONLY)
        bright_cb.grid(row=0, column=3, padx=5, pady=6)

        ttk.Label(param_frame, text="清晰度增强：").grid(row=1, column=0, sticky=W, padx=5, pady=6)
        enhance_cb = ttk.Combobox(param_frame, textvariable=self.enhance_mode,
                                  values=["无", "对比度拉伸", "轻度锐化", "强锐化+去噪"],
                                  width=15, state=READONLY)
        enhance_cb.grid(row=1, column=1, columnspan=3, sticky=W, padx=5, pady=6)

        btn_frame = ttk.Frame(self.root, padding=10)
        btn_frame.pack(fill=X)

        # 预览按钮
        self.preview_btn = ttk.Button(
            btn_frame, text="预览线稿", command=self.preview_lineart,
            bootstyle=INFO, width=20
        )
        self.preview_btn.pack(side=LEFT, padx=5)

        # 生成按钮
        self.gen_btn = ttk.Button(
            btn_frame, text="生成线稿", command=self.generate_lineart,
            bootstyle=SUCCESS, width=20
        )
        self.gen_btn.pack(side=RIGHT, padx=5)

    def open_file(self):
        path = filedialog.askopenfilename(
            title="选择图片",
            filetypes=[("图片文件", "*.png *.jpg *.jpeg *.bmp *.webp"), ("所有文件", "*.*")]
        )
        if path:
            self.input_path.set(path)

    def update_tooltip(self, *args):
        if self.path_tooltip:
            self.path_tooltip.text = self.input_path.get()

    def image_to_lineart(self, input_path, output_path, min_radius, brightness_offset,
                         enhance_mode=0, invert=False):
        data = np.fromfile(input_path, dtype=np.uint8)
        img = cv2.imdecode(data, cv2.IMREAD_COLOR)
        if img is None:
            raise ValueError("无法解码图片")

        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        inverted = 255 - gray
        kernel_size = 2 * min_radius + 1
        kernel = np.ones((kernel_size, kernel_size), np.uint8)
        inverted_min = cv2.erode(inverted, kernel, anchor=(-1, -1), borderType=cv2.BORDER_REPLICATE)
        result = cv2.add(gray, inverted_min)

        offset = (brightness_offset - 50) * 1.0
        if offset != 0:
            result = np.clip(result.astype(np.int16) + offset, 0, 255).astype(np.uint8)

        if enhance_mode == 1:
            p_low, p_high = np.percentile(result, (2, 98))
            if p_high > p_low:
                result = np.clip((result - p_low) / (p_high - p_low) * 255, 0, 255).astype(np.uint8)
        elif enhance_mode == 2:
            gaussian = cv2.GaussianBlur(result, (0, 0), sigmaX=1.5)
            result = cv2.addWeighted(result, 1.5, gaussian, -0.5, 0)
            result = np.clip(result, 0, 255).astype(np.uint8)
        elif enhance_mode == 3:
            kernel_open = np.ones((2, 2), np.uint8)
            result = cv2.morphologyEx(result, cv2.MORPH_OPEN, kernel_open)
            gaussian = cv2.GaussianBlur(result, (0, 0), sigmaX=2.0)
            result = cv2.addWeighted(result, 2.0, gaussian, -1.0, 0)
            result = np.clip(result, 0, 255).astype(np.uint8)

        if invert:
            result = 255 - result

        cv2.imencode('.png', result)[1].tofile(output_path)

    def preview_lineart(self):
        input_path = self.input_path.get()
        if input_path == "未选择图片":
            messagebox.showwarning("提示", "请先选择图片！")
            return

        # 如果已有预览窗口，先关闭它
        if self.preview_window is not None:
            try:
                if self.preview_window.winfo_exists():
                    self.preview_window.destroy()
            except:
                pass
            self.preview_window = None

        # 生成临时文件
        if self.temp_preview_path is None:
            # 创建临时文件，后缀 .png，并立即关闭文件句柄
            fd, self.temp_preview_path = tempfile.mkstemp(suffix='.png', prefix='lineart_preview_')
            os.close(fd)  # 释放文件句柄，以便后续写入

        radius = self.min_radius.get()
        bright = self.brightness_offset.get()
        enhance_str = self.enhance_mode.get()
        enhance_map = {"无": 0, "对比度拉伸": 1, "轻度锐化": 2, "强锐化+去噪": 3}
        enhance = enhance_map.get(enhance_str, 0)

        try:
            self.preview_btn.config(text="预览中...", state=DISABLED)
            self.root.update()

            self.image_to_lineart(
                input_path=input_path,
                output_path=self.temp_preview_path,
                min_radius=radius,
                brightness_offset=bright,
                enhance_mode=enhance,
                invert=False
            )

            # 创建预览窗口
            preview_win = creat_Toplevel("线稿预览", width=1000, height=565, x=70, y=200)
            # 创建框架放置图片查看器
            frame = ttk.Frame(preview_win)
            frame.pack(fill=tk.BOTH, expand=True)

            # 显示图片
            viewer = ImageViewerWithScrollbar(frame, 1000, 565, self.temp_preview_path)

            # 保存引用以便后续关闭
            self.preview_window = preview_win
            # 绑定窗口关闭事件，清理引用和临时文件
            def on_close():
                viewer.destroy()
                preview_win.destroy()
                self.preview_window = None
                # 不删除临时文件，可复用
            preview_win.protocol("WM_DELETE_WINDOW", on_close)

        except Exception as e:
            messagebox.showerror("错误", f"预览失败：{str(e)}")
        finally:
            self.preview_btn.config(text="预览线稿", state=NORMAL)

    def generate_lineart(self):
        input_path = self.input_path.get()
        if input_path == "未选择图片":
            messagebox.showwarning("提示", "请先选择图片！")
            return

        radius = self.min_radius.get()
        bright = self.brightness_offset.get()
        enhance_str = self.enhance_mode.get()
        enhance_map = {"无": 0, "对比度拉伸": 1, "轻度锐化": 2, "强锐化+去噪": 3}
        enhance = enhance_map.get(enhance_str, 0)

        output_path = filedialog.asksaveasfilename(
            title="保存线稿",
            defaultextension=".png",
            filetypes=[("PNG图片", "*.png")]
        )
        if not output_path:
            return

        try:
            self.gen_btn.config(text="生成中...", state=DISABLED)
            self.root.update()

            self.image_to_lineart(
                input_path=input_path,
                output_path=output_path,
                min_radius=radius,
                brightness_offset=bright,
                enhance_mode=enhance,
                invert=False
            )
        except Exception as e:
            messagebox.showerror("错误", f"生成失败：{str(e)}")
        finally:
            self.gen_btn.config(text="生成线稿", state=NORMAL)


if __name__ == "__main__":
    app = ttk.Window(themename="cosmo")
    app.title("图片转线稿工具2.0")
    app.geometry("695x280+1100+360")
    gui = LineArtGUI2(app)
    app.mainloop()