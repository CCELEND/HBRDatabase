
from PyQt5.QtWidgets import QWidget, QGroupBox, QLabel, QGridLayout
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

from canvas_events_qt import get_pixmap, create_image_label

MONO_FONT = QFont("Monospace", 10, QFont.Bold)


def creat_resonance_frame(parent_frame, resonance_frame_row, style):
    name = style.resonance['name']
    resonance_frame = QGroupBox(f"共鸣天赋（{name}）")
    resonance_frame.setFont(MONO_FONT)

    parent_layout = parent_frame.layout()
    if parent_layout is not None:
        parent_layout.addWidget(resonance_frame)

    layout = QGridLayout(resonance_frame)
    layout.setSpacing(5)
    layout.setContentsMargins(10, 10, 10, 10)

    resonance_img_path = "./角色/IconResonance.png"
    resonance_pixmap = get_pixmap(resonance_img_path, (80, 64))
    resonance_label = create_image_label(resonance_frame, resonance_pixmap, 120, 120)
    layout.addWidget(resonance_label, 0, 0, alignment=Qt.AlignCenter)

    text = f"上限突破0：{style.resonance['0']}\n"
    text += f"上限突破1：{style.resonance['1']}\n"
    text += f"上限突破2：{style.resonance['2']}\n"
    text += f"上限突破3：{style.resonance['3']}\n"
    text += f"上限突破4：{style.resonance['4']}"
    resonance_lab = QLabel(text)
    resonance_lab.setFont(MONO_FONT)
    resonance_lab.setWordWrap(True)
    resonance_lab.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
    layout.addWidget(resonance_lab, 0, 1, alignment=Qt.AlignLeft | Qt.AlignVCenter)

    layout.setColumnStretch(0, 0)
    layout.setColumnStretch(1, 1)

    return resonance_frame
