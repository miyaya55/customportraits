"""メインアプリケーション エントリーポイント"""

import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from PyQt5.QtWidgets import QApplication, QMessageBox, QPushButton

from src.ui.main_window import MainWindow
from src.ui.viewer_window import ViewerWindow
from src.ui.editor_window import EditorWindow
from src.core.config import ConfigManager, PortraitureDB
from src.core.file_manager import FileManager
from src.core.image_processor import ImageProcessor
from src.utils.constants import CONFIG_FILE, PORTRAITURE_DB_FILE


class CustomPortraitApp:
    """Custom Portrait アプリケーション"""

    def __init__(self):
        self.config_manager = ConfigManager(CONFIG_FILE)
        self.portraiture_db = PortraitureDB(PORTRAITURE_DB_FILE)
        self.main_window = MainWindow()
        self.viewer_window = ViewerWindow()
        self.editor_window = EditorWindow()
        self.current_category = None
        self.current_subcategory = None
        self.edited_character_image = None
        self.character_states = {}
        self.connect_signals()
        self.setup_export_button()

    def setup_export_button(self):
        """エクスポートボタンをメイン画面に追加する"""
        export_btn = QPushButton("画像を出力")
        export_btn.clicked.connect(self.export_portrait)

        main_layout = self.main_window.centralWidget().layout()
        if main_layout and main_layout.count() >= 2:
            right_layout_item = main_layout.itemAt(1)
            if right_layout_item and right_layout_item.layout():
                right_layout_item.layout().addWidget(export_btn)

    def connect_signals(self):
        """シグナルを接続する"""
        self.main_window.subcategory_selected.connect(
            self.on_subcategory_selected
        )
        self.main_window.character_registration_requested.connect(
            self.on_character_registration_requested
        )
        self.viewer_window.canvas.character_position_changed.connect(
            self.on_viewer_character_position_changed
        )
        self.editor_window.image_updated.connect(self.on_editor_image_updated)
        self.editor_window.image_cleared.connect(self.on_editor_image_cleared)

    def ensure_viewer_window_visible(self):
        """ビューウィンドウが閉じられていたら再表示する"""
        if not self.viewer_window.isVisible():
            self.viewer_window.show()
        self.viewer_window.raise_()
        self.viewer_window.activateWindow()

    def get_current_state_key(self):
        """現在選択中のカテゴリ・サブカテゴリをキーに変換する"""
        if not self.current_category or not self.current_subcategory:
            return None
        return (self.current_category, self.current_subcategory)

    def save_current_state(self, image=None, position=None):
        """現在選択中のドラフト状態を保存する"""
        state_key = self.get_current_state_key()
        if not state_key:
            return

        state = self.character_states.setdefault(state_key, {})
        if image is not None:
            state["image"] = image.copy()
        if position is not None:
            state["position"] = tuple(position)

    def clear_current_state(self):
        """現在選択中のドラフト状態を削除する"""
        state_key = self.get_current_state_key()
        if state_key and state_key in self.character_states:
            del self.character_states[state_key]

    def apply_selection_state(self, sync_editor: bool = False):
        """現在選択中の状態をビューとエディタへ反映する"""
        if not self.current_category or not self.current_subcategory:
            self.edited_character_image = None
            self.viewer_window.set_background()
            self.viewer_window.clear_character()
            if sync_editor:
                self.editor_window.clear_image()
            return

        subcategory_data = self.portraiture_db.get_subcategory(
            self.current_category,
            self.current_subcategory,
        )
        if subcategory_data and subcategory_data.get("background"):
            self.viewer_window.set_background(subcategory_data["background"])
        else:
            self.viewer_window.set_background()

        state = self.character_states.get(self.get_current_state_key())
        if state and state.get("image") is not None:
            self.edited_character_image = state["image"].copy()
            self.viewer_window.set_character_image(self.edited_character_image)
            if state.get("position") is not None:
                self.viewer_window.set_character_position(*state["position"])
            self.save_current_state(
                image=self.edited_character_image,
                position=self.viewer_window.get_character_position(),
            )
            if sync_editor:
                self.editor_window.set_image(self.edited_character_image)
        else:
            self.edited_character_image = None
            self.viewer_window.clear_character()
            if sync_editor:
                self.editor_window.clear_image()

    def on_subcategory_selected(self, category: str, subcategory: str):
        """サブカテゴリ選択時にビューを更新する"""
        self.current_category = category or None
        self.current_subcategory = subcategory or None
        self.apply_selection_state(sync_editor=self.editor_window.isVisible())

    def on_character_registration_requested(self, category: str, subcategory: str):
        """キャラクター登録ボタン押下時に編集画面を開く"""
        self.current_category = category or None
        self.current_subcategory = subcategory or None
        self.apply_selection_state(sync_editor=True)
        self.ensure_viewer_window_visible()
        self.editor_window.show()
        self.editor_window.raise_()
        self.editor_window.activateWindow()

    def on_editor_image_updated(self, edited_image):
        """編集ウィンドウの内容をビューへ同期する"""
        if edited_image is None:
            return

        preserve_position = self.viewer_window.canvas.character_image is not None
        self.edited_character_image = edited_image.copy()
        self.viewer_window.set_character_image(
            self.edited_character_image,
            preserve_position=preserve_position,
        )
        self.save_current_state(
            image=self.edited_character_image,
            position=self.viewer_window.get_character_position(),
        )

    def on_editor_image_cleared(self):
        """編集画像が消えたときにビューもクリアする"""
        self.edited_character_image = None
        self.viewer_window.clear_character()
        self.clear_current_state()

    def on_viewer_character_position_changed(self, x: int, y: int):
        """ビューでのキャラクター位置変更を受け取る"""
        self.save_current_state(position=(x, y))

    def export_portrait(self):
        """ポートレートをエクスポートする"""
        if not self.current_category or not self.current_subcategory:
            QMessageBox.warning(self.main_window, "警告", "カテゴリとサブカテゴリを選択してください")
            return

        if self.edited_character_image is None:
            QMessageBox.warning(self.main_window, "警告", "キャラクターがまだ選択されていません")
            return

        output_format = self.main_window.format_combo.currentText()
        include_background = self.main_window.include_bg_checkbox.isChecked()

        output_dir = FileManager.create_output_directory(
            self.current_category,
            self.current_subcategory,
        )
        if not output_dir:
            QMessageBox.critical(self.main_window, "エラー", "出力ディレクトリの作成に失敗しました")
            return

        if include_background:
            display_image = self.viewer_window.get_display_image()
        else:
            display_image = self.edited_character_image.copy()

        if display_image is None:
            QMessageBox.warning(self.main_window, "警告", "出力できる画像がありません")
            return

        filename = FileManager.get_next_filename(output_dir, output_format)
        output_path = os.path.join(output_dir, filename)

        if ImageProcessor.save_image(display_image, output_path, output_format):
            QMessageBox.information(
                self.main_window,
                "成功",
                f"画像を保存しました\n{output_path}",
            )
        else:
            QMessageBox.critical(self.main_window, "エラー", "画像の保存に失敗しました")

    def run(self):
        """アプリケーションを起動する"""
        self.main_window.show()
        self.viewer_window.show()


def main():
    """メイン関数"""
    app = QApplication(sys.argv)
    custom_portrait_app = CustomPortraitApp()
    custom_portrait_app.run()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
