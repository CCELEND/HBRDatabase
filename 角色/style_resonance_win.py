
import ttkbootstrap as ttk
from ttkbootstrap.constants import *

from canvas_events import get_photo, create_canvas_with_image

# 共鸣天赋
def creat_resonance_frame(parent_frame, resonance_frame_row, style):

    name = style.resonance['name']
    resonance_frame = ttk.Labelframe(parent_frame, text=f"共鸣天赋（{name}）")
    resonance_frame.grid(row=resonance_frame_row, column=0, columnspan=4, padx=10, pady=(5,10), sticky="nsew")
    resonance_frame.grid_rowconfigure(0, weight=1)
    resonance_frame.grid_columnconfigure(0, weight=1, minsize=100)  # 图片列
    resonance_frame.grid_columnconfigure(1, weight=6, minsize=600)  # 描述列

    resonance_img_path = "./角色/IconResonance.webp"

    resonance_photo = get_photo(resonance_img_path, (80, 64))
    resonance_canvas = create_canvas_with_image(resonance_frame, 
        resonance_photo, 120, 120, 20, 28, 0, 0, padx=10)

    text  = f"上限突破0：{style.resonance['0']}\n"
    text += f"上限突破1：{style.resonance['1']}\n"
    text += f"上限突破2：{style.resonance['2']}\n"
    text += f"上限突破3：{style.resonance['3']}\n"
    text += f"上限突破4：{style.resonance['4']}"
    resonance_lab = ttk.Label(resonance_frame, text=text, 
        justify="left", font=("Monospace", 10, "bold"))
    resonance_lab.grid(row=0, column=1, sticky="nsw", padx=0, pady=5)