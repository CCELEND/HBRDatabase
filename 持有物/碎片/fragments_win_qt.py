
from tools import load_json
from 持有物.holding_win_qt import show_holding

fragments_dir = {}

def load_resources():
    global fragments_dir
    if fragments_dir:
        return
    fragments_dir = load_json("./持有物/碎片/fragments.json")


def show_fragments(scrollbar_frame_obj):
    load_resources()
    scrollbar_frame_obj.destroy_components()
    show_holding(scrollbar_frame_obj.scrollable_frame, fragments_dir)
    scrollbar_frame_obj.update_canvas()

