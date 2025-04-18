
import tkinter as tk
from PIL import Image, ImageTk
from tkinter import scrolledtext, Menu, messagebox
import ctypes

import ttkbootstrap as ttk
from ttkbootstrap.constants import *

def set_global_bg(parent_frame, bg="#f0f0f0"):
    # 获取当前主题的颜色配置
    current_theme = parent_frame.style.theme_use()
    colors = parent_frame.style.colors
    # 修改背景色
    colors.primary = "#858585"
    # colors.primary = "#bfbfbf"
    colors.bg = bg  # 修改主题的全局背景色
    colors.selectfg = bg
    colors.inputbg = bg
    colors.light = bg

# 创建一个新窗口 主窗口
def creat_window(title, 
    wide=None, high=None, x=None, y=None):
    new_window = ttk.Window(title=title, size=(wide, high), position=(x,y))

    return new_window   

# 创建一个新窗口 子窗口
def creat_Toplevel(title, 
    wide=None, high=None, x=None, y=None):

    # 设置新窗口的大小
    if wide and high:
        if x and y:
            new_window = ttk.Toplevel(title=title, size=(wide, high), position=(x,y))
        else:
            new_window = ttk.Toplevel(title=title, size=(wide, high))
    else:
        new_window = ttk.Toplevel(title=title)

    return new_window

# 配置窗口的行和列的伸展
def set_window_expand(frame, rowspan=1, columnspan=1):
    for row in range(rowspan):
        frame.grid_rowconfigure(row, weight=1)
    for col in range(columnspan):
        frame.grid_columnconfigure(col, weight=1)

# 配置窗口的行伸展
def set_window_row_expand(frame, rowspan=1):
    for row in range(rowspan):
        frame.grid_rowconfigure(row, weight=1)

# 配置窗口的列伸展
def set_window_colum_expand(frame, columnspan=1):
    for col in range(columnspan):
        frame.grid_columnconfigure(col, weight=1)

# ico 设置窗口图标
def set_window_icon(frame, icon_path):
    try:
        frame.iconbitmap(icon_path)  # 尝试加载 .ico 文件
    except tk.TclError:
        try:
            icon_image = Image.open(icon_path)  # 尝试加载 .png 文件
            icon_photo = ImageTk.PhotoImage(icon_image)
            frame.iconphoto(True, icon_photo)
        except FileNotFoundError:
            messagebox.showerror("错误", "图标文件未找到")

# webp 设置窗口图标，并可以指定图标大小
def set_window_icon_webp_save(frame, webp_path, size=(64, 64)):
    try:
        # 加载图片
        icon_image = Image.open(webp_path).convert("RGBA")
        # 调整图片大小
        icon_image = icon_image.resize(size, Image.LANCZOS)
        # 保存为临时 .ico 文件
        temp_icon_path = webp_path[-4:] + ".ico"
        icon_image.save(temp_icon_path, format="ICO", sizes=[(size[0], size[1])])
        # 设置窗口图标
        frame.iconbitmap(temp_icon_path)
    except FileNotFoundError:
        messagebox.showerror("错误", "图标文件未找到")
    except Exception as e:
        messagebox.showerror("错误", f"无法设置窗口图标: {e}")

# webp 设置窗口图标，并可以指定图标大小
def set_window_icon_webp(frame, webp_path, size=(64, 64)):
    try:
        # 加载图片
        icon_image = Image.open(webp_path).convert("RGBA")
        # 调整图片大小
        icon_image = icon_image.resize(size, Image.LANCZOS)
        # 将图片转换为 Tkinter 可用的格式
        icon_photo = ImageTk.PhotoImage(icon_image)
        # 设置窗口图标
        frame.iconphoto(True, icon_photo)
        frame.icon_photo = icon_photo
    except FileNotFoundError:
        messagebox.showerror("错误", "图标文件未找到")
    except Exception as e:
        messagebox.showerror("错误", f"无法设置窗口图标: {e}")

# 当父窗口被点击时，将其置于顶层
def set_window_top(parent_frame):
    parent_frame.lift()


# 右键复制
def copy_text(event, text_widget):
    try:
        # 获取选中的文本
        selected_text = text_widget.get("sel.first", "sel.last")
        if selected_text:
            text_widget.clipboard_clear()
            text_widget.clipboard_append(selected_text)
    except tk.TclError:
        pass  # 如果没有选中文本，忽略错误

# 右键粘贴
def paste_text(event, text_widget):
    try:
        text_widget.insert(tk.INSERT, text_widget.clipboard_get())
    except tk.TclError:
        pass  # 如果剪贴板为空，忽略错误

# 右键剪切
def cut_text(event, text_widget):
    try:
        selected_text = text_widget.get("sel.first", "sel.last")
        if selected_text:
            text_widget.clipboard_clear()
            text_widget.clipboard_append(selected_text)
            text_widget.delete("sel.first", "sel.last")
    except tk.TclError:
        pass

# 右键菜单
def show_context_menu(event, text_widget):
    # 创建上下文菜单
    context_menu = Menu(text_widget, tearoff=0)
    context_menu.add_command(label="复制", command=lambda e=event: copy_text(e, text_widget))
    context_menu.add_command(label="粘贴", command=lambda e=event: paste_text(e, text_widget))
    context_menu.add_command(label="剪切", command=lambda e=event: cut_text(e, text_widget))
    # 在鼠标右键点击的位置显示菜单
    context_menu.tk_popup(event.x_root, event.y_root)
    context_menu.grab_release()

# 清空输入输出框
def clear_text(*text_widgets):
    for text_widget in text_widgets:
        if text_widget.cget('state') == tk.DISABLED:
            text_widget.config(state=tk.NORMAL)
            text_widget.delete("1.0", tk.END)
            text_widget.config(state=tk.DISABLED)
        else:
            text_widget.delete("1.0", tk.END)

# 编辑文本框
def edit_text(text_widget, data):
    if text_widget.cget('state') == tk.DISABLED:
        text_widget.config(state=tk.NORMAL)
        text_widget.delete("1.0", tk.END)
        text_widget.insert(tk.END, data)
        text_widget.config(state=tk.DISABLED)
    else:
        text_widget.delete("1.0", tk.END)
        text_widget.insert(tk.END, data)


def set_bg_opacity(parent_frame, parent_width, parent_height, bg_path, opacity):
    # 加载背景图片
    bg_image = Image.open(bg_path)
    bg_image = bg_image.resize((parent_width, parent_height), Image.LANCZOS)

    # 将透明度百分比转换为灰度值（0-255）
    opacity_percentage = int(opacity.strip('%')) / 100
    gray_value = int(opacity_percentage * 255)

    # 生成一个透明度遮罩层
    mask = Image.new('L', bg_image.size, gray_value)  # 'L' 表示灰度图
    bg_image.putalpha(mask)

    # 将图片转换为Tkinter可用的格式
    bg_photo = ImageTk.PhotoImage(bg_image)
    
    # 将图片设置为背景
    bg_label = tk.Label(parent_frame, image=bg_photo)
    bg_label.place(relwidth=1, relheight=1)

    return bg_photo
