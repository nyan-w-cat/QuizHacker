import cv2
import numpy as np
from PIL import Image

class ImageNormalizer:
    def normalize_for_hash(self, pil_image: Image) -> Image:
        """
        다크모드/라이트모드 배경을 무시하고 콘텐츠(문제) 영역만 크롭하여 반환합니다.
        (OpenCV C++ 연산으로 사무용 노트북에서도 0.05초 이내에 처리됨)
        """
        # 1. PIL 이미지를 OpenCV 배열(Numpy)로 변환 및 흑백 처리
        cv_image = np.array(pil_image.convert('RGB'))
        gray = cv2.cvtColor(cv_image, cv2.COLOR_RGB2GRAY)
        
        # 2. Canny 엣지 검출 (색상이 아니라 픽셀의 '변화'를 감지)
        # 배경이 까맣든 하얗든 글자와 도형의 윤곽선만 하얗게 따냅니다.
        edges = cv2.Canny(gray, 50, 150)
        
        # 3. 윤곽선이 존재하는 모든 픽셀의 좌표 찾기
        coords = cv2.findNonZero(edges)
        
        # 4. 콘텐츠가 있는 영역만 바운딩 박스로 크롭
        if coords is not None:
            x, y, w, h = cv2.boundingRect(coords)
            
            # 너무 작은 영역이 잡히는 것을 방지 (노이즈 필터링)
            if w > 100 and h > 100:
                cropped = cv_image[y:y+h, x:x+w]
                return Image.fromarray(cropped)
                
        # 엣지를 못 찾았거나 너무 작으면 원본 반환
        return pil_image