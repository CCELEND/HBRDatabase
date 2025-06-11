
from tools import load_json
from holding_win import show_holding

chips_dir = {}
# 加载资源文件
def load_resources():
    global chips_dir
    if chips_dir:
        return
    chips_dir = load_json("./持有物/芯片/chips.json")

# 加载图片并显示的函数
def show_chips(scrollbar_frame_obj):

    load_resources()

    # 清除之前的组件
    scrollbar_frame_obj.destroy_components()

    show_holding(scrollbar_frame_obj.scrollable_frame, chips_dir)

    scrollbar_frame_obj.update_canvas()



