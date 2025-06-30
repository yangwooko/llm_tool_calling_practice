import json
import requests
from typing import List, Dict, Any, Callable
import inspect
import os
from dotenv import load_dotenv
import psycopg2
from util_tool_call import SimpleToolCaller
import re

# .env 파일 로드
load_dotenv()


# 법령 검색 클래스
class LawSearcher:
    def __init__(self):
        self.search_results = []
        self.search_results_dict = {}
        self.current_index = 0
        self.last_query = None

    def extract_first_number(self, text):
        if text == "조항 번호 없음":
            return None

        # 특정 문자열 패턴을 먼저 찾음 (예: "별표" 또는 "부칙"으로 시작하는 경우)
        special_pattern = r"^(별표|별지|부칙)\d+"
        special_match = re.match(special_pattern, text)

        # 특정 문자열 패턴에 매칭되면 해당 문자열 반환
        if special_match:
            return special_match.group()

        # 일반 숫자만 추출하는 패턴
        match = re.search(r"\d+", text)
        if match:
            return match.group()

        # 아무것도 매칭되지 않으면 None 반환
        return None

    def parse_law_results(self, text):
        # 맨 앞에 법률과 조항: 이 있으면 무시
        text = text.split("법률과 조항:")[1].strip()
        # 앞에 \n 등이 있으면 제거
        text = text.lstrip("\n")
        print("🔍 TEXT-->", text)
        # 정규 표현식을 사용하여 법률명과 조항 번호 추출
        pattern = r'법률명:\s*"([^"]+)",\s*조항 번호:\s*"([^"]+)"'
        print("🔍 PATTERN-->", 1)

        # 정규 표현식으로 모든 매칭된 결과를 찾음
        matches = re.findall(pattern, text)
        print("🔍 PATTERN-->", 2)

        # 결과를 저장할 리스트 초기화
        result_list = []
        print("🔍 PATTERN-->", 3)

        # 매칭된 결과를 순회하며 리스트에 딕셔너리 형태로 추가
        for match in matches:
            print("🔍 MATCH-->", match)
            law_info = {
                "법률명": match[0],
                "조항 번호": self.extract_first_number(match[1]),
            }
            result_list.append(law_info)

        print("🔍 RESULT LIST-->", result_list)
        return result_list

    def search_laws(self, query: str) -> Dict[str, Any]:
        """질문에 관련된 법령들을 검색합니다. 호출할 때마다 다음 결과를 반환합니다."""
        # 새로운 쿼리인 경우 검색 수행
        if query != self.last_query:
            self.search_results = []
            self.search_results_dict = {}
            self.current_index = 0
            self.last_query = query

            # LLM을 사용하여 질문에 법령 이름이 있다면 추출합니다.
            messages_law_name = [
                {
                    "role": "system",
                    "content": """다음 문장에서 모든 법률명과 조항 번호를 각각 추출해줘. 각 법률명과 조항 번호를 순서대로 추출하고, 조항 번호가 없는 경우에는 "조항 번호 없음"으로 표시해줘. 만약 질문에 법률, 시행령, 시행규칙, 자치법규, 행정규칙에 대한 명시적인 언급이 없으면 법률명에 "해당없음"으로 응답을 해. 행정규칙은 "건축공사 감리세부기준"처럼 ~기준으로 된 경우도 있으니 이것도 법률명으로 인식해야해.

문장: "정원의 조성 및 진흥에 관한 법률 제18의14조와 개인정보 보호법 제5조를 설명해줘."
법률과 조항: 
1. 법률명: "정원의 조성 및 진흥에 관한 법률", 조항 번호: "제18의14조"
2. 법률명: "개인정보 보호법", 조항 번호: "제5조"

문장: "전기공사업법 시행규칙 별지 제16호 서식을 알려줘."
법률과 조항: 
1. 법률명: "전기공사업법 시행규칙", 조항 번호: "별지16호"

문장: "건축공사 감리세부기준 2.5.6 안전관리"
법률과 조항: 
1. 법률명: "건축공사 감리세부기준", 조항 번호: "2.5.6 안전관리"

문장: "정보통신망 이용촉진 및 정보보호 등에 관한 법률 제32조 제3항, 공공기관의 정보공개에 관한 법률 제9조를 알려줘."
법률과 조항: 
1. 법률명: "정보통신망 이용촉진 및 정보보호 등에 관한 법률", 조항 번호: "제32조 제3항"
2. 법률명: "공공기관의 정보공개에 관한 법률", 조항 번호: "제9조"

문장: "도로교통법과 소득세법 제56조에 대해 설명해줘."
법률과 조항: 
1. 법률명: "도로교통법", 조항 번호: "조항 번호 없음"
2. 법률명: "소득세법", 조항 번호: "제56조"

문장: "건설사업관리기술인의 설계단계 업무 중 설계검토 계획에 대해 알려줘."
법률과 조항: 
1. 법률명: "해당없음", 조항 번호: "해당없음"
""",
                },
                {"role": "user", "content": f"문장: {query}\n법률과 조항: "},
            ]
            messages_keyword = [
                {
                    "role": "system",
                    "content": """다음 문장에서 검색에 사용할 키워드를 추출해줘. 키워드는 법령 이름이 아니라 법령 내용에서 찾고자 하는 주요 키워드를 추출해줘. 의미를 유지하면서도 불필요한 단어 또는 검색 대상에서 제외해야 할 단어는 제거해야 합니다. 단, 질문 속에 의미가 유사한 단어가 등장하는 경우에는 어느 단어로 검색해야 매칭이 더 좋을지 모르므로 모두 포함해주세요. 명사 위주로 추출하세요.
""",
                },
                {"role": "user", "content": f"문장: {query}"},
            ]

            # SimpleToolCaller 인스턴스 생성
            caller = SimpleToolCaller()

            # 질문에 법령 이름이 포함된 경우 추출
            law_name_result = caller.chat(messages_law_name, with_tools=False)
            print("🔍 LAW NAME RESULT-->", law_name_result)
            print("-" * 100)
            law_name_parsed = self.parse_law_results(law_name_result)
            print("+" * 100)
            print("🔍 LAW NAME PARSED-->", law_name_parsed)

            # 질문에서 찾고자 하는 주요 키워드 추출
            keyword = caller.chat(messages_keyword, with_tools=False)
            # 맨 앞에 키워드: 가 있으면 제거
            if keyword.startswith("키워드:"):
                keyword = keyword[len("키워드:") :]
            # 결과를 리스트로 변환
            keyword = keyword.split(",")
            keyword = [keyword.strip() for keyword in keyword]
            # 키워드 중 법률명이 포함된 경우 제거
            keyword = [
                keyword
                for keyword in keyword
                if keyword not in law_name_parsed[0]["법률명"]
            ]
            print("🔍 KEYWORD-->", keyword)

            # execute sql
            # SELECT ch2.id, ch2.text, ch2.meta, document.document_meta, paradedb.score(ch2.id) similarity
            # FROM document JOIN collection cl ON document.collection_id = cl.id join chunk ch2 on ch2.document_id = document.id join embedding_all ea on ea.chunk_id = ch2.id
            # WHERE cl.usage = 'rag' AND (cl.scenario->>'law_no_ordin' = 'Y')  AND (NOT document.collection_id = 4 AND document.document_meta->>'path' NOT ILIKE '/data/law/ordin/%') and keyword1='건축법' and ((text @@@ '경미 변경'))
            # ORDER BY paradedb.score(ch2.id) desc LIMIT 80;
            sql_query = f"""
            SELECT ch2.id, ch2.text, ch2.meta, document.document_meta, paradedb.score(ch2.id) similarity
            FROM document JOIN collection cl ON document.collection_id = cl.id join chunk ch2 on ch2.document_id = document.id join embedding_all ea on ea.chunk_id = ch2.id
            WHERE cl.usage = 'rag' AND (cl.scenario->>'law_no_ordin' = 'Y')  AND (NOT document.collection_id = 4 AND document.document_meta->>'path' NOT ILIKE '/data/law/ordin/%') and keyword1='{law_name_parsed[0]["법률명"]}' and ((text @@@ '{" ".join(keyword)}'))
            ORDER BY paradedb.score(ch2.id) desc LIMIT 80;
            """
            print("🔍 SQL QUERY-->", sql_query)
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
        # print("🔍 SEARCH RESULTS DICT-->", self.search_results_dict)
        self.search_results = list(self.search_results_dict.values())
        # print("🔍 SEARCH RESULTS-->", self.search_results)
        print(f"{self.current_index=} {len(self.search_results)=}")

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
        # 직접 LLM 호출 (tool calling 없이)
        headers = {
            "Authorization": f"Bearer {os.getenv('OPENAI_API_KEY')}",
            "Content-Type": "application/json",
        }

        data = {"model": "gpt-3.5-turbo", "messages": messages, "temperature": 0.7}

        response = requests.post(
            "https://api.openai.com/v1/chat/completions", headers=headers, json=data
        )

        if response.status_code == 200:
            judgment = response.json()["choices"][0]["message"]["content"]
            return f"충분성 판단 결과: {judgment}"
        else:
            return f"API 호출 실패: {response.status_code} - {response.text}"

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

            # print(
            #     "🔍 LAW RESULT(from search_laws)-->",
            #     law_result["document_meta"]["path"],
            #     law_result["meta"],
            # )

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

        #         # 결과 정리
        #         result_summary = f"""
        # === 법령 검색 및 검토 결과 ===
        # 검색한 법령 수: {search_count}개
        # 충분한 법령 수: {len([law for law in relevant_laws if "충분함" in law["sufficiency"]])}개
        # 부분적 충분한 법령 수: {len([law for law in relevant_laws if "부분적 충분함" in law["sufficiency"]])}개
        # 부족한 법령 수: {len(insufficient_laws)}개

        # === 충분한 법령들 ===
        # """

        #         for i, law in enumerate(relevant_laws, 1):
        #             result_summary += f"""
        # 법령 {i}:
        # text: {law["result"]["text"]}
        # meta: {law["result"]["meta"]}
        # path: {law["result"]["document_meta"]["path"]}
        # 충분성: {law["sufficiency"]}
        # """

        #         if insufficient_laws:
        #             result_summary += "\n=== 부족한 법령들 ===\n"
        #             for i, law in enumerate(insufficient_laws, 1):
        #                 result_summary += f"""
        # 법령 {i}:
        # text: {law["result"]["text"]}
        # meta: {law["result"]["meta"]}
        # path: {law["result"]["document_meta"]["path"]}
        # 충분성: {law["sufficiency"]}
        # """

        if not relevant_laws:
            return "\n⚠️ 충분한 법령을 찾지 못했습니다. 다른 키워드로 검색하거나 더 구체적인 질문을 해보세요."

        result_summary = ""
        for law in relevant_laws:
            result_summary += f"""
            {law["result"]["document_meta"]["path"]}
            {law["sufficiency"]}
            """
        return result_summary

    except Exception as e:
        return f"법령 검색 및 검토 중 오류가 발생했습니다: {str(e)}"
