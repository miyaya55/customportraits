"""ビュー用画面 - リアルタイムプレビュー"""

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QImage, QPixmap, QMouseEvent
from PIL import Image
from pathlib import Path

from src.utils.constants import VIEWER_WINDOW_WIDTH, VIEWER_WINDOW_HEIGHT


class ViewerCanvas(QLabel):
    """ビューア用キャンバス"""

    character_position_changed = pyqtSignal(int, int)

    def __init__(self):
        super().__init__()
        self.background_image = None
        self.character_image = None
        self.character_position = (0, 0)
        self.dragging = False
        self.drag_start = None
        self.setStyleSheet("border: 1px solid #cccccc; background-color: #ffffff;")
        self.set_canvas_size(VIEWER_WINDOW_WIDTH, VIEWER_WINDOW_HEIGHT)

    def set_canvas_size(self, width: int, height: int):
        """キャンバスの表示サイズを更新する"""
        self.setMinimumSize(width, height)
        self.setMaximumSize(width, height)
        self.resize(width, height)

    def get_canvas_size(self):
        """現在のキャンバスサイズを返す"""
        if self.background_image:
            return self.background_image.width, self.background_image.height
        return VIEWER_WINDOW_WIDTH, VIEWER_WINDOW_HEIGHT

    def set_background(self, image_path: str = None):
        """背景を設定する"""
        if image_path and Path(image_path).exists():
            self.background_image = Image.open(image_path).convert("RGBA")
            self.set_canvas_size(self.background_image.width, self.background_image.height)
        else:
            self.background_image = None
            self.set_canvas_size(VIEWER_WINDOW_WIDTH, VIEWER_WINDOW_HEIGHT)

        if self.character_image:
            self.character_position = self._clamp_character_position(*self.character_position)
        self.update_display()

    def _default_character_position(self):
        """キャラクターの初期表示位置を返す"""
        canvas_w, canvas_h = self.get_canvas_size()
        char_w = self.character_image.width
        char_h = self.character_image.height
        char_x = max(0, (canvas_w - char_w) // 2)
        char_y = max(0, canvas_h - char_h)
        return char_x, char_y

    def _clamp_character_position(self, x: int, y: int):
        """キャラクターの一部が画面外に出る配置を許可する"""
        if not self.character_image:
            return 0, 0

        canvas_w, canvas_h = self.get_canvas_size()
        min_x = -self.character_image.width + 1
        min_y = -self.character_image.height + 1
        max_x = canvas_w - 1
        max_y = canvas_h - 1
        return min(max(min_x, x), max_x), min(max(min_y, y), max_y)

    def set_character(self, image_path: str = None, preserve_position: bool = False):
        """画像パスからキャラクターを設定する"""
        if image_path and Path(image_path).exists():
            character_image = Image.open(image_path).convert("RGBA")
            self.set_character_image(character_image, preserve_position=preserve_position)
        else:
            self.clear_character()

    def set_character_image(self, character_image, preserve_position: bool = False):
        """PIL Image をキャラクターとして設定する"""
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
        """キャラクター表示をクリアする"""
        self.character_image = None
        self.character_position = (0, 0)
        self.update_display()

    def set_character_position(self, x: int, y: int):
        """キャラクターの位置を設定する"""
        self.character_position = self._clamp_character_position(x, y)
        self.update_display()

    def get_character_position(self):
        """キャラクターの位置を取得する"""
        return self.character_position

    def get_display_image(self):
        """表示中の合成画像を返す"""
        canvas_w, canvas_h = self.get_canvas_size()
        if self.background_image:
            display_image = self.background_image.copy()
        else:
            display_image = Image.new("RGBA", (canvas_w, canvas_h), (255, 255, 255, 255))

        if self.character_image:
            display_image.paste(self.character_image, self.character_position, self.character_image)

        return display_image

    def update_display(self):
        """表示画像を更新する"""
        self.set_pixmap_from_pil(self.get_display_image())

    def set_pixmap_from_pil(self, pil_image: Image.Image):
        """PIL Image から QPixmap を作って表示する"""
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
        """クリック位置がキャラクター上かを判定する"""
        if not self.character_image:
            return False

        char_x, char_y = self.character_position
        char_w, char_h = self.character_image.size
        return char_x <= x < char_x + char_w and char_y <= y < char_y + char_h

    def mousePressEvent(self, event: QMouseEvent):
        """キャラクター上のドラッグを開始する"""
        if self.character_image and self._is_point_on_character(event.x(), event.y()):
            self.dragging = True
            self.drag_start = (event.x(), event.y())
            return

        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent):
        """ドラッグ中ならキャラクター位置を更新する"""
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
        """ドラッグ状態を解除する"""
        self.dragging = False
        self.drag_start = None
        super().mouseReleaseEvent(event)


class ViewerWindow(QWidget):
    """ビュー用ウィンドウ"""

    def __init__(self):
        super().__init__()
        self.canvas = ViewerCanvas()
        self.init_ui()

    def init_ui(self):
        """UI を初期化"""
        layout = QVBoxLayout()
        layout.addWidget(self.canvas)
        self.setLayout(layout)
        self.setWindowTitle("Custom Portrait - ビュー")
        self.setGeometry(1300, 100, VIEWER_WINDOW_WIDTH + 20, VIEWER_WINDOW_HEIGHT + 50)

    def adjust_to_canvas(self):
        """背景サイズに合わせてウィンドウを調整する"""
        layout = self.layout()
        margins = layout.contentsMargins()
        width = self.canvas.width() + margins.left() + margins.right()
        height = self.canvas.height() + margins.top() + margins.bottom()
        self.setFixedSize(width, height)

    def set_background(self, image_path: str = None):
        """背景を設定する"""
        self.canvas.set_background(image_path)
        self.adjust_to_canvas()

    def set_character(self, image_path: str = None, preserve_position: bool = False):
        """画像パスからキャラクターを設定する"""
        self.canvas.set_character(image_path, preserve_position=preserve_position)

    def set_character_image(self, character_image, preserve_position: bool = False):
        """PIL Image をキャラクターとして設定する"""
        self.canvas.set_character_image(character_image, preserve_position=preserve_position)

    def clear_character(self):
        """キャラクター表示をクリアする"""
        self.canvas.clear_character()

    def set_character_position(self, x: int, y: int):
        """キャラクター位置を設定する"""
        self.canvas.set_character_position(x, y)

    def get_character_position(self):
        """キャラクター位置を取得する"""
        return self.canvas.get_character_position()

    def get_display_image(self):
        """表示中の画像を取得する"""
        return self.canvas.get_display_image().copy()
