"""カテゴリ・サブカテゴリ情報の保存処理。"""

import json
from pathlib import Path
from typing import Any, Dict, Optional


class PortraitureDB:
    """カテゴリとサブカテゴリの保存処理を扱う。"""

    def __init__(self, db_file: str):
        self.db_file = Path(db_file)
        self.db_file.parent.mkdir(parents=True, exist_ok=True)
        self.data: Dict[str, Any] = {}
        self.load()

    def load(self) -> None:
        """保存ファイルを読み込む。"""
        if self.db_file.exists():
            try:
                with open(self.db_file, "r", encoding="utf-8") as file:
                    self.data = json.load(file)
            except (json.JSONDecodeError, IOError):
                self.data = {"categories": []}
        else:
            self.data = {"categories": []}
        self._normalize_data()

    def save(self) -> None:
        """保存ファイルへ書き込む。"""
        self.db_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.db_file, "w", encoding="utf-8") as file:
            json.dump(self.data, file, indent=2, ensure_ascii=False)

    def add_category(self, name: str) -> bool:
        """カテゴリを追加する。"""
        if self._category_exists(name):
            return False
        self.data["categories"].append(
            {
                "name": name,
                "subcategories": [],
            }
        )
        self.save()
        return True

    def remove_category(self, name: str) -> bool:
        """カテゴリを削除する。"""
        self.data["categories"] = [
            category for category in self.data["categories"] if category["name"] != name
        ]
        self.save()
        return True

    def update_subcategory_background(
        self,
        category_name: str,
        subcategory_name: str,
        background_path: Optional[str],
    ) -> bool:
        """サブカテゴリの背景画像を更新する。"""
        subcategory = self.get_subcategory(category_name, subcategory_name)
        if subcategory is None:
            return False
        subcategory["background"] = background_path
        self.save()
        return True

    def update_subcategory_guide_image(
        self,
        category_name: str,
        subcategory_name: str,
        guide_image_path: Optional[str],
    ) -> bool:
        """サブカテゴリの位置ガイド画像を更新する。"""
        subcategory = self.get_subcategory(category_name, subcategory_name)
        if subcategory is None:
            return False
        subcategory["guide_image"] = guide_image_path
        self.save()
        return True

    def add_subcategory(
        self,
        category_name: str,
        subcategory_name: str,
        background_path: Optional[str] = None,
        guide_image_path: Optional[str] = None,
    ) -> bool:
        """サブカテゴリを追加する。"""
        category = self.get_category(category_name)
        if category is None:
            return False
        if any(item["name"] == subcategory_name for item in category["subcategories"]):
            return False

        category["subcategories"].append(
            {
                "name": subcategory_name,
                "background": background_path,
                "guide_image": guide_image_path,
                "characters": [],
            }
        )
        self.save()
        return True

    def remove_subcategory(self, category_name: str, subcategory_name: str) -> bool:
        """サブカテゴリを削除する。"""
        category = self.get_category(category_name)
        if category is None:
            return False

        category["subcategories"] = [
            item for item in category["subcategories"] if item["name"] != subcategory_name
        ]
        self.save()
        return True

    def get_categories(self) -> list:
        """カテゴリ名一覧を返す。"""
        return [category["name"] for category in self.data["categories"]]

    def get_category(self, name: str) -> Optional[Dict]:
        """カテゴリ情報を返す。"""
        for category in self.data["categories"]:
            if category["name"] == name:
                return category
        return None

    def get_subcategories(self, category_name: str) -> list:
        """カテゴリ配下のサブカテゴリ名一覧を返す。"""
        category = self.get_category(category_name)
        if category:
            return [subcategory["name"] for subcategory in category["subcategories"]]
        return []

    def get_subcategory(self, category_name: str, subcategory_name: str) -> Optional[Dict]:
        """サブカテゴリ情報を返す。"""
        category = self.get_category(category_name)
        if category:
            for subcategory in category["subcategories"]:
                if subcategory["name"] == subcategory_name:
                    return subcategory
        return None

    def _category_exists(self, name: str) -> bool:
        """カテゴリが既に存在するか判定する。"""
        return any(category["name"] == name for category in self.data["categories"])

    def _normalize_data(self) -> None:
        """古い保存データへ不足キーを補う。"""
        categories = self.data.setdefault("categories", [])
        changed = False

        for category in categories:
            subcategories = category.setdefault("subcategories", [])
            for subcategory in subcategories:
                if "background" not in subcategory:
                    subcategory["background"] = None
                    changed = True
                if "guide_image" not in subcategory:
                    subcategory["guide_image"] = None
                    changed = True
                if "characters" not in subcategory:
                    subcategory["characters"] = []
                    changed = True

        if changed:
            self.save()
