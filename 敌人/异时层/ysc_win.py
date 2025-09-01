
import ttkbootstrap as ttk
from ttkbootstrap.constants import *


from canvas_events import bind_canvas_events, get_photo, create_canvas_with_image, ArtworkDisplayerHeight
from canvas_events import mouse_bind_canvas_events
from canvas_events import ImageViewerWithScrollbar
from window import set_window_icon, creat_Toplevel
from window import win_open_manage, win_close_manage, is_win_open, win_set_top

from tools import load_json
from 异时层.ysc_info import yscs, get_all_ysc_obj

yscs_json = {}
# 加载资源文件
def load_resources():
    global yscs_json
    if yscs_json:
        return
    yscs_json = load_json("./敌人/异时层/yscs.json")

# 绑定异时层 canvas 的事件
def bind_ysc_enemy_canvas(parent_frame, ysc, x, y):
    photo = get_photo(ysc.img_path, (90, 90))
    canvas = create_canvas_with_image(parent_frame, 
        photo, 130, 130, 20, 20, x, y)
    mouse_bind_canvas_events(canvas)
    bind_canvas_events(canvas, 
        creat_ysc_enemy_win, parent_frame=parent_frame, 
        ysc=ysc)


def creat_ysc_enemy_win(event, parent_frame, ysc):

    # 重复打开时，窗口置顶并直接返回
    if is_win_open(ysc.name, __name__):
        win_set_top(ysc.name, __name__)
        return "break"
        
    ysc_win_frame = creat_Toplevel(ysc.name, 600, 840, 200, 120)
    set_window_icon(ysc_win_frame, ysc.logo_path)
    win_open_manage(ysc_win_frame, __name__)

    # 创建 ImageViewerWithScrollbar 实例
    ysc_image_viewer = ImageViewerWithScrollbar(ysc_win_frame, 600, 840, ysc.guide_path)

    # 绑定鼠标点击事件到父窗口，点击置顶
    ysc_win_frame.bind("<Button-1>", win_set_top(ysc_win_frame, __name__))
    # 窗口关闭时清理
    ysc_win_frame.protocol("WM_DELETE_WINDOW", 
        lambda: win_close_manage(ysc_win_frame, __name__, ysc_image_viewer))


    return "break"  # 阻止事件冒泡


# 加载图片并显示的函数
def show_ysc_enemys(scrollbar_frame_obj):

    load_resources()

    get_all_ysc_obj(yscs_json)

    global yscs

    # 清除之前的组件
    scrollbar_frame_obj.destroy_components()

    column_count = 0
    for i, ysc_name in enumerate(yscs):
        # 异时层敌人对象
        ysc = yscs[ysc_name]

        ysc_enemy_frame = ttk.LabelFrame(scrollbar_frame_obj.scrollable_frame, text=ysc_name)
        bind_ysc_enemy_canvas(ysc_enemy_frame, ysc, 0, 0)

        # 计算行和列的位置
        row = i // 5  # 每5个换行
        column = i % 5  # 列位置
        ysc_enemy_frame.grid(row=row, column=column, padx=(10,0), pady=(0,5), sticky="nesw")  # 设置间距
        ysc_enemy_frame.grid_rowconfigure(0, weight=1)
        ysc_enemy_frame.grid_columnconfigure(0, weight=1)

        column_count += 1  # 更新列计数器
        if column_count == 5:  # 如果已经到达第5列，重置列计数器并增加行
            column_count = 0


    scrollbar_frame_obj.update_canvas()
    return "break"  # 阻止事件冒泡
