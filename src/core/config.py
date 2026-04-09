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
        }


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
