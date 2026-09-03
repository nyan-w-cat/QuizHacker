from PIL import ImageGrab
from PIL.Image import Image

class CaptureService:
    def capture_full_screen(self) -> Image:
        """
        주 모니터의 전체 화면을 캡처하여 Pillow Image 객체로 반환.
        디스크 I/O 없이 메모리에만 적재함.
        """
        return ImageGrab.grab()