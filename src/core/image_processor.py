"""画像処理モジュール"""

from pathlib import Path
from typing import Optional, Tuple
from collections import deque
from PIL import Image, ImageFilter
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
    def scale_image(
        image: Image.Image,
        scale_percent: float,
        resampling=Image.Resampling.LANCZOS,
    ) -> Image.Image:
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
        return image.resize(new_size, resampling)

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
    def save_mask_image(mask_image: Image.Image, output_path: str, format: str = "PNG") -> bool:
        try:
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            grayscale_mask = mask_image.convert("L")

            if format.upper() == "PNG":
                grayscale_mask.save(output_path, "PNG")
            elif format.upper() == "BMP":
                grayscale_mask.save(output_path, "BMP")
            else:
                return False

            return True
        except Exception as e:
            print(f"マスク画像の保存エラー: {e}")
            return False

    @staticmethod
    def fill_small_mask_holes(mask_image: Image.Image, max_hole_size: int = 64) -> Image.Image:
        """白地マスク内の小さな黒い穴を埋める。"""
        if max_hole_size <= 0:
            return mask_image.convert("L")

        mask = mask_image.convert("L")
        data = np.array(mask, dtype=np.uint8)
        black = data < 128
        height, width = black.shape
        visited = np.zeros_like(black, dtype=bool)

        for y in range(height):
            for x in range(width):
                if not black[y, x] or visited[y, x]:
                    continue

                queue = deque([(x, y)])
                component = []
                touches_border = False
                visited[y, x] = True

                while queue:
                    cx, cy = queue.popleft()
                    component.append((cx, cy))

                    if cx == 0 or cy == 0 or cx == width - 1 or cy == height - 1:
                        touches_border = True

                    for nx, ny in (
                        (cx - 1, cy),
                        (cx + 1, cy),
                        (cx, cy - 1),
                        (cx, cy + 1),
                    ):
                        if 0 <= nx < width and 0 <= ny < height:
                            if black[ny, nx] and not visited[ny, nx]:
                                visited[ny, nx] = True
                                queue.append((nx, ny))

                if not touches_border and len(component) <= max_hole_size:
                    for px, py in component:
                        data[py, px] = 255

        return Image.fromarray(data, "L")

    @staticmethod
    def expand_mask(mask_image: Image.Image, pixels: int = 0) -> Image.Image:
        """白地マスクを指定ピクセル分だけ膨張させる。"""
        if pixels <= 0:
            return mask_image.convert("L")

        mask = mask_image.convert("L")
        for _ in range(pixels):
            mask = mask.filter(ImageFilter.MaxFilter(3))
        return mask

    @staticmethod
    def refine_alpha_mask(
        mask_image: Image.Image,
        fill_small_holes: bool = True,
        hole_size_threshold: int = 64,
        expand_pixels: int = 0,
    ) -> Image.Image:
        """Alpha マスクの小穴埋めと膨張をまとめて適用する。"""
        refined = mask_image.convert("L")
        if fill_small_holes:
            refined = ImageProcessor.fill_small_mask_holes(
                refined,
                max_hole_size=hole_size_threshold,
            )
        if expand_pixels > 0:
            refined = ImageProcessor.expand_mask(refined, pixels=expand_pixels)
        return refined

    @staticmethod
    def get_image_size(image: Image.Image) -> Tuple[int, int]:
        """画像のサイズを取得"""
        return image.size

    @staticmethod
    def resize_to_fit(image: Image.Image, max_width: int, max_height: int) -> Image.Image:
        """画像を指定サイズ内に収まるようにリサイズ"""
        image.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)
        return image
