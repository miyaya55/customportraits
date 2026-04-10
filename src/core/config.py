"""設定管理モジュール"""

import json
import os
from pathlib import Path
from typing import Any, Dict, Optional


class ConfigManager:
    """アプリケーション設定管理"""

    def __init__(self, config_file: str):
        self.config_file = Path(config_file)
        self.config_file.parent.mkdir(parents=True, exist_ok=True)
        self.data: Dict[str, Any] = {}
        self.load()

    def load(self) -> None:
        """設定ファイルから読み込む"""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    self.data = json.load(f)
            except (json.JSONDecodeError, IOError):
                self.data = self._default_config()
        else:
            self.data = self._default_config()
        self._normalize_config()

    def save(self) -> None:
        """設定ファイルに保存"""
        self.config_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, indent=2, ensure_ascii=False)

    def get(self, key: str, default: Any = None) -> Any:
        """設定値を取得"""
        return self.data.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """設定値を設定"""
        self.data[key] = value
        self.save()

    def _default_config(self) -> Dict[str, Any]:
        """デフォルト設定を返す"""
        return {
            "output_format": "PNG",
            "include_background": True,
            "last_opened_category": None,
            "last_opened_subcategory": None,
            "last_used_output_settings": {
                "output_format": "PNG",
                "include_background": True,
                "use_common_output_folder": False,
                "use_fixed_output_folder": False,
                "output_folder_name": "",
                "output_filename": "",
            },
            "recent_images": [],
        }

    def get_last_used_output_settings(self) -> Dict[str, Any]:
        settings = self.data.get("last_used_output_settings", {})
        defaults = self._default_config()["last_used_output_settings"]
        merged = defaults.copy()
        merged.update(settings)
        return merged

    def save_last_used_output_settings(self, settings: Dict[str, Any]) -> None:
        merged = self.get_last_used_output_settings()
        merged.update(settings)
        self.data["last_used_output_settings"] = merged
        self.save()

    def get_recent_images(self) -> list:
        recent_images = self.data.get("recent_images", [])
        return recent_images if isinstance(recent_images, list) else []

    def add_recent_image(self, item: Dict[str, Any], limit: int = 10) -> None:
        image_path = item.get("image_path")
        if not image_path:
            return

        history_item = dict(item)
        history_item.pop("output_filename", None)

        recent_images = [
            existing for existing in self.get_recent_images()
            if existing.get("image_path") != image_path
        ]
        recent_images.insert(0, history_item)
        self.data["recent_images"] = recent_images[:limit]
        self.save()

    def _normalize_config(self) -> None:
        defaults = self._default_config()
        changed = False

        for key, value in defaults.items():
            if key not in self.data:
                self.data[key] = value
                changed = True

        if not isinstance(self.data.get("recent_images"), list):
            self.data["recent_images"] = []
            changed = True

        if not isinstance(self.data.get("last_used_output_settings"), dict):
            self.data["last_used_output_settings"] = defaults["last_used_output_settings"].copy()
            changed = True
        else:
            for key, value in defaults["last_used_output_settings"].items():
                if key not in self.data["last_used_output_settings"]:
                    self.data["last_used_output_settings"][key] = value
                    changed = True

        if changed:
            self.save()


class PortraitureDB:
    """ポートレートデータベース管理"""

    def __init__(self, db_file: str):
        self.db_file = Path(db_file)
        self.db_file.parent.mkdir(parents=True, exist_ok=True)
        self.data: Dict[str, Any] = {}
        self.load()

    def load(self) -> None:
        """データベースから読み込む"""
        if self.db_file.exists():
            try:
                with open(self.db_file, 'r', encoding='utf-8') as f:
                    self.data = json.load(f)
            except (json.JSONDecodeError, IOError):
                self.data = {"categories": []}
        else:
            self.data = {"categories": []}

    def save(self) -> None:
        """ファイルに保存"""
        self.db_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.db_file, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, indent=2, ensure_ascii=False)

    def add_category(self, name: str) -> bool:
        """カテゴリを追加"""
        if self._category_exists(name):
            return False
        self.data["categories"].append({
            "name": name,
            "subcategories": [],
        })
        self.save()
        return True

    def remove_category(self, name: str) -> bool:
        """カテゴリを削除"""
        self.data["categories"] = [
            c for c in self.data["categories"] if c["name"] != name
        ]
        self.save()
        return True

    def update_subcategory_background(self, category_name: str, subcategory_name: str, background_path: str) -> bool:
        """サブカテゴリの背景を更新"""
        for cat in self.data["categories"]:
            if cat["name"] == category_name:
                for subcat in cat["subcategories"]:
                    if subcat["name"] == subcategory_name:
                        subcat["background"] = background_path
                        self.save()
                        return True
        return False

    def add_subcategory(self, category_name: str, subcategory_name: str, background_path: Optional[str] = None) -> bool:
        """サブカテゴリを追加"""
        for cat in self.data["categories"]:
            if cat["name"] == category_name:
                if any(s["name"] == subcategory_name for s in cat["subcategories"]):
                    return False
                cat["subcategories"].append({
                    "name": subcategory_name,
                    "background": background_path,
                    "characters": [],
                })
                self.save()
                return True
        return False

    def remove_subcategory(self, category_name: str, subcategory_name: str) -> bool:
        """サブカテゴリを削除"""
        for cat in self.data["categories"]:
            if cat["name"] == category_name:
                cat["subcategories"] = [
                    s for s in cat["subcategories"] if s["name"] != subcategory_name
                ]
                self.save()
                return True
        return False

    def get_categories(self) -> list:
        """全カテゴリを取得"""
        return [c["name"] for c in self.data["categories"]]

    def get_category(self, name: str) -> Optional[Dict]:
        """カテゴリ情報を取得"""
        for cat in self.data["categories"]:
            if cat["name"] == name:
                return cat
        return None

    def get_subcategories(self, category_name: str) -> list:
        """カテゴリのサブカテゴリを取得"""
        cat = self.get_category(category_name)
        if cat:
            return [s["name"] for s in cat["subcategories"]]
        return []

    def get_subcategory(self, category_name: str, subcategory_name: str) -> Optional[Dict]:
        """サブカテゴリ情報を取得"""
        cat = self.get_category(category_name)
        if cat:
            for subcat in cat["subcategories"]:
                if subcat["name"] == subcategory_name:
                    return subcat
        return None

    def _category_exists(self, name: str) -> bool:
        """カテゴリが存在するか確認"""
        return any(c["name"] == name for c in self.data["categories"])
