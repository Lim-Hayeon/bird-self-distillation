"""
llm_utils.py
OpenAI API 호출 래퍼: SQL 생성 + self-distillation(KB delta 추출).

.env 파일에 OPENAI_API_KEY가 있어야 함.
"""

from __future__ import annotations

import re
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
_client = OpenAI()  # OPENAI_API_KEY 환경변수를 자동으로 읽음

MODEL = "gpt-4o-mini"  # 필요시 gpt-5.5 등으로 변경


def _extract_sql(raw_text: str) -> str:
    """모델 응답에서 ```sql ... ``` 코드블럭이 있으면 그 안 내용만, 없으면 전체 텍스트를 SQL로 취급."""
    m = re.search(r"```(?:sql)?\s*(.*?)```", raw_text, re.DOTALL | re.IGNORECASE)
    sql = m.group(1) if m else raw_text
    return sql.strip().rstrip(";")


def build_system_prompt(schema_ddl: str, kb_text: str = "") -> str:
    prompt = (
        "당신은 SQLite 전문가입니다. 주어진 스키마를 참고해서 자연어 질문에 대한 "
        "SQL 쿼리 하나만 생성하세요. 설명 없이 SQL만 ```sql ... ``` 코드블럭으로 출력하세요.\n\n"
        f"### 스키마\n{schema_ddl}\n"
    )
    if kb_text.strip():
        prompt += (
            "\n### 참고 지식 (이 데이터베이스를 다뤄본 경험에서 나온 도메인 지식)\n"
            f"{kb_text}\n"
            "위 지식과 스키마가 다르게 보이면 지식 쪽을 우선하세요 (스키마에 없는 암묵적 규칙일 수 있음).\n"
        )
    return prompt


def generate_sql(question: str, evidence: str, schema_ddl: str, kb_text: str = "",
                  history: list | None = None) -> str:
    """
    질문에 대한 SQL을 생성한다.
    history: [{"role": "assistant"/"user", "content": ...}, ...] 형태로 이전 턴(오답+힌트)을 이어붙일 때 사용.
             None이면 첫 시도.
    """
    messages = [{"role": "system", "content": build_system_prompt(schema_ddl, kb_text)}]

    user_msg = f"질문: {question}"
    if evidence:
        user_msg += f"\n힌트(evidence): {evidence}"
    messages.append({"role": "user", "content": user_msg})

    if history:
        messages.extend(history)

    resp = _client.chat.completions.create(
        model=MODEL,
        messages=messages,
        temperature=0,
    )
    raw = resp.choices[0].message.content
    return _extract_sql(raw)


DISTILL_PROMPT = """아래는 Text-to-SQL 세션에서 있었던 대화 기록이다.
각 질문마다 모델이 처음에 어떻게 틀렸고, 사람의 힌트를 받은 뒤 어떻게 고쳐졌는지가 담겨 있다.

너의 임무: 이 대화에서 앞으로 비슷한 질문에 다시 틀리지 않기 위해 기록해둘 가치가 있는
"교정된 순간"만 추출해서, 짧고 재사용 가능한 규칙으로 markdown bullet list로 정리해라.

규칙:
- 이미 맞춘 질문(처음부터 정답)은 포함하지 마라.
- 정답 SQL 전체를 베끼지 말고, "왜 틀렸는지 / 무엇을 알아야 하는지"를 일반화된 규칙으로 써라.
  예: "'매출'을 물으면 total_amount 컬럼을 쓰고, status='cancelled'인 행은 제외해야 함"
- 이미 같은 내용의 규칙이 있다면 새로 만들지 말고 생략해라 (아래 기존 KB 참고).
- 각 항목은 한 줄, 컬럼명/조건은 구체적으로 명시해라.

### 기존 KB (중복 방지용 참고)
{existing_kb}

### 이번 세션 대화 기록
{transcript}

### 출력 형식
- (규칙 1)
- (규칙 2)
...
새로 추가할 규칙이 없으면 "추가할 항목 없음"이라고만 답해라.
"""


def extract_kb_deltas(transcript: str, existing_kb: str = "") -> str:
    """세션 대화 기록에서 self-distillation으로 KB에 추가할 delta를 추출."""
    prompt = DISTILL_PROMPT.format(existing_kb=existing_kb or "(없음)", transcript=transcript)
    resp = _client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0,
    )
    return resp.choices[0].message.content.strip()