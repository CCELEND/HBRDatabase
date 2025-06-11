
from tools import load_json
from holding_win import show_holding

props_dir = {}
# 加载资源文件
def load_resources():
    global props_dir
    if props_dir:
        return
    props_dir = load_json("./持有物/道具/props.json")

# 加载图片并显示的函数
def show_props(scrollbar_frame_obj):

    load_resources()

    # 清除之前的组件
    scrollbar_frame_obj.destroy_components()

    show_holding(scrollbar_frame_obj.scrollable_frame, props_dir)

    scrollbar_frame_obj.update_canvas()



