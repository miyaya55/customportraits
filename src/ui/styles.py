"""UI スタイル定義"""

# スタイルシート
STYLESHEET = """
QMainWindow {
    background-color: #f0f0f0;
}

QGroupBox {
    border: 1px solid #cccccc;
    border-radius: 4px;
    margin-top: 8px;
    padding-top: 8px;
    font-weight: bold;
}

QGroupBox::title {
    subcontrol-origin: margin;
    left: 10px;
    padding: 0 3px 0 3px;
}

QPushButton {
    background-color: #0078d4;
    color: white;
    border: none;
    border-radius: 6px;
    padding: 10px 18px;
    font-size: 13px;
    font-weight: bold;
    min-height: 28px;
    min-width: 116px;
}

QPushButton:hover {
    background-color: #1084d7;
}

QPushButton:pressed {
    background-color: #005a9e;
}

QPushButton:disabled {
    background-color: #cccccc;
    color: #666666;
}

QPushButton[buttonRole="primary"] {
    background-color: #1f9d63;
}

QPushButton[buttonRole="primary"]:hover {
    background-color: #27ad70;
}

QPushButton[buttonRole="primary"]:pressed {
    background-color: #14784a;
}

QPushButton[buttonRole="primary"]:disabled {
    background-color: #b9d8c8;
    color: #f5f5f5;
}

QLineEdit, QSpinBox, QDoubleSpinBox {
    border: 1px solid #cccccc;
    border-radius: 4px;
    padding: 4px;
    background-color: white;
}

QComboBox {
    border: 1px solid #cccccc;
    border-radius: 4px;
    padding: 4px;
    background-color: white;
}

QListWidget {
    border: 1px solid #cccccc;
    border-radius: 4px;
    background-color: white;
}

QListWidget::item:selected {
    background-color: #0078d4;
    color: white;
}

QLabel {
    color: #333333;
}

QSlider::groove:horizontal {
    border: 1px solid #cccccc;
    height: 8px;
    background: white;
    border-radius: 4px;
}

QSlider::handle:horizontal {
    background: #0078d4;
    border: 1px solid #0078d4;
    width: 18px;
    margin: -5px 0;
    border-radius: 9px;
}

QSlider::handle:horizontal:hover {
    background: #1084d7;
}
"""

# カラーパレット
COLORS = {
    "primary": "#0078d4",
    "primary_hover": "#1084d7",
    "primary_active": "#005a9e",
    "background": "#f0f0f0",
    "border": "#cccccc",
    "text": "#333333",
    "white": "#ffffff",
}
