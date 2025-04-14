#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

import tkinter as tk
from tkinter import scrolledtext, Menu, messagebox
import math

import ttkbootstrap as ttk
from ttkbootstrap.constants import *

from window import set_window_expand, set_window_icon, creat_window, set_window_top, set_bg_opacity, set_global_bg
from window import copy_text, paste_text, cut_text, show_context_menu, clear_text, edit_text

maximum_damage_limit_text = None
input_text = None
output_text = None

# 获取伤害上限
def get_maximum_damage_limit():
	maximum_damage_limit_str = maximum_damage_limit_text.get("1.0", ttk.END)
	maximum_damage_limit_str = maximum_damage_limit_str.strip()
	if maximum_damage_limit_str == "":
		return 300000
		
	try:
		maximum_damage_limit = int(maximum_damage_limit_str, 0)
	except Exception as e:
		edit_text(output_text, f"[-] {e}")
		return -1

	return maximum_damage_limit


def get_input():
	input_text_str = input_text.get("1.0", ttk.END)
	input_text_str = input_text_str.strip()
	if input_text_str == "":
		clear_text(output_text)
		return 0

	try:
		input_val = int(input_text_str, 0)
	except Exception as e:
		edit_text(output_text, f"[-] {e}")
		return -1

	return input_val


# 伤害奖励转换伤害值
def damage_value():
	maximum_damage_limit = get_maximum_damage_limit()
	if (maximum_damage_limit == -1):
		return

	damage_reward = get_input()
	if (damage_reward == -1):
		return

	damage_value = math.e ** (damage_reward / maximum_damage_limit - 1 + math.log(maximum_damage_limit*100))
	edit_text(output_text, int(damage_value))

# 伤害值转换伤害奖励
def damage_reward():
	maximum_damage_limit = get_maximum_damage_limit()
	if (maximum_damage_limit == -1):
		return

	damage_value = get_input()
	if (damage_value == -1):
		return

	damage_reward = 0
	if (damage_value <= maximum_damage_limit*100):
		damage_reward = damage_value / 100
	else:
		damage_reward = maximum_damage_limit*(1+math.log(damage_value)-math.log(maximum_damage_limit*100))
	edit_text(output_text, int(damage_reward))


open_dsc_wins = {}
#关闭窗口时，清除窗口字典中的句柄，并销毁窗口
def dsc_win_closing(parent_frame):

	open_dsc_win = parent_frame.title()
	while open_dsc_win in open_dsc_wins:
		del open_dsc_wins[open_dsc_win]

	parent_frame.destroy()  # 销毁窗口

def creat_dsc_win():

	# 重复打开时，窗口置顶并直接返回
	if '伤害分计算' in open_dsc_wins:
		# 判断窗口是否存在
		if open_dsc_wins['伤害分计算'].winfo_exists():
			et_window_top(open_dsc_wins['伤害分计算'])
			return "break"
		del open_dsc_wins['伤害分计算']

	dsc_win_frame = ttk.Toplevel()
	dsc_win_frame.title("伤害分计算")
	dsc_win_frame.geometry("550x400")
	set_window_icon(dsc_win_frame, "./工具/DamageScoreCal/dsc.ico")

	# 配置主窗口的列和行的伸展
	dsc_win_frame.grid_columnconfigure(0, weight=1)  # 第0列会随着窗口调整大小
	dsc_win_frame.grid_columnconfigure(1, weight=1)  # 第1列会随着窗口调整大小

	dsc_win_frame.grid_rowconfigure(0, weight=1)     # input_frame随着窗口调整大小
	dsc_win_frame.grid_rowconfigure(1, weight=1)     # output_frame会随着窗口调整大小

	# 创建一个新的 Frame 用于输入文本框
	input_frame = ttk.Frame(dsc_win_frame)
	input_frame.grid(row=0, column=0, columnspan=2, padx=0, pady=0, sticky="nsew")
	# 配置输入框架的列和行的伸展框架的列和行的伸展
	input_frame.grid_columnconfigure(0, weight=1)  # 使输出框占满整列
	input_frame.grid_columnconfigure(1, weight=1)  # 使输出框占满整列
	input_frame.grid_rowconfigure(1, weight=1)     # 使input_text输入框占满整行
	input_frame.grid_rowconfigure(3, weight=1)     # 使maximum_damage_limit_text输入框占满整行


	global maximum_damage_limit_text
	global input_text
	global output_text

	# 输入标签
	input_label = ttk.Label(input_frame, text="输入伤害奖励 / 伤害值")
	input_label.grid(row=0, column=0, padx=5, pady=0, sticky="w")
	# 输入框
	input_text = scrolledtext.ScrolledText(input_frame, 
		wrap=ttk.WORD, width=50, height=3)
	input_text.grid(row=1, column=0, columnspan=2, padx=10, pady=0, sticky="nsew")
	# 绑定鼠标右键点击事件到上下文菜单
	input_text.bind("<Button-3>", lambda event, tw=input_text: show_context_menu(event, tw))

	# 输入标签
	maximum_damage_limit_label = ttk.Label(input_frame, text="伤害上限（默认为300000）")
	maximum_damage_limit_label.grid(row=2, column=0, padx=5, pady=0, sticky="w")
	# 输入框
	maximum_damage_limit_text = scrolledtext.ScrolledText(input_frame, 
		wrap=ttk.WORD, width=50, height=3)
	maximum_damage_limit_text.grid(row=3, column=0, columnspan=2, padx=10, pady=0, sticky="nsew")
	# 绑定鼠标右键点击事件到上下文菜单
	maximum_damage_limit_text.bind("<Button-3>", 
		lambda event, tw=maximum_damage_limit_text: show_context_menu(event, tw))

	#按钮
	damage_value_button = ttk.Button(input_frame, bootstyle="light",
		width=20, text="伤害奖励->伤害值", command=damage_value)
	damage_value_button.grid(row=4, column=0, padx=0, pady=(10,0))
	#按钮
	damage_reward_button = ttk.Button(input_frame, bootstyle="light",
		width=20, text="伤害值->伤害奖励", command=damage_reward)
	damage_reward_button.grid(row=4, column=1, padx=0, pady=(10,0))


	# 创建一个新的 Frame 用于输出文本框
	output_frame = ttk.Frame(dsc_win_frame)
	output_frame.grid(row=1, column=0, columnspan=2, padx=0, pady=0, sticky="nsew")
	# 配置输出框架的列和行的伸展
	output_frame.grid_columnconfigure(0, weight=1)  # 使输出框占满整列
	output_frame.grid_rowconfigure(1, weight=1)     # 使第一个输出框占满整行

	# 输出标签
	output_label2 = ttk.Label(output_frame, text="输出")
	output_label2.grid(row=0, column=0, padx=5, pady=0, sticky="w")

	# 输出框
	output_text = scrolledtext.ScrolledText(output_frame, 
		wrap=ttk.WORD, width=50, height=3, state=ttk.DISABLED)
	output_text.grid(row=1, column=0, padx=10, pady=0, sticky="nsew")
	# 绑定鼠标右键点击事件到上下文菜单
	output_text.bind("<Button-3>", lambda event, tw=output_text: show_context_menu(event, tw))

	# 创建清空按钮
	clear_button = ttk.Button(dsc_win_frame, bootstyle="light",
		width=20, text="清空", 
		command=lambda: clear_text(input_text, maximum_damage_limit_text, output_text))
	clear_button.grid(row=2, column=0, columnspan=2, padx=5, pady=10)

	open_dsc_wins['词条获取'] = dsc_win_frame
	# 绑定鼠标点击事件到父窗口，点击置顶
	dsc_win_frame.bind("<Button-1>", lambda event: set_window_top(dsc_win_frame))
	# 窗口关闭时清理
	dsc_win_frame.protocol("WM_DELETE_WINDOW", lambda: dsc_win_closing(dsc_win_frame))
	return "break"  # 阻止事件冒泡
