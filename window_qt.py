import os
import numpy as np
import cv2
from PIL import Image

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QMenu, QTextEdit, QLineEdit,
    QMessageBox, QLabel, QGridLayout,
    QGraphicsView, QGraphicsScene, QGraphicsPixmapItem,
    QSizePolicy, QStatusBar
)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QIcon, QPixmap, QImage, QPainter


def set_global_bg(parent: QApplication, bg="#f0f0f0"):
    parent.setStyleSheet(f"""
        QMainWindow, QDialog {{
            background-color: {bg};
        }}
        QGroupBox {{
            background-color: transparent;
            border: 1px solid rgba(200, 200, 200, 120);
            border-radius: 6px;
            margin-top: 10px;
            font-weight: bold;
        }}
        QGroupBox::title {{
            subcontrol-origin: margin;
            left: 10px;
            padding: 2px 8px;
            background-color: rgba(255, 255, 255, 160);
            border-radius: 4px;
            color: #222222;
            font-weight: bold;
        }}

        QMenuBar {{
            background-color: #f0f0f0;
        }}
        QMenuBar::item:selected {{
            background-color: #d0d0d0;
        }}

        QMenu {{
            background-color: #ffffff;
            border: 1px solid #d0d0d0;
            border-radius: 6px;
            padding: 4px 0px;
        }}
        QMenu::item {{
            padding: 6px 30px 6px 20px;      /* 上下6px，左右留白，图标区自动保留 */
            background-color: transparent;
            font-size: 15px;
            font-weight: bold; /*             font-weight: normal; */

        }}
        QMenu::item:selected {{
            background-color: #0078d4;
            color: white;
        }}
        QMenu::item:disabled {{
            color: #b0b0b0;
        }}
        QMenu::separator {{
            height: 1px;
            background: #e0e0e0;
            margin: 4px 10px;               /* 左右留白，更精致 */
        }}
        /* 如果有带图标的菜单项，可调整图标与文字间距 */
        QMenu::icon {{
            padding-right: 8px;
        }}

        QWidget {{
            background-color: {bg};
        }}
        QLabel {{
            background-color: transparent;
        }}
    """)


menu_icons = {}
def load_menu_icon(path: str, name: str) -> QIcon:
    if not path or not os.path.exists(path):
        return QIcon()
    if name in menu_icons:
        return menu_icons[name]
    icon = QIcon(path)
    menu_icons[name] = icon
    return icon


def creat_window(title: str, wide=None, high=None, x=None, y=None) -> QMainWindow:
    new_window = QMainWindow()
    new_window.setWindowTitle(title)
    if wide is not None and high is not None:
        new_window.resize(wide, high)
    if x is not None and y is not None:
        new_window.move(x, y)
    return new_window


def creat_Toplevel(title: str, width=None, height=None, x=None, y=None) -> QMainWindow:
    if not isinstance(title, str):
        raise TypeError("title参数必须是字符串类型")
    for param, name in [(width, "width"), (height, "height"), (x, "x"), (y, "y")]:
        if param is not None and not isinstance(param, int):
            raise TypeError(f"{name}参数必须是整数类型或None")

    new_window = QMainWindow()
    new_window.setWindowTitle(title)
    if width is not None and height is not None:
        new_window.resize(width, height)
    if x is not None and y is not None:
        new_window.move(x, y)

    central = QWidget(new_window)
    new_window.setCentralWidget(central)
    new_window.grid_layout = QGridLayout(central)
    new_window.grid_layout.setContentsMargins(0, 0, 0, 0)
    new_window.grid_layout.setSpacing(0)
    new_window.show()
    return new_window


def _get_grid_layout(frame: QWidget):
    if hasattr(frame, 'grid_layout'):
        return frame.grid_layout
    return frame.layout()


def set_window_expand(frame: QWidget, rowspan=1, columnspan=1):
    layout = _get_grid_layout(frame)
    if layout is None:
        return
    for row in range(rowspan):
        layout.setRowStretch(row, 1)
    for col in range(columnspan):
        layout.setColumnStretch(col, 1)


def set_window_row_expand(frame: QWidget, rowspan=1):
    layout = _get_grid_layout(frame)
    if layout is None:
        return
    for row in range(rowspan):
        layout.setRowStretch(row, 1)


def set_window_colum_expand(frame: QWidget, columnspan=1):
    layout = _get_grid_layout(frame)
    if layout is None:
        return
    for col in range(columnspan):
        layout.setColumnStretch(col, 1)


def set_window_disable_maximize(parent_frame: QMainWindow):
    parent_frame.setWindowFlags(parent_frame.windowFlags() | Qt.Tool)
    parent_frame.show()


def set_window_disable_size(parent_frame: QMainWindow):
    parent_frame.setFixedSize(parent_frame.size())


def _save_ico(icon_path: str, size=(64, 64)) -> str:
    file_ext = os.path.splitext(icon_path)[1].lower()
    if file_ext == '.ico':
        return icon_path
    temp_ico_path = os.path.splitext(icon_path)[0] + '_temp.ico'
    image = Image.open(icon_path)
    image = image.resize(size, Image.LANCZOS)
    image.save(temp_ico_path, format='ICO', sizes=[size])
    return temp_ico_path


def set_window_icon(frame: QMainWindow, icon_path: str):
    if not os.path.exists(icon_path):
        QMessageBox.critical(frame, "错误", "图标文件未找到")
        return
    try:
        ico_path = _save_ico(icon_path)
        frame.setWindowIcon(QIcon(ico_path))
    except Exception as e:
        QMessageBox.critical(frame, "错误", f"设置图标时出错: {str(e)}")


def set_window_icon_webp(frame: QMainWindow, webp_path: str, size=(64, 64)):
    try:
        icon_image = Image.open(webp_path).convert("RGBA")
        icon_image = icon_image.resize(size, Image.LANCZOS)
        data = icon_image.tobytes("raw", "RGBA")
        pixmap = QPixmap.fromImage(
            QImage(data, icon_image.width, icon_image.height,
                   icon_image.width * 4, QImage.Format_RGBA8888)
        )
        frame.setWindowIcon(QIcon(pixmap))
    except FileNotFoundError:
        QMessageBox.critical(frame, "错误", "图标文件未找到")
    except Exception as e:
        QMessageBox.critical(frame, "错误", f"无法设置窗口图标: {e}")


def set_window_top(parent_frame: QMainWindow):
    parent_frame.showNormal()
    parent_frame.raise_()
    parent_frame.activateWindow()


def copy_text(event, text_widget):
    try:
        if isinstance(text_widget, (QTextEdit, QLineEdit)):
            text_widget.copy()
    except Exception:
        pass


def paste_text(event, text_widget):
    try:
        if isinstance(text_widget, (QTextEdit, QLineEdit)):
            text_widget.paste()
    except Exception:
        pass


def cut_text(event, text_widget):
    try:
        if isinstance(text_widget, (QTextEdit, QLineEdit)):
            text_widget.cut()
    except Exception:
        pass


def select_all_text(event, text_widget):
    try:
        if isinstance(text_widget, (QTextEdit, QLineEdit)):
            text_widget.selectAll()
    except Exception:
        pass


def show_context_menu(event, text_widget):
    menu = QMenu(text_widget)
    menu.addAction("复制", lambda: copy_text(event, text_widget))
    menu.addAction("粘贴", lambda: paste_text(event, text_widget))
    menu.addAction("剪切", lambda: cut_text(event, text_widget))
    menu.addAction("全选", lambda: select_all_text(event, text_widget))
    menu.addAction("清空", lambda: clear_text(text_widget))
    if hasattr(event, 'globalPos'):
        menu.exec_(event.globalPos())
    else:
        menu.exec_(text_widget.mapToGlobal(event))


def clear_text(*text_widgets):
    for text_widget in text_widgets:
        if isinstance(text_widget, QTextEdit):
            if not text_widget.isEnabled():
                text_widget.setEnabled(True)
                text_widget.clear()
                text_widget.setEnabled(False)
            else:
                text_widget.clear()
        elif isinstance(text_widget, QLineEdit):
            text_widget.clear()


def edit_text(text_widget, data):
    if isinstance(text_widget, QTextEdit):
        if not text_widget.isEnabled():
            text_widget.setEnabled(True)
            text_widget.clear()
            text_widget.setPlainText(str(data))
            text_widget.setEnabled(False)
        else:
            text_widget.clear()
            text_widget.setPlainText(str(data))
    elif isinstance(text_widget, QLineEdit):
        text_widget.setText(str(data))


def set_bg_opacity(parent_frame, parent_width, parent_height, bg_path, opacity):
    bg_image = Image.open(bg_path)
    bg_image = bg_image.resize((parent_width, parent_height), Image.LANCZOS)
    opacity_percentage = int(opacity.strip('%')) / 100
    gray_value = int(opacity_percentage * 255)
    mask = Image.new('L', bg_image.size, gray_value)
    bg_image.putalpha(mask)
    data = bg_image.tobytes("raw", "RGBA")
    pixmap = QPixmap.fromImage(
        QImage(data, bg_image.width, bg_image.height,
               bg_image.width * 4, QImage.Format_RGBA8888)
    )
    label = QLabel(parent_frame)
    label.setPixmap(pixmap)
    label.setGeometry(0, 0, parent_width, parent_height)
    return label


open_wins = {}
def win_open_manage(open_win_frame: QMainWindow, module: str):
    open_win_name = f"{module}_{open_win_frame.windowTitle()}"
    open_wins[open_win_name] = open_win_frame


def win_close_manage(open_win_frame: QMainWindow, module: str, class_resources=None):
    open_win_name = f"{module}_{open_win_frame.windowTitle()}"
    if open_win_name in open_wins:
        del open_wins[open_win_name]
    if class_resources:
        if hasattr(class_resources, 'destroy'):
            class_resources.destroy()
        elif hasattr(class_resources, 'release'):
            class_resources.release()
    open_win_frame.close()
    open_win_frame.deleteLater()


def win_close_all():
    for open_win_name in list(open_wins.keys()):
        win_frame = open_wins[open_win_name]
        del open_wins[open_win_name]
        win_frame.close()
        win_frame.deleteLater()


def win_set_top(open_win, module: str):
    if isinstance(open_win, str):
        open_win_name = f"{module}_{open_win}"
        if open_win_name in open_wins:
            set_window_top(open_wins[open_win_name])
    else:
        open_win_name = f"{module}_{open_win.windowTitle()}"
        if open_win_name in open_wins:
            set_window_top(open_wins[open_win_name])


def is_win_open(open_win_name: str, module: str) -> bool:
    open_win_name = f"{module}_{open_win_name}"
    return open_win_name in open_wins


def is_win_exist(win_frame: QMainWindow) -> bool:
    return win_frame is not None


def get_ico_path_by_name(name: str) -> str | None:
    if not name:
        return None
    infos = {
        "31A": "./角色/31A/DioramaStamp31a.ico",
        "31B": "./角色/31B/DioramaStamp31b.ico",
        "31C": "./角色/31C/DioramaStamp31c.ico",
        "30G": "./角色/30G/DioramaStamp30G.ico",
        "31D": "./角色/31D/DioramaStamp31d.ico",
        "31E": "./角色/31E/DioramaStamp31e.ico",
        "31F": "./角色/31F/DioramaStamp31f.ico",
        "31X": "./角色/31X/DioramaStamp31x.ico",
        "Angel Beats!": "./角色/Angel Beats!/angelbeats.ico",
        "司令部": "./角色/司令部/司令部.ico",
        "persona5r": "./角色/persona5r/persona5r.ico",
        "主线道具": "./持有物/主线道具/ThumbnailFishingRod.png",
        "道具": "./持有物/道具/ThumbnailHC.png",
        "饰品": "./持有物/饰品/专武/Soul_png.png",
        "饰品材料": "./持有物/饰品材料/ThumbnailDiamond.png",
        "活动奖章": "./持有物/活动奖章/ThumbnailPremierMedal.png",
        "奖杯勋章": "./持有物/奖杯勋章/ThumbnailtrophyBlack.png",
        "成长素材": "./持有物/成长素材/ThumbnailExpAllround5.png",
        "强化素材": "./持有物/强化素材/EternalDaphne.png",
        "增幅器": "./持有物/增幅器/SeraphBooster1.png",
        "芯片": "./持有物/芯片/SeraphArtifactChip1.png",
        "入场券": "./持有物/入场券/ThumbnailStoryHardModeTicket.png",
        "扭蛋材料": "./持有物/扭蛋材料/ThumbnailSSGachaTicket.png",
        "碎片": "./持有物/碎片/ImgIconItemL_StylePieceSSR.png",
        "货币": "./持有物/货币/ThumbnailGP.png",
        "时钟塔": "./敌人/时钟塔/boss.ico",
        "主线": "./敌人/主线/亡骨之翎/亡骨之翎.ico",
        "光球BOSS": "./敌人/光球BOSS/阿蒙之门B/阿蒙之门B.ico",
        "时之修炼场": "./敌人/时之修炼场/灵魂星兽.ico",
        "棱镜战": "./敌人/棱镜战/[幻影]深渊重锤/[幻影]深渊重锤.ico",
        "宝石棱镜战": "./敌人/宝石棱镜战/[幻影]群山重锤/[幻影]群山重锤.ico",
        "恒星扫荡战线": "./敌人/恒星战/DimensionBattleCentralTop_001.png",
        "高分挑战": "./敌人/高分挑战/夏日的诅咒#1/gf1.ico",
        "异时层": "./敌人/异时层/亡骨之翎Ω/亡骨之翎Ω.ico",
        "遭遇战": "./敌人/遭遇战/遭遇战#1/zyz1.ico",
        "职业": "./战斗系统/职业/ADMIRAL.png",
        "武器": "./战斗系统/武器/Sword.png",
        "属性": "./战斗系统/属性/Fire.png",
        "效果、状态": "./战斗系统/状态/Charge.png"
    }
    if name not in infos:
        return None
    return infos[name]


class ImageViewer(QGraphicsView):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)
        self.pixmap_item = QGraphicsPixmapItem()
        self.scene.addItem(self.pixmap_item)
        self.pixmap_item.setTransformationMode(Qt.SmoothTransformation)
        self.setRenderHint(QPainter.Antialiasing)
        self.setRenderHint(QPainter.SmoothPixmapTransform)
        self.setViewportUpdateMode(QGraphicsView.FullViewportUpdate)
        self.setDragMode(QGraphicsView.ScrollHandDrag)
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.AnchorUnderMouse)
        self.setBackgroundBrush(Qt.white)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setMinimumSize(400, 300)
        self._zoom_factor = 1.0
        self._min_zoom = 0.05
        self._max_zoom = 20.0
        self._image_loaded = False
        self._user_zoomed = False

    def _safe_fit_in_view(self):
        if not self._image_loaded:
            return
        rect = self.scene.sceneRect()
        if rect.width() < 1 or rect.height() < 1:
            return
        view_size = self.viewport().size()
        if view_size.width() < 10 or view_size.height() < 10:
            QTimer.singleShot(50, self._safe_fit_in_view)
            return
        self.fitInView(rect, Qt.KeepAspectRatio)
        self._zoom_factor = self.transform().m11()

    def set_image_from_path(self, file_path: str):
        if not os.path.exists(file_path):
            return False
        np_arr = np.fromfile(file_path, dtype=np.uint8)
        np_array = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
        if np_array is None:
            return False
        self.set_image_from_array(np_array)
        return True

    def set_image_from_array(self, np_array: np.ndarray):
        if np_array.ndim == 2:
            h, w = np_array.shape
            qimg = QImage(np_array.data, w, h, w, QImage.Format_Grayscale8)
        else:
            h, w, ch = np_array.shape
            rgb = cv2.cvtColor(np_array, cv2.COLOR_BGR2RGB)
            qimg = QImage(rgb.data, w, h, ch * w, QImage.Format_RGB888)
        pixmap = QPixmap.fromImage(qimg.copy())
        self.pixmap_item.setPixmap(pixmap)
        self.scene.setSceneRect(0, 0, w, h)
        self._image_loaded = True
        self._user_zoomed = False
        QTimer.singleShot(0, self._safe_fit_in_view)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if not self._image_loaded:
            return
        if not self._user_zoomed:
            self._safe_fit_in_view()

    def wheelEvent(self, event):
        delta = event.angleDelta().y()
        factor = 1.15 if delta > 0 else 1 / 1.15
        new_zoom = self._zoom_factor * factor
        if self._min_zoom <= new_zoom <= self._max_zoom:
            self.scale(factor, factor)
            self._zoom_factor = new_zoom
            self._user_zoomed = True

    def mouseDoubleClickEvent(self, event):
        self._user_zoomed = False
        self._safe_fit_in_view()
        super().mouseDoubleClickEvent(event)


class PreviewWindow(QMainWindow):
    def __init__(self, parent=None, title_name=None, width=1362, height=795):
        super().__init__(parent)
        self.setWindowTitle(title_name)
        self.resize(width, height)
        self.setMinimumSize(800, 600)
        self.move(300, 120)
        self.viewer = ImageViewer(self)
        self.setCentralWidget(self.viewer)
        status = QLabel("滚轮缩放 | 拖拽平移 | 双击适配窗口")
        status.setStyleSheet("background: #ecf0f1; padding: 4px 8px; color: #555; font-size: 12px;")
        sb = QStatusBar()
        sb.addPermanentWidget(status)
        self.setStatusBar(sb)

    def show_image(self, image_path: str):
        success = self.viewer.set_image_from_path(image_path)
        if not success:
            QMessageBox.warning(self, "加载失败", f"无法加载图片:\n{image_path}")

    def closeEvent(self, event):
        event.accept()
