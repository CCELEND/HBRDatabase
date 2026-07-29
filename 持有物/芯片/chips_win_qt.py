
from tools import load_json
from 持有物.holding_win_qt import show_holding

chips_dir = {}

def load_resources():
    global chips_dir
    if chips_dir:
        return
    chips_dir = load_json("./持有物/芯片/chips.json")


def show_chips(scrollbar_frame_obj):
    load_resources()
    scrollbar_frame_obj.destroy_components()
    show_holding(scrollbar_frame_obj.scrollable_frame, chips_dir)
    scrollbar_frame_obj.update_canvas()

