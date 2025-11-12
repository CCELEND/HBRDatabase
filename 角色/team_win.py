
import ttkbootstrap as ttk
from ttkbootstrap.constants import *

from canvas_events import bind_canvas_events, get_photo, create_canvas_with_image, ArtworkDisplayerHeight
from canvas_events import mouse_bind_canvas_events, right_click_bind_canvas_events, mouse_bind_canvas_events2
from window import set_window_expand, set_window_icon, creat_Toplevel
from window import win_open_manage, win_close_manage, is_win_open, win_set_top
from scrollbar_frame_win import ScrollbarFrameWin

from 角色.team_info import get_team_obj, get_all_team_obj
from 角色.role_info import get_role_master_img
from 角色.style_win import creat_style_skill_win, creat_style_right_menu
from 角色.master_skill_win import creat_master_skill_win

import 战斗系统.武器.weapons_info
# 加载资源文件
def load_resources():
    战斗系统.武器.weapons_info.get_all_weapon_obj()

# 创建右键菜单
def creat_role_right_menu(event, parent_frame, role, team):
    
    right_click_menu = ttk.Menu(parent_frame, tearoff=0)
    right_click_menu.add_command(label="全身画", 
        command=lambda: show_role_full_img(parent_frame, role, team))
    
    right_click_menu.post(event.x_root, event.y_root)

# 显示全身画
def show_role_full_img(event, parent_frame, role, team):

    open_role_win = role.name+"-full"
    # 重复打开时，窗口置顶并直接返回
    if is_win_open(open_role_win, __name__):
        win_set_top(open_role_win, __name__)
        return "break"

    role_full_img_frame = creat_Toplevel(open_role_win, x=770, y=100)
    set_window_icon(role_full_img_frame, team.logo_path)
    win_open_manage(role_full_img_frame, __name__)

    role_full_path = role.img_path.replace("Profile", "")
    displayer = ArtworkDisplayerHeight(role_full_img_frame, role_full_path, 840)

    # 窗口关闭时清理
    role_full_img_frame.protocol("WM_DELETE_WINDOW", lambda: win_close_manage(role_full_img_frame, displayer))

    return "break"  # 阻止事件冒泡

# 显示缩略图
def show_role_img(event, parent_frame, role, team):

    open_role_win = role.name
    # 重复打开时，窗口置顶并直接返回
    if is_win_open(open_role_win, __name__):
        win_set_top(open_role_win, __name__)
        return "break"

    role_img_frame = creat_Toplevel(open_role_win, 444, 508, 600, 200)
    set_window_icon(role_img_frame, team.logo_path)
    win_open_manage(role_img_frame, __name__)

    displayer = ArtworkDisplayerHeight(role_img_frame, role.img_path, 508)

    return "break"  # 阻止事件冒泡

# 绑定风格 canvas 的事件
def bind_style_canvas(parent_frame, team, style, x, y):

    # 创建一个 Frame 并禁用自动调整大小
    outer_frame = ttk.Frame(parent_frame, width=140, height=134)  # 预留边框空间
    outer_frame.grid_propagate(False)  # 禁止自动调整大小
    outer_frame.grid(row=x, column=y, sticky="nsew")

    photo = get_photo(style.path, (90, 90))
    canvas = create_canvas_with_image(outer_frame, 
        photo, 130, 130, 20, 20, 0, 0)
    
    mouse_bind_canvas_events2(canvas)

    bind_canvas_events(canvas, 
        creat_style_skill_win, parent_frame=parent_frame, team=team, style=style)
    # 右键点击事件绑定
    right_click_bind_canvas_events(canvas, 
        creat_style_right_menu, parent_frame=parent_frame, team=team, style=style)


# 绑定大师技能 canvas 的事件
def bind_master_skill_canvas(parent_frame, role, x, y):

    photo_path = get_role_master_img(role)

    # 创建一个 Frame 并禁用自动调整大小
    outer_frame = ttk.Frame(parent_frame, width=140, height=134)  # 预留边框空间
    outer_frame.grid_propagate(False)  # 禁止自动调整大小
    outer_frame.grid(row=x, column=y, sticky="nsew")

    photo = get_photo(photo_path, (90, 90))
    canvas = create_canvas_with_image(outer_frame, 
        photo, 130, 130, 20, 20, 0, 0)
    
    mouse_bind_canvas_events2(canvas)

    bind_canvas_events(canvas, 
        creat_master_skill_win, parent_frame=outer_frame, role=role)



def show_rarity(frame, role, team, row=2):

    if role.master_skill:
        # 创建 MasterSkillframe 并设置 row
        # 创建一个 Frame 并禁用自动调整大小
        MasterSkillframe = ttk.Frame(frame)
        MasterSkillframe.grid_propagate(False)  # 禁止自动调整大小
        MasterSkillframe.configure(height=145)
        MasterSkillframe.grid(row=row, column=0, padx=10, pady=5, sticky="nsew")

        photo = get_photo("./角色/iconMasterSkill.png", (120, 120))
        canvasMasterSkill = create_canvas_with_image(MasterSkillframe, 
            photo, 134, 134, 5, 5, 0, 0)
        
        mouse_bind_canvas_events2(canvasMasterSkill)

        bind_canvas_events(canvasMasterSkill, 
            creat_master_skill_win, parent_frame=MasterSkillframe, role=role)

        row += 1     

    if role.Astyles:
        # 创建 RarityAframe 并设置 row
        RarityAframe = ttk.Frame(frame)
        RarityAframe.grid(row=row, column=0, padx=10, pady=5, sticky="nsew")
        photoRarityA = get_photo("./角色/IconRarityA.png", (130, 130))
        canvasRarityA = create_canvas_with_image(RarityAframe, 
            photoRarityA, 134, 134, 0, 0, 0, 0)
        for a, Astyle in enumerate(role.Astyles):
            bind_style_canvas(RarityAframe, team, Astyle, 0, a+1)

        row += 1

    if role.Sstyles:
        # 创建 RaritySframe 并设置 row
        RaritySframe = ttk.Frame(frame)
        RaritySframe.grid(row=row, column=0, padx=10, pady=5, sticky="nsew")
        photoRarityS = get_photo("./角色/IconRarityS.png", (130, 130))
        canvasRarityS = create_canvas_with_image(RaritySframe, 
            photoRarityS, 134, 134, 0, 0, 0, 0)
        for s, Sstyle in enumerate(role.Sstyles):
            bind_style_canvas(RaritySframe, team, Sstyle, 0, s+1)

        row += 1

    if role.SSstyles:
        # 创建 RaritySSframe 并设置 row
        RaritySSframe = ttk.Frame(frame)
        RaritySSframe.grid(row=row, column=0, padx=10, pady=5, sticky="nsew")
        photoRaritySS = get_photo("./角色/IconRaritySS.png", (130, 130))
        canvasRaritySS = create_canvas_with_image(RaritySSframe, 
            photoRaritySS, 134, 134, 0, 0, 0, 0)
        for ss, SSstyle in enumerate(role.SSstyles):
            bind_style_canvas(RaritySSframe, team, SSstyle, 0, ss+1)

# 队伍描述
def creat_team_desc_frame(parent_frame, team):
    team_desc_frame = ttk.Labelframe(parent_frame, text=team.name)
    team_desc_frame.grid(row=0, column=0, columnspan=4, padx=10, pady=(0,10), sticky="nsew")
    team_desc_frame.grid_rowconfigure(0, weight=1)
    team_desc_frame.grid_columnconfigure(0, weight=1, minsize=100)
    team_desc_frame.grid_columnconfigure(1, weight=9, minsize=900)

    team_desc_photo = get_photo(team.logo_path, (64, 64))
    team_desc_canvas = create_canvas_with_image(team_desc_frame, 
        team_desc_photo, 100, 64, 18, 0, 0, 0)

    team_desc_label = ttk.Label(team_desc_frame, text=team.description, anchor="w", font=("Monospace", 10, "bold"))
    team_desc_label.grid(row=0, column=1, sticky="nswe", padx=0, pady=10)    


# 武器和大师技能 frame
def creat_weapon_frame(parent_frame, role):

    weapon = 战斗系统.武器.weapons_info.weapons[role.weapon]
    weapon_frame = ttk.Frame(parent_frame)
    weapon_frame.grid(row=0, column=2, padx=5, pady=5, sticky="nsew")
    weapon_frame.grid_rowconfigure(0, weight=1)

    weapon_photo = get_photo(weapon.path, (60, 60))
    weapon_canvas = create_canvas_with_image(weapon_frame, 
        weapon_photo, 100, 200, 20, 90, 0, 2)

def show_team(scrollbar_frame_obj, team):

    # 清除之前的组件
    scrollbar_frame_obj.destroy_components()

    creat_team_desc_frame(scrollbar_frame_obj.scrollable_frame, team)

    for i, role in enumerate(team.roles):

        # 创建 Labelframe
        frame = ttk.Labelframe(scrollbar_frame_obj.scrollable_frame, text=role.name)
        frame.grid(row=i+1, column=0, columnspan=4, padx=10, pady=(0,10), sticky="nsew")
        # 配置网格布局的权重
        frame.grid_rowconfigure(0, weight=1)
        frame.grid_rowconfigure(1, weight=1)
        frame.grid_columnconfigure(0, weight=1)

        # 创建 desc_frame 并设置 rowspan=2，占据两行
        desc_frame = ttk.Frame(frame)
        desc_frame.grid(row=0, column=0, columnspan=4, pady=10, sticky="nsew") #padx=10, 
        desc_frame.grid_rowconfigure(0, weight=1)  
        desc_frame.grid_columnconfigure(0, weight=1, minsize=200)
        desc_frame.grid_columnconfigure(1, weight=4, minsize=750)
        desc_frame.grid_columnconfigure(2, weight=1, minsize=100)

        photo = get_photo(role.img_path, (130, 254))
        canvas = create_canvas_with_image(desc_frame, 
            photo, 200, 254, 45, 0, 0, 0, rowspan=2)
        # 绑定事件到 Canvas
        mouse_bind_canvas_events(canvas)
        bind_canvas_events(canvas, 
            show_role_full_img, parent_frame=frame, role=role, team=team)

        # 角色描述
        # 设置了标签的字体为 Monospace 大小为 10，加粗
        # label = ttk.Label(desc_frame, text=role.description, justify="left", font=("Monospace", 10, "bold"))
        label = ttk.Label(desc_frame, text=role.description, anchor="w", font=("Monospace", 10, "bold"))
        label.grid(row=0, column=1, sticky="nswe", padx=10, pady=10)

        creat_weapon_frame(desc_frame, role)

        show_rarity(frame, role, team)

    scrollbar_frame_obj.update_canvas()


# 创建队伍窗口
def creat_team_win(parent_frame, team_name):

    # 重复打开时，窗口置顶并直接返回
    if is_win_open(team_name, __name__):
        win_set_top(team_name, __name__)
        return


    # 获取全部队伍对象
    get_all_team_obj()
    # 通过队伍名获取队伍对象
    team = get_team_obj(team_name)

    # 加载资源
    load_resources()

    team_win_frame = creat_Toplevel(team_name, 1130, 880, 90, 80)
    set_window_icon(team_win_frame, team.logo_path)
    set_window_expand(team_win_frame, rowspan=1, columnspan=2)
    scrollbar_frame_obj = ScrollbarFrameWin(team_win_frame, columnspan=2)
    win_open_manage(team_win_frame, __name__)

    # 绑定鼠标点击事件到父窗口，点击置顶
    team_win_frame.bind("<Button-1>", lambda event: win_set_top(team_name, __name__))
    # 窗口关闭时清理
    team_win_frame.protocol("WM_DELETE_WINDOW", lambda: win_close_manage(team_win_frame, __name__))

    show_team(scrollbar_frame_obj, team)

    return "break"  # 阻止事件冒泡