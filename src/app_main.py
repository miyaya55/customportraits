"""Custom Portrait Tool application entry point."""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from PyQt5.QtWidgets import QApplication, QMessageBox

from src.core.config import ConfigManager
from src.core.file_manager import FileManager
from src.core.image_processor import ImageProcessor
from src.core.portraiture_db import PortraitureDB
from src.ui.editor_window import EditorWindow
from src.ui.main_window_v3 import MainWindow
from src.ui.viewer_window_v3 import ViewerWindow
from src.utils.constants import CONFIG_FILE, PORTRAITURE_DB_FILE


class CustomPortraitApp:
    """Custom Portrait application controller."""

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
        self.setup_export_action()
        self.load_persisted_ui_state()

    def setup_export_action(self):
        self.editor_window.export_requested.connect(self.export_portrait)
        self.viewer_window.set_mask_preview_include_background(False)
        mask_settings = self.editor_window.get_mask_processing_settings()
        self.viewer_window.set_mask_processing_options(
            mask_settings["fill_small_holes"],
            mask_settings["expand_pixels"],
        )

    def connect_signals(self):
        self.main_window.subcategory_selected.connect(self.on_subcategory_selected)
        self.main_window.character_registration_requested.connect(
            self.on_character_registration_requested
        )
        self.main_window.window_closing.connect(self.on_main_window_closing)
        self.viewer_window.canvas.character_position_changed.connect(
            self.on_viewer_character_position_changed
        )
        self.viewer_window.canvas.scale_wheel_requested.connect(
            self.on_viewer_scale_wheel_requested
        )
        self.viewer_window.canvas.scale_key_requested.connect(
            self.on_viewer_scale_key_requested
        )
        self.editor_window.image_updated.connect(self.on_editor_image_updated)
        self.editor_window.image_cleared.connect(self.on_editor_image_cleared)
        self.editor_window.recent_image_requested.connect(self.on_recent_image_requested)
        self.editor_window.mask_settings_changed.connect(
            self.viewer_window.set_mask_processing_options
        )

    def load_persisted_ui_state(self):
        last_used_settings = self.config_manager.get_last_used_output_settings()
        self.editor_window.set_export_settings(
            output_format=last_used_settings.get("output_format", "PNG"),
            include_background=last_used_settings.get("include_background", True),
            use_common_folder=last_used_settings.get("use_common_output_folder", False),
            use_fixed_folder=last_used_settings.get("use_fixed_output_folder", False),
            folder_name=last_used_settings.get("output_folder_name", ""),
            filename=last_used_settings.get("output_filename", ""),
        )
        self.editor_window.set_recent_images(self.config_manager.get_recent_images())

    def get_selection_output_settings(self, subcategory_data):
        last_used_settings = self.config_manager.get_last_used_output_settings()
        settings = {
            "output_format": last_used_settings.get("output_format", "PNG"),
            "include_background": last_used_settings.get("include_background", True),
            "use_common_folder": last_used_settings.get("use_common_output_folder", False),
            "use_fixed_folder": last_used_settings.get("use_fixed_output_folder", False),
            "folder_name": last_used_settings.get("output_folder_name", ""),
            "filename": last_used_settings.get("output_filename", ""),
        }

        if not subcategory_data:
            return settings

        has_saved_output_settings = any(
            [
                subcategory_data.get("use_common_output_folder", False),
                subcategory_data.get("use_fixed_output_folder", False),
                bool(subcategory_data.get("output_folder_name", "")),
                bool(subcategory_data.get("output_filename", "")),
            ]
        )
        if has_saved_output_settings:
            settings.update(
                {
                    "use_common_folder": subcategory_data.get("use_common_output_folder", False),
                    "use_fixed_folder": subcategory_data.get("use_fixed_output_folder", False),
                    "folder_name": subcategory_data.get("output_folder_name", ""),
                    "filename": subcategory_data.get("output_filename", ""),
                }
            )

        return settings

    def ensure_viewer_window_visible(self):
        if not self.viewer_window.isVisible():
            self.viewer_window.show()
        self.viewer_window.raise_()
        self.viewer_window.activateWindow()

    def get_current_state_key(self):
        if not self.current_category or not self.current_subcategory:
            return None
        return (self.current_category, self.current_subcategory)

    def save_current_state(self, image=None, position=None):
        state_key = self.get_current_state_key()
        if not state_key:
            return

        state = self.character_states.setdefault(state_key, {})
        if image is not None:
            state["image"] = image.copy()
        if position is not None:
            state["position"] = tuple(position)

    def clear_current_state(self):
        state_key = self.get_current_state_key()
        if state_key and state_key in self.character_states:
            del self.character_states[state_key]

    def apply_selection_state(self, sync_editor: bool = False):
        if not self.current_category or not self.current_subcategory:
            self.edited_character_image = None
            self.viewer_window.set_background()
            self.viewer_window.set_guide_image()
            self.viewer_window.set_mask_image()
            self.viewer_window.clear_character()
            last_used_settings = self.config_manager.get_last_used_output_settings()
            self.editor_window.set_export_settings(
                output_format=last_used_settings.get("output_format", "PNG"),
                include_background=last_used_settings.get("include_background", True),
                use_common_folder=last_used_settings.get("use_common_output_folder", False),
                use_fixed_folder=last_used_settings.get("use_fixed_output_folder", False),
                folder_name=last_used_settings.get("output_folder_name", ""),
                filename=last_used_settings.get("output_filename", ""),
            )
            if sync_editor:
                self.editor_window.clear_image()
            return

        self.portraiture_db.load()
        subcategory_data = self.portraiture_db.get_subcategory(
            self.current_category,
            self.current_subcategory,
        )

        background = subcategory_data.get("background") if subcategory_data else None
        guide_image = subcategory_data.get("guide_image") if subcategory_data else None
        mask_image = subcategory_data.get("mask_image") if subcategory_data else None
        self.editor_window.set_export_settings(**self.get_selection_output_settings(subcategory_data))

        self.viewer_window.set_background(background)
        self.viewer_window.set_guide_image(guide_image)
        self.viewer_window.set_mask_image(mask_image)

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
            return

        self.edited_character_image = None
        self.viewer_window.clear_character()
        if sync_editor:
            self.editor_window.clear_image()

    def on_subcategory_selected(self, category: str, subcategory: str):
        self.current_category = category or None
        self.current_subcategory = subcategory or None
        self.apply_selection_state(sync_editor=self.editor_window.isVisible())

    def on_character_registration_requested(self, category: str, subcategory: str):
        self.current_category = category or None
        self.current_subcategory = subcategory or None
        self.apply_selection_state(sync_editor=True)
        self.ensure_viewer_window_visible()
        self.editor_window.show()
        self.editor_window.raise_()
        self.editor_window.activateWindow()

    def on_editor_image_updated(self, edited_image):
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
        self.edited_character_image = None
        self.viewer_window.clear_character()
        self.clear_current_state()

    def on_viewer_character_position_changed(self, x: int, y: int):
        self.save_current_state(position=(x, y))

    def on_viewer_scale_wheel_requested(self, delta_y: int):
        self.editor_window.on_scale_wheel_requested(delta_y)

    def on_viewer_scale_key_requested(self, step: int):
        self.editor_window.on_scale_key_requested(step)

    def on_recent_image_requested(self, recent_item):
        image_path = recent_item.get("image_path", "")
        if not image_path:
            return

        if not self.editor_window.load_image_from_path(image_path):
            return

        current_filename = self.editor_window.get_fixed_output_filename()
        self.editor_window.set_export_settings(
            output_format=recent_item.get("output_format", "PNG"),
            include_background=recent_item.get("include_background", True),
            use_common_folder=recent_item.get("use_common_output_folder", False),
            use_fixed_folder=recent_item.get("use_fixed_output_folder", False),
            folder_name=recent_item.get("output_folder_name", ""),
            filename=current_filename,
        )

    def on_main_window_closing(self):
        self.editor_window.close()
        self.viewer_window.close()

    def export_portrait(self):
        if not self.current_category or not self.current_subcategory:
            QMessageBox.warning(
                self.main_window,
                "注意",
                "カテゴリとサブカテゴリを選択してください",
            )
            return

        if self.edited_character_image is None:
            QMessageBox.warning(
                self.main_window,
                "注意",
                "キャラクター画像がまだ選択されていません",
            )
            return

        output_format = self.editor_window.get_output_format()
        include_background = self.editor_window.should_include_background()
        export_mask = self.editor_window.should_export_mask()
        use_common_output_folder = self.editor_window.should_use_common_output_folder()
        custom_filename = ""
        fixed_folder_name = ""
        if self.editor_window.should_use_fixed_output_folder():
            fixed_folder_name = self.editor_window.get_fixed_output_folder_name()
            if not fixed_folder_name:
                QMessageBox.warning(
                    self.main_window,
                    "注意",
                    "固定で使う出力先フォルダ名を入力してください",
                )
                return

            if not FileManager.is_valid_name(fixed_folder_name):
                QMessageBox.warning(
                    self.main_window,
                    "注意",
                    "固定で使う出力先フォルダ名に使えない文字が含まれています",
                )
                return

            custom_filename = self.editor_window.get_fixed_output_filename()
            if custom_filename and not FileManager.is_valid_name(custom_filename):
                QMessageBox.warning(
                    self.main_window,
                    "注意",
                    "固定で使うファイル名に使えない文字が含まれています",
                )
                return

            output_dir = FileManager.create_named_output_directory(
                self.current_category,
                self.current_subcategory,
                fixed_folder_name,
                use_common_output_folder=use_common_output_folder,
            )
        else:
            output_dir = FileManager.create_output_directory(
                self.current_category,
                self.current_subcategory,
                use_common_output_folder=use_common_output_folder,
            )
        if not output_dir:
            QMessageBox.critical(
                self.main_window,
                "エラー",
                "出力ディレクトリの作成に失敗しました",
            )
            return

        display_image = self.viewer_window.get_export_image(
            include_background=include_background,
            apply_mask=False,
        )

        if display_image is None:
            QMessageBox.warning(
                self.main_window,
                "注意",
                "出力できる画像がありません",
            )
            return

        if custom_filename:
            filename = FileManager.build_output_filename(custom_filename, output_format)
        else:
            filename = FileManager.get_next_filename(output_dir, output_format)
        output_path = os.path.join(output_dir, filename)

        if not ImageProcessor.save_image(display_image, output_path, output_format):
            QMessageBox.critical(
                self.main_window,
                "エラー",
                "画像の保存に失敗しました",
            )
            return

        message = f"画像を保存しました\n{output_path}"
        if export_mask:
            if custom_filename:
                alpha_filename = FileManager.get_custom_alpha_filename(filename)
            else:
                alpha_filename = FileManager.get_alpha_filename(filename)
            alpha_output_path = os.path.join(output_dir, alpha_filename)
            alpha_mask = self.viewer_window.get_effective_mask(include_background=False)
            if not ImageProcessor.save_mask_image(alpha_mask, alpha_output_path, output_format):
                QMessageBox.critical(
                    self.main_window,
                    "エラー",
                    f"Alphaマスク画像の保存に失敗しました\n{alpha_output_path}",
                )
                return
            message += f"\n\nAlphaマスク画像も保存しました\n{alpha_output_path}"

        self.portraiture_db.update_subcategory_output_settings(
            self.current_category,
            self.current_subcategory,
            use_common_output_folder=use_common_output_folder,
            use_fixed_output_folder=self.editor_window.should_use_fixed_output_folder(),
            output_folder_name=fixed_folder_name if self.editor_window.should_use_fixed_output_folder() else "",
            output_filename=custom_filename,
        )
        saved_settings = self.editor_window.get_export_settings()
        self.config_manager.save_last_used_output_settings(saved_settings)
        if self.editor_window.original_image_path:
            self.config_manager.add_recent_image(
                {
                    "image_path": self.editor_window.original_image_path,
                    **saved_settings,
                }
            )
            self.editor_window.set_recent_images(self.config_manager.get_recent_images())
        QMessageBox.information(self.main_window, "完了", message)

    def run(self):
        self.main_window.show()
        self.viewer_window.show()


def main():
    app = QApplication(sys.argv)
    custom_portrait_app = CustomPortraitApp()
    custom_portrait_app.run()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
