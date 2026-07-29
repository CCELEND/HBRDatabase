
from tools import load_json
from 持有物.holding_win_qt import show_holding

main_props_dir = {}

def load_resources():
    global main_props_dir
    if main_props_dir:
        return
    main_props_dir = load_json("./持有物/主线道具/main_props.json")


def show_main_props(scrollbar_frame_obj):
    load_resources()
    scrollbar_frame_obj.destroy_components()
    show_holding(scrollbar_frame_obj.scrollable_frame, main_props_dir)
    scrollbar_frame_obj.update_canvas()

