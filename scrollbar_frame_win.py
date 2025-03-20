
import tkinter as tk

# 滚动条窗口类
class ScrollbarFrameWin:
    def __init__(self, parent_frame, columnspan):
        # 初始化
        self.root = parent_frame
        self.create_scrollbar_frame(columnspan)

    # 调整 Canvas 大小 为父窗口宽度
    def on_canvas_resize(self, event):
        self.canvas.itemconfig(self.window_id, width=event.width)
        self.update_scrollregion()

    # 处理鼠标滚轮事件
    def on_mousewheel(self, event):
        self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    # 更新滚动区域
    def update_scrollregion(self, event=None):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    # 更新 Canvas 的滚动区域
    def update_canvas(self):
        self.scrollable_frame.update_idletasks()
        self.update_scrollregion()

    # 清除之前的组件
    def destroy_components(self):
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()

    # 创建和滚动区域 Frame
    def create_scrollbar_frame(self, columnspan):
        self.scrollbar_frame = tk.Frame(self.root)
        self.scrollbar_frame.grid(row=0, column=0, columnspan=columnspan, sticky="nsew")
        for col in range(columnspan):
            self.scrollbar_frame.grid_columnconfigure(col, weight=1)
        # self.scrollbar_frame.grid_rowconfigure(0, weight=1)

        self.canvas = tk.Canvas(self.scrollbar_frame)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.scrollbar = tk.Scrollbar(self.scrollbar_frame, orient=tk.VERTICAL, command=self.canvas.yview)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.scrollable_frame = tk.Frame(self.canvas)
        self.scrollable_frame.grid_rowconfigure(0, weight=1)
        for col in range(columnspan):
            self.scrollable_frame.grid_columnconfigure(col, weight=1)

        self.window_id = self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor='nw')
        self.canvas.bind("<Configure>", self.on_canvas_resize)
        self.root.bind("<MouseWheel>", self.on_mousewheel)


# 返回一个实例 scrollbar_frame_obj 
# 使用之前应该先销毁组件
# scrollbar_frame_obj.destroy_components()
# 使用后需要更新 canvas
# scrollbar_frame_obj.update_canvas()