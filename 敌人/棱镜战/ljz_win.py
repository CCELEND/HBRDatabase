
import ttkbootstrap as ttk
from ttkbootstrap.constants import *

from canvas_events import bind_canvas_events, get_photo, create_canvas_with_image
from canvas_events import mouse_bind_canvas_events
from canvas_events import ImageViewerWithScrollbar
from window import set_window_icon, creat_Toplevel, set_window_top

from tools import load_json
from 棱镜战.ljz_info import ljzs, get_all_ljz_obj

ljzs_json = {}
# 加载资源文件
def load_resources():
    global ljzs_json
    if ljzs_json:
        return
    ljzs_json = load_json("./敌人/棱镜战/ljz.json")

# 绑定棱镜战 canvas 的事件
def bind_ljz_canvas(parent_frame, ljz, x, y):

    photo = get_photo(ljz.img_path, (128, 176))
    canvas = create_canvas_with_image(parent_frame, 
        photo, 150, 176, 60, 0, x, y)
    mouse_bind_canvas_events(canvas)

    if ljz.guide_path:
        bind_canvas_events(canvas, 
            creat_ljz_win, parent_frame=parent_frame, 
            ljz=ljz)

open_ljz_wins = {}
#关闭窗口时，清除窗口字典中的句柄，并销毁窗口
def ljz_win_closing(parent_frame):

    open_ljz_win = parent_frame.title()
    while open_ljz_win in open_ljz_wins:
        del open_ljz_wins[open_ljz_win]

    parent_frame.destroy()  # 销毁窗口

def creat_ljz_win(event, parent_frame, ljz):

    # 重复打开时，窗口置顶并直接返回
    if ljz.name in open_ljz_wins:
        # 判断窗口是否存在
        if open_ljz_wins[ljz.name].winfo_exists():
            set_window_top(open_ljz_wins[ljz.name])
            return "break"
        del open_ljz_wins[ljz.name]


    ljz_win_frame = creat_Toplevel(ljz.name, 600, 840, 230, 110)
    set_window_icon(ljz_win_frame, ljz.logo_path)
    open_ljz_wins[ljz.name] = ljz_win_frame

    # 创建 ImageViewerWithScrollbar 实例
    ljz_image_viewer = ImageViewerWithScrollbar(ljz_win_frame, 600, 840, ljz.guide_path)

    # 绑定鼠标点击事件到父窗口，点击置顶
    ljz_win_frame.bind("<Button-1>", lambda event: set_window_top(ljz_win_frame))
    # 窗口关闭时清理
    ljz_win_frame.protocol("WM_DELETE_WINDOW", lambda: ljz_win_closing(ljz_win_frame))

    return "break"  # 阻止事件冒泡


# 加载图片并显示的函数
def show_ljz_enemys(scrollbar_frame_obj):

    load_resources()

    get_all_ljz_obj(ljzs_json)

    global ljzs

    # 清除之前的组件
    scrollbar_frame_obj.destroy_components()

    column_count = 0
    for i, ljz_name in enumerate(ljzs):
        # 棱镜战敌人对象
        ljz = ljzs[ljz_name]

        ljz_frame = ttk.LabelFrame(scrollbar_frame_obj.scrollable_frame, text=ljz_name)
        bind_ljz_canvas(ljz_frame, ljz, 0, 0)

        # 计算行和列的位置
        row = i // 5  # 每5个换行
        column = i % 5  # 列位置
        ljz_frame.grid(row=row, column=column, padx=(10,0), pady=(0,5), sticky="nesw")  # 设置间距
        ljz_frame.grid_rowconfigure(0, weight=1)
        ljz_frame.grid_columnconfigure(0, weight=1)

        column_count += 1  # 更新列计数器
        if column_count == 5:  # 如果已经到达第5列，重置列计数器并增加行
            column_count = 0


    scrollbar_frame_obj.update_canvas()
    return "break"  # 阻止事件冒泡
