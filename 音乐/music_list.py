import sys
import os

import tkinter as tk
from PIL import Image, ImageTk
import json
import tkinter as tk
from tkinter import scrolledtext, Menu, messagebox
from tkinter import ttk

import music_player
from music_handle_processing import music_handle

class ExpandableList:
    def __init__(self, parent_frame, categories, row, column):
        # 创建主框架
        self.frame = ttk.Frame(parent_frame)
        self.frame.grid(row=row, column=column, padx=10, pady=10, sticky="nsew")
        self.frame.grid_rowconfigure(0, weight=1)
        self.frame.grid_columnconfigure(0, weight=1)
        
        # 创建Treeview组件
        self.tree = ttk.Treeview(
            self.frame,
            selectmode="browse",
            height=15,
            show="tree"
        )
        self.tree.grid(row=0, column=0, sticky="nsew")
        
        # 添加滚动条
        scrollbar = ttk.Scrollbar(self.frame, command=self.tree.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")

        # 配置滚动条
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        # 绑定双击事件
        self.tree.bind("<Double-1>", self.on_double_click)
        
        # 添加分类数据
        self.add_categories(categories)
    
    # 添加分类和选项数据
    def add_categories(self, categories):
        for category, items in categories.items():
            # 添加分类节点
            parent = self.tree.insert("", "end", text=category, open=False)
            # 添加该分类下的选项
            for item in items:
                self.tree.insert(parent, "end", text=item)
    
    # 处理双击事件
    def on_double_click(self, event):
        item = self.tree.focus()
        file_name = self.tree.item(item, "text")
        
        # 检查是否是分类节点（有子节点）
        if self.tree.get_children(item):
            # 切换展开/折叠状态
            if self.tree.item(item, "open"):
                self.tree.item(item, open=False)
            else:
                self.tree.item(item, open=True)
        else:
            # 获取父节点
            parent_item = self.tree.parent(item)
            if parent_item:  # 确保有父节点
                parent_text = self.tree.item(parent_item, "text")
                album_name, disc_name = parent_text.split()
                all_albun_name = music_player.music_dir[album_name]

                # file_path_album = all_albun_name + "/" + disc_name + "/" + file_name
                # music_handle(all_albun_name, file_path_album)
                music_handle(all_albun_name, disc_name, file_name)
            else:
                print(f"文件名: {file_name}, 没有父节点")
