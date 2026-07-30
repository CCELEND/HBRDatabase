
import types

from PyQt5.QtWidgets import QLabel, QGroupBox, QGridLayout
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

from window_qt import set_window_expand, set_window_icon, creat_Toplevel
from window_qt import win_open_manage, win_close_manage, is_win_open, win_set_top

from 更新.hash import calculate_file_hash


MONO_FONT = QFont("Monospace", 10, QFont.Bold)


def creat_about_win(parent_frame):
    if is_win_open("关于 HBRDatabase", __name__):
        win_set_top("关于 HBRDatabase", __name__)
        return

    about_win_frame = creat_Toplevel("关于 HBRDatabase", 730, 540, 180, 170)
    set_window_icon(about_win_frame, "./关于/KamiSama.ico")
    set_window_expand(about_win_frame, rowspan=3, columnspan=2)

    key, file_hash = calculate_file_hash("./关于/server_file_hashes.json", "server_file_hashes")

    central = about_win_frame.centralWidget()
    layout = central.layout()
    if layout is not None:
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(5)
    else:
        layout = QGridLayout(central)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(5)

    ver_frame = QGroupBox("🧰版本")
    ver_frame.setStyleSheet("QGroupBox::title { font-size: 10px; }")
    ver_layout = QGridLayout(ver_frame)
    ver_layout.setContentsMargins(10, 10, 10, 10)
    describe = f"HBRDatabase2.0a (build-{file_hash[0:8]})"
    label = QLabel(describe)
    label.setFont(MONO_FONT)
    label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
    ver_layout.addWidget(label, 0, 0)
    layout.addWidget(ver_frame, 0, 0, 1, 2)

    develop_frame = QGroupBox("🔧开发")
    develop_frame.setStyleSheet("QGroupBox::title { font-size: 10px; }")
    develop_layout = QGridLayout(develop_frame)
    develop_layout.setContentsMargins(10, 10, 10, 10)
    describe = ("如有疑问请与我联系：\n不吃花椒的汪汪队（B站空间：https://space.bilibili.com/442776860）\n"
                "QQ：2644884626\n邮箱：celend2644884626@163.com\n"
                "GitHub：https://github.com/CCELEND/HBRDatabase\n协议：GPL-3.0 license")
    label = QLabel(describe)
    label.setFont(MONO_FONT)
    label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
    develop_layout.addWidget(label, 0, 0)
    layout.addWidget(develop_frame, 1, 0, 1, 2)

    info_frame = QGroupBox("📰参考资料")
    info_frame.setStyleSheet("QGroupBox::title { font-size: 10px; }")
    info_layout = QGridLayout(info_frame)
    info_layout.setContentsMargins(10, 10, 10, 10)
    describe = ("资料站：https://hbr.quest/\n资料站v5.10：https://o.hbr.quest/\n"
                "快查表：hbr-kc.top\n日服攻略：https://game8.jp/heavenburnsred\n"
                "国服官方工具：https://game.bilibili.com/tool/hbr#/\n"
                "炽焰天穹_HBR（B站空间：https://space.bilibili.com/3546599741458758）\n"
                "道家深湖（B站空间：https://space.bilibili.com/24124162）\n"
                "废纸扔了_快查表（B站空间：https://space.bilibili.com/61357074）\n"
                "兰叔爱玩炽焰天穹（B站空间：https://space.bilibili.com/10147172）\n"
                "茅森月哥（B站空间：https://space.bilibili.com/535889）")
    label = QLabel(describe)
    label.setFont(MONO_FONT)
    label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
    info_layout.addWidget(label, 0, 0)
    layout.addWidget(info_frame, 2, 0, 1, 2)

    win_open_manage(about_win_frame, __name__)
    about_win_frame.mousePressEvent = lambda ev: win_set_top(about_win_frame, __name__)

    # 正确关闭事件
    def on_close(ev):
        win_close_manage(about_win_frame, __name__)
        ev.accept()
    about_win_frame.closeEvent = on_close

    return "break"

