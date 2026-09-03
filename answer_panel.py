from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QHBoxLayout, QFrame
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QScreen

class AnswerPanel(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint | 
            Qt.WindowType.WindowStaysOnTopHint | 
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setFixedSize(420, 160)
        self.setStyleSheet("background: transparent;")
        
        self.current_alpha_ratio = 0.75 
        self.auto_close_seconds = 5 
        self.current_theme = "dark" # 기본 다크 모드
        
        self.init_ui()
        self.position_bottom_right()
        
        self.auto_close_timer = QTimer(self)
        self.auto_close_timer.timeout.connect(self.hide)
        
    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        self.container = QFrame(self)
        self.container.setObjectName("Container")
        
        layout = QVBoxLayout(self.container)
        layout.setContentsMargins(15, 15, 15, 15)
        
        self.status_label = QLabel("Ready")
        self.status_label.setStyleSheet("font-weight: bold; font-size: 15px; background: transparent;")
        
        self.reason_label = QLabel("대기 중...")
        self.reason_label.setWordWrap(True)
        self.reason_label.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.reason_label.setStyleSheet("background: transparent;")
        
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        self.close_btn = QPushButton("Close (Esc)")
        self.close_btn.clicked.connect(self.hide)
        btn_layout.addWidget(self.close_btn)
        
        layout.addWidget(self.status_label)
        layout.addWidget(self.reason_label)
        layout.addLayout(btn_layout)
        
        main_layout.addWidget(self.container)
        
        # 초기 스타일 적용
        self.update_container_style()

    def update_container_style(self):
        alpha_int = int(255 * self.current_alpha_ratio)
        
        if self.current_theme == "dark":
            bg_color = f"rgba(45, 45, 48, {alpha_int})"
            border_color = f"rgba(85, 85, 85, {alpha_int})"
            text_color = "#FFFFFF"
            status_color = "#4DAAFB"
            btn_bg = "rgba(68, 68, 68, 200)"
            btn_hover = "rgba(100, 100, 100, 200)"
            btn_text = "#FFFFFF"
        else: # light 모드
            bg_color = f"rgba(245, 245, 247, {alpha_int})"
            border_color = f"rgba(200, 200, 204, {alpha_int})"
            text_color = "#222222"
            status_color = "#0066CC"
            btn_bg = "rgba(220, 220, 224, 200)"
            btn_hover = "rgba(200, 200, 204, 200)"
            btn_text = "#222222"

        self.container.setStyleSheet(f"""
            QFrame#Container {{
                background-color: {bg_color};
                border-radius: 10px;
                border: 1px solid {border_color};
            }}
            QLabel {{
                color: {text_color};
                font-family: 'Malgun Gothic', 'Segoe UI', sans-serif;
                background: transparent;
            }}
        """)
        
        self.status_label.setStyleSheet(f"font-weight: bold; font-size: 15px; color: {status_color}; background: transparent;")
        
        self.close_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {btn_bg}; 
                color: {btn_text};
                padding: 4px 10px; 
                border-radius: 4px;
                border: none;
            }}
            QPushButton:hover {{ background-color: {btn_hover}; }}
        """)
        
        self.container.style().unpolish(self.container)
        self.container.style().polish(self.container)

    def set_opacity(self, ratio: float):
        self.current_alpha_ratio = ratio
        self.update_container_style()

    def set_theme(self, theme_name: str):
        """테마 설정 ('dark' 또는 'light')"""
        self.current_theme = theme_name
        self.update_container_style()

    def set_auto_close_time(self, seconds: int):
        self.auto_close_seconds = seconds

    def position_bottom_right(self):
        screen = QScreen.availableGeometry(self.screen())
        self.move(screen.width() - self.width() - 20, screen.height() - self.height() - 20)

    def show_result(self, result: dict, mode: str):
        ans = result.get('answer', 'N/A')
        conf = result.get('confidence', '')
        
        self.status_label.setText(f"정답: {ans} ({conf})")
        
        if mode == "full":
            self.reason_label.setText(result.get('reason', ''))
            self.reason_label.show()
        else:
            self.reason_label.hide()
            
        self.show()
        if self.auto_close_seconds > 0:
            self.auto_close_timer.start(self.auto_close_seconds * 1000)
        else:
            self.auto_close_timer.stop()

    def show_loading(self, mode: str):
        self.status_label.setText("분석 중...")
        if mode == "full":
            self.reason_label.setText("API 요청 및 수학적 추론을 진행하고 있습니다.")
            self.reason_label.show()
        else:
            self.reason_label.hide()
            
        self.show()
        self.auto_close_timer.stop()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self.hide()