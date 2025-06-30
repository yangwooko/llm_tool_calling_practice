import json
import requests
from typing import List, Dict, Any, Callable
import inspect
import os
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()


# 간단한 도구 함수들
def get_weather(city: str) -> str:
    """도시의 날씨 정보를 반환합니다."""
    print(">" * 100)
    print("get_weather", city)
    print("<" * 100)
    # 실제로는 날씨 API를 호출하지만, 여기서는 시뮬레이션
    weather_data = {
        # 한국어 도시명
        "서울": "맑음, 22°C",
        "부산": "흐림, 18°C",
        "대구": "비, 15°C",
        "인천": "맑음, 20°C",
        "광주": "구름 많음, 19°C",
        "대전": "맑음, 21°C",
        "울산": "흐림, 17°C",
        "세종": "맑음, 23°C",
        "제주": "맑음, 25°C",
        "수원": "구름 많음, 20°C",
        "창원": "맑음, 19°C",
    }

    # 도시명 정규화 (공백 제거, 소문자 변환)
    normalized_city = city.strip()

    result = weather_data.get(
        normalized_city, f"{normalized_city}의 날씨 정보를 찾을 수 없습니다."
    )
    print(f"도시: {normalized_city} -> 결과: {result}")
    return result


def calculate_math(expression: str) -> str:
    """수학 표현식을 계산합니다."""
    print(">" * 100)
    print("calculate_math", expression)
    print("<" * 100)
    try:
        # 안전한 계산을 위해 제한된 연산만 허용
        allowed_chars = set("0123456789+-*/(). ")
        if not all(c in allowed_chars for c in expression):
            return "안전하지 않은 표현식입니다."

        result = eval(expression)
        return f"{expression} = {result}"
    except Exception as e:
        return f"계산 오류: {str(e)}"


# def search_web(query: str) -> str:
#     """웹 검색을 시뮬레이션합니다."""
#     print(">" * 100)
#     print("search_web", query)
#     print("<" * 100)
#     return f"'{query}'에 대한 검색 결과: 이것은 시뮬레이션된 검색 결과입니다."


def google_search(query: str, num_results: int = 2, max_chars: int = 500) -> str:  # type: ignore[type-arg]
    import os
    import time

    import requests
    from bs4 import BeautifulSoup
    from dotenv import load_dotenv

    print(">" * 100)
    print("google_search", query, num_results, max_chars)
    print("<" * 100)

    load_dotenv()

    api_key = os.getenv("GOOGLE_API_KEY")
    search_engine_id = os.getenv("GOOGLE_SEARCH_ENGINE_ID")

    if not api_key or not search_engine_id:
        return "오류: GOOGLE_API_KEY 또는 GOOGLE_SEARCH_ENGINE_ID 환경변수가 설정되지 않았습니다."

    url = "https://customsearch.googleapis.com/customsearch/v1"
    params = {
        "key": str(api_key),
        "cx": str(search_engine_id),
        "q": str(query),
        "num": str(num_results),
    }

    response = requests.get(url, params=params)

    if response.status_code != 200:
        print(response.json())
        return f"API 요청 오류: {response.status_code}"

    results = response.json().get("items", [])

    def get_page_content(url: str) -> str:
        try:
            response = requests.get(url, timeout=10)
            soup = BeautifulSoup(response.content, "html.parser")
            text = soup.get_text(separator=" ", strip=True)
            words = text.split()
            content = ""
            for word in words:
                if len(content) + len(word) + 1 > max_chars:
                    break
                content += " " + word
            return content.strip()
        except Exception as e:
            print(f"Error fetching {url}: {str(e)}")
            return ""

    enriched_results = []
    for item in results:
        body = get_page_content(item["link"])
        enriched_results.append(
            {
                "title": item["title"],
                "link": item["link"],
                "snippet": item["snippet"],
                "body": body,
            }
        )
        time.sleep(1)  # Be respectful to the servers

    # 결과를 문자열로 포맷팅
    if not enriched_results:
        return f"'{query}'에 대한 검색 결과가 없습니다."

    formatted_results = []
    for i, result in enumerate(enriched_results, 1):
        formatted_result = f"""
검색 결과 {i}:
제목: {result['title']}
링크: {result['link']}
요약: {result['snippet']}
내용: {result['body'][:200]}...
"""
        formatted_results.append(formatted_result)

    return "\n".join(formatted_results)


# 도구 정의
TOOLS = [
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
}


class SimpleToolCaller:
    def __init__(self, api_key: str, base_url: str = "https://api.openai.com/v1"):
        self.api_key = api_key
        self.base_url = base_url
        self.model = "gpt-3.5-turbo"

    def call_llm(self, messages: List[Dict], tools: List[Dict] = None) -> Dict:
        """LLM API를 호출합니다."""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        data = {"model": self.model, "messages": messages, "temperature": 0.7}

        if tools:
            data["tools"] = tools

        response = requests.post(
            f"{self.base_url}/chat/completions", headers=headers, json=data
        )

        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"API 호출 실패: {response.status_code} - {response.text}")

    def execute_tool(self, tool_call: Dict) -> str:
        """도구를 실행합니다."""
        function_name = tool_call["function"]["name"]
        arguments = json.loads(tool_call["function"]["arguments"])

        if function_name in TOOL_FUNCTIONS:
            func = TOOL_FUNCTIONS[function_name]
            return func(**arguments)
        else:
            return f"알 수 없는 도구: {function_name}"

    def chat_with_tools(self, user_message: str) -> str:
        """도구를 사용하여 대화합니다."""
        messages = [
            {
                "role": "system",
                "content": "당신은 도구를 사용할 수 있는 AI 어시스턴트입니다. 필요할 때 적절한 도구를 사용하세요. 날씨 정보를 요청할 때는 한국어 도시명을 그대로 사용하고 영어로 번역하지 마세요.",
            },
            {"role": "user", "content": user_message},
        ]

        # 첫 번째 LLM 호출
        response = self.call_llm(messages, TOOLS)
        assistant_message = response["choices"][0]["message"]
        messages.append(assistant_message)

        # 도구 호출이 있는지 확인
        if assistant_message.get("tool_calls"):
            for tool_call in assistant_message["tool_calls"]:
                # 도구 실행
                tool_result = self.execute_tool(tool_call)

                # 도구 결과를 메시지에 추가
                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tool_call["id"],
                        "content": tool_result,
                    }
                )

            # 도구 결과를 받은 후 두 번째 LLM 호출
            final_response = self.call_llm(messages)
            return final_response["choices"][0]["message"]["content"]
        else:
            return assistant_message["content"]


def main():
    """메인 함수 - 예시 실행"""
    # API 키를 환경변수에서 가져오기
    api_key = os.getenv("OPENAI_API_KEY")

    if not api_key:
        print("오류: OPENAI_API_KEY 환경변수가 설정되지 않았습니다.")
        print("사용법: .env 파일에 OPENAI_API_KEY=your-api-key를 추가하세요.")
        return

    # Google 검색 API 키 확인
    google_api_key = os.getenv("GOOGLE_API_KEY")
    google_search_engine_id = os.getenv("GOOGLE_SEARCH_ENGINE_ID")

    if not google_api_key or not google_search_engine_id:
        print(
            "경고: GOOGLE_API_KEY 또는 GOOGLE_SEARCH_ENGINE_ID가 설정되지 않았습니다."
        )
        print("Google 검색 기능을 사용하려면 .env 파일에 다음을 추가하세요:")
        print("GOOGLE_API_KEY=your-google-api-key")
        print("GOOGLE_SEARCH_ENGINE_ID=your-search-engine-id")

    # SimpleToolCaller 인스턴스 생성
    caller = SimpleToolCaller(api_key)

    # 예시 질문들
    test_questions = [
        "서울의 날씨는 어때?",
        "2 + 3 * 4를 계산해줘",
        "최신 AI 기술 동향에 대해 검색해줘",
        "부산 날씨와 10 + 5 계산을 해줘",
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
