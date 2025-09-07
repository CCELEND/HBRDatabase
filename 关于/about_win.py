
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from window import set_window_expand, set_window_icon, creat_Toplevel
from window import win_open_manage, win_close_manage, is_win_open, win_set_top


# 创建关于窗口
def creat_about_win(parent_frame):

    # 重复打开时，窗口置顶并直接返回
    if is_win_open("关于 HBRDatabase", __name__):
        win_set_top("关于 HBRDatabase", __name__)
        return

    about_win_frame = creat_Toplevel("关于 HBRDatabase", 730, 540, x=180, y=170)
    set_window_icon(about_win_frame, "./关于/KamiSama.ico")
    set_window_expand(about_win_frame, rowspan=3, columnspan=2)

    # 创建 LabelFrame
    ver_frame = ttk.LabelFrame(about_win_frame, text="🧰版本")
    ver_frame.grid(row=0, column=0, columnspan=2, padx=10, pady=(5,0), sticky="nsew")
    describe = "HBRDatabase1.68 (build-0822b1d6) [main 11c0b08]"
    # 设置了标签的字体为 Monospace 大小为 10，加粗
    label = ttk.Label(ver_frame, text=describe, anchor="center", font=("Monospace", 10, "bold"))
    label.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
    # 设置 LabelFrame 的行和列的权重
    ver_frame.grid_rowconfigure(0, weight=1)
    ver_frame.grid_columnconfigure(0, weight=1)

    # 创建 LabelFrame
    develop_frame = ttk.LabelFrame(about_win_frame, text="🔧开发")
    develop_frame.grid(row=1, column=0, columnspan=2, padx=10, pady=(5,0), sticky="nsew")
    describe = "如有疑问请与我联系：\n不吃花椒的汪汪队（B站空间：https://space.bilibili.com/442776860）\nQQ：2644884626\n邮箱：celend2644884626@163.com\nGitHub：https://github.com/CCELEND/HBRDatabase\n协议：GPL-3.0 license"
    # 设置了标签的字体为 Monospace 大小为 10，加粗
    label = ttk.Label(develop_frame, text=describe, anchor="center", font=("Monospace", 10, "bold"))
    label.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
    # 设置 LabelFrame 的行和列的权重
    develop_frame.grid_rowconfigure(0, weight=1)
    develop_frame.grid_columnconfigure(0, weight=1)

    # 创建 LabelFrame
    info_frame = ttk.LabelFrame(about_win_frame, text="📰参考资料")
    info_frame.grid(row=2, column=0, columnspan=2, padx=10, pady=(5,10), sticky="nsew")
    describe = "资料站：https://hbr.quest/\n资料站v5.10：https://o.hbr.quest/\n快查表：hbr-kc.top\n日服攻略：https://game8.jp/heavenburnsred\n国服官方工具：https://game.bilibili.com/tool/hbr#/\n炽焰天穹_HBR（B站空间：https://space.bilibili.com/3546599741458758）\n道家深湖（B站空间：https://space.bilibili.com/24124162）\n废纸扔了_快查表（B站空间：https://space.bilibili.com/61357074）\n兰叔爱玩炽焰天穹（B站空间：https://space.bilibili.com/10147172）\n茅森月哥（B站空间：https://space.bilibili.com/535889）"
    # 设置了标签的字体为 Monospace 大小为 10，加粗
    label = ttk.Label(info_frame, text=describe, anchor="center", font=("Monospace", 10, "bold"))
    label.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
    # 设置 LabelFrame 的行和列的权重
    info_frame.grid_rowconfigure(0, weight=1)
    info_frame.grid_columnconfigure(0, weight=1)

    win_open_manage(about_win_frame, __name__)
    # 绑定鼠标点击事件到父窗口，点击置顶
    about_win_frame.bind("<Button-1>", lambda event: win_set_top(about_win_frame, __name__))
    # 窗口关闭时清理
    about_win_frame.protocol("WM_DELETE_WINDOW", lambda: win_close_manage(about_win_frame, __name__))

    return "break"  # 阻止事件冒泡


