"""ファイル操作モジュール"""

import re
from pathlib import Path
from typing import Optional


class FileManager:
    """ファイル操作クラス"""
    INVALID_NAME_CHARS = '<>:"/\\|?*'
    SERIAL_TOKENS = ("{連番}", "{n}", "{num}")
    SERIAL_PATTERN = re.compile(r"\[(0?)(\d+)\]")
    COMMON_FOLDER_NAME = "output"

    @staticmethod
    def get_next_output_folder(base_path: str) -> str:
        """
        出力フォルダの次の連番フォルダを取得
        existing: 001, 002 -> return 003
        """
        base_dir = Path(base_path)
        base_dir.mkdir(parents=True, exist_ok=True)
        
        # 既存フォルダの番号を取得
        existing_folders = [
            d.name for d in base_dir.iterdir()
            if d.is_dir() and d.name.isdigit()
        ]
        
        if not existing_folders:
            next_num = 1
        else:
            max_num = max(int(f) for f in existing_folders)
            next_num = max_num + 1
        
        return str(next_num).zfill(3)

    @staticmethod
    def create_output_directory(
        category: str,
        subcategory: str,
        use_common_output_folder: bool = False,
    ) -> Optional[str]:
        """
        出力ディレクトリを作成
        構造: customportrait/category/subcategory/001/
        """
        try:
            base_path = FileManager.get_output_base_path(
                category,
                subcategory,
                use_common_output_folder=use_common_output_folder,
            )
            next_folder = FileManager.get_next_output_folder(str(base_path))
            output_dir = base_path / next_folder
            output_dir.mkdir(parents=True, exist_ok=True)
            return str(output_dir)
        except Exception as e:
            print(f"ディレクトリ作成エラー: {e}")
            return None

    @staticmethod
    def create_named_output_directory(
        category: str,
        subcategory: str,
        folder_name: str,
        use_common_output_folder: bool = False,
    ) -> Optional[str]:
        """
        固定名の出力ディレクトリを作成
        構造: customportrait/category/subcategory/folder_name/
        """
        try:
            normalized_name = folder_name.strip()
            if not normalized_name:
                return None

            base_dir = FileManager.get_output_base_path(
                category,
                subcategory,
                use_common_output_folder=use_common_output_folder,
            )
            base_dir.mkdir(parents=True, exist_ok=True)

            output_name = FileManager.resolve_serial_folder_name(base_dir, normalized_name)
            output_dir = base_dir / output_name
            output_dir.mkdir(parents=True, exist_ok=True)
            return str(output_dir)
        except Exception as e:
            print(f"固定ディレクトリ作成エラー: {e}")
            return None

    @staticmethod
    def get_next_filename(output_dir: str, format: str = "PNG") -> str:
        """
        出力ファイルの次のファイル名を取得
        001.png, 002.png ...
        """
        output_path = Path(output_dir)
        ext = ".png" if format.upper() == "PNG" else ".bmp"
        
        existing_files = [
            f.name for f in output_path.glob(f"*{ext}")
        ]
        
        if not existing_files:
            next_num = 1
        else:
            # ファイル名から番号を抽出
            numbers = [
                int(f.replace(ext, ""))
                for f in existing_files
                if f.replace(ext, "").isdigit()
            ]
            next_num = max(numbers) + 1 if numbers else 1
        
        return f"{str(next_num).zfill(3)}{ext}"

    @staticmethod
    def is_valid_name(name: str) -> bool:
        """Windows で使えるフォルダ名 / ファイル名か確認"""
        normalized = name.strip()
        if not normalized:
            return False

        return not any(char in FileManager.INVALID_NAME_CHARS for char in normalized)

    @staticmethod
    def build_output_filename(base_name: str, format: str = "PNG") -> str:
        """指定名から出力ファイル名を生成"""
        ext = ".png" if format.upper() == "PNG" else ".bmp"
        return f"{base_name.strip()}{ext}"

    @staticmethod
    def get_output_base_path(
        category: str,
        subcategory: str,
        use_common_output_folder: bool = False,
    ) -> Path:
        """出力の基準フォルダを返す"""
        leaf = FileManager.COMMON_FOLDER_NAME if use_common_output_folder else subcategory
        return Path("customportrait") / category / leaf

    @staticmethod
    def resolve_serial_folder_name(base_dir: Path, folder_name: str) -> str:
        """連番トークンが含まれる場合は次のフォルダ名へ展開する"""
        match = FileManager.SERIAL_PATTERN.search(folder_name)
        if match:
            token = match.group(0)
            prefix, suffix = folder_name.split(token, 1)
            pad_char = match.group(1)
            width = max(1, int(match.group(2)))
        else:
            token = next((item for item in FileManager.SERIAL_TOKENS if item in folder_name), None)
            if token is None:
                return folder_name
            prefix, suffix = folder_name.split(token, 1)
            pad_char = "0"
            width = 3

        pattern = re.compile(rf"^{re.escape(prefix)}(\d+){re.escape(suffix)}$")
        next_number = 1

        for directory in base_dir.iterdir():
            if not directory.is_dir():
                continue

            match = pattern.match(directory.name)
            if match:
                next_number = max(next_number, int(match.group(1)) + 1)

        if pad_char == "0":
            serial = str(next_number).rjust(width, pad_char)
        else:
            serial = str(next_number)

        return f"{prefix}{serial}{suffix}"

    @staticmethod
    def validate_image_path(image_path: str) -> bool:
        """
        画像ファイルが存在するか確認
        """
        return Path(image_path).exists() and Path(image_path).is_file()

    @staticmethod
    def get_alpha_filename(filename: str) -> str:
        path = Path(filename)
        return f"{path.stem}_Alpha{path.suffix}"

    @staticmethod
    def get_custom_alpha_filename(filename: str) -> str:
        path = Path(filename)
        return f"{path.stem}Alpha{path.suffix}"
