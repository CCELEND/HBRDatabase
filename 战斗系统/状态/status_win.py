
import ttkbootstrap as ttk
from ttkbootstrap.constants import *

from canvas_events import bind_canvas_events, get_photo, create_canvas_with_image
from canvas_events import mouse_bind_canvas_events
from window import set_window_icon_webp, creat_Toplevel, set_window_top


from 状态.status_info import get_all_statu_obj
import 状态.status_info

# 绑定状态 canvas 的事件
def bind_statu_canvas(parent_frame, statu, x, y):

    photo = get_photo(statu.path, (60, 60))
    canvas = create_canvas_with_image(parent_frame, 
        photo, 60, 60, 0, 0, x, y)
    mouse_bind_canvas_events(canvas)
    bind_canvas_events(canvas, 
        creat_statu_win, parent_frame=parent_frame, 
        statu=statu)

open_statu_wins = {}
#关闭窗口时，清除窗口字典中的句柄，并销毁窗口
def statu_win_closing(parent_frame):

    open_statu_win = parent_frame.title()
    while open_statu_win in open_statu_wins:
        del open_statu_wins[open_statu_win]

    parent_frame.destroy()  # 销毁窗口

def creat_statu_win(event, parent_frame, statu):

    # 重复打开时，窗口置顶并直接返回
    if statu.name in open_statu_wins:
        # 判断窗口是否存在
        if open_statu_wins[statu.name].winfo_exists():
            set_window_top(open_statu_wins[statu.name])
            return "break"
        del open_statu_wins[statu.name]


    statu_win_frame = creat_Toplevel(statu.name, 540, 200, 730, 350)
    # 配置 statu_win_frame 的布局
    statu_win_frame.grid_rowconfigure(0, weight=1)  # 确保行填充
    statu_win_frame.grid_columnconfigure(0, weight=1)  # 列

    set_window_icon_webp(statu_win_frame, statu.path)
    open_statu_wins[statu.name] = statu_win_frame

    statu_frame = ttk.LabelFrame(statu_win_frame, text=statu.name)
    statu_frame.grid(row=0, column=0, padx=10, pady=(5, 10), sticky="nsew")
    # 配置 statu_frame 的布局
    statu_frame.grid_rowconfigure(0, weight=1)  # 确保行填充
    statu_frame.grid_columnconfigure(0, weight=3)  # 描述列
    statu_frame.grid_columnconfigure(1, weight=1)  # 叠加数列

    if statu.effect:
        info = statu.effect
    else:
        info = statu.description
    info_label = ttk.Label(statu_frame, text=info, anchor="center")
    info_label.grid(row=0, column=0, sticky="nsew")

    stack_label = ttk.Label(statu_frame, text=statu.stack, anchor="center")
    stack_label.grid(row=0, column=1, sticky="nsew")

    # 绑定鼠标点击事件到父窗口，点击置顶
    statu_win_frame.bind("<Button-1>", lambda event: set_window_top(statu_win_frame))
    # 窗口关闭时清理
    statu_win_frame.protocol("WM_DELETE_WINDOW", lambda: statu_win_closing(statu_win_frame))

    return "break"  # 阻止事件冒泡


def set_frame_newline(frame, item_num, newline_num, column_count):
    # 计算行和列的位置
    row = item_num // newline_num  # 每newline_num个换行
    column = item_num % newline_num  # 列位置
    frame.grid(row=row, column=column, padx=5, pady=(0,5), sticky="nesw")  # 设置间距
    column_count += 1  # 更新列计数器
    if column_count == newline_num:  # 如果已经到达第newline_num列，重置列计数器并增加行
        column_count = 0
    return column_count

# 加载图片并显示的函数
def show_statu(scrollbar_frame_obj):

    get_all_statu_obj()

    # 清除之前的组件
    scrollbar_frame_obj.destroy_components()

    for type_num, type in enumerate(状态.status_info.statu_categories):
        # 状态类型
        type_frame = ttk.LabelFrame(scrollbar_frame_obj.scrollable_frame, text=type+"类型状态")
        type_frame.grid(row=type_num, column=0, columnspan=6, padx=10, pady=(0,10), sticky="nsew") #

        series_column_count = 0
        for series_num, series in enumerate(状态.status_info.statu_categories[type]):
            # 所属系列
            series_frame = ttk.LabelFrame(type_frame, text=series)
            series_frame.grid(row=series_num, column=0, padx=(5,0), pady=(0,5), sticky="nesw")  # 设置间距

            statu_column_count = 0
            for statu_num, statu_name in enumerate(状态.status_info.statu_categories[type][series]):
                # 状态对象
                statu = 状态.status_info.statu_categories[type][series][statu_name]
                # print(statu.name)

                if len(状态.status_info.statu_categories[type][series]) == 1:
                    bind_statu_canvas(series_frame, statu, 0, 0)
                else:
                    statu_frame = ttk.LabelFrame(series_frame, text=statu_name)
                    bind_statu_canvas(statu_frame, statu, 0, 0)

                    if type in ['增益', '减益', '其他', '异常']:
                        if series in ["技能效果强化", "对HP百分比伤害", "减益，异常移除", '强击破', 'EShield']:
                            statu_column_count = set_frame_newline(statu_frame, statu_num, 3, statu_column_count)
                        else: 
                            statu_column_count = set_frame_newline(statu_frame, statu_num, 4, statu_column_count)
                    else:
                        statu_frame.grid(row=0, column=statu_num, padx=5, pady=(0,5), sticky="nesw")  # 设置间距      

            if type in ['增益']:
                # padx=(5,0)
                series_column_count = set_frame_newline(series_frame, series_num, 3, series_column_count)
            elif type in ['减益']: 
                series_column_count = set_frame_newline(series_frame, series_num, 4, series_column_count)           
            elif type in ['其他']:
                series_column_count = set_frame_newline(series_frame, series_num, 5, series_column_count) 
            else:
                series_frame.grid(row=0, column=series_num, padx=(5,0), sticky="nesw")  # 设置间距


    scrollbar_frame_obj.update_canvas()
    return "break"  # 阻止事件冒泡
