
import ttkbootstrap as ttk
from ttkbootstrap.constants import *


from canvas_events import bind_canvas_events, get_photo, create_canvas_with_image
from canvas_events import mouse_bind_canvas_events
from canvas_events import ImageViewerWithScrollbar
from window import set_window_icon, creat_Toplevel, set_window_top

from tools import load_json
from 宝石棱镜战.bsljz_info import bsljzs, get_all_bsljz_obj

bsljzs_json = {}
# 加载资源文件
def load_resources():
    global bsljzs_json
    if bsljzs_json:
        return
    bsljzs_json = load_json("./敌人/宝石棱镜战/bsljz.json")

# 绑定宝石棱镜战 canvas 的事件
def bind_bsljz_canvas(parent_frame, bsljz, x, y):

    photo = get_photo(bsljz.img_path, (128, 176))
    canvas = create_canvas_with_image(parent_frame, 
        photo, 150, 176, 35, 0, x, y)
    mouse_bind_canvas_events(canvas)

    if bsljz.guide_path:
        bind_canvas_events(canvas, 
            creat_bsljz_win, parent_frame=parent_frame, 
            bsljz=bsljz)

open_bsljz_wins = {}
#关闭窗口时，清除窗口字典中的句柄，并销毁窗口
def bsljz_win_closing(parent_frame):

    open_bsljz_win = parent_frame.title()
    while open_bsljz_win in open_bsljz_wins:
        del open_bsljz_wins[open_bsljz_win]

    parent_frame.destroy()  # 销毁窗口

def creat_bsljz_win(event, parent_frame, bsljz):

    # 重复打开时，窗口置顶并直接返回
    if bsljz.name in open_bsljz_wins:
        # 判断窗口是否存在
        if open_bsljz_wins[bsljz.name].winfo_exists():
            set_window_top(open_bsljz_wins[bsljz.name])
            return "break"
        del open_bsljz_wins[bsljz.name]


    bsljz_win_frame = creat_Toplevel(bsljz.name, 600, 840, 440, 50)
    set_window_icon(bsljz_win_frame, bsljz.logo_path)
    open_bsljz_wins[bsljz.name] = bsljz_win_frame

    # 创建 ImageViewerWithScrollbar 实例
    bsljz_image_viewer = ImageViewerWithScrollbar(bsljz_win_frame, 600, 840, bsljz.guide_path)

    # 绑定鼠标点击事件到父窗口，点击置顶
    bsljz_win_frame.bind("<Button-1>", lambda event: set_window_top(bsljz_win_frame))
    # 窗口关闭时清理
    bsljz_win_frame.protocol("WM_DELETE_WINDOW", lambda: bsljz_win_closing(bsljz_win_frame))

    return "break"  # 阻止事件冒泡


# 加载图片并显示的函数
def show_bsljz_enemys(scrollbar_frame_obj):

    load_resources()

    get_all_bsljz_obj(bsljzs_json)

    global bsljzs

    # 清除之前的组件
    scrollbar_frame_obj.destroy_components()

    column_count = 0
    for i, bsljz_name in enumerate(bsljzs):
        # 宝石棱镜战敌人对象
        bsljz = bsljzs[bsljz_name]

        bsljz_frame = ttk.LabelFrame(scrollbar_frame_obj.scrollable_frame, text=bsljz_name)
        bind_bsljz_canvas(bsljz_frame, bsljz, 0, 0)

        # 计算行和列的位置
        row = i // 5  # 每5个换行
        column = i % 5  # 列位置
        bsljz_frame.grid(row=row, column=column, padx=(10,0), pady=(0,5), sticky="nesw")  # 设置间距
        bsljz_frame.grid_rowconfigure(0, weight=1)
        bsljz_frame.grid_columnconfigure(0, weight=1)

        column_count += 1  # 更新列计数器
        if column_count == 5:  # 如果已经到达第5列，重置列计数器并增加行
            column_count = 0


    scrollbar_frame_obj.update_canvas()
    return "break"  # 阻止事件冒泡
