import os
import tkinter as tk
from PIL import Image, ImageTk
from tkinter import Menu, messagebox

import ttkbootstrap as ttk
from ttkbootstrap.constants import *

def set_window_disable_maximize(parent_frame):
    # Windows系统
    parent_frame.wm_attributes("-toolwindow", True)

def set_window_disable_size(parent_frame):
    parent_frame.resizable(False, False)

menu_icons = {}
def load_menu_icon(path, name):
    if not path:
        return None
    if name in menu_icons:
        return menu_icons[name]
    menu_icons[name] = ImageTk.PhotoImage(Image.open(path).resize((22, 22)))
    return menu_icons[name]

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
def creat_Toplevel(title, width=None, height=None, x=None, y=None):
    # 参数类型校验
    if not isinstance(title, str):
        raise TypeError("title参数必须是字符串类型")
    for param, name in [(width, "width"), (height, "height"), (x, "x"), (y, "y")]:
        if param is not None and not isinstance(param, int):
            raise TypeError(f"{name}参数必须是整数类型或None")

    # 构建窗口参数
    window_args = {"title": title}
    
    # 处理尺寸参数
    if width is not None and height is not None:
        window_args["size"] = (width, height)
    
    # 处理位置参数
    if x is not None and y is not None:
        window_args["position"] = (x, y)
    
    # 创建窗口
    new_window = ttk.Toplevel(**window_args)
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

# 设置窗口图标
def set_window_icon(frame, icon_path):
    # 检查文件是否存在
    if not os.path.exists(icon_path):
        messagebox.showerror("错误", "图标文件未找到")
        return

    # 获取文件扩展名并转换为小写
    file_ext = os.path.splitext(icon_path)[1].lower()

    try:
        if file_ext == '.ico':
            # 直接使用ICO文件
            frame.iconbitmap(icon_path)
        elif file_ext in ['.png', '.jpg', '.jpeg', '.bmp']:
            # 加载图像并调整为64×64像素
            image = Image.open(icon_path)
            image = image.resize((64, 64), Image.LANCZOS)
            
            # 创建临时ICO文件路径
            temp_ico_path = os.path.splitext(icon_path)[0] + '_temp.ico'
            
            # 保存为ICO格式
            image.save(temp_ico_path, format='ICO', sizes=[(64, 64)])
            
            # 设置窗口图标
            frame.iconbitmap(temp_ico_path)
            
            # 清理临时文件（可选）
            os.remove(temp_ico_path)
        else:
            messagebox.showerror("错误", "不支持的文件格式，请使用ICO、PNG、JPG或BMP格式")
    except Exception as e:
        messagebox.showerror("错误", f"设置图标时出错: {str(e)}")

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
    parent_frame.deiconify()  # 如果窗口被最小化，先恢复窗口
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




# 已打开的窗口字典，键：名，值：窗口句柄
open_wins = {}

def win_open_manage(open_win_frame, module):
    open_win_name = f"{module}_{open_win_frame.title()}"
    open_wins[open_win_name] = open_win_frame


# 关闭窗口时，清除列表中对应的窗口名，并销毁窗口
def win_close_manage(open_win_frame, module, class_resources = None):

    # print(open_wins)

    open_win_name = f"{module}_{open_win_frame.title()}"
    while open_win_name in open_wins:
        del open_wins[open_win_name]

    if class_resources: class_resources.destroy() # 释放类资源
    open_win_frame.destroy()  # 销毁窗口

# 关闭并清除所有打开的窗口
# 遍历时不能修改字典元素，遍历条件应改为列表
def win_close_all():
    for open_win_name in list(open_wins.keys()):
        win_frame = open_wins[open_win_name]
        del open_wins[open_win_name]
        win_frame.destroy()  # 销毁窗口

def win_set_top(open_win, module):
    if isinstance(open_win, str):
        open_win_name = f"{module}_{open_win}"
        set_window_top(open_wins[open_win_name])
    else:
        open_win_name = f"{module}_{open_win.title()}"
        set_window_top(open_wins[open_win_name])


def is_win_open(open_win_name, module):
    open_win_name = f"{module}_{open_win_name}"
    return True if open_win_name in open_wins else False


def is_win_exist(win_frame):
    return True if win_frame.winfo_exists() else False


def get_ico_path_by_name(name):
    if not name: return None 

    infos = {
        "31A":"./角色/31A/DioramaStamp31a.ico", "31B":"./角色/31B/DioramaStamp31b.ico", 
        "31C":"./角色/31C/DioramaStamp31c.ico", "30G":"./角色/30G/DioramaStamp30G.ico",
        "31D":"./角色/31D/DioramaStamp31d.ico", "31E":"./角色/31E/DioramaStamp31e.ico", 
        "31F":"./角色/31F/DioramaStamp31f.ico", "31X":"./角色/31X/DioramaStamp31x.ico", 
        "Angel Beats!":"./角色/Angel Beats!/angelbeats.ico",
        "司令部":"./角色/司令部/司令部.ico",
        "主线道具":"./持有物/主线道具/ThumbnailFishingRod.png",
        "道具":"./持有物/道具/ThumbnailHC.png",
        "饰品":"./持有物/饰品/专武/Soul_png.png",
        "饰品材料":"./持有物/饰品材料/ThumbnailDiamond.png",
        "活动奖章":"./持有物/活动奖章/ThumbnailPremierMedal.png", 
        "奖杯勋章":"./持有物/奖杯勋章/ThumbnailtrophyBlack.png", 
        "成长素材":"./持有物/成长素材/StyleExp01.png",
        "强化素材":"./持有物/强化素材/EternalDaphne.png",
        "增幅器":"./持有物/增幅器/SeraphBooster1.png",
        "芯片":"./持有物/芯片/SeraphArtifactChip1.png", 
        "入场券":"./持有物/入场券/ThumbnailStoryHardModeTicket.png", 
        "扭蛋材料":"./持有物/扭蛋材料/ThumbnailSSGachaTicket.png", 
        "碎片":"./持有物/碎片/ImgIconItemL_StylePieceSS.png", 
        "货币":"./持有物/货币/ThumbnailGP.png", 

        "时钟塔":"./敌人/时钟塔/boss.ico", 
        "主线":"./敌人/主线/亡骨之翎/亡骨之翎.ico",
        "光球BOSS":"./敌人/光球BOSS/阿蒙之门B/阿蒙之门B.ico",
        "时之修炼场":"./敌人/时之修炼场/灵魂星兽.ico",
        "棱镜战":"./敌人/棱镜战/[幻影]深渊重锤/[幻影]深渊重锤.ico",
        "宝石棱镜战":"./敌人/宝石棱镜战/[幻影]群山重锤/[幻影]群山重锤.ico",
        "恒星扫荡战线":"./敌人/恒星战/DimensionBattleCentralTop_001.png",
        "高分挑战":"./敌人/高分挑战/夏日的诅咒#1/gf1.ico",
        "异时层":"./敌人/异时层/亡骨之翎Ω/亡骨之翎Ω.ico",
        "遭遇战":"./敌人/遭遇战/遭遇战#1/zyz1.ico",

        "职业":"./战斗系统/职业/ADMIRAL.png",
        "武器":"./战斗系统/武器/Sword.png",
        "属性":"./战斗系统/属性/Fire.png",
        "效果、状态":"./战斗系统/状态/Charge.png"


    }
    if name not in infos: return None
    return infos[name]


