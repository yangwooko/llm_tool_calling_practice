import json
import requests
from typing import List, Dict, Any, Callable
import inspect
import os
from util_tool_call import SimpleToolCaller


# 간단한 도구 함수들
def get_weather(city: str) -> str:
    """도시의 날씨 정보를 반환합니다."""
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
    # print(f"도시: {normalized_city} -> 결과: {result}")
    return result


def calculate_math(expression: str) -> str:
    """수학 표현식을 계산합니다."""
    try:
        # 안전한 계산을 위해 제한된 연산만 허용
        allowed_chars = set("0123456789+-*/(). ")
        if not all(c in allowed_chars for c in expression):
            return "안전하지 않은 표현식입니다."

        result = eval(expression)
        return f"{expression} = {result}"
    except Exception as e:
        return f"계산 오류: {str(e)}"


def google_search(query: str, num_results: int = 2, max_chars: int = 500) -> str:  # type: ignore[type-arg]
    import os
    import time

    import requests
    from bs4 import BeautifulSoup
    from dotenv import load_dotenv

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
