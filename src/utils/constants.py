"""アプリケーション定数定義"""

from pathlib import Path


def _load_app_version() -> str:
    """Read the release version from the repository root."""
    version_file = Path(__file__).resolve().parents[2] / "VERSION"
    if version_file.exists():
        version_text = version_file.read_text(encoding="utf-8").strip()
        if version_text:
            return version_text
    return "1.0.0"


# アプリケーション設定
APP_NAME = "Custom Portrait Tool"
APP_VERSION = _load_app_version()

# ファイル形式
SUPPORTED_IMAGE_FORMATS = {
    "PNG": ("*.png", "PNG Image", ".png"),
    "BMP": ("*.bmp", "Bitmap Image", ".bmp"),
    "JPEG": ("*.jpg *.jpeg", "JPEG Image", ".jpg"),
}

OUTPUT_FORMATS = ["PNG", "BMP"]

# ウィンドウサイズ
MAIN_WINDOW_WIDTH = 1200
MAIN_WINDOW_HEIGHT = 800
EDITOR_WINDOW_WIDTH = 1000
EDITOR_WINDOW_HEIGHT = 750
VIEWER_WINDOW_WIDTH = 800
VIEWER_WINDOW_HEIGHT = 600

# デフォルト設定
DEFAULT_OUTPUT_FORMAT = "PNG"
DEFAULT_BACKGROUND_ALPHA = True

# ファイルパス
CONFIG_FILE = "data/config.json"
PORTRAITURE_DB_FILE = "data/portraiture.json"

# 画像処理
MAX_IMAGE_SIZE = (4096, 4096)
MIN_IMAGE_SIZE = (100, 100)
