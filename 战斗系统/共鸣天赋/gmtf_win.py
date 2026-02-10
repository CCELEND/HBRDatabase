
from canvas_events import ImageViewerWithScrollbar
from window import set_window_icon, creat_Toplevel
from window import win_open_manage, win_close_manage, is_win_open, win_set_top

def creat_gmtf_win(parent_frame):

    gmtf_logo_path = "./help.ico"
    gmtf_img_path = "./战斗系统/共鸣天赋/共鸣天赋.png"

    # 重复打开时，窗口置顶并直接返回
    if is_win_open("共鸣天赋", __name__):
        win_set_top("共鸣天赋", __name__)
        return "break"

    gmtf_win_frame = creat_Toplevel('共鸣天赋', 1300, 731, 190, 120)
    set_window_icon(gmtf_win_frame, gmtf_logo_path)
    win_open_manage(gmtf_win_frame, __name__)

    # 创建 ImageViewerWithScrollbar 实例
    gmtf_image_viewer = ImageViewerWithScrollbar(gmtf_win_frame, 1300, 731, gmtf_img_path)

    # 绑定鼠标点击事件到父窗口，点击置顶
    gmtf_win_frame.bind("<Button-1>", win_set_top(gmtf_win_frame, __name__))
    # 窗口关闭时清理
    gmtf_win_frame.protocol("WM_DELETE_WINDOW", 
        lambda: win_close_manage(gmtf_win_frame, __name__, gmtf_image_viewer))

    return "break"  # 阻止事件冒泡

