
import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk

from tools import load_json

strengthen_materials_dir = {}
# 加载资源文件
def load_resources():
    global strengthen_materials_dir
    if strengthen_materials_dir:
        return
    strengthen_materials_dir = load_json("./持有物/强化素材/strengthen_materials.json")




