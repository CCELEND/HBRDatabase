import cv2
import numpy as np
import tkinter as tk
from tkinter import filedialog, messagebox
import ttkbootstrap as ttk
from ttkbootstrap.constants import *

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
        # 修改为 StringVar，默认显示 "无"
        self.enhance_mode = tk.StringVar(value="无")  

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
        # values 为显示文本，textvariable 绑定到 StringVar
        enhance_cb = ttk.Combobox(param_frame, textvariable=self.enhance_mode,
                                  values=["无", "对比度拉伸", "轻度锐化", "强锐化+去噪"],
                                  width=15, state=READONLY)
        enhance_cb.grid(row=1, column=1, columnspan=3, sticky=W, padx=5, pady=6)

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

    def generate_lineart(self):
        input_path = self.input_path.get()
        if input_path == "未选择图片":
            messagebox.showwarning("提示", "请先选择图片！")
            return

        radius = self.min_radius.get()
        bright = self.brightness_offset.get()
        enhance_str = self.enhance_mode.get()   # 获取字符串

        # 映射为整数
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
    app.geometry("695x280")
    gui = LineArtGUI2(app)
    app.mainloop()