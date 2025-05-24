import sys
import os
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from PIL import Image, ImageTk
import threading
import time
from typing import Dict, Any

from canvas_events import bind_canvas_events, get_photo, create_canvas_with_image, ArtworkDisplayerHeight
from canvas_events import mouse_bind_canvas_events, right_click_bind_canvas_events
from canvas_events import ImageViewerWithScrollbar
from window import set_window_expand, set_window_icon, creat_Toplevel, set_window_top
from scrollbar_frame_win import ScrollbarFrameWin

from tools import load_json
from 时钟塔.szt_info import szts, get_all_szt_obj

szts_json = {}
# 加载资源文件
def load_resources():
    global szts_json
    if szts_json:
        return
    szts_json = load_json("./敌人/时钟塔/szt.json")

# 绑定时钟塔 canvas 的事件
def bind_szt_canvas(parent_frame, szt, x, y):

    photo = get_photo(szt.img_path, (72, 72))
    canvas = create_canvas_with_image(parent_frame, 
        photo, 90, 90, 9, 9, x, y)
    mouse_bind_canvas_events(canvas)

    bind_canvas_events(canvas, 
        creat_szt_win, parent_frame=parent_frame, szt=szt)


open_szt_wins = {}
#关闭窗口时，清除窗口字典中的句柄，并销毁窗口
def szt_win_closing(parent_frame):

    open_szt_win = parent_frame.title()
    while open_szt_win in open_szt_wins:
        del open_szt_wins[open_szt_win]

    parent_frame.destroy()  # 销毁窗口


def creat_szt_win(event, parent_frame, szt):

    # 重复打开时，窗口置顶并直接返回
    if szt.name in open_szt_wins:
        # 判断窗口是否存在
        if open_szt_wins[szt.name].winfo_exists():
            set_window_top(open_szt_wins[szt.name])
            return "break"
        del open_szt_wins[szt.name]

    szt_win_frame = creat_Toplevel(szt.name, x=200,y=250)
    set_window_icon(szt_win_frame, szt.logo_path)
    open_szt_wins[szt.name] = szt_win_frame

    # 配置 szt_win_frame 的布局
    szt_win_frame.grid_rowconfigure(0, weight=1)  # 确保行填充
    for col_index in range(4):
        szt_win_frame.grid_columnconfigure(col_index, weight=1)

    for i, enemy in enumerate(szt.enemys):

        # 使用 LabelFrame 作为每一行的容器
        row_frame = ttk.LabelFrame(szt_win_frame, text=enemy.name)
        row_frame.grid(row=i, column=0, columnspan=4, padx=10, pady=(0,10), sticky="nsew")
        row_frame.grid_columnconfigure(0, weight=1)  # 让 inner_frame 适应 row_frame

        # 创建 inner_frame 让 Canvas 和 Label 并排
        inner_frame = ttk.Frame(row_frame)
        inner_frame.grid(row=0, column=0, columnspan=4, sticky="nsew")
        inner_frame.grid_rowconfigure(0, weight=1)  # 确保行填充
        inner_frame.grid_columnconfigure(0, weight=1)  # Canvas 列
        inner_frame.grid_columnconfigure(1, weight=6)  # 右侧信息列，权重更大以填充更多空间

        enemy_photo = get_photo(enemy.img_path, (72, 72))
        row_canvas = create_canvas_with_image(inner_frame, enemy_photo, 
            72, 72, 0, 0, 0, 0, padx=10, pady=5)
        
        # 右侧信息 Frame（放敌人信息）
        info_frame = ttk.Frame(inner_frame)
        info_frame.grid(row=0, column=1, sticky="nsew")
        info_frame.grid_rowconfigure(0, weight=1) # 确保行填充
        info_frame.grid_columnconfigure(0, weight=2, minsize=100)
        info_frame.grid_columnconfigure(1, weight=3, minsize=150)
        info_frame.grid_columnconfigure(2, weight=3, minsize=150)
        info_frame.grid_columnconfigure(3, weight=3, minsize=150)
        info_frame.grid_columnconfigure(4, weight=3, minsize=150)
        
        border_label = ttk.Label(info_frame, text="属性："+enemy.border, anchor="center")
        border_label.grid(row=0, column=0, sticky="nsew")

        DP_label = ttk.Label(info_frame, text="DP："+enemy.DP, anchor="w")
        DP_label.grid(row=0, column=1, sticky="nsew")

        HP_label = ttk.Label(info_frame, text="HP："+enemy.HP, anchor="w")
        HP_label.grid(row=0, column=2, sticky="nsew")

        weakness_label = ttk.Label(info_frame, text="弱点："+enemy.weakness, anchor="w")
        weakness_label.grid(row=0, column=3, sticky="nsew")

        resist_label = ttk.Label(info_frame, text="抗性："+enemy.resist, anchor="w")
        resist_label.grid(row=0, column=4, sticky="nsew")


    # 绑定鼠标点击事件到父窗口，点击置顶
    szt_win_frame.bind("<Button-1>", lambda event: set_window_top(szt_win_frame))
    # 窗口关闭时清理
    szt_win_frame.protocol("WM_DELETE_WINDOW", lambda: szt_win_closing(szt_win_frame))

    return "break"  # 阻止事件冒泡


class sztCreator:
    def __init__(self, scrollbar_frame_obj, szts: Dict[str, Any]):
        self.scrollable_frame = scrollbar_frame_obj.scrollable_frame
        self.scrollbar_frame_obj = scrollbar_frame_obj
        self.szts = szts
        self.lock = threading.Lock()
        self.current_row = 0
        self.created_count = 0
        self.total_szts = len(szts)
        
    def create_szt_frames(self, thread_id):
        while self.created_count < self.total_szts:
            with self.lock:
                if self.created_count >= self.total_szts:
                    break
                
                # 每个线程创建4个框架
                for _ in range(4):
                    if self.created_count >= self.total_szts:
                        break
                        
                    # 获取当前要处理的时钟塔
                    szt_name = list(self.szts.keys())[self.created_count]
                    szt = self.szts[szt_name]
                    enemy = szt.enemys[0]

                    # 创建框架
                    szt_frame = ttk.LabelFrame(self.scrollable_frame, text=enemy.name+"#"+szt_name)
                    bind_szt_canvas(szt_frame, szt, 0, 0)
                    
                    # 计算位置
                    column = self.created_count % 4
                    szt_frame.grid(row=self.current_row, column=column, 
                                   padx=(10, 0), pady=(0, 10), sticky="nesw")
                    szt_frame.grid_rowconfigure(0, weight=1)
                    szt_frame.grid_columnconfigure(0, weight=1)
                    
                    self.created_count += 1
                    
                    # 每4个框架换行
                    if self.created_count % 4 == 0:
                        self.current_row += 1
                
                self.scrollbar_frame_obj.update_canvas()
            
            # 短暂休眠，让另一个线程有机会执行
            time.sleep(0.05)

def create_szt_interface(scrollbar_frame_obj, szts):

    creator = sztCreator(scrollbar_frame_obj, szts)
    
    # 创建两个线程
    thread1 = threading.Thread(target=creator.create_szt_frames, args=(1,))
    thread2 = threading.Thread(target=creator.create_szt_frames, args=(2,))
    
    # 启动线程
    thread1.start()
    thread2.start()
    
    # 不需要join线程，因为Tkinter主循环会持续运行
    # 线程会在完成工作后自动结束


# 加载图片并显示的函数
def show_szt_enemys(scrollbar_frame_obj):

    load_resources()

    get_all_szt_obj(szts_json)

    global szts

    # 清除之前的组件
    scrollbar_frame_obj.destroy_components()

    create_szt_interface(scrollbar_frame_obj, szts)

    # scrollbar_frame_obj.update_canvas()
    return "break"  # 阻止事件冒泡




