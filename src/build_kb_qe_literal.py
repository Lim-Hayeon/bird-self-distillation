"""
build_kb_qe_literal.py

build_kb_qe.py와 구조는 100% 동일(Raw -> R1 -> R2 -> R3, Test set 평가, QE 검색 방식
그대로)하되, distillation 프롬프트만 바꾼 버전이다.

바뀐 것: 상황/교정 내용을 "일반화된 규칙"으로 패러프레이즈하지 않고, 그 교정이 나온
실제 질문 문장 + 실제 오답 SQL + 실제 정답 SQL을 verbatim으로 그대로 인용해서 저장한다.
(diagnose_self_consistency_v2.py의 tier1-soft 실험에서, 일반화된 규칙 대신 원본
질문+정답 SQL을 그대로 예시로 보여줬을 때 구조적 교정(DISTINCT/JOIN/GROUP BY 등)은
5개 중 5개 다 성공했던 것에 착안.)

바뀌지 않은 것:
  - 태그(키워드) 필드: 검색에 쓰이는 색인이라 지금처럼 카테고리화된 채로 유지
    (테이블/컬럼명 + SQL 요소 + 오류유형). 이것까지 literal하게 바꾸면 QE 검색이
    오히려 덜 걸릴 수 있어서 그대로 둠.
  - 검색(predict_query_elements, select_entries_by_tags): build_kb_qe.py 그대로 재사용,
    이번엔 안 건드림 (내용만 바꿨을 때 순수 효과를 보기 위해 변수 하나만 바꾸는 것).
  - kb_id 넘버링, dedup 로직, Raw->R1->R2->R3 평가 흐름: build_kb_qe.py의 main()과 동일.

주의: 엔트리 하나하나가 이제 실제 SQL 두 개(오답+정답)를 포함해서 텍스트가 길어짐.
과검색이 이미 77~98%였던 걸 감안하면 프롬프트 토큰이 꽤 커질 수 있음 - 결과 보고
필요하면 다음 단계로 검색 쪽(태그 겹침 임계값 등)을 손볼 것.

기존 kb/*.md, results/round_results*.json, build_kb_qe.py는 전혀 안 건드림.
새 KB: kb/{db_id}_kb_qe_literal_R1.md / _R2.md / _R3.md
새 결과: results/round_results_qe_literal.json (조건명: Raw/R1/R2/R3)

사용법 (리포 루트에서):
    python3 src/build_kb_qe_literal.py
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import db_utils as db
import llm_utils as llm
from build_kb_qe import (
    TARGET_DBS,
    BATCHES,
    BATCH_TO_ROUND,
    SPLIT_DIR,
    TRANSCRIPTS_DIR,
    format_transcript_for_distill,
    load_evidence_map,
    format_evidence_summary,
    parse_kb_entries,
    predict_query_elements,
    select_entries_by_tags,
)

KB_DIR = Path("kb")
RESULTS_DIR = Path("results")
QE_LITERAL_RESULTS_PATH = RESULTS_DIR / "round_results_qe_literal.json"


# ---------------- self-distillation: literal 버전 ----------------

QE_DISTILL_PROMPT_LITERAL = """아래는 Text-to-SQL 세션에서 있었던 대화 기록이다.
각 질문마다 모델이 처음에 어떻게 틀렸고, 사람의 힌트를 받은 뒤 어떻게 고쳐졌는지가 담겨 있다.

너의 임무: 앞으로 비슷한 질문에 다시 틀리지 않기 위해 기록해둘 가치가 있는 "교정된 순간"만
추출해서, 아래 형식으로만 markdown 작성해라. 다른 설명 붙이지 마라.

**중요: 상황과 교정 내용은 절대 요약하거나 일반화해서 패러프레이즈하지 마라.
아래 "이번 세션 대화 기록"에 있는 실제 질문 문장, 실제 SQL을 그대로(verbatim) 가져와서 채워라.**

각 항목은 반드시 이 4개 필드를 다 채워야 한다:

## KB-NNN
- 상황: "질문: <이 교정이 나온 질문을 원문 그대로 인용>" 으로 시작하고, 필요하면 왜
  틀렸는지를 한 문장만 덧붙여라. "~하는 경우", "~해야 할 때" 같은 패턴화된 표현으로
  바꿔쓰지 마라 - 그 질문 자체를 그대로 보여줘야 한다.
- 태그: (관련 테이블명, 컬럼명(스키마의 정확한 이름), 관련 SQL 요소(JOIN/DISTINCT/GROUP BY/
  집계함수(COUNT,AVG,SUM 등)/날짜함수(STRFTIME 등)/서브쿼리 등), 오류유형(WRONG_TABLE/
  WRONG_COLUMN/MISSING_DISTINCT/EXTRA_DISTINCT/DATE_LOGIC/AGGREGATION_LOGIC/VALUE_ENCODING/
  JOIN_LOGIC/COLUMN_ORDER/SUBQUERY_VS_JOIN 중 해당하는 것) 을 콤마로 구분해서 나열.
  이 필드만 예외적으로 일반화된 카테고리 단어를 써라 - 검색에 쓰이는 색인이기 때문이다.
- 교정 내용: 정확히 이 형식으로만 써라(줄바꿈 없이 한 줄로):
  "오답: <틀린 시도의 SQL을 원문 그대로 한 글자도 안 바꾸고 인용> / 정답: <최종 정답
  SQL을 원문 그대로 한 글자도 안 바꾸고 인용>"
  설명을 풀어써서 대체하지 말고 SQL 자체를 그대로 인용해라. 숫자/코드값도 정확히 그대로.
- 예외: 이번 세션 대화 기록에서 실제로 언급되거나 관찰된 예외적 상황이 있을 때만 적어라.
  짐작하거나 있을 법한 예외를 지어내지 마라. 실제로 없으면 반드시 "없음"이라고만 써라.

규칙:
- 이미 맞춘 질문(처음부터 정답)은 포함하지 마라.
- 아래 "이번 세션 질문별 evidence"에 이미 나온 내용은 추출하지 마라.
- 아래 스키마의 PRIMARY KEY/FOREIGN KEY 관계로 당연히 유추 가능한 JOIN 조건은 추출하지 마라.
- 태그의 테이블/컬럼명은 반드시 스키마에 실제로 존재하는 정확한 이름을 써라.
- 아래 기존 KB에 이미 같은 질문/같은 교정이 있으면 생략해라.

### 스키마 (PK/FK 확인 및 정확한 테이블/컬럼명 확인용)
{schema_ddl}

### 기존 KB (중복 확인용)
{existing_kb_markdown}

### 이번 세션 질문별 evidence
{evidence_summary}

### 이번 세션 대화 기록
{transcript}

새로 추가할 항목이 없으면 "추가할 항목 없음"이라고만 답해라.
"""


def extract_qe_deltas_literal(transcript: str, evidence_summary: str, schema_ddl: str,
                               existing_kb_markdown: str) -> str:
    prompt = QE_DISTILL_PROMPT_LITERAL.format(
        schema_ddl=schema_ddl,
        existing_kb_markdown=existing_kb_markdown or "(없음)",
        evidence_summary=evidence_summary,
        transcript=transcript,
    )
    resp = llm._client.chat.completions.create(
        model=llm.MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0,
    )
    return resp.choices[0].message.content.strip()


# ---------------- 텍스트 변환: situation도 같이 주입 (이미 literal이라 quote 그대로 보임) ----------------

def build_kb_text_literal(selected: list[dict]) -> str:
    lines = []
    for e in selected:
        line = f"- {e['situation']} => {e['correction']}"
        if e["exception"]:
            line += f" (단, {e['exception']})"
        lines.append(line)
    return "\n".join(lines)


# ---------------- 평가 (build_kb_qe.py의 evaluate와 동일 로직, 함수만 새로 바인딩) ----------------

def load_split(db_id: str, split_name: str) -> list[dict]:
    with open(SPLIT_DIR / f"{db_id}_{split_name}.json", encoding="utf-8") as f:
        return json.load(f)


def evaluate(db_id: str, schema_ddl: str, questions: list[dict], entries: list[dict]) -> tuple[float, dict]:
    correctness = {}
    for q in questions:
        if entries:
            predicted_elements = predict_query_elements(q["question"], q.get("evidence", ""), schema_ddl)
            selected = select_entries_by_tags(entries, predicted_elements)
            kb_text = build_kb_text_literal(selected)
        else:
            kb_text = ""
        predicted = llm.generate_sql(q["question"], q.get("evidence", ""), schema_ddl, kb_text=kb_text)
        correctness[str(q["question_id"])] = int(db.check_correct(db_id, predicted, q["SQL"]))
    acc = sum(correctness.values()) / len(correctness) if correctness else 0.0
    return acc, correctness


def save_result(record: dict):
    RESULTS_DIR.mkdir(exist_ok=True)
    existing = []
    if QE_LITERAL_RESULTS_PATH.exists():
        with open(QE_LITERAL_RESULTS_PATH, encoding="utf-8") as f:
            existing = json.load(f)
    existing.append(record)
    with open(QE_LITERAL_RESULTS_PATH, "w", encoding="utf-8") as f:
        json.dump(existing, f, ensure_ascii=False, indent=2)


def main():
    for db_id in TARGET_DBS:
        print(f"\n{'#'*60}\n# {db_id} (Query Expansion + literal 상황/교정내용: Raw -> R1 -> R2 -> R3)\n{'#'*60}")
        schema_ddl = db.get_schema_ddl(db_id)
        test_qs = load_split(db_id, "test")

        raw_acc, raw_correctness = evaluate(db_id, schema_ddl, test_qs, [])
        print(f"[Raw] {raw_acc:.1%}")
        save_result({"db_id": db_id, "condition": "Raw", "accuracy": raw_acc, "correctness": raw_correctness})

        entries: list[dict] = []
        kb_markdown = ""
        kb_id_counter = 1

        for batch in BATCHES:
            round_name = BATCH_TO_ROUND[batch]
            transcript_path = TRANSCRIPTS_DIR / f"{db_id}_{round_name}.json"

            if transcript_path.exists():
                with open(transcript_path, encoding="utf-8") as f:
                    transcripts = json.load(f)
                evidence_map = load_evidence_map(db_id, batch)
                transcript_text = format_transcript_for_distill(transcripts)
                evidence_summary = format_evidence_summary(transcripts, evidence_map)

                delta_text = extract_qe_deltas_literal(transcript_text, evidence_summary, schema_ddl, kb_markdown)

                if "추가할 항목 없음" not in delta_text:
                    renumbered_lines = []
                    for line in delta_text.splitlines():
                        if re.match(r"^## KB-", line):
                            renumbered_lines.append(f"## KB-{kb_id_counter:03d}")
                            kb_id_counter += 1
                        else:
                            renumbered_lines.append(line)
                    delta_text = "\n".join(renumbered_lines)
                    kb_markdown += ("\n\n" if kb_markdown else "") + delta_text
                    new_entries = parse_kb_entries(delta_text)
                    entries.extend(new_entries)
                    print(f"  [{round_name}] 새 항목 {len(new_entries)}개 추출")
                else:
                    print(f"  [{round_name}] 새 항목 없음")
            else:
                print(f"  [경고] {transcript_path} 없음, 이 단계는 이전 상태 유지")

            KB_DIR.mkdir(exist_ok=True)
            (KB_DIR / f"{db_id}_kb_qe_literal_{round_name}.md").write_text(kb_markdown + "\n", encoding="utf-8")

            acc, correctness = evaluate(db_id, schema_ddl, test_qs, entries)
            delta = acc - raw_acc
            print(f"[{round_name}] {acc:.1%}  (Raw 대비 {delta:+.1%}p, 누적 항목 {len(entries)}개)")
            save_result({"db_id": db_id, "condition": round_name, "accuracy": acc, "correctness": correctness,
                         "n_entries": len(entries)})

    print("\n완료. results/round_results_qe_literal.json, kb/*_kb_qe_literal_*.md 확인하세요.")
    print("build_kb_qe.py의 round_results_qe.json과 db_id/condition 기준으로 나란히 비교하면 됨.")


if __name__ == "__main__":
    main()