import os
import re
import json
from PIL.Image import Image
from dotenv import load_dotenv
from google import genai
from google.genai import types
from pydantic import BaseModel, Field

load_dotenv()

# 구조화된 출력을 위한 Pydantic 스키마 정의
class ProblemAnalysis(BaseModel):
    thinking_process: str = Field(description="문제를 단계별로 상세히 풀이하고 검산하는 과정")
    answer: str = Field(description="최종 정답")
    confidence: str = Field(description="high, medium, low 중 하나")
    reason: str = Field(description="정답에 도달한 핵심 이유 1~2문장")
    ocr_warning: str = Field(description="잘못 인식했을 가능성이 있는 부분. 없으면 None")

SYSTEM_INSTRUCTION = """
너는 수능 및 대학 수준의 문제를 푸는 최상위 수학/CS 튜터다.
이미지의 문제를 분석할 때 반드시 다음 지침을 따라라.

1. Thinking Process (중요):
   - 곧바로 정답을 출력하지 마라.
   - 단계별로 연산하고, 풀이가 끝난 후 검산을 거쳐 최종 답을 도출하라.
2. 수식 표기:
   - LaTeX 기호($, \\ 등)를 절대 사용하지 마라.
   - 모든 수식은 일반 텍스트로 변환하여 작성하라.
"""

class GeminiService:
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY is not set in .env")
        
        self.client = genai.Client(api_key=self.api_key)

    def analyze_image(self, image: Image, model_name: str) -> dict:
        config = types.GenerateContentConfig(
            system_instruction=SYSTEM_INSTRUCTION,
            temperature=0.0, # 논리적/결정론적 추론을 위해 0.0 설정
            response_mime_type="application/json",
            response_schema=ProblemAnalysis,
        )

        try:
            chat = self.client.chats.create(model=model_name, config=config)
            response = chat.send_message(["이 문제를 정확히 풀어줘.", image])
            
            data = json.loads(response.text)
            
            # 수학 기호 2차 정제
            data["answer"] = self._clean_math_text(data.get("answer", ""))
            data["reason"] = self._clean_math_text(data.get("reason", ""))
            return data
            
        except Exception as e:
            return {
                "answer": "오류 발생",
                "confidence": "low",
                "reason": f"API 호출 실패: {str(e)}",
            }

    def _clean_math_text(self, text: str) -> str:
        text = re.sub(r'\$(.*?)\$', r'\1', text)
        text = text.replace('\\Wsum', '∑').replace('\\sum', '∑')
        text = text.replace('\\frac', '').replace('\\sqrt', '√')
        text = text.replace('\\', '')
        return text