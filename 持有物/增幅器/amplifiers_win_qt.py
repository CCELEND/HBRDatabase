
from tools import load_json
from 持有物.holding_win_qt import show_holding

amplifiers_dir = {}

def load_resources():
    global amplifiers_dir
    if amplifiers_dir:
        return
    amplifiers_dir = load_json("./持有物/增幅器/amplifiers.json")


def show_amplifiers(scrollbar_frame_obj):
    load_resources()
    scrollbar_frame_obj.destroy_components()
    show_holding(scrollbar_frame_obj.scrollable_frame, amplifiers_dir)
    scrollbar_frame_obj.update_canvas()

