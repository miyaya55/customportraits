"""ファイル操作モジュール"""

from pathlib import Path
from typing import Optional


class FileManager:
    """ファイル操作クラス"""

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
    def create_output_directory(category: str, subcategory: str) -> Optional[str]:
        """
        出力ディレクトリを作成
        構造: customportrait/category/subcategory/001/
        """
        try:
            base_path = Path("customportrait") / category / subcategory
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
    ) -> Optional[str]:
        """
        固定名の出力ディレクトリを作成
        構造: customportrait/category/subcategory/folder_name/
        """
        try:
            normalized_name = folder_name.strip()
            if not normalized_name:
                return None

            output_dir = Path("customportrait") / category / subcategory / normalized_name
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
    def validate_image_path(image_path: str) -> bool:
        """
        画像ファイルが存在するか確認
        """
        return Path(image_path).exists() and Path(image_path).is_file()

    @staticmethod
    def get_alpha_filename(filename: str) -> str:
        path = Path(filename)
        return f"{path.stem}_Alpha{path.suffix}"
