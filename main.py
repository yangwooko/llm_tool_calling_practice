import json
import requests
from typing import List, Dict, Any, Callable
import inspect
import os
from dotenv import load_dotenv
import psycopg2
from util_tool_call import SimpleToolCaller
from util_tools import get_weather, calculate_math, google_search
from util_law_search import find_relevant_laws

# 도구 정의
TOOLS = [
    # {
    #     "type": "function",
    #     "function": {
    #         "name": "find_relevant_laws",
    #         "description": "주어진 질문과 관련된 법령을 찾고 하나씩 검토하여 관련된 법령을 추려냅니다. search_laws와 check_law_sufficiency를 자동으로 연속 호출하여 최적의 법령들을 찾습니다.",
    #         "parameters": {
    #             "type": "object",
    #             "properties": {
    #                 "user_question": {
    #                     "type": "string",
    #                     "description": "검색할 사용자 질문",
    #                     "examples": [
    #                         "건축법에서 정의하는 경미한 설계변경에 대해 알려줘",
    #                     ],
    #                 },
    #                 "max_search_count": {
    #                     "type": "integer",
    #                     "description": "최대 검색할 법령 수 (기본값: 5)",
    #                     "default": 5,
    #                 },
    #             },
    #             "required": ["user_question"],
    #         },
    #     },
    # },
    {
        "type": "function",
        "function": {
            "name": "find_relevant_laws",
            "description": "주어진 질문과 관련된 법령을 찾고 하나씩 검토하여 관련된 법령을 추려냅니다.",
            "parameters": {
                "type": "object",
                "properties": {
                    "user_question": {
                        "type": "string",
                        "description": "검색할 사용자 질문",
                        "examples": [
                            "건축법에서 정의하는 경미한 설계변경에 대해 알려줘",
                        ],
                    },
                    "max_search_count": {
                        "type": "integer",
                        "description": "최대 검색할 법령 수 (기본값: 5)",
                        "default": 5,
                    },
                },
                "required": ["user_question"],
            },
        },
    },
    # {
    #     "type": "function",
    #     "function": {
    #         "name": "search_laws",
    #         "description": "질문에 관련된 법령을 검색하여 한번에 하나씩 리턴합니다. 같은 질문을 검색하면 검색 결과에서 다음 법령을 리턴합니다. 더 이상 검색 결과가 없으면 더 이상 검색 결과가 없습니다. 라고 리턴합니다.",
    #         "parameters": {
    #             "type": "object",
    #             "properties": {
    #                 "query": {
    #                     "type": "string",
    #                     "description": "검색할 질문",
    #                     "examples": [
    #                         "건축법에서 정의하는 경미한 설계변경에 대해 알려줘",
    #                     ],
    #                 }
    #             },
    #             "required": ["query"],
    #         },
    #     },
    # },
    # {
    #     "type": "function",
    #     "function": {
    #         "name": "check_law_sufficiency",
    #         "description": "LLM을 사용하여 법령 내용이 사용자 질문에 답변하기에 충분한지 판단합니다.",
    #         "parameters": {
    #             "type": "object",
    #             "properties": {
    #                 "law_content": {
    #                     "type": "string",
    #                     "description": "판단할 법령 내용",
    #                 },
    #                 "user_question": {
    #                     "type": "string",
    #                     "description": "사용자의 원래 질문",
    #                 },
    #             },
    #             "required": ["law_content", "user_question"],
    #         },
    #     },
    # },
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "도시의 날씨 정보를 반환합니다. 한국 도시명을 그대로 사용하세요 (예: 서울, 부산, 대구, 인천, 광주, 대전, 울산, 세종, 제주, 수원, 창원)",
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {
                        "type": "string",
                        "description": "날씨를 확인할 도시명 (한국어 도시명을 그대로 사용, 영어로 번역하지 마세요)",
                        "examples": [
                            "서울",
                            "부산",
                            "대구",
                            "인천",
                            "광주",
                            "대전",
                            "울산",
                            "세종",
                            "제주",
                            "수원",
                            "창원",
                        ],
                    }
                },
                "required": ["city"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "calculate_math",
            "description": "수학 표현식을 계산합니다",
            "parameters": {
                "type": "object",
                "properties": {
                    "expression": {
                        "type": "string",
                        "description": "계산할 수학 표현식 (예: 2+3*4)",
                    }
                },
                "required": ["expression"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "google_search",
            "description": "Google Custom Search API를 사용하여 웹 검색을 수행하고 검색 결과의 내용을 가져옵니다",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "검색할 쿼리"},
                    "num_results": {
                        "type": "integer",
                        "description": "가져올 검색 결과 수 (기본값: 2, 최대: 10)",
                        "default": 2,
                    },
                    "max_chars": {
                        "type": "integer",
                        "description": "각 페이지에서 가져올 최대 문자 수 (기본값: 500)",
                        "default": 500,
                    },
                },
                "required": ["query"],
            },
        },
    },
]

# 도구 함수 매핑
TOOL_FUNCTIONS = {
    "get_weather": get_weather,
    "calculate_math": calculate_math,
    "google_search": google_search,
    # "search_laws": search_laws,
    # "check_law_sufficiency": check_law_sufficiency,
    "find_relevant_laws": find_relevant_laws,
}


def main():
    """메인 함수 - 예시 실행"""
    # .env 파일 로드
    load_dotenv()

    # SimpleToolCaller 인스턴스 생성
    caller = SimpleToolCaller(TOOLS, TOOL_FUNCTIONS)

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
            answer = caller.chat(
                [
                    {"role": "user", "content": question},
                ],
                with_tools=True,
            )
            print(f"답변: {answer}")
        except Exception as e:
            print(f"오류: {e}")
        print("-" * 50)


if __name__ == "__main__":
    main()
