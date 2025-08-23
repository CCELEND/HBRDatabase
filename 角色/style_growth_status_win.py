
import ttkbootstrap as ttk
from ttkbootstrap.constants import *

# 成长状态
def creat_growth_status_frame(parent_frame, style, growth_status_row):
    growth_status_frame = ttk.LabelFrame(parent_frame, text="成长状态")
    growth_status_frame.grid(row=growth_status_row, column=0, 
        columnspan=4, padx=10, pady=(5,10), sticky="nsew")
    growth_status_frame.grid_rowconfigure(0, weight=1)
    growth_status_frame.grid_columnconfigure(0, weight=1)
    growth_status_frame.grid_columnconfigure(1, weight=1)


    text = f"DP {style.status_growth['DP']}\n"
    text += "力量" + f"{style.status_growth['力量']}\n".rjust(10)
    text += "体力" + f"{style.status_growth['体力']}\n".rjust(10)
    text += "智慧" + f"{style.status_growth['智慧']}".rjust(9)
    growth_status_lab = ttk.Label(growth_status_frame, text=text, 
        justify="right", font=("Monospace", 10, "bold"))
    growth_status_lab.grid(row=0, column=0, sticky="sw", padx=20, pady=5)

    text =  "灵巧" + f"{style.status_growth['灵巧']}\n".rjust(10)
    text += "精神" + f"{style.status_growth['精神']}\n".rjust(10)
    text += "运气" + f"{style.status_growth['运气']}".rjust(9)

    growth_status_lab1 = ttk.Label(growth_status_frame, text=text, 
        justify="right", font=("Monospace", 10, "bold"))
    growth_status_lab1.grid(row=0, column=1, sticky="sw", padx=20, pady=5)