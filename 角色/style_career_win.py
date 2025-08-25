
import ttkbootstrap as ttk
from ttkbootstrap.constants import *

from canvas_events import get_photo, create_canvas_with_image

import 战斗系统.职业.careers_info

# 职能 frame
def creat_career_frame(parent_frame, career_frame_row, style):

    career = 战斗系统.职业.careers_info.careers[style.career]
    career_frame = ttk.LabelFrame(parent_frame, text=style.career)
    career_frame.grid(row=career_frame_row, column=0, columnspan=4, padx=10, pady=5, sticky="nsew")
    career_frame.grid_rowconfigure(0, weight=1)

    career_photo = get_photo(career.path, (200, 40))
    career_canvas = create_canvas_with_image(career_frame, 
        career_photo, 240, 40, 20, 0, 0, 0)