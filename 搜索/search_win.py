
from window import set_window_expand, set_window_icon, creat_Toplevel, show_context_menu, set_window_top
from tkinter import scrolledtext

import ttkbootstrap as ttk
from ttkbootstrap.constants import *

from 角色.team_info import get_all_team_obj, get_role_by_master_name
from 角色.team_win import bind_style_canvas, bind_master_skill_canvas
import 角色.team_info

from 搜索.search_processing import on_select, get_filtered_styles, keyword_processing
from 搜索.search_processing_master import get_filtered_master_skills

# 创建选项的 frame
def creat_select_frame(label_content, options, selected_values,
    parent_frame, row, column):

    # 创建标签
    label_frame = ttk.LabelFrame(parent_frame, text=label_content)
    label_frame.grid(row=row, column=column, padx=(10,0), pady=(0,5), sticky="nesw")

    # 创建 Frame 用于容纳水平排列的多选按钮
    check_frame = ttk.Frame(label_frame)
    check_frame.grid(row=0, column=0, padx=5, sticky="nsw")

    # 存储每个 Checkbutton 的 BooleanVar
    check_vars = []

    # 初始化 last 列表，记录上一次的状态
    last = [False] * len(options)

    # 定义自定义样式（背景色 + 字体颜色）
    style = ttk.Style()
    style.configure(
        "Custom.TCheckbutton",  # 自定义样式名
        background="#f0f0f0",   # 背景颜色（浅灰色）
        foreground="#333333",   # 文字颜色（深灰色）
    )
    # 创建多选按钮并使用 grid 布局
    column_count = 0  # 初始化列计数器
    for i, value in enumerate(options):
        check_var = ttk.BooleanVar()  # 每个选项使用独立的 BooleanVar
        check_button = ttk.Checkbutton(
            check_frame,  # 将多选按钮放在 check_frame 中
            text=value,
            variable=check_var,  # 绑定 BooleanVar
            style="Custom.TCheckbutton",
            command=lambda: on_select(check_vars, options, last, selected_values)
        )

        # 计算行和列的位置
        row = i // 4  # 每四个按钮换行
        column = i % 4  # 列位置
        check_button.grid(row=row, column=column, padx=5, pady=5, sticky="nsw")  # 设置间距

        check_vars.append(check_var)
        column_count += 1  # 更新列计数器
        if column_count == 4:  # 如果已经到达第四列，重置列计数器并增加行
            column_count = 0

    return label_frame


# 显示搜索结果
def show_search(scrollbar_frame_obj, search_win_frame, key_word_text, selected_values_dir):

    set_window_top(search_win_frame)
    # 获取关键词
    key_word_str = key_word_text.get("1.0", ttk.END)
    key_word_str = key_word_str.strip()

    # 关键词处理
    keyword_list = keyword_processing(key_word_str)

    # 清除之前的组件
    scrollbar_frame_obj.destroy_components()

    if selected_values_dir["大师技能"]:
        filtered_master_skills = get_filtered_master_skills(selected_values_dir, keyword_list)
        column_count = 0
        for i, master_skill in enumerate(filtered_master_skills):
            role = get_role_by_master_name(master_skill.name)

            master_skill_frame = ttk.LabelFrame(scrollbar_frame_obj.scrollable_frame, text=master_skill.name)
            # 设置LabelFrame的最小高度
            master_skill_frame.grid_propagate(False)
            master_skill_frame.configure(height=170)
            bind_master_skill_canvas(master_skill_frame, role, 0, 0)

            # 计算行和列的位置
            row = i // 6  # 每6个换行
            column = i % 6  # 列位置
            master_skill_frame.grid(row=row, column=column, padx=(10,0), pady=(0,10), sticky="nesw")  # 设置间距
            master_skill_frame.grid_rowconfigure(0, weight=1)
            master_skill_frame.grid_columnconfigure(0, weight=1)

            column_count += 1  # 更新列计数器
            if column_count == 6:  # 如果已经到达第6列，重置列计数器并增加行
                column_count = 0

        scrollbar_frame_obj.update_canvas()
        return "break"

    # 获取筛选的风格列表
    filtered_styles = get_filtered_styles(selected_values_dir, keyword_list)

    # # 清除之前的组件
    # scrollbar_frame_obj.destroy_components()

    column_count = 0
    for i, style in enumerate(filtered_styles):
        team = 角色.team_info.teams[style.team_name]

        style_frame = ttk.LabelFrame(scrollbar_frame_obj.scrollable_frame, text=style.name)
        # 设置LabelFrame的最小高度
        style_frame.grid_propagate(False)
        style_frame.configure(height=170)
        bind_style_canvas(style_frame, team, style, 0, 0)

        # 计算行和列的位置
        row = i // 6  # 每6个换行
        column = i % 6  # 列位置
        style_frame.grid(row=row, column=column, padx=(10,0), pady=(0,10), sticky="nesw")  # 设置间距
        style_frame.grid_rowconfigure(0, weight=1)
        style_frame.grid_columnconfigure(0, weight=1)

        column_count += 1  # 更新列计数器
        if column_count == 6:  # 如果已经到达第6列，重置列计数器并增加行
            column_count = 0

    scrollbar_frame_obj.update_canvas()
    return "break"  # 阻止事件冒泡



# 已打开的窗口字典，键：名，值：窗口句柄
open_search_wins = {}
#关闭窗口时，清除窗口字典中的句柄，并销毁窗口
def search_win_closing(parent_frame):

    open_search_win = parent_frame.title()
    while open_search_win in open_search_wins:
        del open_search_wins[open_search_win]

    parent_frame.destroy()  # 销毁窗口

# 创建搜索窗口
def creat_search_win(parent_frame, scrollbar_frame_obj):

    # 重复打开时，窗口置顶并直接返回
    if "搜索" in open_search_wins:
        set_window_top(open_search_wins["搜索"])
        return "break"  # 阻止事件冒泡

    # 获取全部队伍对象
    get_all_team_obj()

    search_win_frame = creat_Toplevel("搜索", 715, 540, x=190, y=210) #715, 485
    set_window_icon(search_win_frame, "./搜索/search.ico")
    set_window_expand(search_win_frame, rowspan=1, columnspan=2)

    role_search_frame = ttk.LabelFrame(search_win_frame, text="角色、风格")
    role_search_frame.grid(row=0, column=0, columnspan=2, padx=10, sticky="nsew")

    rarity_options = [
        "ALL", "A", "S", "SS"
    ]
    rarity_selected_values = []
    rarity_frame = creat_select_frame("稀有度", 
        rarity_options, rarity_selected_values,
        role_search_frame, 0, 0)

    career_options = [
        "ALL", 
        "攻击者", "破盾者", "破坏者", "治疗者", 
        "增益者", "减益者", "防御者"
    ]
    career_selected_values = []
    career_frame = creat_select_frame("职能", 
        career_options, career_selected_values,
        role_search_frame, 0, 1)

    team_options = [
        "ALL", 
        "31A", "31B", "31C", "30G", 
        "31D", "31E", "31F", "31X", 
        "Angel Beats!"
    ]
    team_selected_values = []
    team_frame = creat_select_frame("队伍", 
        team_options, team_selected_values,
        role_search_frame, 1, 0)

    weapon_attribute_options = [
        "ALL", "斩", "突", "打"
    ]
    weapon_attribute_selected_values = []
    weapon_attribute_frame = creat_select_frame("武器属性", 
        weapon_attribute_options, weapon_attribute_selected_values,
        role_search_frame, 1, 1)

    element_attribute_options = [
        "ALL", 
        "火", "冰", "雷", "光", 
        "暗", "无"
    ]
    element_attribute_selected_values = []
    element_attribute_frame = creat_select_frame("元素属性", 
        element_attribute_options, element_attribute_selected_values,
        role_search_frame, 2, 0)

    skill_options = [
        "ALL", 
        "主动技能", "被动技能"
    ]
    skill_selected_values = []
    skill_frame = creat_select_frame("技能", 
        skill_options, skill_selected_values,
        role_search_frame, 2, 1)

    master_skill_options = [
        "ALL", 
        "大师技能"
    ]
    master_skill_selected_values = []
    master_skill_frame = creat_select_frame("大师技能", 
        master_skill_options, master_skill_selected_values,
        role_search_frame, 3, 0)


    # 关键词标签
    key_word_label = ttk.Label(search_win_frame, text="关键词")
    key_word_label.grid(row=1, column=0, padx=5, pady=5, sticky="w")
    # 关键词输入框
    key_word_text = scrolledtext.ScrolledText(search_win_frame, 
        wrap=ttk.WORD, height=3)
    key_word_text.grid(row=2, column=0, columnspan=2, padx=10, pady=0, sticky="nsew")
    # 绑定鼠标右键点击事件到上下文菜单
    key_word_text.bind("<Button-3>", 
        lambda event, tw=key_word_text: show_context_menu(event, tw))

    selected_values_dir = {}
    selected_values_dir["稀有度"] = rarity_selected_values
    selected_values_dir["职能"] = career_selected_values
    selected_values_dir["队伍"] = team_selected_values
    selected_values_dir["武器属性"] = weapon_attribute_selected_values
    selected_values_dir["元素属性"] = element_attribute_selected_values
    selected_values_dir["技能"] = skill_selected_values
    selected_values_dir["大师技能"] = master_skill_selected_values

    # 创建搜索按钮
    search_button = ttk.Button(search_win_frame, 
        width=20, text="搜索", bootstyle="primary-outline",
        command=lambda: show_search(scrollbar_frame_obj, search_win_frame,
            key_word_text, selected_values_dir))
    search_button.grid(row=3, column=0, columnspan=2, padx=5, pady=10)


    search_win_frame.maxsize(715, 540)
    search_win_frame.minsize(715, 540)

    open_search_wins["搜索"] = search_win_frame
    # 窗口关闭时清理
    search_win_frame.protocol("WM_DELETE_WINDOW", lambda: search_win_closing(search_win_frame))

    return "break"  # 阻止事件冒泡
