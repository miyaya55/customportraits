"""メイン画面 - カテゴリ・サブカテゴリ管理"""

from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGroupBox,
    QPushButton, QListWidget, QListWidgetItem, QDialog, QLabel,
    QLineEdit, QMessageBox, QFileDialog, QComboBox, QSplitter,
    QFormLayout, QCheckBox
)
from PyQt5.QtCore import Qt, pyqtSignal, QMimeData
from PyQt5.QtGui import QIcon, QPixmap
from pathlib import Path
import sys

from src.core.config import PortraitureDB
from src.ui.styles import STYLESHEET
from src.utils.constants import MAIN_WINDOW_WIDTH, MAIN_WINDOW_HEIGHT


class CategoryDialog(QDialog):
    """カテゴリ追加ダイアログ"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()

    def init_ui(self):
        """UI を初期化"""
        layout = QVBoxLayout()

        # カテゴリ名
        name_layout = QHBoxLayout()
        name_layout.addWidget(QLabel("カテゴリ名:"))
        self.name_input = QLineEdit()
        name_layout.addWidget(self.name_input)
        layout.addLayout(name_layout)

        # ボタン
        btn_layout = QHBoxLayout()
        ok_btn = QPushButton("OK")
        ok_btn.clicked.connect(self.accept)
        cancel_btn = QPushButton("キャンセル")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(ok_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)

        self.setLayout(layout)
        self.setWindowTitle("カテゴリ追加")
        self.setMinimumWidth(300)

    def get_data(self):
        """ダイアログのデータを取得"""
        return {
            "name": self.name_input.text(),
        }


class SubcategoryDialog(QDialog):
    """サブカテゴリ追加ダイアログ"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.background_path = None
        self.init_ui()

    def dragEnterEvent(self, event):
        """ドラッグ開始時の処理"""
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event):
        """ドロップ時の処理"""
        if event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            if urls:
                file_path = urls[0].toLocalFile()
                self.background_path = file_path
                pixmap = QPixmap(file_path)
                self.bg_label.setPixmap(pixmap.scaledToHeight(80, Qt.SmoothTransformation))
            event.accept()
        else:
            event.ignore()

    def init_ui(self):
        """UI を初期化"""
        layout = QVBoxLayout()

        # サブカテゴリ名
        name_layout = QHBoxLayout()
        name_layout.addWidget(QLabel("サブカテゴリ名:"))
        self.name_input = QLineEdit()
        name_layout.addWidget(self.name_input)
        layout.addLayout(name_layout)

        # 背景画像
        bg_layout = QHBoxLayout()
        bg_layout.addWidget(QLabel("背景画像:"))
        self.bg_label = QLabel()
        self.bg_label.setText("背景が選択されていません")
        bg_layout.addWidget(self.bg_label)

        select_bg_btn = QPushButton("背景を選択")
        select_bg_btn.clicked.connect(self.select_background)
        bg_layout.addWidget(select_bg_btn)
        layout.addLayout(bg_layout)

        # ボタン
        btn_layout = QHBoxLayout()
        ok_btn = QPushButton("OK")
        ok_btn.clicked.connect(self.accept)
        cancel_btn = QPushButton("キャンセル")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(ok_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)

        self.setLayout(layout)
        self.setWindowTitle("サブカテゴリ追加")
        self.setMinimumWidth(400)

    def select_background(self):
        """背景画像を選択"""
        file_dialog = QFileDialog()
        file_path, _ = file_dialog.getOpenFileName(
            self,
            "背景画像を選択",
            "",
            "画像ファイル (*.png *.bmp *.jpg *.jpeg);;すべてのファイル (*.*)"
        )
        if file_path:
            self.background_path = file_path
            pixmap = QPixmap(file_path)
            self.bg_label.setPixmap(pixmap.scaledToHeight(80, Qt.SmoothTransformation))

    def get_data(self):
        """ダイアログのデータを取得"""
        return {
            "name": self.name_input.text(),
            "background": self.background_path,
        }


class MainWindow(QMainWindow):
    """メイン画面"""

    subcategory_selected = pyqtSignal(str, str)  # category, subcategory
    character_registration_requested = pyqtSignal(str, str)  # category, subcategory

    def __init__(self):
        super().__init__()
        self.db = PortraitureDB("data/portraiture.json")
        self.init_ui()
        self.setStyleSheet(STYLESHEET)

    def init_ui(self):
        """UI を初期化"""
        self.setWindowTitle("Custom Portrait Tool")
        self.setGeometry(100, 100, MAIN_WINDOW_WIDTH, MAIN_WINDOW_HEIGHT)

        # メインレイアウト
        central_widget = QWidget()
        main_layout = QHBoxLayout()

        # 左側: カテゴリ管理
        left_layout = QVBoxLayout()
        category_group = QGroupBox("カテゴリ")
        category_layout = QVBoxLayout()

        self.category_list = QListWidget()
        self.category_list.itemSelectionChanged.connect(self.on_category_selected)
        category_layout.addWidget(self.category_list)

        category_btn_layout = QHBoxLayout()
        add_cat_btn = QPushButton("カテゴリ追加")
        add_cat_btn.clicked.connect(self.add_category)
        del_cat_btn = QPushButton("カテゴリ削除")
        del_cat_btn.clicked.connect(self.delete_category)
        category_btn_layout.addWidget(add_cat_btn)
        category_btn_layout.addWidget(del_cat_btn)
        category_layout.addLayout(category_btn_layout)

        category_group.setLayout(category_layout)
        left_layout.addWidget(category_group)

        # 右側: サブカテゴリ管理
        right_layout = QVBoxLayout()
        subcategory_group = QGroupBox("サブカテゴリ")
        subcategory_layout = QVBoxLayout()

        self.subcategory_list = QListWidget()
        self.subcategory_list.itemSelectionChanged.connect(self.on_subcategory_selected)
        subcategory_layout.addWidget(self.subcategory_list)

        subcat_btn_layout = QHBoxLayout()
        add_subcat_btn = QPushButton("サブカテゴリ追加")
        add_subcat_btn.clicked.connect(self.add_subcategory)
        edit_subcat_btn = QPushButton("背景変更")
        edit_subcat_btn.clicked.connect(self.edit_subcategory_background)
        del_subcat_btn = QPushButton("サブカテゴリ削除")
        del_subcat_btn.clicked.connect(self.delete_subcategory)
        subcat_btn_layout.addWidget(add_subcat_btn)
        subcat_btn_layout.addWidget(edit_subcat_btn)
        subcat_btn_layout.addWidget(del_subcat_btn)
        subcategory_layout.addLayout(subcat_btn_layout)

        subcategory_group.setLayout(subcategory_layout)
        right_layout.addWidget(subcategory_group)

        # キャラクター登録ボタン
        char_layout = QHBoxLayout()
        self.char_registration_btn = QPushButton("キャラクター登録")
        self.char_registration_btn.clicked.connect(self.on_character_registration)
        self.char_registration_btn.setEnabled(False)
        char_layout.addWidget(self.char_registration_btn)
        right_layout.addLayout(char_layout)

        # 出力形式選択
        format_layout = QHBoxLayout()
        format_layout.addWidget(QLabel("出力形式:"))
        self.format_combo = QComboBox()
        self.format_combo.addItems(["PNG", "BMP"])
        format_layout.addWidget(self.format_combo)
        right_layout.addLayout(format_layout)

        # 背景を含めるチェックボックス
        self.include_bg_checkbox = QCheckBox("背景を含める")
        self.include_bg_checkbox.setChecked(True)
        right_layout.addWidget(self.include_bg_checkbox)

        # レイアウト結合
        main_layout.addLayout(left_layout, 1)
        main_layout.addLayout(right_layout, 1)

        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)

        # 初期表示
        self.refresh_category_list()

    def refresh_category_list(self):
        """カテゴリリストを更新"""
        self.category_list.clear()
        for cat_name in self.db.get_categories():
            self.category_list.addItem(cat_name)

    def refresh_subcategory_list(self):
        """サブカテゴリリストを更新"""
        self.subcategory_list.clear()
        selected_items = self.category_list.selectedItems()
        if selected_items:
            category_name = selected_items[0].text()
            for subcat_name in self.db.get_subcategories(category_name):
                self.subcategory_list.addItem(subcat_name)

    def on_category_selected(self):
        """カテゴリが選択されたときの処理"""
        self.refresh_subcategory_list()
        self.enable_character_registration(False)
        self.subcategory_selected.emit("", "")

    def on_subcategory_selected(self):
        """サブカテゴリが選択されたときの処理"""
        selected_cat = self.category_list.selectedItems()
        selected_subcat = self.subcategory_list.selectedItems()
        
        if selected_cat and selected_subcat:
            category_name = selected_cat[0].text()
            subcategory_name = selected_subcat[0].text()
            self.enable_character_registration(True)
            self.subcategory_selected.emit(category_name, subcategory_name)
        else:
            self.enable_character_registration(False)
            self.subcategory_selected.emit("", "")

    def add_category(self):
        """カテゴリを追加"""
        dialog = CategoryDialog(self)
        if dialog.exec_():
            data = dialog.get_data()
            if not data["name"]:
                QMessageBox.warning(self, "警告", "カテゴリ名を入力してください")
                return
            if self.db.add_category(data["name"]):
                self.refresh_category_list()
                QMessageBox.information(self, "成功", "カテゴリを追加しました")
            else:
                QMessageBox.warning(self, "警告", "カテゴリは既に存在します")

    def delete_category(self):
        """カテゴリを削除"""
        selected_items = self.category_list.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "警告", "カテゴリを選択してください")
            return

        category_name = selected_items[0].text()
        reply = QMessageBox.question(
            self,
            "確認",
            f"カテゴリ '{category_name}' を削除しますか？",
            QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            self.db.remove_category(category_name)
            self.refresh_category_list()
            self.refresh_subcategory_list()
            QMessageBox.information(self, "成功", "カテゴリを削除しました")

    def add_subcategory(self):
        """サブカテゴリを追加"""
        selected_items = self.category_list.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "警告", "カテゴリを選択してください")
            return

        category_name = selected_items[0].text()
        dialog = SubcategoryDialog(self)
        if dialog.exec_():
            data = dialog.get_data()
            if not data["name"]:
                QMessageBox.warning(self, "警告", "サブカテゴリ名を入力してください")
                return
            if self.db.add_subcategory(category_name, data["name"], data["background"]):
                self.refresh_subcategory_list()
                QMessageBox.information(self, "成功", "サブカテゴリを追加しました")
            else:
                QMessageBox.warning(self, "警告", "サブカテゴリは既に存在します")

    def delete_subcategory(self):
        """サブカテゴリを削除"""
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
            QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            self.db.remove_subcategory(category_name, subcategory_name)
            self.refresh_subcategory_list()
            QMessageBox.information(self, "成功", "サブカテゴリを削除しました")

    def edit_subcategory_background(self):
        """選択中サブカテゴリの背景画像を変更する"""
        selected_cat = self.category_list.selectedItems()
        selected_subcat = self.subcategory_list.selectedItems()

        if not selected_cat or not selected_subcat:
            QMessageBox.warning(self, "警告", "カテゴリとサブカテゴリを選択してください")
            return

        category_name = selected_cat[0].text()
        subcategory_name = selected_subcat[0].text()
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            f"背景画像を選択: {subcategory_name}",
            "",
            "画像ファイル (*.png *.bmp *.jpg *.jpeg);;すべてのファイル (*.*)",
        )
        if not file_path:
            return

        if self.db.update_subcategory_background(category_name, subcategory_name, file_path):
            self.subcategory_selected.emit(category_name, subcategory_name)
            QMessageBox.information(self, "成功", "背景画像を更新しました")
        else:
            QMessageBox.warning(self, "警告", "背景画像の更新に失敗しました")

    def on_character_registration(self):
        """キャラクター登録ボタンが押されたときの処理"""
        selected_cat = self.category_list.selectedItems()
        selected_subcat = self.subcategory_list.selectedItems()

        if not selected_cat or not selected_subcat:
            QMessageBox.warning(self, "警告", "カテゴリとサブカテゴリを選択してください")
            return

        category_name = selected_cat[0].text()
        subcategory_name = selected_subcat[0].text()
        self.character_registration_requested.emit(category_name, subcategory_name)

    def enable_character_registration(self, enabled: bool):
        """キャラクター登録ボタンを有効/無効にする"""
        self.char_registration_btn.setEnabled(enabled)
