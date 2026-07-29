
from tools import load_json
from 持有物.holding_win_qt import show_holding

medals_dir = {}

def load_resources():
    global medals_dir
    if medals_dir:
        return
    medals_dir = load_json("./持有物/活动奖章/medals.json")


def show_medals(scrollbar_frame_obj):
    load_resources()
    scrollbar_frame_obj.destroy_components()
    show_holding(scrollbar_frame_obj.scrollable_frame, medals_dir)
    scrollbar_frame_obj.update_canvas()

