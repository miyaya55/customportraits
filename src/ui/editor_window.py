"""キャラクター編集画面 - 画像の読み込みと編集"""

from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QCheckBox,
    QComboBox,
    QGroupBox,
    QPushButton,
    QLabel,
    QSlider,
    QSpinBox,
    QLineEdit,
    QFileDialog,
    QMessageBox,
)
from PyQt5.QtCore import Qt, pyqtSignal, QPoint, QRect, QTimer
from PyQt5.QtGui import QImage, QPixmap, QMouseEvent, QPainter, QColor, QPen
from PIL import Image, ImageDraw

from src.core.image_processor import ImageProcessor
from src.utils.constants import EDITOR_WINDOW_WIDTH, EDITOR_WINDOW_HEIGHT
from src.ui.styles import STYLESHEET


class CharacterCanvas(QLabel):
    """キャラクター編集用キャンバス"""

    crop_region_changed = pyqtSignal()
    image_dropped = pyqtSignal(str)
    color_picked = pyqtSignal(tuple)

    def __init__(self):
        super().__init__()
        self.image = None
        self.placeholder_text = "ここに画像をドラッグしてください\nまたは右側の「画像を選択」をクリック"
        self._checkerboard_cache = {}
        self.crop_rect = None
        self.is_cropping = False
        self.crop_start = None
        self.picking_color = False
        self.selected_color = None
        self.setMinimumSize(500, 500)
        self.setStyleSheet("border: 1px solid #cccccc; background-color: #ffffff;")
        self.setAlignment(Qt.AlignCenter)
        self.setWordWrap(True)
        self.setAcceptDrops(True)
        self.show_placeholder()

    def dragEnterEvent(self, event):
        """ドラッグ中のファイルを受け付ける"""
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event):
        """ドロップされた画像を読み込む"""
        if event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            if urls:
                self.image_dropped.emit(urls[0].toLocalFile())
            event.accept()
        else:
            event.ignore()

    def set_image(self, pil_image):
        """キャンバスに表示する画像を設定する"""
        self.image = pil_image
        self.update_display()

    def clear_interaction_state(self):
        """編集中の選択状態をクリアする"""
        self.crop_rect = None
        self.crop_start = None
        self.selected_color = None

    def update_display(self):
        """ディスプレイを更新"""
        if self.image:
            self.set_pixmap_from_pil(self.image)
        else:
            self.show_placeholder()

    def show_placeholder(self):
        """画像未読み込み時の案内文を表示する"""
        self.clear()
        self.setText(self.placeholder_text)

    def resizeEvent(self, event):
        """リサイズ時に表示画像も更新する"""
        super().resizeEvent(event)
        self.update_display()

    def set_pixmap_from_pil(self, pil_image: Image.Image, draw_crop=True):
        """PIL Image から QLabel 表示用の QPixmap を作る"""
        if pil_image.mode == "RGBA":
            preview_image = self._build_checkerboard(pil_image.size)
            preview_image.alpha_composite(pil_image)
            data = preview_image.tobytes("raw", "RGBA")
            qimage = QImage(
                data,
                preview_image.width,
                preview_image.height,
                QImage.Format_RGBA8888,
            )
        else:
            data = pil_image.tobytes("raw", "RGB")
            qimage = QImage(data, pil_image.width, pil_image.height, QImage.Format_RGB888)

        pixmap = QPixmap.fromImage(qimage)
        scaled_pixmap = pixmap.scaled(
            self.width(),
            self.height(),
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation,
        )

        if draw_crop and self.crop_rect:
            crop_rect = self.crop_rect.translated(-self._pixmap_rect().x(), -self._pixmap_rect().y())
            painter = QPainter(scaled_pixmap)
            painter.setPen(QPen(QColor(0, 255, 0), 2, Qt.DashLine))
            painter.drawRect(crop_rect)
            painter.end()

        self.setPixmap(scaled_pixmap)

    def _build_checkerboard(self, size, cell_size=16):
        """透過確認用の市松背景を生成する。"""
        cache_key = (size, cell_size)
        cached = self._checkerboard_cache.get(cache_key)
        if cached is not None:
            return cached.copy()

        width, height = size
        board = Image.new("RGBA", size, (0, 0, 0, 255))
        draw = ImageDraw.Draw(board)
        light = (238, 238, 238, 255)
        dark = (210, 210, 210, 255)

        for y in range(0, height, cell_size):
            for x in range(0, width, cell_size):
                color = light if ((x // cell_size) + (y // cell_size)) % 2 == 0 else dark
                draw.rectangle(
                    (
                        x,
                        y,
                        min(x + cell_size - 1, width - 1),
                        min(y + cell_size - 1, height - 1),
                    ),
                    fill=color,
                )

        self._checkerboard_cache[cache_key] = board
        return board.copy()

    def _pixmap_rect(self):
        """ラベル内で実際に画像が表示されている矩形を返す"""
        pixmap = self.pixmap()
        if not pixmap:
            return QRect()

        x = (self.width() - pixmap.width()) // 2
        y = (self.height() - pixmap.height()) // 2
        return QRect(x, y, pixmap.width(), pixmap.height())

    def _clamp_to_pixmap(self, pos: QPoint):
        """画像表示領域内に座標を丸める"""
        rect = self._pixmap_rect()
        if rect.isNull():
            return None

        x = min(max(pos.x(), rect.left()), rect.right())
        y = min(max(pos.y(), rect.top()), rect.bottom())
        return QPoint(x, y)

    def _widget_pos_to_image_pos(self, pos: QPoint):
        """ウィジェット座標を画像座標へ変換する"""
        if not self.image:
            return None

        rect = self._pixmap_rect()
        if rect.isNull():
            return None

        clamped = self._clamp_to_pixmap(pos)
        if clamped is None:
            return None

        rel_x = clamped.x() - rect.x()
        rel_y = clamped.y() - rect.y()

        img_x = int(rel_x * self.image.width / max(1, rect.width()))
        img_y = int(rel_y * self.image.height / max(1, rect.height()))

        img_x = min(max(img_x, 0), self.image.width - 1)
        img_y = min(max(img_y, 0), self.image.height - 1)
        return img_x, img_y

    def mousePressEvent(self, event: QMouseEvent):
        """マウスボタン押下時の処理"""
        if self.is_cropping and self.image:
            point = self._clamp_to_pixmap(event.pos())
            if point is not None:
                self.crop_start = point
                self.crop_rect = QRect(point, point)
                self.update_display()
            return

        if self.picking_color and self.image:
            image_pos = self._widget_pos_to_image_pos(event.pos())
            if image_pos is None:
                return

            pixel = self.image.getpixel(image_pos)
            self.selected_color = pixel[:3]
            self.color_picked.emit(self.selected_color)
            return

        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent):
        """マウス移動時の処理"""
        if self.is_cropping and self.crop_start and self.image:
            current_point = self._clamp_to_pixmap(event.pos())
            if current_point is None:
                return

            self.crop_rect = QRect(self.crop_start, current_point).normalized()
            self.update_display()
            return

        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent):
        """マウスボタン解放時の処理"""
        if self.is_cropping and self.crop_rect:
            self.crop_region_changed.emit()
            return

        super().mouseReleaseEvent(event)

    def get_crop_region(self):
        """切り抜き領域を現在の表示画像座標で返す"""
        if not self.crop_rect or not self.image:
            return None

        rect = self._pixmap_rect()
        if rect.isNull():
            return None

        left = max(0, self.crop_rect.left() - rect.x())
        top = max(0, self.crop_rect.top() - rect.y())
        right = min(rect.width(), self.crop_rect.right() - rect.x() + 1)
        bottom = min(rect.height(), self.crop_rect.bottom() - rect.y() + 1)

        if right <= left or bottom <= top:
            return None

        scale_x = self.image.width / max(1, rect.width())
        scale_y = self.image.height / max(1, rect.height())
        return (
            int(left * scale_x),
            int(top * scale_y),
            int(right * scale_x),
            int(bottom * scale_y),
        )

    def start_cropping(self):
        """切り抜きモードを開始する"""
        self.picking_color = False
        self.is_cropping = True
        self.setCursor(Qt.CrossCursor)

    def end_cropping(self):
        """切り抜きモードを終了する"""
        self.is_cropping = False
        self.crop_start = None
        self.setCursor(Qt.ArrowCursor)

    def start_color_picking(self):
        """色選択モードを開始する"""
        self.is_cropping = False
        self.crop_start = None
        self.setCursor(Qt.CrossCursor)
        self.picking_color = True

    def end_color_picking(self):
        """色選択モードを終了する"""
        self.picking_color = False
        self.setCursor(Qt.ArrowCursor)


class EditorWindow(QWidget):
    """キャラクター編集ウィンドウ"""

    image_updated = pyqtSignal(object)
    image_cleared = pyqtSignal()
    export_requested = pyqtSignal()
    include_background_changed = pyqtSignal(bool)
    mask_settings_changed = pyqtSignal(bool, int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.canvas = CharacterCanvas()
        self.base_image = None
        self.preview_image = None
        self.original_image_path = None
        self.scale_percent = 100
        self.scale_dragging = False
        self.last_crop_backup = None
        self.fill_small_holes_enabled = True
        self.mask_expand_pixels = 1
        self.preview_update_timer = QTimer(self)
        self.preview_update_timer.setSingleShot(True)
        self.preview_update_timer.timeout.connect(self.refresh_preview)
        self.init_ui()
        self.on_mask_setting_changed()
        self.setStyleSheet(STYLESHEET)
        self.canvas.image_dropped.connect(self.load_image_from_path)
        self.canvas.color_picked.connect(self.on_color_picked)
        self.canvas.crop_region_changed.connect(self.on_crop_region_changed)

    def init_ui(self):
        """UI を初期化"""
        main_layout = QHBoxLayout()

        canvas_layout = QVBoxLayout()
        canvas_layout.addWidget(self.canvas)
        main_layout.addLayout(canvas_layout, 2)

        tool_layout = QVBoxLayout()

        load_group = QGroupBox("画像読み込み")
        load_layout = QVBoxLayout()
        load_btn = QPushButton("画像を選択")
        load_btn.setProperty("buttonRole", "primary")
        load_btn.setMinimumHeight(42)
        load_btn.clicked.connect(self.load_image)
        load_layout.addWidget(load_btn)
        load_group.setLayout(load_layout)
        tool_layout.addWidget(load_group)

        crop_group = QGroupBox("範囲指定切り抜き")
        crop_layout = QVBoxLayout()
        self.crop_toggle_btn = QPushButton("切り抜きモード開始")
        self.crop_toggle_btn.setEnabled(False)
        self.crop_toggle_btn.clicked.connect(self.toggle_crop_mode)
        self.crop_apply_btn = QPushButton("切り抜きを適用")
        self.crop_apply_btn.setEnabled(False)
        self.crop_apply_btn.clicked.connect(self.apply_crop)
        self.crop_restore_btn = QPushButton("切り抜きを復元")
        self.crop_restore_btn.setEnabled(False)
        self.crop_restore_btn.clicked.connect(self.restore_crop)
        crop_layout.addWidget(self.crop_toggle_btn)
        crop_layout.addWidget(self.crop_apply_btn)
        crop_layout.addWidget(self.crop_restore_btn)
        crop_group.setLayout(crop_layout)
        tool_layout.addWidget(crop_group)

        scale_group = QGroupBox("ビュー上のキャラサイズ調整")
        scale_layout = QVBoxLayout()
        scale_layout.addWidget(QLabel("スケール (%)"))
        scale_layout_h = QHBoxLayout()
        self.scale_slider = QSlider(Qt.Horizontal)
        self.scale_slider.setMinimum(10)
        self.scale_slider.setMaximum(300)
        self.scale_slider.setValue(100)
        self.scale_slider.setTickPosition(QSlider.TicksBelow)
        self.scale_slider.setEnabled(False)
        self.scale_slider.valueChanged.connect(self.on_scale_changed)
        self.scale_slider.sliderPressed.connect(self.on_scale_slider_pressed)
        self.scale_slider.sliderReleased.connect(self.on_scale_slider_released)
        scale_layout_h.addWidget(self.scale_slider, 4)
        self.scale_spinbox = QSpinBox()
        self.scale_spinbox.setMinimum(10)
        self.scale_spinbox.setMaximum(300)
        self.scale_spinbox.setValue(100)
        self.scale_spinbox.setEnabled(False)
        self.scale_spinbox.valueChanged.connect(self.on_scale_spinbox_changed)
        scale_layout_h.addWidget(self.scale_spinbox, 1)
        scale_layout.addLayout(scale_layout_h)
        scale_layout.addWidget(QLabel("ビューに表示されるキャラクターの大きさを調整します"))
        scale_group.setLayout(scale_layout)
        tool_layout.addWidget(scale_group)

        alpha_group = QGroupBox("簡易背景透過")
        alpha_layout = QVBoxLayout()
        self.alpha_status_label = QLabel("単色背景向けの簡易機能です。開始後に背景色をクリックすると、その色を透過します")
        self.alpha_mode_btn = QPushButton("簡易透過モード開始")
        self.alpha_mode_btn.setEnabled(False)
        self.alpha_mode_btn.clicked.connect(self.toggle_alpha_mode)
        alpha_layout.addWidget(self.alpha_status_label)
        alpha_layout.addWidget(self.alpha_mode_btn)
        alpha_group.setLayout(alpha_layout)
        tool_layout.addWidget(alpha_group)

        flip_group = QGroupBox("左右反転")
        flip_layout = QVBoxLayout()
        self.flip_btn = QPushButton("左右を反転")
        self.flip_btn.setEnabled(False)
        self.flip_btn.clicked.connect(self.apply_flip)
        flip_layout.addWidget(self.flip_btn)
        flip_group.setLayout(flip_layout)
        tool_layout.addWidget(flip_group)

        export_group = QGroupBox("画像出力")
        export_layout = QVBoxLayout()
        format_layout = QHBoxLayout()
        format_layout.addWidget(QLabel("出力形式:"))
        self.format_combo = QComboBox()
        self.format_combo.addItems(["PNG", "BMP"])
        self.format_combo.currentTextChanged.connect(self.on_output_format_changed)
        format_layout.addWidget(self.format_combo)
        export_layout.addLayout(format_layout)
        self.format_warning_label = QLabel(
            "BMP は透過状態が維持されない場合があります。必要に応じて Alpha マスクと組み合わせてください"
        )
        self.format_warning_label.setWordWrap(True)
        self.format_warning_label.setStyleSheet("color: #c62828; font-weight: bold;")
        self.format_warning_label.hide()
        export_layout.addWidget(self.format_warning_label)
        self.include_bg_checkbox = QCheckBox("背景を含める")
        self.include_bg_checkbox.setChecked(True)
        self.include_bg_checkbox.toggled.connect(self.include_background_changed.emit)
        export_layout.addWidget(self.include_bg_checkbox)
        self.export_mask_checkbox = QCheckBox("Alphaマスクを自動生成して出力")
        self.export_mask_checkbox.setChecked(False)
        export_layout.addWidget(self.export_mask_checkbox)
        self.fill_small_holes_checkbox = QCheckBox("Alphaマスクの小さい穴を埋める")
        self.fill_small_holes_checkbox.setChecked(False)
        self.fill_small_holes_checkbox.toggled.connect(self.on_mask_setting_changed)
        export_layout.addWidget(self.fill_small_holes_checkbox)
        mask_expand_layout = QHBoxLayout()
        self.mask_expand_label = QLabel("Alphaマスク拡張 (px)")
        self.mask_expand_label.setEnabled(False)
        mask_expand_layout.addWidget(self.mask_expand_label)
        self.mask_expand_spinbox = QSpinBox()
        self.mask_expand_spinbox.setMinimum(0)
        self.mask_expand_spinbox.setMaximum(2)
        self.mask_expand_spinbox.setValue(1)
        self.mask_expand_spinbox.setEnabled(False)
        self.mask_expand_spinbox.valueChanged.connect(self.on_mask_setting_changed)
        mask_expand_layout.addWidget(self.mask_expand_spinbox)
        export_layout.addLayout(mask_expand_layout)
        self.fixed_output_folder_checkbox = QCheckBox("出力先フォルダ名を固定")
        self.fixed_output_folder_checkbox.setChecked(False)
        self.fixed_output_folder_checkbox.toggled.connect(self.on_fixed_output_folder_toggled)
        export_layout.addWidget(self.fixed_output_folder_checkbox)
        self.fixed_output_folder_input = QLineEdit()
        self.fixed_output_folder_input.setPlaceholderText("例: latest")
        self.fixed_output_folder_input.setEnabled(False)
        export_layout.addWidget(self.fixed_output_folder_input)
        self.export_btn = QPushButton("画像を出力")
        self.export_btn.setProperty("buttonRole", "primary")
        self.export_btn.setMinimumHeight(44)
        self.export_btn.clicked.connect(self.export_requested.emit)
        export_layout.addWidget(self.export_btn)
        export_group.setLayout(export_layout)
        tool_layout.addWidget(export_group)

        tool_layout.addStretch()
        main_layout.addLayout(tool_layout, 1)

        self.setLayout(main_layout)
        self.setWindowTitle("キャラクター編集")
        self.setGeometry(100, 100, EDITOR_WINDOW_WIDTH, EDITOR_WINDOW_HEIGHT)
        self.on_output_format_changed(self.format_combo.currentText())

    def load_image(self):
        """ファイルダイアログから画像を読み込む"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "キャラクター画像を選択",
            "",
            "画像ファイル (*.png *.bmp *.jpg *.jpeg);;すべてのファイル (*.*)",
        )
        if file_path:
            self.load_image_from_path(file_path)

    def load_image_from_path(self, file_path: str):
        """指定パスの画像を編集対象として読み込む"""
        image = ImageProcessor.load_image(file_path)
        if not image:
            QMessageBox.warning(self, "警告", "画像の読み込みに失敗しました")
            return

        self.set_image(image, original_image_path=file_path)

    def set_image(self, image, original_image_path: str = None):
        """既存の PIL Image を編集対象として設定する"""
        if image is None:
            self.clear_image()
            return

        self.original_image_path = original_image_path
        self.base_image = image.copy().convert("RGBA")
        self.preview_image = None
        self.scale_percent = 100
        self.last_crop_backup = None
        self.canvas.clear_interaction_state()
        self.canvas.end_cropping()
        self.canvas.end_color_picking()
        self.crop_toggle_btn.setText("切り抜きモード開始")
        self.alpha_mode_btn.setText("簡易透過モード開始")
        self.crop_apply_btn.setEnabled(False)
        self.crop_restore_btn.setEnabled(False)
        self.alpha_status_label.setText("単色背景向けの簡易機能です。開始後に背景色をクリックすると、その色を透過します")

        self.scale_slider.blockSignals(True)
        self.scale_spinbox.blockSignals(True)
        self.scale_slider.setValue(100)
        self.scale_spinbox.setValue(100)
        self.scale_slider.blockSignals(False)
        self.scale_spinbox.blockSignals(False)

        self.enable_tools()
        self.schedule_preview_refresh(immediate=True)

    def enable_tools(self):
        """ツールを有効にする"""
        self.crop_toggle_btn.setEnabled(True)
        self.scale_slider.setEnabled(True)
        self.scale_spinbox.setEnabled(True)
        self.alpha_mode_btn.setEnabled(True)
        self.flip_btn.setEnabled(True)

    def disable_tools(self):
        """ツールを無効にする"""
        self.crop_toggle_btn.setEnabled(False)
        self.crop_apply_btn.setEnabled(False)
        self.crop_restore_btn.setEnabled(False)
        self.scale_slider.setEnabled(False)
        self.scale_spinbox.setEnabled(False)
        self.alpha_mode_btn.setEnabled(False)
        self.flip_btn.setEnabled(False)

    def clear_image(self):
        """編集中の画像をクリアする"""
        self.base_image = None
        self.preview_image = None
        self.original_image_path = None
        self.scale_percent = 100
        self.last_crop_backup = None
        self.canvas.clear_interaction_state()
        self.canvas.end_cropping()
        self.canvas.end_color_picking()
        self.crop_toggle_btn.setText("切り抜きモード開始")
        self.crop_apply_btn.setEnabled(False)
        self.crop_restore_btn.setEnabled(False)
        self.alpha_mode_btn.setText("簡易透過モード開始")
        self.alpha_status_label.setText("単色背景向けの簡易機能です。開始後に背景色をクリックすると、その色を透過します")
        self.scale_slider.blockSignals(True)
        self.scale_spinbox.blockSignals(True)
        self.scale_slider.setValue(100)
        self.scale_spinbox.setValue(100)
        self.scale_slider.blockSignals(False)
        self.scale_spinbox.blockSignals(False)
        self.disable_tools()
        self.schedule_preview_refresh(immediate=True)

    def reset_crop_selection(self):
        """切り抜き選択状態をクリアする"""
        self.canvas.crop_rect = None
        self.canvas.crop_start = None
        self.canvas.end_cropping()
        self.crop_toggle_btn.setText("切り抜きモード開始")
        self.crop_apply_btn.setEnabled(False)
        self.crop_restore_btn.setEnabled(self.last_crop_backup is not None)
        self.canvas.update_display()

    def schedule_preview_refresh(self, immediate: bool = False):
        """プレビュー更新を少しまとめて、操作時の引っかかりを減らす。"""
        if immediate:
            self.preview_update_timer.stop()
            self.refresh_preview()
            return

        self.preview_update_timer.start(16)

    def refresh_preview(self):
        """現在の編集状態からプレビューを再生成する"""
        if not self.base_image:
            self.preview_image = None
            self.canvas.set_image(None)
            self.image_cleared.emit()
            return

        if self.scale_percent == 100:
            self.preview_image = self.base_image.copy()
        else:
            resampling = (
                Image.Resampling.BILINEAR
                if self.scale_dragging
                else Image.Resampling.LANCZOS
            )
            self.preview_image = ImageProcessor.scale_image(
                self.base_image,
                self.scale_percent,
                resampling=resampling,
            )

        self.canvas.set_image(self.preview_image)
        self.image_updated.emit(self.preview_image.copy())

    def on_crop_region_changed(self):
        """切り抜き選択の有無に応じて適用ボタンを切り替える"""
        self.crop_apply_btn.setEnabled(self.canvas.crop_rect is not None)
        self.crop_restore_btn.setEnabled(self.last_crop_backup is not None)

    def toggle_crop_mode(self):
        """切り抜きモードの切り替え"""
        if self.canvas.is_cropping:
            self.reset_crop_selection()
        else:
            self.canvas.start_cropping()
            self.crop_toggle_btn.setText("切り抜きモード終了")
            self.crop_restore_btn.setEnabled(self.last_crop_backup is not None)
            self.alpha_mode_btn.setText("簡易透過モード開始")
            self.canvas.end_color_picking()

    def restore_crop(self):
        """最後に適用した切り抜き前の状態へ戻す"""
        if self.last_crop_backup is None:
            return

        self.base_image = self.last_crop_backup.copy()
        self.last_crop_backup = None
        self.reset_crop_selection()
        self.schedule_preview_refresh(immediate=True)

    def apply_crop(self):
        """切り抜きを適用する"""
        if not self.base_image or not self.preview_image:
            return

        crop_region = self.canvas.get_crop_region()
        if not crop_region:
            QMessageBox.warning(self, "警告", "切り抜く範囲を選択してください")
            return

        preview_w = max(1, self.preview_image.width)
        preview_h = max(1, self.preview_image.height)
        base_box = (
            int(crop_region[0] * self.base_image.width / preview_w),
            int(crop_region[1] * self.base_image.height / preview_h),
            int(crop_region[2] * self.base_image.width / preview_w),
            int(crop_region[3] * self.base_image.height / preview_h),
        )

        if base_box[2] <= base_box[0] or base_box[3] <= base_box[1]:
            QMessageBox.warning(self, "警告", "有効な範囲を選択してください")
            return

        self.last_crop_backup = self.base_image.copy()
        self.base_image = ImageProcessor.crop_image(self.base_image, base_box)
        self.canvas.clear_interaction_state()
        self.reset_crop_selection()
        self.schedule_preview_refresh(immediate=True)

    def on_scale_changed(self, value):
        """スライダー変更時に即時反映する"""
        self.scale_spinbox.blockSignals(True)
        self.scale_spinbox.setValue(value)
        self.scale_spinbox.blockSignals(False)
        self.scale_percent = value
        self.schedule_preview_refresh()

    def on_scale_spinbox_changed(self, value):
        """スピンボックス変更時に即時反映する"""
        self.scale_slider.blockSignals(True)
        self.scale_slider.setValue(value)
        self.scale_slider.blockSignals(False)
        self.scale_percent = value
        self.schedule_preview_refresh(immediate=True)

    def on_scale_slider_pressed(self):
        self.scale_dragging = True

    def on_scale_slider_released(self):
        self.scale_dragging = False
        self.schedule_preview_refresh(immediate=True)

    def toggle_alpha_mode(self):
        """色選択モードの切り替え"""
        if self.canvas.picking_color:
            self.canvas.end_color_picking()
            self.alpha_mode_btn.setText("簡易透過モード開始")
            self.alpha_status_label.setText("単色背景向けの簡易機能です。開始後に背景色をクリックすると、その色を透過します")
        else:
            self.canvas.start_color_picking()
            self.reset_crop_selection()
            self.alpha_mode_btn.setText("背景をクリック中...")
            self.alpha_status_label.setText("単色背景の色をクリックしてください")

    def on_color_picked(self, color):
        """クリックした色を透過して即時反映する"""
        if not self.base_image:
            return

        self.base_image = ImageProcessor.remove_background_by_color(self.base_image, color)
        self.canvas.selected_color = None
        self.canvas.end_color_picking()
        self.alpha_mode_btn.setText("簡易透過モード開始")
        self.alpha_status_label.setText(
            f"RGB{color} を簡易透過しました。必要ならもう一度開始してください"
        )
        self.schedule_preview_refresh(immediate=True)

    def apply_flip(self):
        """左右反転を適用する"""
        if not self.base_image:
            return

        self.base_image = ImageProcessor.flip_horizontal(self.base_image)
        self.schedule_preview_refresh(immediate=True)

    def get_edited_image(self):
        """現在の編集済み画像を返す"""
        if not self.preview_image:
            return None
        return self.preview_image.copy()

    def get_output_format(self):
        """選択中の出力形式を返す。"""
        return self.format_combo.currentText()

    def on_output_format_changed(self, output_format: str):
        """出力形式に応じた補助メッセージを切り替える。"""
        self.format_warning_label.setVisible(output_format.upper() == "BMP")

    def should_include_background(self):
        """背景を含めて出力するか返す。"""
        return self.include_bg_checkbox.isChecked()

    def should_export_mask(self):
        return self.export_mask_checkbox.isChecked()

    def on_mask_setting_changed(self):
        self.fill_small_holes_enabled = self.fill_small_holes_checkbox.isChecked()
        self.mask_expand_label.setEnabled(self.fill_small_holes_enabled)
        self.mask_expand_spinbox.setEnabled(self.fill_small_holes_enabled)
        self.mask_expand_pixels = (
            self.mask_expand_spinbox.value() if self.fill_small_holes_enabled else 0
        )
        self.mask_settings_changed.emit(
            self.fill_small_holes_enabled,
            self.mask_expand_pixels,
        )

    def get_mask_processing_settings(self):
        return {
            "fill_small_holes": self.fill_small_holes_checkbox.isChecked(),
            "expand_pixels": (
                self.mask_expand_spinbox.value()
                if self.fill_small_holes_checkbox.isChecked()
                else 0
            ),
        }

    def on_fixed_output_folder_toggled(self, checked):
        self.fixed_output_folder_input.setEnabled(bool(checked))

    def should_use_fixed_output_folder(self):
        return self.fixed_output_folder_checkbox.isChecked()

    def get_fixed_output_folder_name(self):
        return self.fixed_output_folder_input.text().strip()
