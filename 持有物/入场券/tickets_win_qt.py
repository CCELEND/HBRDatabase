
from tools import load_json
from 持有物.holding_win_qt import show_holding

tickets_dir = {}

def load_resources():
    global tickets_dir
    if tickets_dir:
        return
    tickets_dir = load_json("./持有物/入场券/tickets.json")


def show_tickets(scrollbar_frame_obj):
    load_resources()
    scrollbar_frame_obj.destroy_components()
    show_holding(scrollbar_frame_obj.scrollable_frame, tickets_dir)
    scrollbar_frame_obj.update_canvas()

