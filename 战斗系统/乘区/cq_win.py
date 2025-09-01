
from canvas_events import ImageViewerWithScrollbar
from window import set_window_icon, creat_Toplevel
from window import win_open_manage, win_close_manage, is_win_open, win_set_top

def creat_cq_win(parent_frame):

    cq_logo_path = "./战斗系统/乘区/乘区.ico"
    cq_img_path = "./战斗系统/乘区/乘区.png"

    # 重复打开时，窗口置顶并直接返回
    if is_win_open("乘区", __name__):
        win_set_top("乘区", __name__)
        return "break"

    cq_win_frame = creat_Toplevel('乘区', 820, 500, 330, 220)
    set_window_icon(cq_win_frame, cq_logo_path)
    win_open_manage(cq_win_frame, __name__)

    # 创建 ImageViewerWithScrollbar 实例
    cq_image_viewer = ImageViewerWithScrollbar(cq_win_frame, 820, 500, cq_img_path)

    # 绑定鼠标点击事件到父窗口，点击置顶
    cq_win_frame.bind("<Button-1>", win_set_top(cq_win_frame, __name__))
    # 窗口关闭时清理
    cq_win_frame.protocol("WM_DELETE_WINDOW", 
        lambda: win_close_manage(cq_win_frame, __name__, cq_image_viewer))

    return "break"  # 阻止事件冒泡

