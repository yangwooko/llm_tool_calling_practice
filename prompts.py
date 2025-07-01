# 법령 이름 및 조항 번호 추출 프롬프트
LAW_NAME_EXTRACTION_PROMPT = """다음 문장에서 모든 법률명과 조항 번호를 각각 추출해줘. 각 법률명과 조항 번호를 순서대로 추출하고, 조항 번호가 없는 경우에는 "조항 번호 없음"으로 표시해줘. 만약 질문에 법률, 시행령, 시행규칙, 자치법규, 행정규칙에 대한 명시적인 언급이 없으면 법률명에 "해당없음"으로 응답을 해. 행정규칙은 "건축공사 감리세부기준"처럼 ~기준으로 된 경우도 있으니 이것도 법률명으로 인식해야해.

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
"""

# 키워드 추출 프롬프트
KEYWORD_EXTRACTION_PROMPT = """다음 문장에서 검색에 사용할 키워드를 추출해줘. 키워드는 법령 이름이 아니라 법령 내용에서 찾고자 하는 주요 키워드를 추출해줘. 의미를 유지하면서도 불필요한 단어 또는 검색 대상에서 제외해야 할 단어는 제거해야 합니다. 단, 질문 속에 의미가 유사한 단어가 등장하는 경우에는 어느 단어로 검색해야 매칭이 더 좋을지 모르므로 모두 포함해주세요. 명사 위주로 추출하세요."""

# 시스템 프롬프트
SYSTEM_PROMPT = "당신은 도구를 사용할 수 있는 AI 어시스턴트입니다. 필요할 때 적절한 도구를 사용하세요. 질문에 포함된 단어(예를 들어, 도시명)를 다른 언어로 번역하지 말고 질문에 있는 그대로 사용하세요."

# 법령 전문가 프롬프트
LAW_EXPERT_PROMPT = (
    "당신은 법령 전문가입니다. 사용자의 질문에 대해 정확하고 상세하게 답변해주세요."
)

# 배치 법령 충분성 검사 프롬프트
BATCH_LAW_SUFFICIENCY_PROMPT = """다음 법령 내용들을 분석하여 각각이 사용자 질문에 답변하기에 충분한지 판단해주세요.

각 법령 내용에 대해 다음 중 하나로 답변해주세요:
- "충분함": 해당 법령 내용이 질문에 대한 완전한 답변을 제공할 수 있는 경우
- "부분적 충분함": 일부 답변은 가능하지만 추가 정보가 필요한 경우  
- "부족함": 해당 법령 내용이 질문에 답변하기에 부족한 경우

답변 형식:
1번 법령: [충분함/부분적 충분함/부족함]
2번 법령: [충분함/부분적 충분함/부족함]
...
"""

# 배치 추가 검색 필요성 판단 프롬프트
BATCH_ADDITIONAL_SEARCH_PROMPT = """당신은 법령 내용을 분석하여 사용자의 질문에 답하기 위해 추가 검색이 필요한지 판단하는 전문가입니다.

사용자의 질문과 현재 법령 텍스트를 분석하여 다음을 판단해주세요:

1. **관련성 확인**: 현재 법령 텍스트가 사용자의 질문과 직접적으로 관련이 있는가?
2. **추가 검색 필요성**: 관련이 있는 경우, 현재 법령 텍스트만으로는 사용자의 질문에 완전히 답할 수 없어 추가 검색이 필요한가?
3. **검색 대상**: 어떤 법령, 시행령, 시행규칙, 고시 등을 추가로 검색해야 하는가?
4. **검색 키워드**: 추가 검색에 사용할 구체적인 키워드는 무엇인가?

판단 기준:
**1단계: 관련성 판단 (매우 엄격하게)**
- 현재 법령 텍스트에 사용자 질문의 핵심 키워드가 명시적으로 포함되어 있는가?
- 사용자 질문에서 요구하는 내용과 법령 내용이 직접적으로 일치하는가?
- 키워드 매칭 기준:
  * 사용자 질문의 핵심 용어가 법령 텍스트에 정확히 포함되어야 함
  * 유사한 의미라도 정확한 키워드가 없으면 관련 없음으로 판단
  * "경미한 사항의 변경" 질문 → 법령에 "경미한 사항의 변경"이 정확히 포함되어야 함
  * "건축물 높이" 질문 → 법령에 "건축물 높이" 또는 "높이"가 정확히 포함되어야 함
- 관련이 없다면 즉시 "추가 검색 불필요"로 판단

**2단계: 추가 검색 필요성 판단 (관련이 있는 경우에만)**
- 사용자의 질문에서 요구하는 구체적인 내용이 현재 법령에 명시되지 않은 경우
- "대통령령으로 정한다", "시행령으로 정한다" 등의 표현이 있고, 그 내용이 사용자 질문과 직접 관련된 경우
- 구체적인 수치, 기준, 절차, 정의 등이 다른 법령에 위임되어 있고, 그 내용이 사용자 질문과 관련된 경우
- 사용자의 질문이 현재 법령의 예외사항이나 세부규정을 요구하는 경우
- "별도로 정하는 바에 따른다", "관리규정에 따른다" 등의 표현이 있고, 그 내용이 사용자 질문과 직접 관련된 경우

**검색 대상 설정 규칙:**
- "대통령령으로 정한다"가 있는 경우: 현재 법령명에 "시행령"을 붙인 형태로 검색 (예: "건축법" → "건축법 시행령")
- "시행령으로 정한다"가 있는 경우: 현재 법령명에 "시행령"을 붙인 형태로 검색
- "시행규칙으로 정한다"가 있는 경우: 현재 법령명에 "시행규칙"을 붙인 형태로 검색
- 구체적인 법령명이 언급된 경우: 해당 법령명을 그대로 사용

각 법령 내용에 대해 다음 형식으로 답변해주세요:

1번 법령: [추가 검색 필요/추가 검색 불필요]
- 검색 대상: [검색할 법령/시행령/시행규칙명] (추가 검색이 필요한 경우만)
- 검색 키워드: [검색에 사용할 키워드들] (추가 검색이 필요한 경우만)
- 검색 이유: [왜 추가 검색이 필요한지, 사용자 질문과의 연관성] (추가 검색이 필요한 경우만)

2번 법령: [추가 검색 필요/추가 검색 불필요]
- 검색 대상: [검색할 법령/시행령/시행규칙명] (추가 검색이 필요한 경우만)
- 검색 키워드: [검색에 사용할 키워드들] (추가 검색이 필요한 경우만)
- 검색 이유: [왜 추가 검색이 필요한지, 사용자 질문과의 연관성] (추가 검색이 필요한 경우만)

...
"""


# 프롬프트 매핑
PROMPT_MAPPING = {
    "law_name_extraction": LAW_NAME_EXTRACTION_PROMPT,
    "keyword_extraction": KEYWORD_EXTRACTION_PROMPT,
    "batch_law_sufficiency": BATCH_LAW_SUFFICIENCY_PROMPT,
    "batch_additional_search": BATCH_ADDITIONAL_SEARCH_PROMPT,
    "system": SYSTEM_PROMPT,
    "law_expert": LAW_EXPERT_PROMPT,
}


def generate_prompt(prompt_type: str, **kwargs) -> list:
    """통합 프롬프트 생성 함수"""

    if prompt_type not in PROMPT_MAPPING:
        raise ValueError(f"Unknown prompt type: {prompt_type}")

    system_content = PROMPT_MAPPING[prompt_type]

    if prompt_type == "law_name_extraction":
        query = kwargs.get("query", "")
        return [
            {
                "role": "system",
                "content": system_content,
            },
            {"role": "user", "content": f"문장: {query}\n법률과 조항: "},
        ]

    elif prompt_type == "keyword_extraction":
        query = kwargs.get("query", "")
        return [
            {
                "role": "system",
                "content": system_content,
            },
            {"role": "user", "content": f"문장: {query}"},
        ]

    elif prompt_type == "system":
        return [
            {
                "role": "system",
                "content": system_content,
            }
        ]

    elif prompt_type == "law_expert":
        return [
            {
                "role": "system",
                "content": system_content,
            }
        ]

    elif prompt_type == "batch_law_sufficiency":
        law_contents = kwargs.get("law_contents", [])
        user_question = kwargs.get("user_question", "")

        # 각 법령에 번호를 부여하여 표시
        numbered_contents = []
        for i, content in enumerate(law_contents, 1):
            numbered_contents.append(f"{i}번 법령:\n{content}")
        combined_content = "\n\n---\n\n".join(numbered_contents)

        return [
            {
                "role": "system",
                "content": system_content,
            },
            {
                "role": "user",
                "content": f"""사용자 질문: {user_question}

법령 내용들:
{combined_content}""",
            },
        ]

    elif prompt_type == "batch_additional_search":
        law_contents = kwargs.get("law_contents", [])
        user_question = kwargs.get("user_question", "")

        # 각 법령에 번호를 부여하여 표시
        numbered_contents = []
        for i, content in enumerate(law_contents, 1):
            numbered_contents.append(f"{i}번 법령:\n{content}")
        combined_content = "\n\n---\n\n".join(numbered_contents)

        return [
            {
                "role": "system",
                "content": system_content,
            },
            {
                "role": "user",
                "content": f"""사용자 질문: {user_question}

법령 내용들:
{combined_content}""",
            },
        ]

    else:
        raise ValueError(f"Unsupported prompt type: {prompt_type}")
