import json
import requests
from typing import List, Dict, Any, Callable
import inspect
import os
from dotenv import load_dotenv
import psycopg2

# .env 파일 로드
load_dotenv()


# 법령 검색 클래스
class LawSearcher:
    def __init__(self):
        self.search_results = []
        self.search_results_dict = {}
        self.current_index = 0
        self.last_query = None

    def search_laws(self, query: str) -> Dict[str, Any]:
        """질문에 관련된 법령들을 검색합니다. 호출할 때마다 다음 결과를 반환합니다."""
        # 새로운 쿼리인 경우 검색 수행
        if query != self.last_query:
            self.search_results = []
            self.search_results_dict = {}
            self.current_index = 0
            self.last_query = query

            # execute sql
            # SELECT ch2.id, ch2.text, ch2.meta, document.document_meta, paradedb.score(ch2.id) similarity
            # FROM document JOIN collection cl ON document.collection_id = cl.id join chunk ch2 on ch2.document_id = document.id join embedding_all ea on ea.chunk_id = ch2.id
            # WHERE cl.usage = 'rag' AND (cl.scenario->>'law_no_ordin' = 'Y')  AND (NOT document.collection_id = 4 AND document.document_meta->>'path' NOT ILIKE '/data/law/ordin/%') and keyword1='건축법' and ((text @@@ '경미 변경'))
            # ORDER BY paradedb.score(ch2.id) desc LIMIT 80;
            sql_query = f"""
            SELECT ch2.id, ch2.text, ch2.meta, document.document_meta, paradedb.score(ch2.id) similarity
            FROM document JOIN collection cl ON document.collection_id = cl.id join chunk ch2 on ch2.document_id = document.id join embedding_all ea on ea.chunk_id = ch2.id
            WHERE cl.usage = 'rag' AND (cl.scenario->>'law_no_ordin' = 'Y')  AND (NOT document.collection_id = 4 AND document.document_meta->>'path' NOT ILIKE '/data/law/ordin/%') and keyword1='건축법' and ((text @@@ '경미 변경'))
            ORDER BY paradedb.score(ch2.id) desc LIMIT 80;
            """
            try:
                db = psycopg2.connect(
                    host=os.getenv("POSTGRES_HOST"),
                    port=os.getenv("POSTGRES_PORT"),
                    database=os.getenv("POSTGRES_DB"),
                    user=os.getenv("POSTGRES_USER"),
                    password=os.getenv("POSTGRES_PASS"),
                )
                cursor = db.cursor()
                cursor.execute(sql_query)
                results = cursor.fetchall()
                for result in results:
                    self.search_results_dict[result[0]] = {
                        "id": result[0],
                        "text": result[1],
                        "meta": result[2],
                        "document_meta": result[3],
                    }
                cursor.close()
                db.close()
            except Exception as e:
                print(f"데이터베이스 연결 오류: {e}")
                return {"error": f"데이터베이스 연결 오류: {str(e)}"}

        # 검색 결과가 없는 경우
        if len(self.search_results_dict) == 0:
            return {"error": f"'{query}'에 대한 검색 결과가 없습니다."}

        # 리스트로 변환
        self.search_results = list(self.search_results_dict.values())

        # 현재 인덱스가 범위를 벗어난 경우
        if self.current_index >= len(self.search_results):
            return {"error": "더 이상 검색 결과가 없습니다."}

        # 현재 결과 반환
        result = self.search_results[self.current_index]
        self.current_index += 1

        return result


# 전역 LawSearcher 인스턴스
law_searcher = LawSearcher()


# 법령 검색 함수 (기존 함수를 래퍼로 변경)
def search_laws(query: str) -> Dict[str, Any]:
    """질문에 관련된 법령들을 검색합니다. 호출할 때마다 다음 결과를 반환합니다."""
    return law_searcher.search_laws(query)


# 법령 내용 충분성 검사 함수 (LLM 기반)
def check_law_sufficiency(law_content: str, user_question: str) -> str:
    """LLM을 사용하여 법령 내용이 사용자 질문에 답변하기에 충분한지 판단합니다."""
    # LLM을 사용하여 충분성 판단
    messages = [
        {
            "role": "system",
            "content": """당신은 법령 내용이 사용자의 질문에 답변하기에 충분한지 판단하는 전문가입니다.

판단 기준:
1. 법령 내용이 질문의 핵심 요구사항을 직접적으로 다루고 있는가?
2. 구체적인 조항, 정의, 기준, 절차 등이 명시되어 있는가?
3. 내용의 길이와 상세도가 적절한가?

답변 형식:
- "충분함": 법령 내용이 질문에 대한 완전한 답변을 제공할 수 있는 경우
- "부분적 충분함": 일부 답변은 가능하지만 추가 정보가 필요한 경우  
- "부족함": 법령 내용이 질문에 답변하기에 부족한 경우

간단하고 명확하게 판단 결과만 답변하세요.""",
        },
        {
            "role": "user",
            "content": f"""사용자 질문: {user_question}

법령 내용:
{law_content}

위 법령 내용이 사용자 질문에 답변하기에 충분한지 판단해주세요.""",
        },
    ]

    try:
        # SimpleToolCaller 인스턴스 생성 (LLM 호출용)
        load_dotenv()
        if USE_OPENAI:
            caller = SimpleToolCaller(os.getenv("OPENAI_API_KEY"))
        else:
            model = "Qwen/Qwen3-32B-AWQ"
            base_url = "https://5c86-109-61-127-28.ngrok-free.app/v1"
            api_key = "EMPTY"
            caller = SimpleToolCaller(api_key, base_url, model)

        # LLM 호출하여 충분성 판단
        response = caller.call_llm(messages)
        judgment = response["choices"][0]["message"]["content"]

        return f"충분성 판단 결과: {judgment}"

    except Exception as e:
        return f"충분성 판단 중 오류가 발생했습니다: {str(e)}"


# 관련 법령 찾기 및 검토 함수
def find_relevant_laws(user_question: str, max_search_count: int = 10) -> str:
    """주어진 질문과 관련된 법령을 찾고 하나씩 검토하여 관련된 법령을 추려냅니다."""

    relevant_laws = []
    insufficient_laws = []
    search_count = 0

    try:
        # 법령 검색 및 충분성 검사 반복
        while search_count < max_search_count:
            search_count += 1

            # 법령 검색
            law_result = search_laws(user_question)

            # 오류가 있는 경우
            if "error" in law_result:
                print(f"🔍 LAW SEARCH ERROR: {law_result['error']}")
                break

            print(
                "🔍 LAW RESULT(from search_laws)-->",
                law_result["document_meta"]["path"],
                law_result["meta"],
            )

            # 법령 내용 추출
            law_content = law_result.get("text", "")
            if not law_content:
                continue

            # 충분성 검사
            sufficiency_result = check_law_sufficiency(law_content, user_question)

            # 결과 분류
            if "충분함" in sufficiency_result:
                relevant_laws.append(
                    {
                        "content": law_content,
                        "result": law_result,
                        "sufficiency": sufficiency_result,
                    }
                )
            elif "부분적 충분함" in sufficiency_result:
                relevant_laws.append(
                    {
                        "content": law_content,
                        "result": law_result,
                        "sufficiency": sufficiency_result,
                    }
                )
            else:
                insufficient_laws.append(
                    {
                        "content": law_content,
                        "result": law_result,
                        "sufficiency": sufficiency_result,
                    }
                )

        # 결과 정리
        result_summary = f"""
=== 법령 검색 및 검토 결과 ===
검색한 법령 수: {search_count}개
충분한 법령 수: {len([law for law in relevant_laws if "충분함" in law["sufficiency"]])}개
부분적 충분한 법령 수: {len([law for law in relevant_laws if "부분적 충분함" in law["sufficiency"]])}개
부족한 법령 수: {len(insufficient_laws)}개

=== 충분한 법령들 ===
"""

        for i, law in enumerate(relevant_laws, 1):
            result_summary += f"""
법령 {i}:
text: {law["result"]["text"]}
meta: {law["result"]["meta"]}
path: {law["result"]["document_meta"]["path"]}
충분성: {law["sufficiency"]}
"""

        if insufficient_laws:
            result_summary += "\n=== 부족한 법령들 ===\n"
            for i, law in enumerate(insufficient_laws, 1):
                result_summary += f"""
법령 {i}:
text: {law["result"]["text"]}
meta: {law["result"]["meta"]}
path: {law["result"]["document_meta"]["path"]}
충분성: {law["sufficiency"]}
"""

        if not relevant_laws:
            result_summary += "\n⚠️ 충분한 법령을 찾지 못했습니다. 다른 키워드로 검색하거나 더 구체적인 질문을 해보세요."

        return result_summary

    except Exception as e:
        return f"법령 검색 및 검토 중 오류가 발생했습니다: {str(e)}"


def main():
    """메인 함수 - 예시 실행"""
    # .env 파일 로드
    load_dotenv()

    # SimpleToolCaller 인스턴스 생성
    if USE_OPENAI:
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
        # "건축법에서 정의하는 경미한 설계변경에 대해 알려줘",
        "건축법에서 대통령령으로 정하는 경미한 변경에 대해 알려줘",
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
