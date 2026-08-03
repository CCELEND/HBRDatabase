from PyQt5.QtWidgets import (
    QScrollArea, QWidget, QFrame, QMainWindow,
    QGridLayout, QSizePolicy
)
from PyQt5.QtCore import Qt, QObject, QEvent

from canvas_events_qt import BackgroundFrame


class _VerticalGridLayout(QGridLayout):
    """
    QGridLayout 兼容布局：
    - 无行列参数调用 addWidget(widget) 时自动按垂直方向堆叠
    - 带行列参数调用 addWidget(widget, row, col, ...) 时按网格布局
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self._next_row = 0

    def addWidget(self, widget, *args, **kwargs):
        if len(args) == 0:
            super().addWidget(widget, self._next_row, 0, **kwargs)
            self._next_row += 1
        else:
            super().addWidget(widget, *args, **kwargs)


class ScrollbarFrameWin(QObject):
    def __init__(self, parent_widget: QWidget, columnspan: int = 6,
                 bg_image_path: str = None, bg_opacity: str = "100%"):
        super().__init__(parent_widget)
        self.root = parent_widget
        self.columnspan = columnspan

        self.scroll_area = QScrollArea(parent_widget)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.scroll_area.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.scroll_area.setFrameShape(QFrame.NoFrame)

        # 若指定了背景图，在滚动区域视口内创建固定的 BackgroundFrame
        self._bg_frame = None
        if bg_image_path and __import__("os").path.exists(bg_image_path):
            viewport = self.scroll_area.viewport()
            self._bg_frame = BackgroundFrame(viewport, bg_image_path, bg_opacity)
            self._bg_frame.setGeometry(viewport.rect())
            self._bg_frame.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
            # 监听视口尺寸变化，保持背景铺满
            viewport.installEventFilter(self)

        # 滚动条样式
        self.scroll_area.setStyleSheet("""
            /* 滚动区域本身无边框无背景 */
            QScrollArea {
                border: none;
                background: transparent;
            }

            /* ----- 垂直滚动条 ----- */
            QScrollBar:vertical {
                border: none;
                background: rgba(0, 0, 0, 0.06);   /* 极浅的灰色底 */
                width: 8px;
                margin: 0px;
                border-radius: 4px;
            }
            QScrollBar::handle:vertical {
                background: rgba(0, 0, 0, 0.25);   /* 手柄半透明深灰 */
                min-height: 30px;
                border-radius: 4px;
            }
            QScrollBar::handle:vertical:hover {
                background: rgba(0, 0, 0, 0.40);   /* 悬停变深 */
            }
            QScrollBar::handle:vertical:pressed {
                background: rgba(0, 0, 0, 0.60);   /* 按下更深 */
            }
            /* 隐藏上下箭头按钮，更简洁 */
            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical {
                border: none;
                background: none;
                height: 0px;
            }
            /* 隐藏滚动条占位区域（页眉/页脚） */
            QScrollBar::add-page:vertical,
            QScrollBar::sub-page:vertical {
                background: none;
            }

            /* ----- 水平滚动条 ----- */
            QScrollBar:horizontal {
                border: none;
                background: rgba(0, 0, 0, 0.06);
                height: 8px;
                margin: 0px;
                border-radius: 4px;
            }
            QScrollBar::handle:horizontal {
                background: rgba(0, 0, 0, 0.25);
                min-width: 30px;
                border-radius: 4px;
            }
            QScrollBar::handle:horizontal:hover {
                background: rgba(0, 0, 0, 0.40);
            }
            QScrollBar::handle:horizontal:pressed {
                background: rgba(0, 0, 0, 0.60);
            }
            /* 隐藏左右箭头按钮 */
            QScrollBar::add-line:horizontal,
            QScrollBar::sub-line:horizontal {
                border: none;
                background: none;
                width: 0px;
            }
            QScrollBar::add-page:horizontal,
            QScrollBar::sub-page:horizontal {
                background: none;
            }
        """)


        # 将垂直滚动条设为始终显示
        # self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)

        self.scrollable_frame = QWidget()
        self.scrollable_frame.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        if self._bg_frame is not None:
            # 滚动内容区域透明，让视口层的背景图透出来
            self.scrollable_frame.setStyleSheet("""
                QWidget {
                    background-color: transparent;
                }
            """)
        self.scroll_area.setWidget(self.scrollable_frame)

        self.layout = _VerticalGridLayout(self.scrollable_frame)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(5)
        self.layout.setAlignment(Qt.AlignTop)

        target_widget = parent_widget
        if isinstance(parent_widget, QMainWindow):
            target_widget = parent_widget.centralWidget()
            if target_widget is None:
                target_widget = QWidget(parent_widget)
                parent_widget.setCentralWidget(target_widget)

        parent_layout = target_widget.layout()
        if parent_layout is None:
            parent_layout = QGridLayout(target_widget)
            parent_layout.setContentsMargins(0, 0, 0, 0)
            parent_layout.setSpacing(0)
        if isinstance(parent_layout, QGridLayout):
            parent_layout.setRowStretch(0, 1)
            for col in range(self.columnspan):
                parent_layout.setColumnStretch(col, 1)
            parent_layout.addWidget(self.scroll_area, 0, 0, 1, self.columnspan)
        else:
            parent_layout.addWidget(self.scroll_area)

    def eventFilter(self, watched, event):
        if self._bg_frame is not None:
            try:
                viewport = self.scroll_area.viewport()
            except RuntimeError:
                # 窗口关闭/销毁过程中，滚动区域可能已被释放
                return False
            if watched is viewport and event.type() == QEvent.Resize:
                try:
                    self._bg_frame.setGeometry(viewport.rect())
                except RuntimeError:
                    pass
        return super().eventFilter(watched, event)

    def destroy_components(self):
        layout = self.scrollable_frame.layout()
        if layout is None:
            return
        layout._next_row = 0
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
            sub_layout = item.layout()
            if sub_layout:
                self._clear_layout(sub_layout)

    def _clear_layout(self, layout):
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
            sub_layout = item.layout()
            if sub_layout:
                self._clear_layout(sub_layout)

    def update_canvas(self):
        self.scroll_area.updateGeometry()
        self.scrollable_frame.updateGeometry()

    def on_mousewheel(self, event):
        delta = event.angleDelta().y()
        self.scroll_area.verticalScrollBar().setValue(
            self.scroll_area.verticalScrollBar().value() - int(delta / 40)
        )
