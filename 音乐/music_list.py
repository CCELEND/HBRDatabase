import sys
import os
import importlib
import subprocess

import tkinter as tk
from tkinter import scrolledtext, Menu, messagebox
from PIL import Image, ImageTk
import json
# from tkinter import ttk

import music_player
from music_handle_processing import music_handle

currently_selected = ""

try:
    import ttkbootstrap as ttk
    from ttkbootstrap.constants import *
except:
    print("[*] ttkbootstrap 未安装，正在尝试自动安装...")
    pip_args = [
        sys.executable, "-m", "pip", "install",
        "ttkbootstrap",
        "-i", "https://pypi.tuna.tsinghua.edu.cn/simple",  # 清华镜像
        "--trusted-host", "pypi.tuna.tsinghua.edu.cn"      # 避免 SSL 错误
    ]
    subprocess.check_call(pip_args)
    import ttkbootstrap as ttk
    from ttkbootstrap.constants import *


class ExpandableList_old:
    def __init__(self, parent_frame, categories, row, column):
        # 创建主框架
        self.frame = ttk.Frame(parent_frame, padding=(5, 5))
        self.frame.grid(row=row, column=column, padx=5, pady=5, sticky="nsew")
        self.frame.grid_rowconfigure(0, weight=1)
        self.frame.grid_columnconfigure(0, weight=1)

        # 配置Treeview样式
        style = ttk.Style()
        self.style_name = "ExpandableList.Treeview"
        style.configure(self.style_name,
                        font=('微软雅黑', 10, 'normal'),
                        rowheight=22)
        style.map(self.style_name,
                  background=[('selected', '#d3d3d3')],
                  foreground=[('selected', 'black')])

        # 创建Treeview
        self.tree = ttk.Treeview(
            self.frame,
            style=self.style_name,  # 应用自定义样式
            selectmode="browse",
            height=10,  # 优化可见行数
            show="tree",
        )
        self.tree.grid(row=0, column=0, sticky="nsew", padx=2, pady=2)

        # 滚动条样式
        style.configure(
            "Custom.Vertical.TScrollbar",  # 垂直滚动条样式
            background="#f0f0f0",          # 滚动条背景色
            troughcolor="#f0f0f0",         # 滚动槽颜色
            gripcount=0                    # 移除默认的条纹效果
        )
        scrollbar = tk.Scrollbar(self.frame, command=self.tree.yview)
        # scrollbar = ttk.Scrollbar(self.frame, command=self.tree.yview, style="Custom.Vertical.TScrollbar")
        scrollbar.grid(row=0, column=1, sticky="ns", padx=(0, 2), pady=2)
        self.tree.configure(yscrollcommand=scrollbar.set)

        # 增强交互反馈
        self.tree.bind("<Double-1>", self.on_double_click)
        self.tree.bind("<Enter>", lambda e: self.tree.config(cursor="hand2"))
        self.tree.bind("<Leave>", lambda e: self.tree.config(cursor="arrow"))

        # 初始化数据
        self.add_categories(categories)

        # 当前选中项和父节点
        self.currently_selected_item = None
        self.currently_selected_parent = None

    def add_categories(self, categories):
        for category, items in categories.items():
            parent = self.tree.insert("", "end",
                                      text=category,
                                      open=False,
                                      tags=('category',))
            for idx, item in enumerate(items, 1):
                self.tree.insert(parent, "end",
                                 text=item,
                                 tags=('item', f'item-{idx}'))
        self.tree.tag_configure('category', font=('微软雅黑', 10, 'bold'))  # 分类加粗
        self.tree.tag_configure('selected', background='#bfbfbf', foreground='black')  # 子项选中样式
        self.tree.tag_configure('parent-selected', background='#858585', foreground='white')  # 父节点选中样式

    def on_double_click(self, event):
        item = self.tree.selection()[0]

        # 清除之前的选中项高亮
        if self.currently_selected_item:
            self.tree.item(self.currently_selected_item, tags=('item',))  # 移除子节点选中样式

        # 清除之前的父节点高亮
        if self.currently_selected_parent:
            self.tree.item(self.currently_selected_parent, tags=('category',))  # 恢复父节点默认样式

        # 节点类型判断（通过tags识别）
        if 'category' in self.tree.item(item, 'tags'):
            if self.tree.item(item, "open"):
                self.tree.item(item, open=False)
                self.tree.after(100, lambda: self.tree.yview_moveto(0))  # 折叠后滚动到顶
            else:
                self.tree.item(item, open=True)
        else:
            # 处理文件选择
            file_name = self.tree.item(item, "text")
            if file_name == self.currently_selected_item:
                return

            parent_item = self.tree.parent(item)
            if parent_item:
                parent_text = self.tree.item(parent_item, "text")
                try:
                    album_name, disc_name = parent_text.split(maxsplit=1)
                    all_album_name = music_player.music_dir[album_name]

                    # 更新当前选中项
                    self.currently_selected_item = item
                    self.tree.item(item, tags=('item', 'selected'))  # 添加子节点选中样式

                    # 更新当前父节点
                    self.currently_selected_parent = parent_item
                    self.tree.item(parent_item, tags=('category', 'parent-selected'))  # 添加父节点选中样式

                    music_handle(all_album_name, disc_name, file_name)
                except Exception as e:
                    # print(f"节点解析错误: {str(e)}")
                    messagebox.showerror("错误", f"节点解析错误：{str(e)}")
            else:
                # print(f"未找到父节点: {file_name}")
                messagebox.showerror("错误", f"未找到父节点：{file_name}")

# 鼠标悬停选项时提示
class ExpandableList:
    def __init__(self, parent_frame, categories, row, column):
        # 创建主框架
        self.frame = ttk.Frame(parent_frame, padding=(5, 5))
        self.frame.grid(row=row, column=column, padx=5, pady=5, sticky="nsew")
        self.frame.grid_rowconfigure(0, weight=1)
        self.frame.grid_columnconfigure(0, weight=1)

        # 配置Treeview样式
        style = ttk.Style()
        self.style_name = "ExpandableList.Treeview"
        style.configure(self.style_name,
                        font=('微软雅黑', 10, 'normal'),
                        rowheight=22)
        style.map(self.style_name,
                  background=[('selected', '#d3d3d3')],
                  foreground=[('selected', 'black')])

        # 创建Treeview
        self.tree = ttk.Treeview(
            self.frame,
            style=self.style_name,  # 应用自定义样式
            selectmode="browse",
            height=10,  # 优化可见行数
            show="tree",
        )
        self.tree.grid(row=0, column=0, sticky="nsew", padx=2, pady=2)

        # 滚动条样式
        style.configure(
            "Custom.Vertical.TScrollbar",  # 垂直滚动条样式
            background="#f0f0f0",          # 滚动条背景色
            troughcolor="#f0f0f0",         # 滚动槽颜色
            gripcount=0                    # 移除默认的条纹效果
        )
        scrollbar = tk.Scrollbar(self.frame, command=self.tree.yview)
        scrollbar.grid(row=0, column=1, sticky="ns", padx=(0, 2), pady=2)
        self.tree.configure(yscrollcommand=scrollbar.set)

        # 增强交互反馈
        self.tree.bind("<Double-1>", self.on_double_click)
        self.tree.bind("<Enter>", lambda e: self.tree.config(cursor="hand2"))
        self.tree.bind("<Leave>", lambda e: self.tree.config(cursor="arrow"))
        
        # 添加鼠标悬停事件绑定
        self.tree.bind("<Motion>", self.on_mouse_hover)
        self.last_hovered_item = None
        self.tooltip_window = None

        # 初始化数据
        self.add_categories(categories)

        # 当前选中项和父节点
        self.currently_selected_item = None
        self.currently_selected_parent = None

    def add_categories(self, categories):
        for category, items in categories.items():
            parent = self.tree.insert("", "end",
                                      text=category,
                                      open=False,
                                      tags=('category',))
            for idx, item in enumerate(items, 1):
                self.tree.insert(parent, "end",
                                 text=item,
                                 tags=('item', f'item-{idx}'))
        self.tree.tag_configure('category', font=('微软雅黑', 10, 'bold'))  # 分类加粗
        self.tree.tag_configure('selected', background='#bfbfbf', foreground='black')  # 子项选中样式
        self.tree.tag_configure('parent-selected', background='#858585', foreground='white')  # 父节点选中样式

    def on_mouse_hover(self, event):
        # 处理鼠标悬停事件，显示工具提示
        item = self.tree.identify_row(event.y)
        
        # 如果鼠标不在任何项目上，隐藏工具提示
        if not item:
            if self.tooltip_window:
                self.tooltip_window.destroy()
                self.tooltip_window = None
            self.last_hovered_item = None
            return
            
        # 如果鼠标仍在同一个项目上，不做任何操作
        if item == self.last_hovered_item:
            return
            
        # 更新最后悬停的项目
        self.last_hovered_item = item
        
        # 如果工具提示窗口已存在，先销毁它
        if self.tooltip_window:
            self.tooltip_window.destroy()
            self.tooltip_window = None
            
        # 获取项目文本
        item_text = self.tree.item(item, "text")
        
        # 获取项目在屏幕上的位置
        bbox = self.tree.bbox(item)
        if not bbox:  # 如果项目不可见（不在视图中）
            return
            
        x, y, width, height = bbox
        
        # 计算工具提示位置
        x_root = self.tree.winfo_rootx() + x + width + 5
        y_root = self.tree.winfo_rooty() + y
        
        # 创建工具提示窗口
        self.tooltip_window = tk.Toplevel(self.tree)
        self.tooltip_window.wm_overrideredirect(True)
        self.tooltip_window.wm_geometry(f"+{x_root}+{y_root}")
        
        # 设置工具提示样式
        label = tk.Label(self.tooltip_window, 
                         text=item_text,
                         background="#ffffe0", 
                         relief="solid", 
                         borderwidth=1,
                         font=('微软雅黑', 9),
                         padx=2, pady=1)
        label.pack()
        
        # 绑定鼠标离开事件
        self.tree.bind("<Leave>", lambda e: self.hide_tooltip())

    def hide_tooltip(self):
        # 隐藏工具提示
        if self.tooltip_window:
            self.tooltip_window.destroy()
            self.tooltip_window = None
        self.last_hovered_item = None

    def on_double_click(self, event):
        # 隐藏工具提示（如果存在）
        self.hide_tooltip()
        
        item = self.tree.selection()[0]

        # 清除之前的选中项高亮
        if self.currently_selected_item:
            self.tree.item(self.currently_selected_item, tags=('item',))  # 移除子节点选中样式

        # 清除之前的父节点高亮
        if self.currently_selected_parent:
            self.tree.item(self.currently_selected_parent, tags=('category',))  # 恢复父节点默认样式

        # 节点类型判断（通过tags识别）
        if 'category' in self.tree.item(item, 'tags'):
            if self.tree.item(item, "open"):
                self.tree.item(item, open=False)
                self.tree.after(100, lambda: self.tree.yview_moveto(0))  # 折叠后滚动到顶
            else:
                self.tree.item(item, open=True)
        else:
            # 处理文件选择
            file_name = self.tree.item(item, "text")
            if file_name == self.currently_selected_item:
                return

            parent_item = self.tree.parent(item)
            if parent_item:
                parent_text = self.tree.item(parent_item, "text")
                try:
                    album_name, disc_name = parent_text.split(maxsplit=1)
                    all_album_name = music_player.music_dir[album_name]

                    # 更新当前选中项
                    self.currently_selected_item = item
                    self.tree.item(item, tags=('item', 'selected'))  # 添加子节点选中样式

                    # 更新当前父节点
                    self.currently_selected_parent = parent_item
                    self.tree.item(parent_item, tags=('category', 'parent-selected'))  # 添加父节点选中样式

                    music_handle(all_album_name, disc_name, file_name)
                except Exception as e:
                    messagebox.showerror("错误", f"节点解析错误：{str(e)}")
            else:
                messagebox.showerror("错误", f"未找到父节点：{file_name}")