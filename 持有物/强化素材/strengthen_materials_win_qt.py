
from 持有物.holding_win_qt import show_holding

import 持有物.强化素材.strengthen_materials


def show_strengthen_materials(scrollbar_frame_obj):
    持有物.强化素材.strengthen_materials.load_resources()
    scrollbar_frame_obj.destroy_components()
    show_holding(scrollbar_frame_obj.scrollable_frame, 持有物.强化素材.strengthen_materials.strengthen_materials_dir)
    scrollbar_frame_obj.update_canvas()

