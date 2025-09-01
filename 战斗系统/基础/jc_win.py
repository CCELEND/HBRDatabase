
from canvas_events import ImageViewerWithScrollbar
from window import set_window_icon, creat_Toplevel
from window import win_open_manage, win_close_manage, is_win_open, win_set_top

def creat_jc_win(parent_frame):

    jc_logo_path = "./help.ico"
    jc_img_path = "./战斗系统/基础/基础.png"

    # 重复打开时，窗口置顶并直接返回
    if is_win_open("基础", __name__):
        win_set_top("基础", __name__)
        return "break"

    jc_win_frame = creat_Toplevel('基础', 600, 840, 190, 120)
    set_window_icon(jc_win_frame, jc_logo_path)
    win_open_manage(jc_win_frame, __name__)

    # 创建 ImageViewerWithScrollbar 实例
    jc_image_viewer = ImageViewerWithScrollbar(jc_win_frame, 600, 840, jc_img_path)

    # 绑定鼠标点击事件到父窗口，点击置顶
    jc_win_frame.bind("<Button-1>", win_set_top(jc_win_frame, __name__))
    # 窗口关闭时清理
    jc_win_frame.protocol("WM_DELETE_WINDOW", 
        lambda: win_close_manage(jc_win_frame, __name__, jc_image_viewer))

    return "break"  # 阻止事件冒泡

