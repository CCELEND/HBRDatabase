
from PyQt5.QtWidgets import QWidget, QGroupBox, QLabel, QGridLayout
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

MONO_FONT = QFont("Monospace", 10, QFont.Bold)


def creat_growth_status_frame(parent_frame, growth_status_frame_row, style):
    growth_status_frame = QGroupBox("成长状态")
    growth_status_frame.setFont(MONO_FONT)

    parent_layout = parent_frame.layout()
    if parent_layout is not None:
        parent_layout.addWidget(growth_status_frame)

    layout = QGridLayout(growth_status_frame)
    layout.setSpacing(5)
    layout.setContentsMargins(10, 10, 10, 10)

    text = f"DP {style.status_growth['DP']}\n"
    text += "力量" + f"{style.status_growth['力量']}\n".rjust(10)
    text += "体力" + f"{style.status_growth['体力']}\n".rjust(10)
    text += "智慧" + f"{style.status_growth['智慧']}".rjust(9)
    growth_status_lab = QLabel(text)
    growth_status_lab.setFont(MONO_FONT)
    growth_status_lab.setAlignment(Qt.AlignLeft | Qt.AlignBottom)
    layout.addWidget(growth_status_lab, 0, 0, alignment=Qt.AlignLeft | Qt.AlignBottom)

    text = "灵巧" + f"{style.status_growth['灵巧']}\n".rjust(10)
    text += "精神" + f"{style.status_growth['精神']}\n".rjust(10)
    text += "运气" + f"{style.status_growth['运气']}".rjust(9)
    growth_status_lab1 = QLabel(text)
    growth_status_lab1.setFont(MONO_FONT)
    growth_status_lab1.setAlignment(Qt.AlignLeft | Qt.AlignBottom)
    layout.addWidget(growth_status_lab1, 0, 1, alignment=Qt.AlignLeft | Qt.AlignBottom)

    layout.setColumnStretch(0, 1)
    layout.setColumnStretch(1, 1)

    return growth_status_frame
