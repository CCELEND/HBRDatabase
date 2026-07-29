
from tools import load_json
from 持有物.holding_win_qt import show_holding

jewelry_materials_dir = {}

def load_resources():
    global jewelry_materials_dir
    if jewelry_materials_dir:
        return
    jewelry_materials_dir = load_json("./持有物/饰品材料/jewelry_materials.json")


def show_jewelry_materials(scrollbar_frame_obj):
    load_resources()
    scrollbar_frame_obj.destroy_components()
    show_holding(scrollbar_frame_obj.scrollable_frame, jewelry_materials_dir)
    scrollbar_frame_obj.update_canvas()

