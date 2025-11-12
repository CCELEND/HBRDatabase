
import ttkbootstrap as ttk
from ttkbootstrap.constants import *


from canvas_events import bind_canvas_events, get_photo, create_canvas_with_image
from canvas_events import mouse_bind_canvas_events
from canvas_events import ImageViewerWithScrollbar
from window import set_window_icon, creat_Toplevel
from window import win_open_manage, win_close_manage, is_win_open, win_set_top


from tools import load_json
from 光球BOSS.gqboss_info import gqbosss, get_all_gqboss_obj

gqbosss_json = {}
# 加载资源文件
def load_resources():
    global gqbosss_json
    if gqbosss_json:
        return
    gqbosss_json = load_json("./敌人/光球BOSS/gqboss.json")

# 绑定光球BOSS canvas 的事件
def bind_gqboss_canvas(parent_frame, gqboss, x, y):

    photo = get_photo(gqboss.img_path, (149, 210))
    canvas = create_canvas_with_image(parent_frame, 
        photo, 160, 210, 20, 0, x, y)
    mouse_bind_canvas_events(canvas)

    if gqboss.guide_path:
        bind_canvas_events(canvas, 
            creat_gqboss_win, parent_frame=parent_frame, 
            gqboss=gqboss)

def creat_gqboss_win(event, parent_frame, gqboss):

    print(gqboss.name)

    # 重复打开时，窗口置顶并直接返回
    if is_win_open(gqboss.name, __name__):
        win_set_top(gqboss.name, __name__)
        return "break"

    if "攻略" in gqboss.name:
        gqboss_win_frame = creat_Toplevel(gqboss.name, 600, 840, 230, 110)
    else:
        gqboss_win_frame = creat_Toplevel(gqboss.name, 600, 840, 230, 110)
    set_window_icon(gqboss_win_frame, gqboss.logo_path)
    win_open_manage(gqboss_win_frame, __name__)

    # 创建 ImageViewerWithScrollbar 实例
    gqboss_image_viewer = ImageViewerWithScrollbar(gqboss_win_frame, 600, 840, gqboss.guide_path)

    # 绑定鼠标点击事件到父窗口，点击置顶
    gqboss_win_frame.bind("<Button-1>", win_set_top(gqboss_win_frame, __name__))
    # 窗口关闭时清理
    gqboss_win_frame.protocol("WM_DELETE_WINDOW", 
        lambda: win_close_manage(gqboss_win_frame, __name__, gqboss_image_viewer))

    return "break"  # 阻止事件冒泡


# 加载图片并显示的函数
def show_gqboss_enemys(scrollbar_frame_obj):

    load_resources()

    get_all_gqboss_obj(gqbosss_json)

    global gqbosss

    # 清除之前的组件
    scrollbar_frame_obj.destroy_components()

    column_count = 0
    for i, gqboss_name in enumerate(gqbosss):
        # 光球BOSS敌人对象
        gqboss = gqbosss[gqboss_name]

        gqboss_frame = ttk.Labelframe(scrollbar_frame_obj.scrollable_frame, text=gqboss_name)
        bind_gqboss_canvas(gqboss_frame, gqboss, 0, 0)

        # 计算行和列的位置
        row = i // 5  # 每5个换行
        column = i % 5  # 列位置
        gqboss_frame.grid(row=row, column=column, padx=(10,0), pady=(0,5), sticky="nesw")  # 设置间距
        gqboss_frame.grid_rowconfigure(0, weight=1)
        gqboss_frame.grid_columnconfigure(0, weight=1)

        column_count += 1  # 更新列计数器
        if column_count == 5:  # 如果已经到达第5列，重置列计数器并增加行
            column_count = 0


    scrollbar_frame_obj.update_canvas()
    return "break"  # 阻止事件冒泡
