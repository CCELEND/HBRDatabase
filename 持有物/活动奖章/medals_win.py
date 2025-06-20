

from tools import load_json
from holding_win import show_holding

medals_dir = {}
# 加载资源文件
def load_resources():
    global medals_dir
    if medals_dir:
        return
    medals_dir = load_json("./持有物/活动奖章/medals.json")

# 加载图片并显示的函数
def show_medals(scrollbar_frame_obj):

    load_resources()

    # 清除之前的组件
    scrollbar_frame_obj.destroy_components()

    show_holding(scrollbar_frame_obj.scrollable_frame, medals_dir)

    scrollbar_frame_obj.update_canvas()



