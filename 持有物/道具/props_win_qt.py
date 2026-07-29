
from tools import load_json
from 持有物.holding_win_qt import show_holding

props_dir = {}

def load_resources():
    global props_dir
    if props_dir:
        return
    props_dir = load_json("./持有物/道具/props.json")


def show_props(scrollbar_frame_obj):
    load_resources()
    scrollbar_frame_obj.destroy_components()
    show_holding(scrollbar_frame_obj.scrollable_frame, props_dir)
    scrollbar_frame_obj.update_canvas()

