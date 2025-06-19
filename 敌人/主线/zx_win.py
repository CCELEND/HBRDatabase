
import ttkbootstrap as ttk
from ttkbootstrap.constants import *

from canvas_events import bind_canvas_events, get_photo, create_canvas_with_image, ArtworkDisplayerHeight
from canvas_events import mouse_bind_canvas_events
from canvas_events import ImageViewerWithScrollbar
from window import set_window_icon, creat_Toplevel, set_window_top

from tools import load_json
from 主线.zx_info import zxs, get_all_zx_obj

zxs_json = {}
# 加载资源文件
def load_resources():
    global zxs_json
    if zxs_json:
        return
    zxs_json = load_json("./敌人/主线/zx.json")

# 绑定主线 canvas 的事件
def bind_zx_canvas(parent_frame, zx, x, y):

    photo = get_photo(zx.img_path, (90, 90))
    canvas = create_canvas_with_image(parent_frame, 
        photo, 130, 130, 20, 20, x, y)
    mouse_bind_canvas_events(canvas)

    if zx.guide_path:
        bind_canvas_events(canvas, 
            creat_zx_win, parent_frame=parent_frame, 
            zx=zx)

open_zx_wins = {}
#关闭窗口时，清除窗口字典中的句柄，并销毁窗口
def zx_win_closing(parent_frame):

    open_zx_win = parent_frame.title()
    while open_zx_win in open_zx_wins:
        del open_zx_wins[open_zx_win]

    parent_frame.destroy()  # 销毁窗口

def creat_zx_win(event, parent_frame, zx):

    # 重复打开时，窗口置顶并直接返回
    if zx.name in open_zx_wins:
        # 判断窗口是否存在
        if open_zx_wins[zx.name].winfo_exists():
            set_window_top(open_zx_wins[zx.name])
            return "break"
        del open_zx_wins[zx.name]


    zx_win_frame = creat_Toplevel(zx.name, 600, 840, 200, 120)
    set_window_icon(zx_win_frame, zx.logo_path)
    open_zx_wins[zx.name] = zx_win_frame

    # 创建 ImageViewerWithScrollbar 实例
    zx_image_viewer = ImageViewerWithScrollbar(zx_win_frame, 600, 840, zx.guide_path)

    # 绑定鼠标点击事件到父窗口，点击置顶
    zx_win_frame.bind("<Button-1>", lambda event: set_window_top(zx_win_frame))
    # 窗口关闭时清理
    zx_win_frame.protocol("WM_DELETE_WINDOW", lambda: zx_win_closing(zx_win_frame))

    return "break"  # 阻止事件冒泡


# 加载图片并显示的函数
def show_zx_enemys(scrollbar_frame_obj):

    load_resources()

    get_all_zx_obj(zxs_json)

    global zxs

    # 清除之前的组件
    scrollbar_frame_obj.destroy_components()

    column_count = 0
    for i, zx_name in enumerate(zxs):
        # 主线敌人对象
        zx = zxs[zx_name]

        zx_frame = ttk.LabelFrame(scrollbar_frame_obj.scrollable_frame, text=zx_name)
        bind_zx_canvas(zx_frame, zx, 0, 0)

        # 计算行和列的位置
        row = i // 5  # 每5个换行
        column = i % 5  # 列位置
        zx_frame.grid(row=row, column=column, padx=(10,0), pady=(0,5), sticky="nesw")  # 设置间距
        zx_frame.grid_rowconfigure(0, weight=1)
        zx_frame.grid_columnconfigure(0, weight=1)

        column_count += 1  # 更新列计数器
        if column_count == 5:  # 如果已经到达第5列，重置列计数器并增加行
            column_count = 0


    scrollbar_frame_obj.update_canvas()
    return "break"  # 阻止事件冒泡
