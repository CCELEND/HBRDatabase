
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
import threading
import time
from typing import Dict, Any

from canvas_events import bind_canvas_events, get_photo, create_canvas_with_image
from canvas_events import mouse_bind_canvas_events
from canvas_events import ImageViewerWithScrollbar
from window import set_window_icon, creat_Toplevel, set_window_top

from tools import load_json
from 高分挑战.gftz_info import gftzs, get_all_gftz_obj

gftzs_json = {}
# 加载资源文件
def load_resources():
    global gftzs_json
    if gftzs_json:
        return
    gftzs_json = load_json("./敌人/高分挑战/gftz.json")

# 绑定高分挑战 canvas 的事件
def bind_gftz_canvas(parent_frame, gftz, x, y):

    if "攻略" in gftz.name:
        photo = get_photo(gftz.img_path, (90, 90))
        canvas = create_canvas_with_image(parent_frame, 
            photo, 130, 130, 20, 20, x, y)
    else:
        photo = get_photo(gftz.img_path, (128, 72))
        canvas = create_canvas_with_image(parent_frame, 
            photo, 130, 130, 1, 29, x, y)
    mouse_bind_canvas_events(canvas)

    if gftz.guide_path:
        bind_canvas_events(canvas, 
            creat_gftz_win, parent_frame=parent_frame, 
            gftz=gftz)

open_gftz_wins = {}
#关闭窗口时，清除窗口字典中的句柄，并销毁窗口
def gftz_win_closing(parent_frame):

    open_gftz_win = parent_frame.title()
    while open_gftz_win in open_gftz_wins:
        del open_gftz_wins[open_gftz_win]

    parent_frame.destroy()  # 销毁窗口

def creat_gftz_win(event, parent_frame, gftz):

    # 重复打开时，窗口置顶并直接返回
    if gftz.name in open_gftz_wins:
        # 判断窗口是否存在
        if open_gftz_wins[gftz.name].winfo_exists():
            set_window_top(open_gftz_wins[gftz.name])
            return "break"
        del open_gftz_wins[gftz.name]

    if "攻略" in gftz.name:
        gftz_win_frame = creat_Toplevel(gftz.name, 600, 840, 180, 140)
    else:
        gftz_win_frame = creat_Toplevel(gftz.name, 1280, 715, 180, 140)
    set_window_icon(gftz_win_frame, gftz.logo_path)
    open_gftz_wins[gftz.name] = gftz_win_frame

    # 创建 ImageViewerWithScrollbar 实例
    gftz_image_viewer = ImageViewerWithScrollbar(gftz_win_frame, 1280, 715, gftz.guide_path)

    # 绑定鼠标点击事件到父窗口，点击置顶
    gftz_win_frame.bind("<Button-1>", lambda event: set_window_top(gftz_win_frame))
    # 窗口关闭时清理
    gftz_win_frame.protocol("WM_DELETE_WINDOW", lambda: gftz_win_closing(gftz_win_frame))

    return "break"  # 阻止事件冒泡

class GFTZCreator:
    def __init__(self, scrollbar_frame_obj, gftzs: Dict[str, Any]):
        self.scrollable_frame = scrollbar_frame_obj.scrollable_frame
        self.scrollbar_frame_obj = scrollbar_frame_obj
        self.gftzs = gftzs
        self.lock = threading.Lock()
        self.current_row = 0
        self.created_count = 0
        self.total_gftzs = len(gftzs)
        
    def create_gftz_frames(self, thread_id):
        while self.created_count < self.total_gftzs:
            with self.lock:
                if self.created_count >= self.total_gftzs:
                    break
                
                # 每个线程创建5个框架
                for _ in range(5):
                    if self.created_count >= self.total_gftzs:
                        break
                        
                    # 获取当前要处理的高分挑战
                    gftz_name = list(self.gftzs.keys())[self.created_count]
                    gftz = self.gftzs[gftz_name]
                    
                    # 创建框架
                    gftz_frame = ttk.LabelFrame(self.scrollable_frame, text=gftz_name)
                    bind_gftz_canvas(gftz_frame, gftz, 0, 0)
                    
                    # 计算位置
                    column = self.created_count % 5
                    gftz_frame.grid(row=self.current_row, column=column, 
                                   padx=(10, 0), pady=(0, 10), sticky="nesw")
                    gftz_frame.grid_rowconfigure(0, weight=1)
                    gftz_frame.grid_columnconfigure(0, weight=1)
                    
                    self.created_count += 1
                    
                    # 每5个框架换行
                    if self.created_count % 5 == 0:
                        self.current_row += 1
                
                self.scrollbar_frame_obj.update_canvas()
            
            # 短暂休眠，让另一个线程有机会执行
            time.sleep(0.05)

def create_gftz_interface(scrollbar_frame_obj, gftzs):

    creator = GFTZCreator(scrollbar_frame_obj, gftzs)
    
    # 创建两个线程
    thread1 = threading.Thread(target=creator.create_gftz_frames, args=(1,))
    thread2 = threading.Thread(target=creator.create_gftz_frames, args=(2,))
    
    # 启动线程
    thread1.start()
    thread2.start()
    
    # 不需要join线程，因为Tkinter主循环会持续运行
    # 线程会在完成工作后自动结束


# 加载图片并显示的函数
def show_gftz_enemys(scrollbar_frame_obj):

    load_resources()

    get_all_gftz_obj(gftzs_json)

    global gftzs

    # 清除之前的组件
    scrollbar_frame_obj.destroy_components()

    create_gftz_interface(scrollbar_frame_obj, gftzs)

    # scrollbar_frame_obj.update_canvas()
    return "break"  # 阻止事件冒泡




