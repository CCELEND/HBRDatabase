
import ttkbootstrap as ttk
from ttkbootstrap.constants import *

from canvas_events import get_photo, create_canvas_with_image

import 战斗系统.职业.careers_info
import 战斗系统.属性.attributes_info

# 职能 frame
def creat_career_frame(parent_frame, career_frame_row, style):

    element_attribute = style.element_attribute if style.element_attribute is not None else "无"

    career = 战斗系统.职业.careers_info.careers[style.career]
    career_frame = ttk.LabelFrame(parent_frame, text=style.career+"-"+element_attribute)
    career_frame.grid(row=career_frame_row, column=0, columnspan=4, padx=10, pady=5, sticky="nsew")
    career_frame.grid_rowconfigure(0, weight=1)

    career_photo = get_photo(career.path, (200, 40))
    career_canvas = create_canvas_with_image(career_frame, 
        career_photo, 240, 40, 20, 0, 0, 0)

    if len(element_attribute) == 1:
        element_attribute_path = 战斗系统.属性.attributes_info.attributes[element_attribute].path
        element_attribute_photo = get_photo(element_attribute_path, (40, 40))
        element_attribute_canvas = create_canvas_with_image(career_frame, 
            element_attribute_photo, 80, 40, 0, 0, 0, 1)
    else:
        element_attribute_path0  = 战斗系统.属性.attributes_info.attributes[element_attribute[0]].path
        element_attribute_path1  = 战斗系统.属性.attributes_info.attributes[element_attribute[1]].path

        element_attribute_photo = get_photo(element_attribute_path0, (40, 40))
        element_attribute_canvas = create_canvas_with_image(career_frame, 
            element_attribute_photo, 60, 40, 0, 0, 0, 1)

        element_attribute_photo1 = get_photo(element_attribute_path1, (40, 40))
        element_attribute_canvas = create_canvas_with_image(career_frame, 
            element_attribute_photo1, 40, 40, 0, 0, 0, 2)

