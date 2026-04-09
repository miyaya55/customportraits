"""ビュー画面。背景・位置ガイド・キャラクターを合成表示する。"""

from pathlib import Path

from PIL import Image
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QImage, QMouseEvent, QPixmap
from PyQt5.QtWidgets import QCheckBox, QHBoxLayout, QLabel, QSlider, QVBoxLayout, QWidget

from src.utils.constants import VIEWER_WINDOW_HEIGHT, VIEWER_WINDOW_WIDTH


DEFAULT_GUIDE_OPACITY_PERCENT = 42
GUIDE_BACKGROUND_THRESHOLD = 8


class ViewerCanvas(QLabel):
    """ビューア用キャンバス。"""

    character_position_changed = pyqtSignal(int, int)

    def __init__(self):
        super().__init__()
        self.background_image = None
        self.guide_image = None
        self.guide_visible = False
        self.guide_opacity = DEFAULT_GUIDE_OPACITY_PERCENT / 100
        self.character_image = None
        self.character_position = (0, 0)
        self.dragging = False
        self.drag_start = None
        self.setStyleSheet("border: 1px solid #cccccc; background-color: #ffffff;")
        self.set_canvas_size(VIEWER_WINDOW_WIDTH, VIEWER_WINDOW_HEIGHT)

    def set_canvas_size(self, width: int, height: int):
        self.setMinimumSize(width, height)
        self.setMaximumSize(width, height)
        self.resize(width, height)

    def _resolve_canvas_size(self):
        if self.background_image:
            return self.background_image.width, self.background_image.height
        if self.guide_image:
            return self.guide_image.width, self.guide_image.height
        return VIEWER_WINDOW_WIDTH, VIEWER_WINDOW_HEIGHT

    def get_canvas_size(self):
        return self._resolve_canvas_size()

    def _refresh_canvas_size(self):
        width, height = self._resolve_canvas_size()
        self.set_canvas_size(width, height)
        if self.character_image:
            self.character_position = self._clamp_character_position(*self.character_position)

    def set_background(self, image_path: str = None):
        if image_path and Path(image_path).exists():
            self.background_image = Image.open(image_path).convert("RGBA")
        else:
            self.background_image = None
        self._refresh_canvas_size()
        self.update_display()

    def set_guide_image(self, image_path: str = None):
        if image_path and Path(image_path).exists():
            self.guide_image = Image.open(image_path).convert("RGBA")
        else:
            self.guide_image = None
        self._refresh_canvas_size()
        self.update_display()

    def set_guide_visible(self, visible: bool):
        self.guide_visible = bool(visible)
        self.update_display()

    def set_guide_opacity_percent(self, percent: int):
        self.guide_opacity = max(0.05, min(percent / 100, 1.0))
        self.update_display()

    def has_guide_image(self):
        return self.guide_image is not None

    def _default_character_position(self):
        canvas_w, canvas_h = self.get_canvas_size()
        char_w = self.character_image.width
        char_h = self.character_image.height
        char_x = max(0, (canvas_w - char_w) // 2)
        char_y = max(0, canvas_h - char_h)
        return char_x, char_y

    def _clamp_character_position(self, x: int, y: int):
        if not self.character_image:
            return 0, 0

        canvas_w, canvas_h = self.get_canvas_size()
        min_x = -self.character_image.width + 1
        min_y = -self.character_image.height + 1
        max_x = canvas_w - 1
        max_y = canvas_h - 1
        return min(max(min_x, x), max_x), min(max(min_y, y), max_y)

    def set_character(self, image_path: str = None, preserve_position: bool = False):
        if image_path and Path(image_path).exists():
            character_image = Image.open(image_path).convert("RGBA")
            self.set_character_image(character_image, preserve_position=preserve_position)
        else:
            self.clear_character()

    def set_character_image(self, character_image, preserve_position: bool = False):
        if character_image:
            self.character_image = character_image.copy().convert("RGBA")
            if preserve_position:
                self.character_position = self._clamp_character_position(*self.character_position)
            else:
                self.character_position = self._default_character_position()
        else:
            self.character_image = None
            self.character_position = (0, 0)
        self.update_display()

    def clear_character(self):
        self.character_image = None
        self.character_position = (0, 0)
        self.update_display()

    def set_character_position(self, x: int, y: int):
        self.character_position = self._clamp_character_position(x, y)
        self.update_display()

    def get_character_position(self):
        return self.character_position

    def _build_guide_layer(self, canvas_size):
        if not self.guide_image or not self.guide_visible:
            return None

        layer = Image.new("RGBA", canvas_size, (0, 0, 0, 0))
        guide_image = self.guide_image.copy()
        alpha = guide_image.getchannel("A")
        rgb_image = guide_image.convert("RGB")
        visibility_mask = rgb_image.convert("L").point(
            lambda value: 0 if value <= GUIDE_BACKGROUND_THRESHOLD else 255
        )
        alpha = Image.eval(
            alpha,
            lambda value: int(value * self.guide_opacity),
        )
        alpha = Image.composite(alpha, Image.new("L", guide_image.size, 0), visibility_mask)
        guide_image.putalpha(alpha)
        layer.paste(guide_image, (0, 0), guide_image)
        return layer

    def get_display_image(self, include_guide: bool = True):
        canvas_w, canvas_h = self.get_canvas_size()
        canvas_size = (canvas_w, canvas_h)

        if self.background_image:
            display_image = self.background_image.copy()
        else:
            display_image = Image.new("RGBA", canvas_size, (255, 255, 255, 255))

        if include_guide:
            guide_layer = self._build_guide_layer(canvas_size)
            if guide_layer:
                display_image.alpha_composite(guide_layer)

        if self.character_image:
            display_image.paste(self.character_image, self.character_position, self.character_image)

        return display_image

    def update_display(self):
        self.set_pixmap_from_pil(self.get_display_image(include_guide=True))

    def set_pixmap_from_pil(self, pil_image: Image.Image):
        if pil_image.mode == "RGBA":
            data = pil_image.tobytes("raw", "RGBA")
            qimage = QImage(data, pil_image.width, pil_image.height, QImage.Format_RGBA8888)
        else:
            data = pil_image.tobytes("raw", "RGB")
            qimage = QImage(data, pil_image.width, pil_image.height, QImage.Format_RGB888)

        pixmap = QPixmap.fromImage(qimage)
        self.setPixmap(pixmap)
        self.resize(pixmap.width(), pixmap.height())

    def _is_point_on_character(self, x: int, y: int):
        if not self.character_image:
            return False

        char_x, char_y = self.character_position
        char_w, char_h = self.character_image.size
        return char_x <= x < char_x + char_w and char_y <= y < char_y + char_h

    def mousePressEvent(self, event: QMouseEvent):
        if self.character_image and self._is_point_on_character(event.x(), event.y()):
            self.dragging = True
            self.drag_start = (event.x(), event.y())
            return

        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent):
        if self.dragging and self.drag_start:
            dx = event.x() - self.drag_start[0]
            dy = event.y() - self.drag_start[1]
            new_x = self.character_position[0] + dx
            new_y = self.character_position[1] + dy
            self.set_character_position(new_x, new_y)
            self.drag_start = (event.x(), event.y())
            self.character_position_changed.emit(*self.character_position)
            return

        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent):
        self.dragging = False
        self.drag_start = None
        super().mouseReleaseEvent(event)


class ViewerWindow(QWidget):
    """ビュー用ウィンドウ。"""

    def __init__(self):
        super().__init__()
        self.canvas = ViewerCanvas()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        self.guide_toggle = QCheckBox("位置ガイドを表示")
        self.guide_toggle.setEnabled(False)
        self.guide_toggle.toggled.connect(self.canvas.set_guide_visible)
        layout.addWidget(self.guide_toggle)

        opacity_layout = QHBoxLayout()
        self.guide_opacity_label = QLabel("ガイド濃度")
        opacity_layout.addWidget(self.guide_opacity_label)
        self.guide_opacity_slider = QSlider(Qt.Horizontal)
        self.guide_opacity_slider.setMinimum(5)
        self.guide_opacity_slider.setMaximum(100)
        self.guide_opacity_slider.setValue(DEFAULT_GUIDE_OPACITY_PERCENT)
        self.guide_opacity_slider.setEnabled(False)
        self.guide_opacity_slider.valueChanged.connect(self.on_guide_opacity_changed)
        opacity_layout.addWidget(self.guide_opacity_slider, 1)
        self.guide_opacity_value_label = QLabel(f"{DEFAULT_GUIDE_OPACITY_PERCENT}%")
        opacity_layout.addWidget(self.guide_opacity_value_label)
        layout.addLayout(opacity_layout)
        layout.addWidget(self.canvas)

        self.setLayout(layout)
        self.setWindowTitle("Custom Portrait - ビュー")
        self.setGeometry(1300, 100, VIEWER_WINDOW_WIDTH + 20, VIEWER_WINDOW_HEIGHT + 50)

    def adjust_to_canvas(self):
        layout = self.layout()
        margins = layout.contentsMargins()
        width = max(
            self.canvas.width(),
            self.guide_toggle.sizeHint().width(),
            self.guide_opacity_label.sizeHint().width() + self.guide_opacity_slider.sizeHint().width(),
        ) + margins.left() + margins.right()
        controls_height = self.guide_toggle.sizeHint().height() + self.guide_opacity_slider.sizeHint().height()
        height = self.canvas.height() + margins.top() + margins.bottom() + controls_height
        self.setFixedSize(width, height)

    def on_guide_opacity_changed(self, value: int):
        self.guide_opacity_value_label.setText(f"{value}%")
        self.canvas.set_guide_opacity_percent(value)

    def set_background(self, image_path: str = None):
        self.canvas.set_background(image_path)
        self.adjust_to_canvas()

    def set_guide_image(self, image_path: str = None):
        was_enabled = self.guide_toggle.isEnabled()
        self.canvas.set_guide_image(image_path)
        has_guide = self.canvas.has_guide_image()

        self.guide_toggle.blockSignals(True)
        self.guide_toggle.setEnabled(has_guide)
        self.guide_opacity_slider.setEnabled(has_guide)
        if has_guide and not was_enabled:
            self.guide_toggle.setChecked(True)
        elif not has_guide:
            self.guide_toggle.setChecked(False)
        self.guide_toggle.blockSignals(False)

        self.canvas.set_guide_visible(self.guide_toggle.isChecked())
        self.adjust_to_canvas()

    def set_character(self, image_path: str = None, preserve_position: bool = False):
        self.canvas.set_character(image_path, preserve_position=preserve_position)

    def set_character_image(self, character_image, preserve_position: bool = False):
        self.canvas.set_character_image(character_image, preserve_position=preserve_position)

    def clear_character(self):
        self.canvas.clear_character()

    def set_character_position(self, x: int, y: int):
        self.canvas.set_character_position(x, y)

    def get_character_position(self):
        return self.canvas.get_character_position()

    def get_display_image(self, include_guide: bool = False):
        return self.canvas.get_display_image(include_guide=include_guide).copy()
