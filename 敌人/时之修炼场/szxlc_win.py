
import ttkbootstrap as ttk
from ttkbootstrap.constants import *

from canvas_events import bind_canvas_events, get_photo, create_canvas_with_image
from canvas_events import mouse_bind_canvas_events
from canvas_events import ImageViewerWithScrollbar
from window import set_window_icon, creat_Toplevel
from window import win_open_manage, win_close_manage, is_win_open, win_set_top

from tools import load_json
from 时之修炼场.szxlc_info import szxlcs, get_all_szxlc_obj

szxlcs_json = {}
# 加载资源文件
def load_resources():
    global szxlcs_json
    if szxlcs_json:
        return
    szxlcs_json = load_json("./敌人/时之修炼场/szxlc.json")

# 绑定时之修炼场 canvas 的事件
def bind_szxlc_canvas(parent_frame, szxlc, x, y):

    photo = get_photo(szxlc.img_path, (90, 90))
    canvas = create_canvas_with_image(parent_frame, 
        photo, 130, 130, 20, 20, x, y)
    mouse_bind_canvas_events(canvas)

    if szxlc.guide_path:
        bind_canvas_events(canvas, 
            creat_szxlc_win, parent_frame=parent_frame, 
            szxlc=szxlc)

def creat_szxlc_win(event, parent_frame, szxlc):

    # 重复打开时，窗口置顶并直接返回
    if is_win_open(szxlc.name, __name__):
        win_set_top(szxlc.name, __name__)
        return "break"


    szxlc_win_frame = creat_Toplevel(szxlc.name, 600, 840, 230, 110)
    set_window_icon(szxlc_win_frame, szxlc.logo_path)
    win_open_manage(szxlc_win_frame, __name__)

    # 创建 ImageViewerWithScrollbar 实例
    szxlc_image_viewer = ImageViewerWithScrollbar(szxlc_win_frame, 600, 840, szxlc.guide_path)

    # 绑定鼠标点击事件到父窗口，点击置顶
    szxlc_win_frame.bind("<Button-1>", win_set_top(szxlc_win_frame, __name__))
    # 窗口关闭时清理
    szxlc_win_frame.protocol("WM_DELETE_WINDOW", 
        lambda: win_close_manage(szxlc_win_frame, __name__, szxlc_image_viewer))

    return "break"  # 阻止事件冒泡


# 加载图片并显示的函数
def show_szxlc_enemys(scrollbar_frame_obj):

    load_resources()

    get_all_szxlc_obj(szxlcs_json)

    global szxlcs

    # 清除之前的组件
    scrollbar_frame_obj.destroy_components()

    column_count = 0
    for i, szxlc_name in enumerate(szxlcs):
        # 时之修炼场敌人对象
        szxlc = szxlcs[szxlc_name]

        szxlc_frame = ttk.Labelframe(scrollbar_frame_obj.scrollable_frame, text=szxlc_name)
        bind_szxlc_canvas(szxlc_frame, szxlc, 0, 0)

        # 计算行和列的位置
        row = i // 5  # 每5个换行
        column = i % 5  # 列位置
        szxlc_frame.grid(row=row, column=column, padx=(10,0), pady=(0,5), sticky="nesw")  # 设置间距
        szxlc_frame.grid_rowconfigure(0, weight=1)
        szxlc_frame.grid_columnconfigure(0, weight=1)

        column_count += 1  # 更新列计数器
        if column_count == 5:  # 如果已经到达第5列，重置列计数器并增加行
            column_count = 0


    scrollbar_frame_obj.update_canvas()
    return "break"  # 阻止事件冒泡
