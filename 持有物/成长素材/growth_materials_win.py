
from tools import load_json
from holding_win import show_holding

growth_materials_dir = {}
# 加载资源文件
def load_resources():
    global growth_materials_dir
    if growth_materials_dir:
        return
    growth_materials_dir = load_json("./持有物/成长素材/growth_materials.json")

# 加载图片并显示的函数
def show_growth_materials(scrollbar_frame_obj):

    load_resources()

    # 清除之前的组件
    scrollbar_frame_obj.destroy_components()

    show_holding(scrollbar_frame_obj.scrollable_frame, growth_materials_dir)

    scrollbar_frame_obj.update_canvas()



