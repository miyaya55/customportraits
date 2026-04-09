"""画像処理モジュール"""

from pathlib import Path
from typing import Optional, Tuple
from PIL import Image
import numpy as np


class ImageProcessor:
    """画像処理クラス"""

    @staticmethod
    def load_image(image_path: str) -> Optional[Image.Image]:
        """画像ファイルを読み込む"""
        try:
            return Image.open(image_path).convert("RGBA")
        except Exception as e:
            print(f"画像の読み込みエラー: {e}")
            return None

    @staticmethod
    def crop_image(image: Image.Image, box: Tuple[int, int, int, int]) -> Image.Image:
        """
        画像を指定した範囲で切り抜く
        box: (left, top, right, bottom)
        """
        return image.crop(box)

    @staticmethod
    def scale_image(image: Image.Image, scale_percent: float) -> Image.Image:
        """
        画像を拡大・縮小する
        scale_percent: 100%を基準（100=等倍、200=2倍など）
        """
        if scale_percent <= 0:
            return image
        
        scale_factor = scale_percent / 100.0
        new_size = (
            int(image.width * scale_factor),
            int(image.height * scale_factor),
        )
        return image.resize(new_size, Image.Resampling.LANCZOS)

    @staticmethod
    def flip_horizontal(image: Image.Image) -> Image.Image:
        """画像を左右反転"""
        return image.transpose(Image.Transpose.FLIP_LEFT_RIGHT)

    @staticmethod
    def remove_background_by_color(
        image: Image.Image, color: Tuple[int, int, int], tolerance: int = 10
    ) -> Image.Image:
        """
        指定した色の背景を透過する
        color: (R, G, B)
        tolerance: 色の許容範囲
        """
        if image.mode != "RGBA":
            image = image.convert("RGBA")
        
        data = np.array(image)
        r, g, b = color
        
        # 色の範囲内ピクセルを透明化
        mask = (
            (np.abs(data[:, :, 0] - r) <= tolerance) &
            (np.abs(data[:, :, 1] - g) <= tolerance) &
            (np.abs(data[:, :, 2] - b) <= tolerance)
        )
        
        data[mask, 3] = 0  # アルファチャンネルを0にする
        return Image.fromarray(data, "RGBA")

    @staticmethod
    def composite_images(
        background: Image.Image, character: Image.Image, position: Tuple[int, int]
    ) -> Image.Image:
        """
        キャラクター画像を背景の上に合成
        position: (x, y) キャラクターの左上座標
        """
        if background.mode != "RGBA":
            background = background.convert("RGBA")
        if character.mode != "RGBA":
            character = character.convert("RGBA")
        
        result = background.copy()
        result.paste(character, position, character)
        return result

    @staticmethod
    def save_image(image: Image.Image, output_path: str, format: str = "PNG") -> bool:
        """
        画像を保存
        format: "PNG" or "BMP"
        """
        try:
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            
            if format.upper() == "PNG":
                image.save(output_path, "PNG")
            elif format.upper() == "BMP":
                # BMPは透明度をサポートしないため、背景が白の画像に変換
                if image.mode == "RGBA":
                    rgb_image = Image.new("RGB", image.size, (255, 255, 255))
                    rgb_image.paste(image, mask=image.split()[3])
                    rgb_image.save(output_path, "BMP")
                else:
                    image.save(output_path, "BMP")
            else:
                return False
            
            return True
        except Exception as e:
            print(f"画像の保存エラー: {e}")
            return False

    @staticmethod
    def get_image_size(image: Image.Image) -> Tuple[int, int]:
        """画像のサイズを取得"""
        return image.size

    @staticmethod
    def resize_to_fit(image: Image.Image, max_width: int, max_height: int) -> Image.Image:
        """画像を指定サイズ内に収まるようにリサイズ"""
        image.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)
        return image
