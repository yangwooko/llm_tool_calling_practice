import json
import requests
from typing import List, Dict, Any, Callable
import inspect
import os
from dotenv import load_dotenv
import psycopg2
from util_tool_call import SimpleToolCaller


def main():
    """메인 함수 - 예시 실행"""
    # .env 파일 로드
    load_dotenv()

    # SimpleToolCaller 인스턴스 생성
    if os.getenv("USE_OPENAI") == "True":
        caller = SimpleToolCaller(os.getenv("OPENAI_API_KEY"))
    else:
        model = "Qwen/Qwen3-32B-AWQ"
        base_url = "https://5c86-109-61-127-28.ngrok-free.app/v1"
        api_key = "EMPTY"
        caller = SimpleToolCaller(api_key, base_url, model)

    # 예시 질문들
    test_questions = [
        # "서울의 날씨는 어때?",
        # "2 + 3 * 4를 계산해줘",
        # "최신 AI 기술 동향에 대해 검색해줘",
        # "윤석열의 특검 조사에 대해 검색해서 결과를 요약해줘",
        # "부산 날씨와 10 + 5 계산을 해줘",
        "건축법에서 정의하는 경미한 변경에 대해 알려줘",
    ]

    print("=== LLM Tool Calling 예시 ===\n")

    for question in test_questions:
        print(f"질문: {question}")
        try:
            answer = caller.chat_with_tools(question)
            print(f"답변: {answer}")
        except Exception as e:
            print(f"오류: {e}")
        print("-" * 50)


if __name__ == "__main__":
    main()
