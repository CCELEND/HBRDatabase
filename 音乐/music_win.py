
from tkinter import messagebox
from tkinter import ttk

from window import set_window_icon, creat_Toplevel
from window import win_open_manage, win_close_manage, is_win_open, win_set_top
from tools import load_json

from music_list import ExpandableList
from music_player import FLACPlayerApp
import music_player

from 日志.advanced_logger import AdvancedLogger
logger = AdvancedLogger.get_logger(__name__)

def creat_music_win():
    # 重复打开时，窗口置顶并直接返回
    if is_win_open("音乐", __name__):
        win_set_top("音乐", __name__)
        return "break"

    music_win_frame = creat_Toplevel("音乐", 850, 575, x=190, y=140)
    set_window_icon(music_win_frame, "./音乐/Sound.ico")
    
    music_win_frame.grid_rowconfigure(0, weight=1)
    music_win_frame.grid_columnconfigure(0, weight=7, minsize=350)
    music_win_frame.grid_columnconfigure(1, weight=10, minsize=500)

    categories = load_json("./音乐/music.json")
    ListApp = ExpandableList(music_win_frame, categories, 0, 0)

    music_player.play_info_frame = ttk.Frame(music_win_frame)
    music_player.play_info_frame.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")
    music_player.play_info_frame.grid_rowconfigure(0, weight=1, minsize=300)
    music_player.play_info_frame.grid_rowconfigure(1, weight=1, minsize=200)
    music_player.play_info_frame.grid_columnconfigure(0, weight=1)

    try:
        music_player.PlayerApp = FLACPlayerApp(music_player.play_info_frame, 1, 0)
    except Exception as e:
        logger.error(str(e))
        messagebox.showerror("错误", f"请重试：{str(e)}")
        music_win_frame.destroy()
        return

    # music_win_frame.resizable(False, False)
    # 设置最大尺寸和最小尺寸相同，以阻止最大化
    music_win_frame.maxsize(850, 575)
    music_win_frame.minsize(850, 575)

    win_open_manage(music_win_frame, __name__)

    # 窗口关闭时清理
    music_win_frame.protocol("WM_DELETE_WINDOW", 
        lambda: (music_player.PlayerApp.on_close(), 
        win_close_manage(music_win_frame, __name__))
    )

