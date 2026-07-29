
from PyQt5.QtWidgets import (
    QFrame, QTreeWidget, QTreeWidgetItem, QVBoxLayout,
    QToolTip, QMessageBox, QTreeWidgetItemIterator, QAbstractItemView
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

import music_player_qt as music_player
from music_handle_processing_qt import music_handle

from 日志.advanced_logger import AdvancedLogger
logger = AdvancedLogger.get_logger(__name__)


currently_selected = ""


class MusicTreeWidget(QTreeWidget):
    """自定义树形控件，直接处理鼠标事件绕过 Qt 信号问题"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.expandable_list = None

    def set_expandable_list(self, expandable_list):
        self.expandable_list = expandable_list

    def mousePressEvent(self, event):
        super().mousePressEvent(event)
        if self.expandable_list:
            item = self.itemAt(event.pos())
            if item:
                self.expandable_list.handle_item_click(item)

    def mouseDoubleClickEvent(self, event):
        super().mouseDoubleClickEvent(event)
        if self.expandable_list:
            item = self.itemAt(event.pos())
            if item:
                self.expandable_list.handle_item_double_click(item)


class ExpandableList:
    def __init__(self, parent_frame, categories, row, column, music_win_name):
        self.frame = QFrame(parent_frame)
        self.frame.setLayout(QVBoxLayout())
        self.frame.layout().setContentsMargins(5, 5, 5, 5)
        self.music_win_name = music_win_name

        if hasattr(parent_frame, 'grid_layout'):
            parent_frame.grid_layout.addWidget(self.frame, row, column)

        self.tree = MusicTreeWidget(self.frame)
        self.tree.set_expandable_list(self)
        self.tree.setHeaderHidden(True)
        self.tree.setColumnCount(1)
        self.tree.setFocusPolicy(Qt.StrongFocus)
        self.tree.setEnabled(True)
        self.tree.setCursor(Qt.PointingHandCursor)
        self.frame.layout().addWidget(self.tree)

        self.tree.itemEntered.connect(self.on_mouse_hover)
        self.tree.setMouseTracking(True)

        self.currently_selected_item = None
        self.currently_selected_parent = None

        self.add_categories(categories)

    def handle_item_click(self, item):
        self.tree.setCurrentItem(item)

    def handle_item_double_click(self, item):
        self.on_double_click(item, 0)

    def add_categories(self, categories):
        try:
            bold_font = QFont("微软雅黑", 10, QFont.Bold)
            for category, items in categories.items():
                parent = QTreeWidgetItem(self.tree)
                parent.setText(0, category)
                parent.setFont(0, bold_font)
                parent.setData(0, Qt.UserRole, "category")
                parent.setExpanded(False)
                for idx, item in enumerate(items, 1):
                    child = QTreeWidgetItem(parent)
                    child.setText(0, item)
                    child.setData(0, Qt.UserRole, "item")
        except Exception as e:
            logger.error(f"add_categories error: {e}", exc_info=True)

    def on_mouse_hover(self, item, column):
        if item is None:
            QToolTip.hideText()
            return
        QToolTip.showText(self.tree.mapToGlobal(
            self.tree.visualItemRect(item).topRight()
        ), item.text(column), self.tree)

    def on_double_click(self, item, column):
        QToolTip.hideText()

        item_type = item.data(0, Qt.UserRole)
        if item_type == "category":
            item.setExpanded(not item.isExpanded())
            if not item.isExpanded():
                self.tree.scrollToTop()
            return

        file_name = item.text(0)
        if file_name == self.currently_selected_item:
            return

        parent_item = item.parent()
        if parent_item:
            parent_text = parent_item.text(0)
            try:
                album_name, disc_name = parent_text.split(maxsplit=1)
                all_album_name = music_player.music_dir[album_name]

                if self.currently_selected_item:
                    prev = self._find_item_by_text(self.currently_selected_item)
                    if prev:
                        prev.setBackground(0, Qt.transparent)
                        prev.setForeground(0, Qt.black)

                if self.currently_selected_parent:
                    prev_parent = self._find_item_by_text(self.currently_selected_parent, parent_only=True)
                    if prev_parent:
                        prev_parent.setBackground(0, Qt.transparent)
                        prev_parent.setForeground(0, Qt.black)

                self.currently_selected_item = file_name
                item.setBackground(0, Qt.gray)
                item.setForeground(0, Qt.white)

                self.currently_selected_parent = parent_text
                parent_item.setBackground(0, Qt.darkGray)
                parent_item.setForeground(0, Qt.white)

                music_handle(all_album_name, disc_name, file_name, self.music_win_name)
            except Exception as e:
                logger.error(f"节点解析错误：{str(e)}")
                QMessageBox.critical(self.frame, "错误", f"节点解析错误：{str(e)}")
        else:
            logger.error(f"未找到父节点：{file_name}")
            QMessageBox.critical(self.frame, "错误", f"未找到父节点：{file_name}")

    def _find_item_by_text(self, text, parent_only=False):
        iterator = QTreeWidgetItemIterator(self.tree)
        while iterator.value():
            item = iterator.value()
            if item.text(0) == text:
                if parent_only:
                    if item.data(0, Qt.UserRole) == "category":
                        return item
                else:
                    if item.data(0, Qt.UserRole) == "item":
                        return item
            iterator += 1
        return None

