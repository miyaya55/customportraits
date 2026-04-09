"""アプリケーション定数定義"""

# アプリケーション設定
APP_NAME = "Custom Portrait Tool"
APP_VERSION = "1.0.0"

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
