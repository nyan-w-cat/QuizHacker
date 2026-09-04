import os
import json
import imagehash
from PIL.Image import Image

# 1. Normalizer 임포트
from image_normalizer import ImageNormalizer

class CacheService:
    def __init__(self, cache_file="problem_cache.json", threshold=12):
        self.cache_file = cache_file
        self.threshold = threshold
        self.cache_data = self._load_cache()
        # 2. 인스턴스화
        self.normalizer = ImageNormalizer()

    def _load_cache(self) -> dict:
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                print(f"캐시 로드 실패: {e}")
                return {}
        return {}

    def _save_cache(self):
        with open(self.cache_file, "w", encoding="utf-8") as f:
            json.dump(self.cache_data, f, ensure_ascii=False, indent=2)

    def get_cached_result(self, image: Image, current_model: str) -> dict:
        # 3. 해시 계산 전 이미지를 크롭(정규화)합니다. ⚡
        normalized_img = self.normalizer.normalize_for_hash(image)
        current_hash = imagehash.phash(normalized_img)
        
        for stored_hash_str, result in self.cache_data.items():
            stored_hash = imagehash.hex_to_hash(stored_hash_str)
            
            if current_hash - stored_hash <= self.threshold:
                if result.get("model") == current_model:
                    return result 
                else:
                    return None 
                
        return None

    def save_result(self, image: Image, result: dict, current_model: str):
        # 4. 저장할 때도 정규화된 이미지의 해시를 키로 사용합니다. ⚡
        normalized_img = self.normalizer.normalize_for_hash(image)
        current_hash = imagehash.phash(normalized_img)
        
        result["model"] = current_model
        
        self.cache_data[str(current_hash)] = result
        self._save_cache()