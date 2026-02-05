from tkinter import messagebox

import queue
# 创建线程安全的队列，用于子线程向主线程传递错误信息
error_queue = queue.Queue()

def check_error_queue(root):
    # 主线程轮询错误队列，处理GUI提示，需在主线程调用
    try:
        # 非阻塞获取队列中的错误信息
        while not error_queue.empty():
            error_msg = error_queue.get_nowait()
            messagebox.showerror("错误", error_msg)
    except queue.Empty:
        pass
    # 每隔100ms轮询一次、tkinter事件循环
    root.after(100, lambda: check_error_queue(root))