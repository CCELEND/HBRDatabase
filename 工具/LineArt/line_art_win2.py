import cv2
import numpy as np
import tkinter as tk
from tkinter import filedialog, messagebox
import ttkbootstrap as ttk
from ttkbootstrap.constants import *

from window import creat_Toplevel
from window import win_open_manage, win_close_manage, is_win_open, win_set_top

from 日志.advanced_logger import AdvancedLogger
logger = AdvancedLogger.get_logger(__name__)


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
        # 变量
        self.input_path = tk.StringVar(value="未选择图片")
        self.min_radius = tk.IntVar(value=3)          # 最小值半径
        self.brightness_offset = tk.IntVar(value=50)  # 亮度补偿（0~100）
        
        self.create_widgets()

    def create_widgets(self):
        # 选择文件
        file_frame = ttk.Frame(self.root, padding=10)
        file_frame.pack(fill=X, anchor=W)
        
        ttk.Label(file_frame, text="输入图片：").pack(side=LEFT, padx=5)

        self.path_entry = ttk.Entry(file_frame, textvariable=self.input_path, width=40, state=READONLY)
        self.path_entry.pack(side=LEFT, padx=5)
        self.path_tooltip = ToolTip(self.path_entry, text=self.input_path.get())
        self.input_path.trace_add("write", self.update_tooltip)

        ttk.Button(file_frame, text="打开文件", command=self.open_file, bootstyle=PRIMARY).pack(side=LEFT, padx=5)

        # 参数面板（修改后只保留两个参数）
        param_frame = ttk.LabelFrame(self.root, text="参数设置（最小值半径控制线条粗细，亮度补偿调节明暗）", padding=15)
        param_frame.pack(fill=BOTH, expand=YES, padx=10, pady=5)
        
        # 最小值半径
        ttk.Label(param_frame, text="最小值半径（1~10）").grid(row=0, column=0, sticky=W, padx=5, pady=8)
        radius_cb = ttk.Combobox(param_frame, textvariable=self.min_radius, 
                                 values=list(range(1, 11)), width=10, state=READONLY)
        radius_cb.grid(row=0, column=1, padx=5, pady=8)

        # 亮度补偿（相当于线性减淡后的亮度微调）
        ttk.Label(param_frame, text="亮度补偿（0~100）").grid(row=0, column=2, sticky=W, padx=5, pady=8)
        bright_cb = ttk.Combobox(param_frame, textvariable=self.brightness_offset,
                                 values=list(range(0, 101, 5)), width=10, state=READONLY)
        bright_cb.grid(row=0, column=3, padx=5, pady=8)

        # 生成按钮
        btn_frame = ttk.Frame(self.root, padding=10)
        btn_frame.pack(fill=X)
        
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
            win_set_top('图片转线稿工具2.0', __name__)
            self.input_path.set(path)

    def update_tooltip(self, *args):
        if self.path_tooltip:
            self.path_tooltip.text = self.input_path.get()

    def image_to_lineart(self, input_path, output_path, min_radius, brightness_offset, invert=False):
        """
        PS风格线稿提取：去色 → 反相 → 最小值滤波 → 线性减淡（相加）
        min_radius: 最小值滤波半径（核大小 = 2*radius+1）
        brightness_offset: 亮度补偿，范围0~100，用于调整线性减淡后的整体亮度
        """
        # 读取图片
        data = np.fromfile(input_path, dtype=np.uint8)
        img = cv2.imdecode(data, cv2.IMREAD_COLOR)
        if img is None:
            raise ValueError("无法解码图片")

        # 1. 去色（灰度）
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        # 2. 反相
        inverted = 255 - gray

        # 3. 最小值滤波（腐蚀）核大小 = 2*radius+1
        kernel_size = 2 * min_radius + 1
        kernel = np.ones((kernel_size, kernel_size), np.uint8)
        inverted_min = cv2.erode(inverted, kernel, anchor=(-1, -1), borderType=cv2.BORDER_REPLICATE)

        # 4. 线性减淡（亮部相加）：结果 = 原灰度 + 反相最小值图
        result = cv2.add(gray, inverted_min)  # 自动截断至[0,255]

        # 5. 亮度补偿（若不为0，则整体调整亮度，相当于调整曝光）
        if brightness_offset != 50:  # 默认50为不调整，此处可做映射
            # 将50映射为0偏移，范围0~100映射到 -50~+50
            offset = (brightness_offset - 50) * 1.0  # 直接加减
            result = np.clip(result.astype(np.int16) + offset, 0, 255).astype(np.uint8)

        # 如果需要反色
        if invert:
            result = 255 - result

        # 保存
        cv2.imencode('.png', result)[1].tofile(output_path)

    def generate_lineart(self):
        input_path = self.input_path.get()
        if input_path == "未选择图片":
            messagebox.showwarning("提示", "请先选择图片！")
            win_set_top('图片转线稿工具2.0', __name__)
            return
        
        radius = self.min_radius.get()
        bright = self.brightness_offset.get()

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
                invert=False
            )
            
            win_set_top('图片转线稿工具2.0', __name__)
        except Exception as e:
            logger.error(str(e))
            messagebox.showerror("错误", f"生成失败：{str(e)}")
            win_set_top('图片转线稿工具2.0', __name__)
        finally:
            self.gen_btn.config(text="生成线稿", state=NORMAL)


def creat_line_art_win2():
    if is_win_open('图片转线稿工具2.0', __name__):
        win_set_top('图片转线稿工具2.0', __name__)
        return "break"

    line_art_win_frame = creat_Toplevel("图片转线稿工具2.0", 695, 280, x=500, y=300)
    gui = LineArtGUI2(line_art_win_frame)

    win_open_manage(line_art_win_frame, __name__)
    line_art_win_frame.protocol("WM_DELETE_WINDOW", 
        lambda: win_close_manage(line_art_win_frame, __name__))