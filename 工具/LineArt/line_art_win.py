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

class LineArtGUI:
    def __init__(self, root):
        self.root = root
        # self.root.title("图片转线稿工具")
        # self.root.geometry("600x280")
        
        # 变量
        self.input_path = tk.StringVar(value="未选择图片")
        self.line_thickness = tk.IntVar(value=3)
        self.threshold1 = tk.IntVar(value=30)
        self.threshold2 = tk.IntVar(value=80)
        
        # 创建界面
        self.create_widgets()

    def create_widgets(self):
        # 选择文件
        file_frame = ttk.Frame(self.root, padding=10)
        file_frame.pack(fill=X, anchor=W)
        
        ttk.Label(file_frame, text="输入图片：").pack(side=LEFT, padx=5)

        # ttk.Entry(file_frame, textvariable=self.input_path, width=40, state=READONLY).pack(side=LEFT, padx=5)
        self.path_entry = ttk.Entry(file_frame, textvariable=self.input_path, width=40, state=READONLY)
        self.path_entry.pack(side=LEFT, padx=5)
        # 初始化提示
        self.path_tooltip = ToolTip(self.path_entry, text=self.input_path.get())
        # 路径变化时同步更新提示文本
        self.input_path.trace_add("write", self.update_tooltip)

        ttk.Button(file_frame, text="打开文件", command=self.open_file, bootstyle=PRIMARY).pack(side=LEFT, padx=5)

        # 参数面板
        param_frame = ttk.LabelFrame(self.root, text="参数设置（数值越小细节越多，但是噪声会更多）", padding=15)
        param_frame.pack(fill=BOTH, expand=YES, padx=10, pady=5)
        
        # 线条粗细
        ttk.Label(param_frame, text="高斯模糊核大小").grid(row=0, column=0, sticky=W, padx=5, pady=8)
        thickness_cb = ttk.Combobox(param_frame, textvariable=self.line_thickness, values=[1,2,3,4,5,6,7,8,9,10], width=10, state=READONLY)
        thickness_cb.grid(row=0, column=1, padx=5, pady=8)

        # 阈值1
        ttk.Label(param_frame, text="Canny算子低阈值(10-300)").grid(row=0, column=2, sticky=W, padx=5, pady=8)
        t1_cb = ttk.Combobox(param_frame, textvariable=self.threshold1, values=list(range(10, 301, 10)), width=10, state=READONLY)
        t1_cb.grid(row=0, column=3, padx=5, pady=8)

        # 阈值2
        ttk.Label(param_frame, text="Canny算子高阈值(10-300)").grid(row=1, column=0, sticky=W, padx=5, pady=8)
        t2_cb = ttk.Combobox(param_frame, textvariable=self.threshold2, values=list(range(10, 301, 10)), width=10, state=READONLY)
        t2_cb.grid(row=1, column=1, padx=5, pady=8)

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
            win_set_top('图片转线稿工具', __name__)
            self.input_path.set(path)

    def update_tooltip(self, *args):
        # 路径改变时自动更新悬浮提示内容
        if self.path_tooltip:
            self.path_tooltip.text = self.input_path.get()

    def image_to_lineart(self, input_path, output_path, line_thickness, threshold1, threshold2, invert=False):
        data = np.fromfile(input_path, dtype=np.uint8)
        img = cv2.imdecode(data, cv2.IMREAD_COLOR)
        
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (line_thickness, line_thickness), 0)
        edges = cv2.Canny(blurred, threshold1=threshold1, threshold2=threshold2)
        kernel = np.ones((1, 1), np.uint8)
        edges = cv2.dilate(edges, kernel, iterations=1)
        if not invert:
            edges = cv2.bitwise_not(edges)
        
        cv2.imencode('.png', edges)[1].tofile(output_path)

    def generate_lineart(self):
        input_path = self.input_path.get()
        if input_path == "未选择图片":
            messagebox.showwarning("提示", "请先选择图片！")
            win_set_top('图片转线稿工具', __name__)
            return
        
        lt = self.line_thickness.get()
        t1 = self.threshold1.get()
        t2 = self.threshold2.get()

        # 保存路径
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
                line_thickness=lt,
                threshold1=t1,
                threshold2=t2,
                invert=False
            )
            
            # messagebox.showinfo("成功", f"线稿已保存！\n{output_path}")
            win_set_top('图片转线稿工具', __name__)
        except Exception as e:
            logger.error(str(e))
            messagebox.showerror("错误", f"生成失败：{str(e)}")
            win_set_top('图片转线稿工具', __name__)
        finally:
            self.gen_btn.config(text="生成线稿", state=NORMAL)


def creat_line_art_win():
    # 重复打开时，窗口置顶并直接返回
    if is_win_open('图片转线稿工具', __name__):
        win_set_top('图片转线稿工具', __name__)
        return "break"

    line_art_win_frame = creat_Toplevel("图片转线稿工具", 695, 280,x=500, y=300)
    gui = LineArtGUI(line_art_win_frame)

    win_open_manage(line_art_win_frame, __name__)
    # 窗口关闭时清理
    line_art_win_frame.protocol("WM_DELETE_WINDOW", 
        lambda: win_close_manage(line_art_win_frame, __name__))
    # return "break"  # 阻止事件冒泡
