
import ttkbootstrap as ttk
from ttkbootstrap.constants import *

from canvas_events import get_photo, create_canvas_with_image

import 持有物.强化素材.strengthen_materials

# 宝珠强化
def creat_growth_ability_frame(parent_frame, style):
    
    growth_ability_frame = ttk.LabelFrame(parent_frame, text="强化")
    growth_ability_frame.grid(row=3, column=0, columnspan=4, padx=5, pady=5, sticky="nsew")
    growth_ability_frame.grid_rowconfigure(0, weight=1)
    growth_ability_frame.grid_columnconfigure(0, weight=1, minsize=100)  # 图片列
    growth_ability_frame.grid_columnconfigure(1, weight=6, minsize=600)  # 描述列

    # 判断元素属性
    if style.element_attribute:
        if len(style.element_attribute) == 1:
            hoju_img_path = 持有物.强化素材.strengthen_materials.strengthen_materials_dir[
                f"宝珠（{style.element_attribute}属性）"]['path']
        else:
            hoju_img_path0 = 持有物.强化素材.strengthen_materials.strengthen_materials_dir[
                f"宝珠（{style.element_attribute[0]}属性）"]['path']
            hoju_img_path1 = 持有物.强化素材.strengthen_materials.strengthen_materials_dir[
                f"宝珠（{style.element_attribute[1]}属性）"]['path']
    else:
        hoju_img_path = 持有物.强化素材.strengthen_materials.strengthen_materials_dir[
            f"宝珠（{style.weapon_attribute}属性）"]['path']

    if not style.element_attribute or len(style.element_attribute) == 1:
        hoju_photo = get_photo(hoju_img_path, (80, 80))
        hoju_canvas = create_canvas_with_image(growth_ability_frame, 
            hoju_photo, 80, 80, 0, 0, 0, 0, padx=10)
        text = style.growth_ability.description
        growth_ability_lab = ttk.Label(growth_ability_frame, text=text, 
            justify="left", font=("Monospace", 10, "bold"))
        growth_ability_lab.grid(row=0, column=1, sticky="nsw", padx=15, pady=5)
    else:
        growth_ability_frame.grid_columnconfigure(1, weight=1, minsize=100)  # 图片列
        growth_ability_frame.grid_columnconfigure(2, weight=5, minsize=500)  # 描述列

        hoju_photo0 = get_photo(hoju_img_path0, (80, 80))
        hoju_canvas0 = create_canvas_with_image(growth_ability_frame, 
            hoju_photo0, 80, 80, 0, 0, 0, 0, padx=10)
        hoju_photo1 = get_photo(hoju_img_path1, (80, 80))
        hoju_canvas1 = create_canvas_with_image(growth_ability_frame, 
            hoju_photo1, 80, 80, 0, 0, 0, 1, padx=10)

        text = style.growth_ability.description
        growth_ability_lab = ttk.Label(growth_ability_frame, text=text, 
            justify="left", font=("Monospace", 10, "bold"))
        growth_ability_lab.grid(row=0, column=2, sticky="nsw", padx=15, pady=5)