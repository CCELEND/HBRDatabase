
from canvas_events import ImageViewerWithScrollbar
from window import set_window_icon, creat_Toplevel
from window import win_open_manage, win_close_manage, is_win_open, win_set_top

def creat_od_win(parent_frame):

    od_logo_path = "./战斗系统/OD/OD.ico"
    od_img_path = "./战斗系统/OD/OD.png"

    # 重复打开时，窗口置顶并直接返回
    if is_win_open('OD', __name__):
        win_set_top('OD', __name__)
        return "break"

    od_win_frame = creat_Toplevel('OD', 1100, 386, 330, 220)
    set_window_icon(od_win_frame, od_logo_path)
    win_open_manage(od_win_frame, __name__)

    # 创建 ImageViewerWithScrollbar 实例
    od_image_viewer = ImageViewerWithScrollbar(od_win_frame, 1100, 386, od_img_path)

    # 绑定鼠标点击事件到父窗口，点击置顶
    od_win_frame.bind("<Button-1>", win_set_top(od_win_frame, __name__))
    # 窗口关闭时清理
    od_win_frame.protocol("WM_DELETE_WINDOW", 
        lambda: win_close_manage(od_win_frame, __name__, od_image_viewer))

    return "break"  # 阻止事件冒泡

