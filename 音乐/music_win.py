
import sys
import os
import tkinter as tk

from tkinter import scrolledtext, Menu, messagebox
from tkinter import ttk

from canvas_events import get_photo, create_canvas_with_image
from window import set_window_expand, set_window_icon, show_context_menu, set_window_top, creat_Toplevel
from tools import load_json

from music_list import ExpandableList
from music_player import FLACPlayerApp
import music_player


# 窗口关闭处理
def music_win_closing(parent_frame):
    open_music_win = parent_frame.title()
    while open_music_win in open_music_wins:
        del open_music_wins[open_music_win]

    # 窗口关闭时清理资源
    music_player.PlayerApp.on_close()
    parent_frame.destroy()  # 销毁窗口

open_music_wins = {}
def creat_music_win():
    # 重复打开时，窗口置顶并直接返回
    if "音乐" in open_music_wins:
        # 判断窗口是否存在
        if open_music_wins["音乐"].winfo_exists():
            set_window_top(open_music_wins["音乐"])
            return "break"
        del open_music_wins["音乐"]

    music_win_frame = creat_Toplevel("音乐", 850, 575, x=190, y=160)
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

    music_player.PlayerApp = FLACPlayerApp(music_player.play_info_frame, 1, 0)

    # music_win_frame.resizable(False, False)
    # 设置最大尺寸和最小尺寸相同，以阻止最大化
    music_win_frame.maxsize(850, 575)
    music_win_frame.minsize(850, 575)

    open_music_wins["音乐"] = music_win_frame

    # 窗口关闭时清理
    music_win_frame.protocol("WM_DELETE_WINDOW", lambda: music_win_closing(music_win_frame))

