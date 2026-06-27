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

from window import creat_Toplevel
from window import win_open_manage, win_close_manage, is_win_open, win_set_top

from 日志.advanced_logger import AdvancedLogger
logger = AdvancedLogger.get_logger(__name__)

# 显示图片，根据宽度调整，加入滚动条
class ImageViewerWithScrollbar:
    def __init__(self, parent_frame, parent_width=1000, parent_height=565, image_path=None):
        self.parent_frame = parent_frame
        self.parent_width = parent_width
        self.parent_height = parent_height
        self.image_path = image_path

        self.image = Image.open(self.image_path)
        self.original_width, self.original_height = self.image.size

        self.tk_image = ImageTk.PhotoImage(self.image)

        self.canvas = tk.Canvas(self.parent_frame, width=self.parent_width, height=self.parent_height)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.image_id = self.canvas.create_image(0, 0, anchor=tk.NW, image=self.tk_image)
        self.canvas.config(scrollregion=(0, 0, self.original_width, self.original_height))

        self.v_scrollbar = tk.Scrollbar(self.parent_frame, orient=tk.VERTICAL, command=self.canvas.yview)
        self.v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.canvas.config(yscrollcommand=self.v_scrollbar.set)

        self.canvas.image = self.tk_image

        self.last_width = parent_frame.winfo_width()
        self.last_height = parent_frame.winfo_height()
        self.resize_timeout = None
        self.parent_frame.bind("<Configure>", self.on_resize)
        self.bind_mouse_wheel_events()

        self.resize_image()

    def update_image(self, new_image_path):
        # 更新显示新图片
        self.image_path = new_image_path
        self.image = Image.open(self.image_path)
        self.original_width, self.original_height = self.image.size
        self.tk_image = ImageTk.PhotoImage(self.image)
        self.canvas.itemconfig(self.image_id, image=self.tk_image)
        self.canvas.image = self.tk_image
        self.canvas.config(scrollregion=(0, 0, self.original_width, self.original_height))
        self.resize_image()
        self.canvas.update_idletasks()

    def on_resize(self, event):
        if event.widget != self.parent_frame:
            return
        if event.width < 50 or event.height < 50:
            return
        if event.width != self.last_width or event.height != self.last_height:
            self.last_width = event.width
            self.last_height = event.height
            if self.resize_timeout:
                self.parent_frame.after_cancel(self.resize_timeout)
            self.resize_timeout = self.parent_frame.after(200, self.resize_image)

    def resize_image(self):
        scrollbar_width = self.v_scrollbar.winfo_width() if self.v_scrollbar.winfo_ismapped() else 0
        new_width = self.parent_frame.winfo_width() - scrollbar_width
        new_width = max(1, new_width)
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
        else:
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

        self.preview_window = None          # 预览窗口引用
        self.viewer = None                  # 图片查看器对象
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

        self.preview_btn = ttk.Button(
            btn_frame, text="预览线稿", command=self.preview_lineart,
            bootstyle=INFO, width=20
        )
        self.preview_btn.pack(side=LEFT, padx=5)

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
            win_set_top('图片转线稿工具2.0', __name__)
            return

        # 如果预览窗口存在且有效，则更新图片
        if self.preview_window is not None and self.preview_window.winfo_exists():
            # 生成最新线稿到临时文件
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

                # 更新查看器中的图片
                self.viewer.update_image(self.temp_preview_path)
                self.preview_window.lift()  # 窗口提到最前
            except Exception as e:
                logger.error(str(e))
                messagebox.showerror("错误", f"预览更新失败：{str(e)}")
            finally:
                self.preview_btn.config(text="预览线稿", state=NORMAL)
            return

        # 否则创建新预览窗口
        # 生成临时文件（如果尚未创建）
        if self.temp_preview_path is None:
            fd, self.temp_preview_path = tempfile.mkstemp(suffix='.png', prefix='lineart_preview_')
            os.close(fd)

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

            preview_win = creat_Toplevel("线稿预览", width=1000, height=900, x=70, y=70)
            frame = ttk.Frame(preview_win)
            frame.pack(fill=tk.BOTH, expand=True)

            viewer = ImageViewerWithScrollbar(frame, 1000, 900, self.temp_preview_path)

            self.preview_window = preview_win
            self.viewer = viewer

            def on_close():
                self.viewer.destroy()
                preview_win.destroy()
                self.preview_window = None
                self.viewer = None
            preview_win.protocol("WM_DELETE_WINDOW", on_close)

        except Exception as e:
            logger.error(str(e))
            messagebox.showerror("错误", f"预览失败：{str(e)}")
        finally:
            self.preview_btn.config(text="预览线稿", state=NORMAL)

    def generate_lineart(self):
        input_path = self.input_path.get()
        if input_path == "未选择图片":
            messagebox.showwarning("提示", "请先选择图片！")
            win_set_top('图片转线稿工具2.0', __name__)
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

    line_art_win_frame = creat_Toplevel("图片转线稿工具2.0", 695, 280, x=1100, y=360)
    gui = LineArtGUI2(line_art_win_frame)

    win_open_manage(line_art_win_frame, __name__)
    line_art_win_frame.protocol("WM_DELETE_WINDOW", 
        lambda: win_close_manage(line_art_win_frame, __name__))