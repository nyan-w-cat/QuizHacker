import sys
import keyboard
from PIL.Image import Image
from PySide6.QtWidgets import QApplication, QSystemTrayIcon, QMenu, QStyle, QInputDialog
from PySide6.QtCore import Qt, QThread, Signal, QObject
from PySide6.QtGui import QAction, QActionGroup

from capture_service import CaptureService
from gemini_service import GeminiService
from answer_panel import AnswerPanel
from cache_service import CacheService 

class HotkeySignal(QObject):
    triggered = Signal()

class ApiWorker(QThread):
    finished = Signal(dict)
    
    def __init__(self, image: Image, gemini_service: GeminiService, cache_service: CacheService, model_name: str):
        super().__init__()
        self.image = image
        self.gemini_service = gemini_service
        self.cache_service = cache_service
        self.model_name = model_name
        
    def run(self):
        try:
            # 1. Cache 조회
            cached_result = self.cache_service.get_cached_result(self.image, self.model_name)
            
            if cached_result:
                conf = cached_result.get('confidence', '')
                if "Cached ⚡" not in conf:
                    cached_result['confidence'] = f"{conf} / Cached ⚡"
                self.finished.emit(cached_result)
                return

            # 2. Cache Miss 시 API 호출
            result = self.gemini_service.analyze_image(self.image, self.model_name)
            
            # 3. 캐시에 저장
            if result.get("answer") != "오류 발생":
                self.cache_service.save_result(self.image, result, self.model_name)
                
            self.finished.emit(result)
            
        except Exception as e:
            # 🚨 스레드 내부 크래시 방지 및 원인 출력 로직
            import traceback
            error_details = traceback.format_exc()
            self.finished.emit({
                "answer": "시스템 에러 발생",
                "confidence": "low",
                "reason": f"백그라운드 스레드에서 오류가 발생했습니다:\n{str(e)}\n\n(주요 원인: imagehash/numpy/scipy 모듈 누락, 또는 JSON 파일 쓰기 권한 부족)"
            })

class StudyAssistantApp:
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.app.setQuitOnLastWindowClosed(False)
        
        self.capture_service = CaptureService()
        self.gemini_service = GeminiService()
        self.cache_service = CacheService()
        self.panel = AnswerPanel()
        
        self.display_mode = "full"
        self.current_model = "gemini-3.5-flash-lite" 
        
        self.setup_tray_icon()
        
        self.hotkey_signal = HotkeySignal()
        self.hotkey_signal.triggered.connect(self.on_hotkey_pressed)
        keyboard.add_hotkey('ctrl+alt+a', lambda: self.hotkey_signal.triggered.emit())
        
    def setup_tray_icon(self):
        self.tray_icon = QSystemTrayIcon(self.app)
        icon = self.app.style().standardIcon(QStyle.StandardPixmap.SP_ComputerIcon)
        self.tray_icon.setIcon(icon)
        
        menu = QMenu()
        
        # --- 1. 표시 모드 설정 ---
        display_menu = menu.addMenu("표시 모드")
        display_group = QActionGroup(display_menu)
        
        full_mode_action = QAction("정답 + 해설 표시", display_menu, checkable=True, checked=True)
        full_mode_action.triggered.connect(lambda: self.set_display_mode("full"))
        display_group.addAction(full_mode_action)
        
        answer_mode_action = QAction("정답만 표시", display_menu, checkable=True)
        answer_mode_action.triggered.connect(lambda: self.set_display_mode("answer_only"))
        display_group.addAction(answer_mode_action)
        
        display_menu.addAction(full_mode_action)
        display_menu.addAction(answer_mode_action)
        
        # --- 2. 테마 설정 (다크/라이트) ---
        theme_menu = menu.addMenu("테마 설정")
        theme_group = QActionGroup(theme_menu)
        
        dark_action = QAction("다크 모드 (기본)", theme_menu, checkable=True, checked=True)
        dark_action.triggered.connect(lambda: self.panel.set_theme("dark"))
        theme_group.addAction(dark_action)
        
        light_action = QAction("라이트 모드", theme_menu, checkable=True)
        light_action.triggered.connect(lambda: self.panel.set_theme("light"))
        theme_group.addAction(light_action)
        
        theme_menu.addActions([dark_action, light_action])
        
        # --- 3. 투명도 설정 ---
        opacity_menu = menu.addMenu("투명도 설정")
        opacity_group = QActionGroup(opacity_menu)
        
        op_100 = QAction("100% (불투명)", opacity_menu, checkable=True)
        op_100.triggered.connect(lambda: self.panel.set_opacity(1.0))
        opacity_group.addAction(op_100)
        
        op_75 = QAction("75% (기본)", opacity_menu, checkable=True, checked=True)
        op_75.triggered.connect(lambda: self.panel.set_opacity(0.75))
        opacity_group.addAction(op_75)
        
        op_50 = QAction("50%", opacity_menu, checkable=True)
        op_50.triggered.connect(lambda: self.panel.set_opacity(0.50))
        opacity_group.addAction(op_50)
        
        op_25 = QAction("25%", opacity_menu, checkable=True)
        op_25.triggered.connect(lambda: self.panel.set_opacity(0.25))
        opacity_group.addAction(op_25)
        
        op_0 = QAction("0% (완전 투명)", opacity_menu, checkable=True)
        op_0.triggered.connect(lambda: self.panel.set_opacity(0.0))
        opacity_group.addAction(op_0)
        
        opacity_menu.addActions([op_100, op_75, op_50, op_25, op_0])
        
        # --- 4. 자동 닫기 시간 설정 ---
        time_menu = menu.addMenu("자동 닫기 시간")
        time_group = QActionGroup(time_menu)
        
        t_1 = QAction("1초", time_menu, checkable=True)
        t_1.triggered.connect(lambda: self.panel.set_auto_close_time(1))
        time_group.addAction(t_1)
        
        t_3 = QAction("3초", time_menu, checkable=True)
        t_3.triggered.connect(lambda: self.panel.set_auto_close_time(3))
        time_group.addAction(t_3)
        
        t_5 = QAction("5초 (기본)", time_menu, checkable=True, checked=True)
        t_5.triggered.connect(lambda: self.panel.set_auto_close_time(5))
        time_group.addAction(t_5)
        
        t_inf = QAction("닫을 때까지 표시", time_menu, checkable=True)
        t_inf.triggered.connect(lambda: self.panel.set_auto_close_time(0))
        time_group.addAction(t_inf)
        
        time_menu.addActions([t_1, t_3, t_5, t_inf])
        
        # --- 5. AI 모델 선택 설정 ---
        model_menu = menu.addMenu("AI 모델 선택")
        model_group = QActionGroup(model_menu)
        
        lite_35_action = QAction("Gemini 3.5 Flash Lite (기본 / 500회)", model_menu, checkable=True, checked=True)
        lite_35_action.triggered.connect(lambda: self.set_model("gemini-3.5-flash-lite"))
        model_group.addAction(lite_35_action)
        
        lite_31_action = QAction("Gemini 3.1 Flash Lite (예비 / 500회)", model_menu, checkable=True)
        lite_31_action.triggered.connect(lambda: self.set_model("gemini-3.1-flash-lite"))
        model_group.addAction(lite_31_action)
        
        flash_38_action = QAction("Gemini 3.8 Flash (고성능 / 20회)", model_menu, checkable=True)
        flash_38_action.triggered.connect(lambda: self.set_model("gemini-3.8-flash"))
        model_group.addAction(flash_38_action)
        
        model_menu.addAction(lite_35_action)
        model_menu.addAction(lite_31_action)
        model_menu.addAction(flash_38_action)
        
        # --- 6. 종료 ---
        menu.addSeparator()
        exit_action = QAction("종료", menu)
        exit_action.triggered.connect(self.quit_app)
        menu.addAction(exit_action)
        
        self.tray_icon.setContextMenu(menu)
        self.tray_icon.show()

    def set_display_mode(self, mode: str):
        self.display_mode = mode
        
    def set_model(self, model_name: str):
        self.current_model = model_name

    def quit_app(self):
        self.tray_icon.hide()
        self.app.quit()

    def on_hotkey_pressed(self):
        # 1. 화면 캡처를 가장 먼저 실행 (UI 간섭 완벽 배제)
        screenshot = self.capture_service.capture_full_screen()
        
        # 2. 캡처가 끝난 후 로딩 패널 표시
        self.panel.show_loading(self.display_mode)
        
        # 3. 워커 스레드 시작
        self.worker = ApiWorker(screenshot, self.gemini_service, self.cache_service, self.current_model)
        self.worker.finished.connect(self.on_api_finished)
        self.worker.start()
        
    def on_api_finished(self, result: dict):
        self.panel.show_result(result, self.display_mode)
        self.worker.deleteLater()
        
    def run(self):
        sys.exit(self.app.exec())

if __name__ == "__main__":
    assistant = StudyAssistantApp()
    assistant.run()