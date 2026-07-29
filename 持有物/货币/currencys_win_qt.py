
from tools import load_json
from 持有物.holding_win_qt import show_holding

currencys_dir = {}

def load_resources():
    global currencys_dir
    if currencys_dir:
        return
    currencys_dir = load_json("./持有物/货币/currencys.json")


def show_currencys(scrollbar_frame_obj):
    load_resources()
    scrollbar_frame_obj.destroy_components()
    show_holding(scrollbar_frame_obj.scrollable_frame, currencys_dir)
    scrollbar_frame_obj.update_canvas()

