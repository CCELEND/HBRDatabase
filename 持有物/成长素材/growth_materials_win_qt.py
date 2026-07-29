
from tools import load_json
from 持有物.holding_win_qt import show_holding

growth_materials_dir = {}

def load_resources():
    global growth_materials_dir
    if growth_materials_dir:
        return
    growth_materials_dir = load_json("./持有物/成长素材/growth_materials.json")


def show_growth_materials(scrollbar_frame_obj):
    load_resources()
    scrollbar_frame_obj.destroy_components()
    show_holding(scrollbar_frame_obj.scrollable_frame, growth_materials_dir)
    scrollbar_frame_obj.update_canvas()

