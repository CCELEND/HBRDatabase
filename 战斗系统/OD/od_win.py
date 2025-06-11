
from canvas_events import ImageViewerWithScrollbar
from window import set_window_icon, creat_Toplevel, set_window_top

open_od_wins = {}
#关闭窗口时，清除窗口字典中的句柄，并销毁窗口
def od_win_closing(parent_frame):

    open_od_win = parent_frame.title()
    while open_od_win in open_od_wins:
        del open_od_wins[open_od_win]

    parent_frame.destroy()  # 销毁窗口

def creat_od_win(parent_frame):

    od_logo_path = "./战斗系统/OD/OD.ico"
    od_img_path = "./战斗系统/OD/OD.png"

    # 重复打开时，窗口置顶并直接返回
    if 'OD' in open_od_wins:
        # 判断窗口是否存在
        if open_od_wins['OD'].winfo_exists():
            set_window_top(open_od_wins['OD'])
            return "break"
        del open_od_wins['OD']

    od_win_frame = creat_Toplevel('OD', 1100, 386, 330, 220)
    set_window_icon(od_win_frame, od_logo_path)
    open_od_wins['OD'] = od_win_frame

    # 创建 ImageViewerWithScrollbar 实例
    od_image_viewer = ImageViewerWithScrollbar(od_win_frame, 1100, 386, od_img_path)

    # 绑定鼠标点击事件到父窗口，点击置顶
    od_win_frame.bind("<Button-1>", lambda event: set_window_top(od_win_frame))
    # 窗口关闭时清理
    od_win_frame.protocol("WM_DELETE_WINDOW", lambda: od_win_closing(od_win_frame))

    return "break"  # 阻止事件冒泡

