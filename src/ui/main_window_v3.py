"""メイン画面。カテゴリ・サブカテゴリ管理を行う。"""

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import (
    QDialog,
    QFileDialog,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from src.core.portraiture_db import PortraitureDB
from src.ui.styles import STYLESHEET
from src.utils.constants import MAIN_WINDOW_HEIGHT, MAIN_WINDOW_WIDTH


class ImageDropLabel(QLabel):
    """ドラッグ&ドロップで画像を受け取れるプレビューラベル。"""

    file_dropped = pyqtSignal(str)

    def __init__(self, empty_text: str, parent=None):
        super().__init__(parent)
        self.empty_text = empty_text
        self.current_file_path = None
        self.setAcceptDrops(True)
        self.setAlignment(Qt.AlignCenter)
        self.setMinimumSize(160, 90)
        self.setStyleSheet("border: 1px dashed #999999; background-color: #fafafa;")
        self.show_empty_text()

    def show_empty_text(self):
        self.current_file_path = None
        self.clear()
        self.setText(self.empty_text)

    def show_image(self, file_path: str):
        if not file_path:
            self.show_empty_text()
            return

        self.current_file_path = file_path
        pixmap = QPixmap(file_path)
        if pixmap.isNull():
            self.show_empty_text()
            return

        self.setPixmap(
            pixmap.scaled(
                self.size(),
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation,
            )
        )

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self.current_file_path:
            self.show_image(self.current_file_path)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            return
        event.ignore()

    def dropEvent(self, event):
        if not event.mimeData().hasUrls():
            event.ignore()
            return

        urls = event.mimeData().urls()
        if not urls:
            event.ignore()
            return

        self.file_dropped.emit(urls[0].toLocalFile())
        event.acceptProposedAction()


class CategoryDialog(QDialog):
    """カテゴリ追加ダイアログ。"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        name_layout = QHBoxLayout()
        name_layout.addWidget(QLabel("カテゴリ名:"))
        self.name_input = QLineEdit()
        name_layout.addWidget(self.name_input)
        layout.addLayout(name_layout)

        button_layout = QHBoxLayout()
        ok_btn = QPushButton("OK")
        ok_btn.clicked.connect(self.accept)
        cancel_btn = QPushButton("キャンセル")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(ok_btn)
        button_layout.addWidget(cancel_btn)
        layout.addLayout(button_layout)

        self.setLayout(layout)
        self.setWindowTitle("カテゴリ追加")
        self.setMinimumWidth(320)

    def get_data(self):
        return {"name": self.name_input.text().strip()}


class SubcategoryDialog(QDialog):
    """サブカテゴリ追加ダイアログ。"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.background_path = None
        self.guide_image_path = None
        self.mask_image_path = None
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        name_layout = QHBoxLayout()
        name_layout.addWidget(QLabel("サブカテゴリ名:"))
        self.name_input = QLineEdit()
        name_layout.addWidget(self.name_input)
        layout.addLayout(name_layout)

        layout.addLayout(
            self._build_image_selector(
                title="背景画像:",
                empty_text="背景画像を選択するか、ここへドロップしてください",
                on_pick=self.select_background,
                on_drop=self.set_background_path,
                attr_name="bg_preview",
            )
        )

        layout.addLayout(
            self._build_image_selector(
                title="位置ガイド画像:",
                empty_text="位置ガイド画像を選択するか、ここへドロップしてください",
                on_pick=self.select_guide_image,
                on_drop=self.set_guide_image_path,
                attr_name="guide_preview",
            )
        )

        layout.addLayout(
            self._build_image_selector(
                title="固定マスク画像（任意）",
                empty_text="固定マスク画像を選択するか、ここへドラッグ&ドロップしてください",
                on_pick=self.select_mask_image,
                on_drop=self.set_mask_image_path,
                attr_name="mask_preview",
            )
        )

        button_layout = QHBoxLayout()
        ok_btn = QPushButton("OK")
        ok_btn.clicked.connect(self.accept)
        cancel_btn = QPushButton("キャンセル")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(ok_btn)
        button_layout.addWidget(cancel_btn)
        layout.addLayout(button_layout)

        self.setLayout(layout)
        self.setWindowTitle("サブカテゴリ追加")
        self.setMinimumWidth(520)

    def _build_image_selector(self, title, empty_text, on_pick, on_drop, attr_name):
        layout = QVBoxLayout()
        layout.addWidget(QLabel(title))

        preview = ImageDropLabel(empty_text, self)
        preview.file_dropped.connect(on_drop)
        setattr(self, attr_name, preview)
        layout.addWidget(preview)

        button_row = QHBoxLayout()
        select_btn = QPushButton("画像を選択")
        select_btn.clicked.connect(on_pick)
        clear_btn = QPushButton("クリア")
        clear_btn.clicked.connect(lambda: on_drop(""))
        button_row.addWidget(select_btn)
        button_row.addWidget(clear_btn)
        layout.addLayout(button_row)
        return layout

    def _select_image_file(self, title: str):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            title,
            "",
            "画像ファイル (*.png *.bmp *.jpg *.jpeg);;すべてのファイル (*.*)",
        )
        return file_path

    def select_background(self):
        file_path = self._select_image_file("背景画像を選択")
        if file_path:
            self.set_background_path(file_path)

    def set_background_path(self, file_path: str):
        self.background_path = file_path or None
        self.bg_preview.show_image(self.background_path)

    def select_guide_image(self):
        file_path = self._select_image_file("位置ガイド画像を選択")
        if file_path:
            self.set_guide_image_path(file_path)

    def set_guide_image_path(self, file_path: str):
        self.guide_image_path = file_path or None
        self.guide_preview.show_image(self.guide_image_path)

    def select_mask_image(self):
        file_path = self._select_image_file("固定マスク画像を選択")
        if file_path:
            self.set_mask_image_path(file_path)

    def set_mask_image_path(self, file_path: str):
        self.mask_image_path = file_path or None
        self.mask_preview.show_image(self.mask_image_path)

    def get_data(self):
        return {
            "name": self.name_input.text().strip(),
            "background": self.background_path,
            "guide_image": self.guide_image_path,
            "mask_image": self.mask_image_path,
        }


class MainWindow(QMainWindow):
    """メイン画面。"""

    subcategory_selected = pyqtSignal(str, str)
    character_registration_requested = pyqtSignal(str, str)

    def __init__(self):
        super().__init__()
        self.db = PortraitureDB("data/portraiture.json")
        self.init_ui()
        self.setStyleSheet(STYLESHEET)

    def init_ui(self):
        self.setWindowTitle("Custom Portrait Tool")
        self.setGeometry(100, 100, MAIN_WINDOW_WIDTH, MAIN_WINDOW_HEIGHT)

        central_widget = QWidget()
        main_layout = QHBoxLayout()

        left_layout = QVBoxLayout()
        category_group = QGroupBox("カテゴリ")
        category_layout = QVBoxLayout()

        self.category_list = QListWidget()
        self.category_list.itemSelectionChanged.connect(self.on_category_selected)
        category_layout.addWidget(self.category_list)

        category_button_layout = QHBoxLayout()
        add_cat_btn = QPushButton("カテゴリ追加")
        add_cat_btn.clicked.connect(self.add_category)
        del_cat_btn = QPushButton("カテゴリ削除")
        del_cat_btn.clicked.connect(self.delete_category)
        category_button_layout.addWidget(add_cat_btn)
        category_button_layout.addWidget(del_cat_btn)
        category_layout.addLayout(category_button_layout)

        category_group.setLayout(category_layout)
        left_layout.addWidget(category_group)

        right_layout = QVBoxLayout()
        subcategory_group = QGroupBox("サブカテゴリ")
        subcategory_layout = QVBoxLayout()

        self.subcategory_list = QListWidget()
        self.subcategory_list.itemSelectionChanged.connect(self.on_subcategory_selected)
        subcategory_layout.addWidget(self.subcategory_list)

        subcategory_button_layout = QHBoxLayout()
        add_subcat_btn = QPushButton("サブカテゴリ追加")
        add_subcat_btn.clicked.connect(self.add_subcategory)
        edit_bg_btn = QPushButton("背景変更")
        edit_bg_btn.clicked.connect(self.edit_subcategory_background)
        edit_guide_btn = QPushButton("位置ガイド変更")
        edit_guide_btn.clicked.connect(self.edit_subcategory_guide_image)
        edit_mask_btn = QPushButton("固定マスク変更")
        edit_mask_btn.clicked.connect(self.edit_subcategory_mask_image)
        del_subcat_btn = QPushButton("サブカテゴリ削除")
        del_subcat_btn.clicked.connect(self.delete_subcategory)
        subcategory_button_layout.addWidget(add_subcat_btn)
        subcategory_button_layout.addWidget(edit_bg_btn)
        subcategory_button_layout.addWidget(edit_guide_btn)
        subcategory_button_layout.addWidget(edit_mask_btn)
        subcategory_button_layout.addWidget(del_subcat_btn)
        subcategory_layout.addLayout(subcategory_button_layout)

        subcategory_group.setLayout(subcategory_layout)
        right_layout.addWidget(subcategory_group)

        character_layout = QHBoxLayout()
        self.char_registration_btn = QPushButton("キャラクター登録")
        self.char_registration_btn.clicked.connect(self.on_character_registration)
        self.char_registration_btn.setEnabled(False)
        character_layout.addWidget(self.char_registration_btn)
        right_layout.addLayout(character_layout)

        main_layout.addLayout(left_layout, 1)
        main_layout.addLayout(right_layout, 1)

        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)

        self.refresh_category_list()

    def refresh_category_list(self):
        self.category_list.clear()
        for cat_name in self.db.get_categories():
            self.category_list.addItem(cat_name)

    def refresh_subcategory_list(self):
        self.subcategory_list.clear()
        selected_items = self.category_list.selectedItems()
        if not selected_items:
            return

        category_name = selected_items[0].text()
        for subcat_name in self.db.get_subcategories(category_name):
            self.subcategory_list.addItem(subcat_name)

    def on_category_selected(self):
        self.refresh_subcategory_list()
        self.enable_character_registration(False)
        self.subcategory_selected.emit("", "")

    def on_subcategory_selected(self):
        selected_cat = self.category_list.selectedItems()
        selected_subcat = self.subcategory_list.selectedItems()

        if selected_cat and selected_subcat:
            category_name = selected_cat[0].text()
            subcategory_name = selected_subcat[0].text()
            self.enable_character_registration(True)
            self.subcategory_selected.emit(category_name, subcategory_name)
            return

        self.enable_character_registration(False)
        self.subcategory_selected.emit("", "")

    def add_category(self):
        dialog = CategoryDialog(self)
        if not dialog.exec_():
            return

        data = dialog.get_data()
        if not data["name"]:
            QMessageBox.warning(self, "警告", "カテゴリ名を入力してください")
            return

        if self.db.add_category(data["name"]):
            self.refresh_category_list()
            QMessageBox.information(self, "成功", "カテゴリを追加しました")
            return

        QMessageBox.warning(self, "警告", "カテゴリは既に存在します")

    def delete_category(self):
        selected_items = self.category_list.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "警告", "カテゴリを選択してください")
            return

        category_name = selected_items[0].text()
        reply = QMessageBox.question(
            self,
            "確認",
            f"カテゴリ '{category_name}' を削除しますか？",
            QMessageBox.Yes | QMessageBox.No,
        )
        if reply != QMessageBox.Yes:
            return

        self.db.remove_category(category_name)
        self.refresh_category_list()
        self.refresh_subcategory_list()
        QMessageBox.information(self, "成功", "カテゴリを削除しました")

    def add_subcategory(self):
        selected_items = self.category_list.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "警告", "カテゴリを選択してください")
            return

        category_name = selected_items[0].text()
        dialog = SubcategoryDialog(self)
        if not dialog.exec_():
            return

        data = dialog.get_data()
        if not data["name"]:
            QMessageBox.warning(self, "警告", "サブカテゴリ名を入力してください")
            return

        if self.db.add_subcategory(
            category_name,
            data["name"],
            data["background"],
            data["guide_image"],
            data["mask_image"],
        ):
            self.refresh_subcategory_list()
            QMessageBox.information(self, "成功", "サブカテゴリを追加しました")
            return

        QMessageBox.warning(self, "警告", "サブカテゴリは既に存在します")

    def delete_subcategory(self):
        selected_cat = self.category_list.selectedItems()
        selected_subcat = self.subcategory_list.selectedItems()
        if not selected_cat or not selected_subcat:
            QMessageBox.warning(self, "警告", "カテゴリとサブカテゴリを選択してください")
            return

        category_name = selected_cat[0].text()
        subcategory_name = selected_subcat[0].text()
        reply = QMessageBox.question(
            self,
            "確認",
            f"サブカテゴリ '{subcategory_name}' を削除しますか？",
            QMessageBox.Yes | QMessageBox.No,
        )
        if reply != QMessageBox.Yes:
            return

        self.db.remove_subcategory(category_name, subcategory_name)
        self.refresh_subcategory_list()
        QMessageBox.information(self, "成功", "サブカテゴリを削除しました")

    def _get_selected_subcategory_names(self):
        selected_cat = self.category_list.selectedItems()
        selected_subcat = self.subcategory_list.selectedItems()
        if not selected_cat or not selected_subcat:
            return None, None
        return selected_cat[0].text(), selected_subcat[0].text()

    def _select_image_file(self, title: str):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            title,
            "",
            "画像ファイル (*.png *.bmp *.jpg *.jpeg);;すべてのファイル (*.*)",
        )
        return file_path

    def edit_subcategory_background(self):
        category_name, subcategory_name = self._get_selected_subcategory_names()
        if not category_name or not subcategory_name:
            QMessageBox.warning(self, "警告", "カテゴリとサブカテゴリを選択してください")
            return

        file_path = self._select_image_file(f"背景画像を選択: {subcategory_name}")
        if not file_path:
            return

        if self.db.update_subcategory_background(category_name, subcategory_name, file_path):
            self.subcategory_selected.emit(category_name, subcategory_name)
            QMessageBox.information(self, "成功", "背景画像を更新しました")
            return

        QMessageBox.warning(self, "警告", "背景画像の更新に失敗しました")

    def edit_subcategory_guide_image(self):
        category_name, subcategory_name = self._get_selected_subcategory_names()
        if not category_name or not subcategory_name:
            QMessageBox.warning(self, "警告", "カテゴリとサブカテゴリを選択してください")
            return

        file_path = self._select_image_file(f"位置ガイド画像を選択: {subcategory_name}")
        if not file_path:
            return

        if self.db.update_subcategory_guide_image(category_name, subcategory_name, file_path):
            self.subcategory_selected.emit(category_name, subcategory_name)
            QMessageBox.information(self, "成功", "位置ガイド画像を更新しました")
            return

        QMessageBox.warning(self, "警告", "位置ガイド画像の更新に失敗しました")

    def edit_subcategory_mask_image(self):
        category_name, subcategory_name = self._get_selected_subcategory_names()
        if not category_name or not subcategory_name:
            QMessageBox.warning(self, "注意", "カテゴリとサブカテゴリを選択してください")
            return

        file_path = self._select_image_file(f"固定マスク画像を選択 {subcategory_name}")
        if not file_path:
            return

        if self.db.update_subcategory_mask_image(category_name, subcategory_name, file_path):
            self.subcategory_selected.emit(category_name, subcategory_name)
            QMessageBox.information(self, "完了", "固定マスク画像を更新しました")
            return

        QMessageBox.warning(self, "注意", "固定マスク画像の更新に失敗しました")

    def on_character_registration(self):
        category_name, subcategory_name = self._get_selected_subcategory_names()
        if not category_name or not subcategory_name:
            QMessageBox.warning(self, "警告", "カテゴリとサブカテゴリを選択してください")
            return

        self.character_registration_requested.emit(category_name, subcategory_name)

    def enable_character_registration(self, enabled: bool):
        self.char_registration_btn.setEnabled(enabled)
