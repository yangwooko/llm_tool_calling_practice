import json
import requests
from typing import List, Dict, Any, Callable
import inspect
import os
import psycopg2
import re
from util_tool_call import SimpleToolCaller
from prompts import generate_prompt
from db_utils import db_manager


# 법령 검색 클래스
class LawSearcher:
    def __init__(self):
        pass

    def extract_article_number(self, text):
        """법령의 조항 번호를 추출합니다."""
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
        """법률명과 조항 번호 목록를 추출"""
        # 맨 앞에 법률과 조항: 이 나오면 무시
        if "법률과 조항:" in text:
            text = text.split("법률과 조항:")[1].strip()
        # 앞에 \n 등이 있으면 제거
        text = text.lstrip("\n")
        # 정규 표현식을 사용하여 법률명과 조항 번호 추출
        pattern = r'법률명:\s*"([^"]+)",\s*조항 번호:\s*"([^"]+)"'

        # 정규 표현식으로 모든 매칭된 결과를 찾음
        matches = re.findall(pattern, text)
        # print("🔍 MATCHES-->", matches)

        # 결과를 저장할 리스트 초기화
        result_list = []

        # 매칭된 결과를 순회하며 리스트에 딕셔너리 형태로 추가
        for match in matches:
            # print("🔍 MATCH-->", match)
            law_info = {
                "법률명": match[0],
                "조항 번호": self.extract_article_number(match[1]),
            }
            result_list.append(law_info)

        # print("🔍 RESULT LIST-->", result_list)
        return result_list

    def search_laws(self, query: str, k: int = 40) -> Dict[str, Any]:
        """질문에 관련된 법령들을 검색하여 chunk ID 리스트를 반환합니다."""
        # SimpleToolCaller 인스턴스 생성
        caller = SimpleToolCaller()

        # 질문에 법령 이름이 포함된 경우 추출
        law_name_result = caller.chat(
            generate_prompt("law_name_extraction", query=query), with_tools=False
        )
        # print("🔍 포함된 법령 이름-->", law_name_result)
        law_name_parsed = self.parse_law_results(law_name_result)
        print("🔍 법령 이름 추출 결과-->", law_name_parsed)

        # 질문에서 찾고자 하는 주요 키워드 추출
        keyword = caller.chat(
            generate_prompt("keyword_extraction", query=query), with_tools=False
        )
        # print("🔍 LLM이 찾은 키워드-->", keyword)
        # 맨 앞에 키워드: 가 있으면 제거
        if keyword.startswith("키워드:"):
            keyword = keyword[len("키워드:") :]
        # 결과를 리스트로 변환
        keyword = keyword.split(",")
        keyword = [keyword.strip() for keyword in keyword]
        # 키워드 중 법률명 또는 "대통령령"이 포함된 경우 제거
        keyword = [
            keyword
            for keyword in keyword
            if keyword not in law_name_parsed[0]["법률명"] and keyword != "대통령령"
        ]
        print("🔍 포함된 키워드-->", keyword)

        # 법률명에서 공백 제거
        law_name_no_space = law_name_parsed[0]["법률명"].replace(" ", "")

        # execute sql
        if law_name_no_space == "해당없음":
            sql_query = f"""SELECT ch2.id FROM document JOIN collection cl ON document.collection_id = cl.id JOIN chunk ch2 ON ch2.document_id = document.id WHERE cl.usage = 'rag' AND (cl.scenario->>'law_no_ordin' = 'Y')  AND (NOT document.collection_id = 4  AND document.document_meta->>'path' NOT ILIKE '/data/law/ordin/%') AND ((text @@@ '{" ".join(keyword)}')) ORDER BY paradedb.score(ch2.id) DESC LIMIT {k};"""
        else:
            sql_query = f"""WITH t1 AS (SELECT ch2.id, ch2.keyword1, paradedb.score(ch2.id) AS similarity FROM document JOIN collection cl ON document.collection_id = cl.id JOIN chunk ch2 ON ch2.document_id = document.id WHERE cl.usage = 'rag' AND (cl.scenario->>'law_no_ordin' = 'Y')  AND (NOT document.collection_id = 4  AND document.document_meta->>'path' NOT ILIKE '/data/law/ordin/%') AND ((text @@@ '{" ".join(keyword)}')) OFFSET 0
            ) SELECT id, similarity FROM t1 WHERE keyword1='{law_name_no_space}' ORDER BY similarity DESC LIMIT {k};"""

        return db_manager.execute_query(sql_query)

    def get_law_content_by_id(self, id: int) -> str:
        """chunk id에 해당하는 법령 내용을 반환합니다."""
        sql_query = f"""SELECT text FROM chunk WHERE id = {id};"""

        result = db_manager.execute_query_single(sql_query)
        if "error" in result:
            return result
        else:
            # print("🔍 RESULT-->", result)
            return {"results": [result["result"]["text"]]}


# 법령 내용 충분성 검사 함수 (LLM 기반)
def check_law_sufficiency(law_contents: List[str], user_question: str) -> List[str]:
    """LLM을 사용하여 여러 법령 내용이 사용자 질문에 답변하기에 충분한지 판단합니다."""
    try:
        # SimpleToolCaller 인스턴스 생성
        caller = SimpleToolCaller()

        # LLM에게 각 청크별로 판단하도록 요청
        result = caller.chat(
            generate_prompt(
                "batch_law_sufficiency",
                law_contents=law_contents,
                user_question=user_question,
            ),
            with_tools=False,
        )
        # print("🔍 BATCH LAW SUFFICIENCY RESULT-->", result)

        # 결과 파싱
        results = []
        lines = result.strip().split("\n")

        for i, line in enumerate(lines):
            if f"{i+1}번 법령:" in line:
                if "충분함" in line:
                    results.append("충분함")
                elif "부분적 충분함" in line:
                    results.append("부분적 충분함")
                else:
                    results.append("부족함")
            else:
                # 파싱 실패 시 기본값
                results.append("부족함")

        # 결과 개수가 청크 개수와 맞지 않으면 기본값으로 채움
        while len(results) < len(law_contents):
            results.append("부족함")

        return results[: len(law_contents)]

    except Exception as e:
        print(f"충분성 검사 오류: {e}")
        return ["검사 중 오류가 발생했습니다."] * len(law_contents)


def search_and_analyze_laws(
    query: str, user_question: str, batch_size: int = 10
) -> Dict[str, Any]:
    """질문에 관련된 법령을 검색하고 충분성을 검사하여 관련된 법령들을 반환합니다."""
    relevant_laws = []

    try:
        # 법령 검색
        law_result_ids = LawSearcher().search_laws(query)

        if "error" in law_result_ids:
            print(f"법령 검색 오류: {law_result_ids['error']}")
            return {"error": law_result_ids["error"], "results": relevant_laws}

        if not law_result_ids["results"]:
            print("검색 결과가 없습니다.")
            return {"error": None, "results": relevant_laws}

        # 법령 내용을 배치 단위로 가져오기
        law_contents = []
        for law_result_id in law_result_ids["results"]:
            law_content = LawSearcher().get_law_content_by_id(law_result_id["id"])
            if "error" not in law_content:
                law_contents.extend(law_content["results"])

        # 배치 단위로 충분성 검사 수행
        for i in range(0, len(law_contents), batch_size):
            batch = law_contents[i : i + batch_size]

            # 배치 전체를 한번에 충분성 검사
            sufficiency_results = check_law_sufficiency(batch, user_question)
            # print("🔍 SUFFICIENCY RESULTS-->", sufficiency_results)

            # 각 청크별 결과에 따라 relevant_laws에 추가
            for j, (law_content, sufficiency_result) in enumerate(
                zip(batch, sufficiency_results)
            ):
                if (
                    "충분함" in sufficiency_result
                    or "부분적 충분함" in sufficiency_result
                ):
                    print("🔍 발견한 내용-->", law_content.split("\n")[0])
                    relevant_laws.append(law_content)

        return {"error": None, "results": relevant_laws}

    except Exception as e:
        print(f"법령 검색 및 분석 중 오류 발생: {e}")
        return {"error": str(e), "results": relevant_laws}


def check_additional_search_needed(
    law_contents: List[str], user_question: str, current_law_name: str = ""
) -> List[Dict[str, Any]]:
    """여러 법령 내용을 분석하여 사용자 질문에 답하기 위해 추가 검색이 필요한지 판단합니다."""
    try:
        # SimpleToolCaller 인스턴스 생성
        caller = SimpleToolCaller()

        # # 여러 청크를 구분자로 연결
        # combined_content = "\n\n---\n\n".join(law_contents)

        # result = caller.chat(
        #     generate_prompt(
        #         "additional_search",
        #         law_content=combined_content,
        #         user_question=user_question,
        #     ),
        #     with_tools=False,
        # )

        # 결과 파싱 - 각 청크별로 추가 검색 필요성 판단
        results = []

        # LLM에게 각 청크별로 판단하도록 요청
        batch_result = caller.chat(
            generate_prompt(
                "batch_additional_search",
                law_contents=law_contents,
                user_question=user_question,
            ),
            with_tools=False,
        )

        # 결과 파싱
        lines = batch_result.strip().split("\n")
        current_law_index = -1
        current_search_target = ""
        current_search_keywords = ""
        current_search_reason = ""

        for line in lines:
            # 새로운 법령 시작 확인
            for i in range(len(law_contents)):
                if f"{i+1}번 법령:" in line:
                    # 이전 법령의 결과 저장
                    if current_law_index >= 0:
                        if "추가 검색 필요" in lines[current_law_index]:
                            results.append(
                                {
                                    "needs_additional_search": True,
                                    "search_target": current_search_target
                                    or (
                                        current_law_name + " 시행령"
                                        if current_law_name
                                        else ""
                                    ),
                                    "search_keywords": current_search_keywords,
                                    "search_reason": current_search_reason
                                    or "법령 내용에서 추가 검색이 필요함",
                                    "full_result": lines[current_law_index],
                                }
                            )
                        else:
                            results.append(
                                {
                                    "needs_additional_search": False,
                                    "full_result": lines[current_law_index],
                                }
                            )

                    # 새로운 법령 시작
                    current_law_index = len(results)
                    current_search_target = ""
                    current_search_keywords = ""
                    current_search_reason = ""
                    break

            # 검색 대상, 키워드, 이유 파싱
            if "검색 대상:" in line:
                current_search_target = line.split("검색 대상:")[1].strip()
            elif "검색 키워드:" in line:
                current_search_keywords = line.split("검색 키워드:")[1].strip()
            elif "검색 이유:" in line:
                current_search_reason = line.split("검색 이유:")[1].strip()

        # 마지막 법령의 결과 저장
        if current_law_index >= 0 and current_law_index < len(lines):
            if "추가 검색 필요" in lines[current_law_index]:
                results.append(
                    {
                        "needs_additional_search": True,
                        "search_target": current_search_target
                        or (current_law_name + " 시행령" if current_law_name else ""),
                        "search_keywords": current_search_keywords,
                        "search_reason": current_search_reason
                        or "법령 내용에서 추가 검색이 필요함",
                        "full_result": lines[current_law_index],
                    }
                )
            else:
                results.append(
                    {
                        "needs_additional_search": False,
                        "full_result": lines[current_law_index],
                    }
                )

        # 결과 개수가 청크 개수와 맞지 않으면 기본값으로 채움
        while len(results) < len(law_contents):
            results.append(
                {
                    "needs_additional_search": False,
                    "full_result": "기본값",
                }
            )

        return results[: len(law_contents)]

    except Exception as e:
        print(f"추가 검색 필요성 판단 오류: {e}")
        return [
            {
                "needs_additional_search": False,
                "error": f"판단 중 오류가 발생했습니다: {str(e)}",
            }
        ] * len(law_contents)


def collect_additional_search_requirements(
    law_content: str,
    additional_search_result: Dict[str, Any],
    requirements_list: List[Dict],
) -> None:
    """추가 검색 요구사항을 수집하고 중복을 제거합니다."""
    # print("🔍 ADDITIONAL SEARCH RESULT-->", additional_search_result)
    if additional_search_result.get("needs_additional_search", False):
        search_target = additional_search_result.get("search_target", "")
        search_keywords = additional_search_result.get("search_keywords", "")

        if search_target and search_keywords:
            if search_target == "없음" and search_keywords == "없음":
                return
            # 중복 검사를 위한 키 생성
            search_key = f"{search_target}:{search_keywords}"
            # print("🔍 추가로 검색해야 할 법령-->", search_key)
            # 기존 요구사항에서 동일한 키가 있는지 확인
            existing_req = None
            for req in requirements_list:
                if req["search_key"] == search_key:
                    existing_req = req
                    break
            if existing_req:
                # 중복된 경우 원본 법령만 추가
                # existing_req["original_laws"].append(law_content)
                pass
            else:
                # 새로운 요구사항 추가
                requirements_list.append(
                    {
                        "search_key": search_key,
                        "search_target": search_target,
                        "search_keywords": search_keywords,
                        "search_reason": additional_search_result.get(
                            "search_reason", ""
                        ),
                        # "original_laws": [law_content],
                    }
                )


def perform_batch_additional_searches(
    requirements_list: List[Dict], user_question: str
) -> List[Dict]:
    """여러 추가 검색을 일괄적으로 수행합니다."""
    results = []

    # print(f"🔍 PERFORMING BATCH SEARCHES FOR {len(requirements_list)} REQUIREMENTS")

    # 배치 단위로 추가 검색 수행
    batch_size = 10  # 배치 크기를 10으로 통일
    for i in range(0, len(requirements_list), batch_size):
        batch_requirements = requirements_list[i : i + batch_size]

        for req in batch_requirements:
            additional_query = f"{req["search_target"]} {req["search_keywords"]}"
            additional_search_result_data = search_and_analyze_laws(
                additional_query, user_question, batch_size=10
            )
            # print("🔍 ADDITIONAL SEARCH RESULT DATA-->", additional_search_result_data)

            if additional_search_result_data["error"] is None:
                results.append(
                    {
                        "search_target": req["search_target"],
                        "search_keywords": req["search_keywords"],
                        # "search_reason": req["search_reason"],
                        # "original_laws": req["original_laws"],
                        "additional_law_content": additional_search_result_data[
                            "results"
                        ],
                    }
                )
            else:
                print(
                    f"🔍 BATCH SEARCH FAILED: {additional_search_result_data['error']}"
                )

    return results


def find_relevant_laws(user_question: str, max_search_count: int = 10) -> str:
    """주어진 질문과 관련된 법령을 찾고 충분성을 검사하여 관련된 법령을 추려냅니다."""
    additional_search_requirements = []  # 추가 검색 요구사항을 모으는 리스트
    additional_search_results = []

    try:
        # 현재 법령명 추출
        messages_law_name = generate_prompt("law_name_extraction", query=user_question)
        caller = SimpleToolCaller()
        law_name_result = caller.chat(messages_law_name, with_tools=False)
        law_name_parsed = LawSearcher().parse_law_results(law_name_result)
        current_law_name = law_name_parsed[0]["법률명"] if law_name_parsed else ""

        # search_and_analyze_laws 함수를 활용하여 기본 검색 수행
        relevant_laws = search_and_analyze_laws(user_question, user_question)
        # print("🔍 RELEVANT LAWS 1-->", [o[:40] for o in relevant_laws["results"]])

        # 배치 단위로 추가 검색 필요성 확인
        batch_size = 10
        for i in range(0, len(relevant_laws["results"]), batch_size):
            batch = relevant_laws["results"][i : i + batch_size]

            print(
                f"🔍 추가 검색 필요성 확인 (총 {len(relevant_laws['results']) // batch_size + 1}개 배치 중 {i//batch_size + 1}번째)-->",
                len(batch),
                "개 텍스트 청크",
            )

            # 배치 전체를 한번에 추가 검색 필요성 확인
            additional_search_results = check_additional_search_needed(
                batch, user_question, current_law_name
            )

            # 각 청크별 결과에 따라 요구사항 수집
            for j, (law_content, additional_search_result) in enumerate(
                zip(batch, additional_search_results)
            ):
                collect_additional_search_requirements(
                    law_content,
                    additional_search_result,
                    additional_search_requirements,
                )

        # print("🔍 RELEVANT LAWS 2-->", [o[:40] for o in relevant_laws["results"]])
        print("🔍 추가 검색할 대상")
        for req in additional_search_requirements:
            print("-->", req["search_target"], req["search_keywords"])

        # 2단계: 수집된 추가 검색 요구사항들을 일괄 처리
        if additional_search_requirements:
            additional_search_results = perform_batch_additional_searches(
                additional_search_requirements, user_question
            )
        # print("🔍 ADDITIONAL SEARCH RESULTS-->", additional_search_results)

        # 결과 정리
        result_summary = "=== 법령 검색 및 분석 결과 ===\n\n"

        if relevant_laws:
            result_summary += "=== 관련 법령들 ===\n"
            for i, law in enumerate(relevant_laws, 1):
                result_summary += f"\n법령 {i}:\n"
                result_summary += f"내용: {law}\n"
        else:
            result_summary += "⚠️ 충분한 법령을 찾지 못했습니다.\n"

        if additional_search_results:
            result_summary += "\n=== 추가 검색 결과 ===\n"
            for i, result in enumerate(additional_search_results, 1):
                result_summary += f"\n추가 검색 {i}:\n"
                result_summary += f"검색 대상: {result['search_target']}\n"
                result_summary += f"검색 키워드: {result['search_keywords']}\n"

                if "error" in result:
                    pass
                else:
                    result_summary += (
                        f"추가 검색 결과 내용: {result['additional_law_content']}...\n"
                    )

        return result_summary

    except Exception as e:
        print(f"법령 검색 중 오류 발생: {e}")
        return f"법령 검색 중 오류가 발생했습니다: {str(e)}"
