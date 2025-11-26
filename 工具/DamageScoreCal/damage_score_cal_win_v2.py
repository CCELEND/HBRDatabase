#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

from tkinter import scrolledtext
import math

import ttkbootstrap as ttk
from ttkbootstrap.constants import *

from window import set_window_icon, creat_Toplevel
from window import win_open_manage, win_close_manage, is_win_open, win_set_top
from window import show_context_menu, clear_text, edit_text

from 日志.advanced_logger import AdvancedLogger
logger = AdvancedLogger.get_logger(__name__)

from decimal import Decimal, ROUND_HALF_UP, DecimalException

threshold_value_text = None
damage_coefficient_text = None
input_text_v2 = None
output_text_v2 = None

# 获取伤害阈值
def get_threshold_value():
	threshold_value_str = threshold_value_text.get("1.0", 'end')
	threshold_value_str = threshold_value_str.strip()
	if threshold_value_str == "":
		return 42000000
		
	try:
		threshold_value = int(threshold_value_str, 0)
	except Exception as e:
		logger.error(str(e))
		edit_text(output_text_v2, f"[-] {e}")
		return -1

	return threshold_value

# 获取伤害分系数
def get_damage_coefficient():
	damage_coefficient_str = damage_coefficient_text.get("1.0", 'end')
	damage_coefficient_str = damage_coefficient_str.strip()
	if damage_coefficient_str == "":
		return 0.47
		
	try:
		damage_coefficient = float(damage_coefficient_str)
	except Exception as e:
		logger.error(str(e))
		edit_text(output_text_v2, f"[-] {e}")
		return -1

	return damage_coefficient

def get_input():
	input_text_v2_str = input_text_v2.get("1.0", 'end')
	input_text_v2_str = input_text_v2_str.strip()
	if input_text_v2_str == "":
		clear_text(output_text_v2)
		return 0

	try:
		input_val = int(input_text_v2_str, 0)
	except Exception as e:
		logger.error(str(e))
		edit_text(output_text_v2, f"[-] {e}")
		return -1

	return input_val


# 伤害奖励转换伤害值
def damage_value():
	threshold_value = get_threshold_value()
	if (threshold_value == -1):
		return
	
	damage_coefficient = get_damage_coefficient()
	if (damage_coefficient == -1):
		return
	
	damage_reward = get_input()
	if (damage_reward == -1):
		return

	# 转换为 Decimal 类型
	damage_reward = Decimal(str(damage_reward))
	threshold_value = Decimal(str(threshold_value))
	damage_coefficient = Decimal(str(damage_coefficient))
	# 计算指数部分
	try:
		exponent = (Decimal('100') * damage_reward) / (threshold_value * damage_coefficient) - Decimal('1') + threshold_value.ln()
		# 使用 math.exp 计算e的幂
		damage_value = Decimal(str(math.exp(exponent)))
	except DecimalException as de:
		logger.error(str(de))
		raise ValueError(f"Decimal计算错误: {de}")
	except Exception as e:
		logger.error(str(e))
		raise ValueError(f"计算错误: {e}")

	edit_text(output_text_v2, int(damage_value))

# 伤害值转换伤害奖励
def damage_reward():
	threshold_value = get_threshold_value()
	if (threshold_value == -1):
		return
	
	damage_coefficient = get_damage_coefficient()
	if (damage_coefficient == -1):
		return
	
	damage_value = get_input()
	if (damage_value == -1):
		return
	

	# 转换为 Decimal 类型
	damage_coefficient = Decimal(str(damage_coefficient))
	threshold_value = Decimal(str(threshold_value))
	damage_value = Decimal(str(damage_value))
	# 计算对数部分，使用 ln 函数
	try:
		log_damage = damage_value.ln()
		log_threshold = threshold_value.ln()
	except Exception as e:
		logger.error(str(e))
		raise ValueError(f"对数计算错误: {e}")

	# 确保damage_value大于等于threshold_value，避免对数结果为负
	if damage_value < threshold_value:
		raise ValueError("damage_value 必须大于或等于 threshold_value")
    
	# 计算奖励值
	damage_reward = (damage_coefficient/Decimal('100')) * threshold_value * ( Decimal('1') + log_damage - log_threshold )
	edit_text(output_text_v2, int(damage_reward))


def creat_dsc_win_v2():


    # 重复打开时，窗口置顶并直接返回
	if is_win_open('伤害分计算V2', __name__):
		win_set_top('伤害分计算V2', __name__)
		return "break"

	dsc_win_frame = creat_Toplevel("伤害分计算V2", 650, 520, 160, 160)
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
	input_frame.grid_rowconfigure(1, weight=1)     # 使input_text_v2输入框占满整行
	input_frame.grid_rowconfigure(3, weight=1)     # 使threshold_value_text输入框占满整行


	global threshold_value_text
	global damage_coefficient_text
	global input_text_v2
	global output_text_v2

	# 输入标签
	input_label = ttk.Label(input_frame, text="输入伤害奖励 / 伤害值")
	input_label.grid(row=0, column=0, padx=5, pady=0, sticky="w")
	# 输入框
	input_text_v2 = scrolledtext.ScrolledText(input_frame, 
		wrap="word", width=50, height=3)
	input_text_v2.grid(row=1, column=0, columnspan=2, padx=10, pady=0, sticky="nsew")
	# 绑定鼠标右键点击事件到上下文菜单
	input_text_v2.bind("<Button-3>", lambda event, tw=input_text_v2: show_context_menu(event, tw))

	# 输入标签
	threshold_value_label = ttk.Label(input_frame, text="伤害阈值（默认为42000000）")
	threshold_value_label.grid(row=2, column=0, padx=5, pady=0, sticky="w")
	# 输入框
	threshold_value_text = scrolledtext.ScrolledText(input_frame, 
		wrap="word", width=50, height=3)
	threshold_value_text.grid(row=3, column=0, columnspan=2, padx=10, pady=0, sticky="nsew")
	# 绑定鼠标右键点击事件到上下文菜单
	threshold_value_text.bind("<Button-3>", 
		lambda event, tw=threshold_value_text: show_context_menu(event, tw))

	# 输入标签
	damage_coefficient_label = ttk.Label(input_frame, text="伤害分系数（默认为0.47）")
	damage_coefficient_label.grid(row=4, column=0, padx=5, pady=0, sticky="w")
	# 输入框
	damage_coefficient_text = scrolledtext.ScrolledText(input_frame, 
		wrap="word", width=50, height=3)
	damage_coefficient_text.grid(row=5, column=0, columnspan=2, padx=10, pady=0, sticky="nsew")
	# 绑定鼠标右键点击事件到上下文菜单
	damage_coefficient_text.bind("<Button-3>", 
		lambda event, tw=damage_coefficient_text: show_context_menu(event, tw))

	#按钮
	damage_value_button = ttk.Button(input_frame, bootstyle="primary-outline",
		width=20, text="伤害奖励->伤害值", command=damage_value)
	damage_value_button.grid(row=6, column=0, padx=0, pady=(10,0))
	#按钮
	damage_reward_button = ttk.Button(input_frame, bootstyle="primary-outline",
		width=20, text="伤害值->伤害奖励", command=damage_reward)
	damage_reward_button.grid(row=6, column=1, padx=0, pady=(10,0))


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
	output_text_v2 = scrolledtext.ScrolledText(output_frame, 
		wrap="word", width=50, height=3, state='disabled')
	output_text_v2.grid(row=1, column=0, padx=10, pady=0, sticky="nsew")
	# 绑定鼠标右键点击事件到上下文菜单
	output_text_v2.bind("<Button-3>", lambda event, tw=output_text_v2: show_context_menu(event, tw))

	# 创建清空按钮
	clear_button = ttk.Button(dsc_win_frame, bootstyle="primary-outline",
		width=20, text="清空", 
		command=lambda: clear_text(input_text_v2, threshold_value_text, output_text_v2))
	clear_button.grid(row=2, column=0, columnspan=2, padx=5, pady=10)

	win_open_manage(dsc_win_frame, __name__)
	# 窗口关闭时清理
	dsc_win_frame.protocol("WM_DELETE_WINDOW", lambda: win_close_manage(dsc_win_frame, __name__))
	return "break"  # 阻止事件冒泡
