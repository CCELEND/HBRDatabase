
import os
import time
from threading import Thread

from PyQt5.QtWidgets import (
    QFrame, QLabel, QPushButton, QSlider, QHBoxLayout,
    QVBoxLayout, QMessageBox, QFileDialog, QStyle, QStyleOptionSlider
)
from PyQt5.QtCore import Qt, QTimer

os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"
import pygame

play_info_frame = None
PlayerApp = None
ost_name = ""

from 日志.advanced_logger import AdvancedLogger
logger = AdvancedLogger.get_logger(__name__)

music_dir = {
    "OST1": "HEAVEN_BURNS_RED_Original_Sound_Track_Vol1",
    "OST2": "HEAVEN_BURNS_RED_Original_Sound_Track_Vol2",
    "Love_Song_from_the_Water": "Love_Song_from_the_Water",
    "麻枝准_やなぎなぎ": "麻枝准_やなぎなぎ",
    "麻枝准_rionos": "麻枝准_rionos",
    "佐々木恵梨": "佐々木恵梨",
    "She_is_Legend": "She_is_Legend",
    "Stargazer": "Stargazer",
    "Summer_Pockets_Original_Sound_Track": "Summer_Pockets_Original_Sound_Track",
    "Summer_Pockets_REFLECTION_BLUE_Original_SoundTrack": "Summer_Pockets_REFLECTION_BLUE_Original_SoundTrack",
    "CLANNAD_Original_Sound_Track": "CLANNAD_Original_Sound_Track",
    "Rewrite_Original_Sound_Track": "Rewrite_Original_Sound_Track",
    "Inst_Test_Examples": "Inst_Test_Examples"
}


class ClickableSlider(QSlider):
    """支持点击轨道直接跳转到点击位置的滑块，同时保留拖动功能"""

    def _handle_rect(self):
        """获取滑块手柄的矩形区域"""
        option = QStyleOptionSlider()
        self.initStyleOption(option)
        return self.style().subControlRect(
            QStyle.CC_Slider, option, QStyle.SC_SliderHandle, self
        )

    def mousePressEvent(self, event):
        handle_rect = self._handle_rect()
        
        # 如果点击的是手柄本身，走默认拖动逻辑
        if handle_rect.contains(event.pos()):
            super().mousePressEvent(event)
            return

        # 点击轨道时，阻止 valueChanged 触发 on_progress_value_changed 中的 seeking=True
        if self.orientation() == Qt.Horizontal:
            slider_min = handle_rect.width() // 2
            slider_max = self.width() - handle_rect.width() // 2
            pos = max(slider_min, min(event.pos().x(), slider_max))
            ratio = (pos - slider_min) / max(1, slider_max - slider_min)
        else:
            slider_min = handle_rect.height() // 2
            slider_max = self.height() - handle_rect.height() // 2
            pos = max(slider_min, min(event.pos().y(), slider_max))
            ratio = 1 - (pos - slider_min) / max(1, slider_max - slider_min)

        value = int(self.minimum() + ratio * (self.maximum() - self.minimum()))

        # 先 blockSignals 防止触发 on_progress_value_changed 中的 seeking=True
        self.blockSignals(True)
        self.setValue(value)
        self.blockSignals(False)

        # 手动触发一次 sliderReleased，让 _seek_from_slider 统一处理跳转
        self.sliderReleased.emit()


class FLACPlayerApp:
    def __init__(self, parent_frame, row, column):
        self.frame = QFrame(parent_frame)
        self.frame.setLayout(QVBoxLayout())
        self.frame.layout().setContentsMargins(10, 10, 10, 10)
        self.frame.layout().setSpacing(5)

        if hasattr(parent_frame, 'grid_layout'):
            parent_frame.grid_layout.addWidget(self.frame, row, column)
        elif parent_frame.layout() is not None:
            parent_frame.layout().addWidget(self.frame)

        pygame.mixer.init()

        self.current_file = None
        self.paused = False
        self.playing = False
        self.volume = 0.5
        self.duration = 0
        self.seeking = False
        self.current_position = 0
        self.seek_position = 0
        self.position_selected = False

        self.loop_enabled = False

        self.create_widgets()

        self.progress_timer = QTimer(self.frame)
        self.progress_timer.timeout.connect(self._update_progress)
        self.running = True
        self.volume_thread = None

    def create_widgets(self):
        file_frame = QFrame(self.frame)
        file_frame.setLayout(QHBoxLayout())
        self.file_label = QLabel("未选择文件")
        file_frame.layout().addWidget(self.file_label)
        self.frame.layout().addWidget(file_frame)

        self.progress_slider = ClickableSlider(Qt.Horizontal)
        self.progress_slider.setRange(0, 1000)
        self.progress_slider.setValue(0)
        self.progress_slider.setPageStep(50)
        self.progress_slider.setSingleStep(10)
        self.progress_slider.sliderPressed.connect(lambda: self.on_progress_click(None))
        self.progress_slider.sliderMoved.connect(self.on_progress_drag)
        self.progress_slider.sliderReleased.connect(lambda: self.on_progress_release(None))
        self.progress_slider.valueChanged.connect(self.on_progress_value_changed)
        self.frame.layout().addWidget(self.progress_slider)

        self.time_label = QLabel("00:00 / 00:00")
        self.time_label.setAlignment(Qt.AlignCenter)
        self.frame.layout().addWidget(self.time_label)

        control_frame = QFrame(self.frame)
        control_frame.setLayout(QHBoxLayout())
        self.frame.layout().addWidget(control_frame)

        self.play_btn = QPushButton("播放▶")
        self.play_btn.setEnabled(False)
        self.play_btn.clicked.connect(self.play)
        control_frame.layout().addWidget(self.play_btn)

        self.pause_btn = QPushButton("暂停⏸︎")
        self.pause_btn.setEnabled(False)
        self.pause_btn.clicked.connect(self.pause)
        control_frame.layout().addWidget(self.pause_btn)

        self.stop_btn = QPushButton("停止⏹︎")
        self.stop_btn.setEnabled(False)
        self.stop_btn.clicked.connect(self.stop)
        control_frame.layout().addWidget(self.stop_btn)

        self.loop_btn = QPushButton("循环◻")
        self.loop_btn.setEnabled(False)
        self.loop_btn.clicked.connect(self.toggle_loop)
        control_frame.layout().addWidget(self.loop_btn)

        volume_frame = QFrame(self.frame)
        volume_frame.setLayout(QHBoxLayout())
        volume_label = QLabel("音量🔉")
        volume_frame.layout().addWidget(volume_label)
        self.volume_slider = QSlider(Qt.Horizontal)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(50)
        self.volume_slider.valueChanged.connect(self.set_volume)
        volume_frame.layout().addWidget(self.volume_slider)
        self.frame.layout().addWidget(volume_frame)

        self.frame.layout().addStretch()

    def select_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self.frame,
            "选择音频文件",
            "",
            "flac文件 (*.flac);;mp3文件 (*.mp3);;所有文件 (*.*)"
        )
        if file_path:
            self.load_file(file_path)

    def load_file(self, file_path):
        try:
            pygame.mixer.music.load(file_path)
            self.current_file = file_path
            self.file_label.setText(os.path.basename(file_path))

            sound = pygame.mixer.Sound(file_path)
            self.duration = sound.get_length()
            self.current_position = 0
            self.seek_position = 0
            self.position_selected = False

            self.update_progress_display(0)
            self.update_time_display(0, self.duration)
            self.play_btn.setEnabled(True)
            self.loop_btn.setEnabled(True)

        except Exception as e:
            logger.error(f"无法加载文件: {e}")
            QMessageBox.critical(self.frame, "错误", f"无法加载文件: {e}")

    def toggle_loop(self):
        self.loop_enabled = not self.loop_enabled
        self.loop_btn.setText("循环🔁" if self.loop_enabled else "循环◻")

    def play(self):
        if self.current_file:
            self._start_volume_fade("up")

            if self.loop_enabled and self.current_position >= self.duration:
                self.current_position = 0
                self.seek_time = time.time()

            if self.paused:
                pygame.mixer.music.unpause()
                self.paused = False
                self.running = True
                self.seek_time = time.time()
                if self.position_selected:
                    pygame.mixer.music.set_pos(self.seek_position)
                    self.current_position = self.seek_position
                    self.position_selected = False
                self.sync_progress_and_time()
                self.progress_timer.start(100)
            else:
                pygame.mixer.music.stop()
                start_position = self.seek_position if self.position_selected else 0
                pygame.mixer.music.play()

                if self.position_selected:
                    pygame.mixer.music.set_pos(start_position)
                    self.current_position = start_position
                else:
                    self.current_position = 0

                self.seek_time = time.time()
                self.position_selected = False
                self.seeking = False

                self.playing = True
                self.running = True
                self.progress_timer.start(100)

            self.play_btn.setEnabled(False)
            self.pause_btn.setEnabled(True)
            self.stop_btn.setEnabled(True)

    def sync_progress_and_time(self):
        current_pos = self.get_current_pos()
        progress_percent = (current_pos / self.duration) * 100 if self.duration else 0
        self.update_progress_display(progress_percent)
        self.update_time_display(current_pos, self.duration)

    def pause(self):
        if self.playing and not self.paused:
            self._start_volume_fade("down")
            pygame.mixer.music.pause()
            self.paused = True
            self.current_position = self.get_current_pos()
            self.seek_time = time.time()
            self.progress_timer.stop()
            self.play_btn.setEnabled(True)
            self.pause_btn.setEnabled(False)

    def stop(self):
        self.running = False
        self.progress_timer.stop()
        self._start_volume_fade("down")
        pygame.mixer.music.stop()
        self.playing = False
        self.paused = False
        self.current_position = 0
        self.seek_position = 0
        self.position_selected = False

        self.update_progress_display(0)
        self.update_time_display(0, self.duration)
        self.play_btn.setEnabled(True)
        self.pause_btn.setEnabled(False)
        self.stop_btn.setEnabled(False)

    def set_volume(self, val):
        self.volume = val / 100
        pygame.mixer.music.set_volume(self.volume)

    def get_current_pos(self):
        if not self.playing or self.seeking:
            return self.current_position
        if self.loop_enabled and self.current_position >= self.duration:
            self.current_position = 0
            self.seek_time = time.time()
        elapsed_since_seek = time.time() - self.seek_time
        return min(self.current_position + elapsed_since_seek, self.duration)

    def _update_progress(self):
        if not self.playing or not self.running or self.paused or self.seeking:
            return

        current_pos = self.get_current_pos()

        if self.duration > 0 and current_pos >= self.duration - 0.5:
            self.progress_timer.stop()
            if self.loop_enabled:
                self.stop()
                self.play()
            else:
                self.stop()
            return

        progress_percent = (current_pos / self.duration) * 100 if self.duration else 0
        progress_percent = max(0, min(100, progress_percent))

        self.update_progress_display(progress_percent)
        self.update_time_display(current_pos, self.duration)

    def update_progress_display(self, percent):
        self.progress_slider.blockSignals(True)
        self.progress_slider.setValue(int(percent * 10))
        self.progress_slider.blockSignals(False)

    def update_time_display(self, current, total):
        current_m, current_s = divmod(int(current), 60)
        total_m, total_s = divmod(int(total), 60)
        self.time_label.setText(
            f"{current_m:02d}:{current_s:02d} / {total_m:02d}:{total_s:02d}"
        )

    def _seek_from_slider(self):
        """根据当前滑块值计算并跳转到目标位置"""
        if self.duration <= 0 or not self.current_file:
            return

        value = self.progress_slider.value()
        seek_percent = max(0, min(100, value / 1000.0 * 100))
        self.seek_position = (seek_percent / 100) * self.duration
        self.position_selected = True

        if self.playing or self.paused:
            try:
                # 先记录目标位置和时间戳，再操作 pygame
                self.current_position = self.seek_position
                self.seek_time = time.time()
                
                # stop + play + set_pos 的顺序优化
                pygame.mixer.music.stop()
                pygame.mixer.music.play()
                # 给 mixer 一个微小的缓冲时间再 set_pos
                # 注意：这里不能用 time.sleep，改用 QTimer.singleShot
                from PyQt5.QtCore import QTimer
                QTimer.singleShot(50, lambda: self._apply_seek_position())
                
            except Exception as e:
                logger.error(f"跳转失败: {e}")
                QMessageBox.critical(self.frame, "错误", f"无法跳转到指定位置: {e}")
                return

            self.playing = True
            self.paused = False
            self.running = True
            self.seeking = False  # 立即重置 seeking
            self.progress_timer.start(100)
            self.play_btn.setEnabled(False)
            self.pause_btn.setEnabled(True)
            self.stop_btn.setEnabled(True)

        self.update_progress_display(seek_percent)
        self.update_time_display(self.seek_position, self.duration)

    def _apply_seek_position(self):
        """延迟应用 seek 位置，避免 pygame 时序问题"""
        try:
            pygame.mixer.music.set_pos(self.seek_position)
        except Exception as e:
            logger.warning(f"延迟 set_pos 失败: {e}")

    def on_progress_click(self, event):
        if self.duration > 0 and self.current_file:
            self.seeking = True

    def on_progress_value_changed(self, value):
        if self.duration > 0 and self.current_file:
            self.seeking = True
            seek_percent = value / 1000.0 * 100
            seek_percent = max(0, min(100, seek_percent))
            self.seek_position = (seek_percent / 100) * self.duration
            self.position_selected = True
            self.update_time_display(self.seek_position, self.duration)

    def on_progress_drag(self, event):
        if self.duration > 0 and self.current_file:
            value = self.progress_slider.value()
            seek_percent = value / 1000.0 * 100
            seek_percent = max(0, min(100, seek_percent))
            self.seek_position = (seek_percent / 100) * self.duration
            self.position_selected = True
            self.update_time_display(self.seek_position, self.duration)

    def on_progress_release(self, event):
        if self.duration > 0 and self.current_file:
            self._seek_from_slider()
            self.seeking = False

    def on_close(self):
        self.running = False
        self.progress_timer.stop()
        pygame.mixer.music.stop()
        pygame.mixer.quit()
        self.frame.deleteLater()

    def on_clean(self):
        self.running = False
        pygame.mixer.music.stop()
        pygame.mixer.quit()


    def _start_volume_fade(self, direction: str):
        """direction: 'up' or 'down'"""
        target = self.volume if direction == "up" else 0.0
        current = 0.0 if direction == "up" else self.volume
        step = 0.02  # 每步增量
        interval = 50  # ms
        
        fade_timer = QTimer(self.frame)
        fade_timer.setInterval(interval)
        
        def _fade_step():
            nonlocal current
            if direction == "up":
                current = min(current + step, target)
            else:
                current = max(current - step, target)
            
            pygame.mixer.music.set_volume(current)
            
            if abs(current - target) < step:
                pygame.mixer.music.set_volume(target)
                fade_timer.stop()
                fade_timer.deleteLater()
        
        fade_timer.timeout.connect(_fade_step)
        fade_timer.start()
