"""
build_kb_qe.py
build_kb_unified.py의 상황/교정내용/예외 구조는 유지하되, 두 가지를 바꾼다:

1. Query Expansion: Test 질문이 오면, 질문 텍스트로 바로 KB를 검색하지 않고
   먼저 LLM에게 "이 질문을 풀려면 어떤 테이블/컬럼/SQL 요소가 필요할지" 예측시킨 뒤,
   그 예측된 SQL 요소로 KB를 검색한다. (질문의 자연어 단어가 KB 태그랑 안 겹쳐도,
   예측된 SQL 요소는 겹칠 수 있음 - 동의어 문제 완화 시도)

2. 구조화된 error_tags: "키워드"(도메인 단어) 대신, 관련 테이블/컬럼명 + SQL 요소
   (JOIN/DISTINCT/GROUP BY/집계함수/날짜함수 등) + 오류유형을 섞은 태그로 저장.
   Query Expansion이 예측하는 것과 같은 어휘(테이블/컬럼/SQL 요소)를 쓰게 해서
   두 쪽이 자연스럽게 맞물리게 함.

self-distillation 구조(세션 교정 -> LLM이 스스로 markdown 추출 -> 다음 세션 주입) 그대로.
기존 kb/*.md, kb/*.json, results/round_results*.json은 전혀 안 건드림.

새 KB: kb/{db_id}_kb_qe_R1.md / _R2.md / _R3.md
새 결과: results/round_results_qe.json (조건명: Raw/R1/R2/R3)

비용 주의: Test 질문마다 Query Expansion 예측 호출이 1번 더 붙어서
(entries가 있을 때만) 이전 실험들보다 호출 수가 좀 더 늘어남.

사용법 (리포 루트에서):
    python3 src/build_kb_qe.py
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import db_utils as db
import llm_utils as llm

TARGET_DBS = ["thrombosis_prediction", "formula_1", "card_games"]
BATCHES = ["T1", "T2", "T3"]
BATCH_TO_ROUND = {"T1": "R1", "T2": "R2", "T3": "R3"}

SPLIT_DIR = Path("split_output")
TRANSCRIPTS_DIR = Path("results/transcripts")
KB_DIR = Path("kb")
RESULTS_DIR = Path("results")
QE_RESULTS_PATH = RESULTS_DIR / "round_results_qe.json"


# ---------------- self-distillation: 구조화 태그 추출 ----------------

QE_DISTILL_PROMPT = """아래는 Text-to-SQL 세션에서 있었던 대화 기록이다.
각 질문마다 모델이 처음에 어떻게 틀렸고, 사람의 힌트를 받은 뒤 어떻게 고쳐졌는지가 담겨 있다.

너의 임무: 앞으로 비슷한 질문에 다시 틀리지 않기 위해 기록해둘 가치가 있는 "교정된 순간"만
추출해서, 아래 형식으로만 markdown 작성해라. 다른 설명 붙이지 마라.

각 항목은 반드시 이 4개 필드를 다 채워야 한다:

## KB-NNN
- 상황: (이 지식이 필요해지는 질문 유형을 자연어로)
- 태그: (관련 테이블명, 컬럼명(스키마의 정확한 이름), 관련 SQL 요소(JOIN/DISTINCT/GROUP BY/
  집계함수(COUNT,AVG,SUM 등)/날짜함수(STRFTIME 등)/서브쿼리 등), 오류유형(WRONG_TABLE/
  WRONG_COLUMN/MISSING_DISTINCT/EXTRA_DISTINCT/DATE_LOGIC/AGGREGATION_LOGIC/VALUE_ENCODING/
  JOIN_LOGIC/COLUMN_ORDER/SUBQUERY_VS_JOIN 중 해당하는 것) 을 콤마로 구분해서 나열
- 교정 내용: (원래 뭘 틀렸고, 뭐가 맞는지, 왜 그런지 - 숫자/코드값은 정확히 그대로)
- 예외: (이 규칙을 적용하면 안 되는 상황. 진지하게 고민해서 채워라. 정말 없으면 "없음")

규칙:
- 이미 맞춘 질문(처음부터 정답)은 포함하지 마라.
- 아래 "이번 세션 질문별 evidence"에 이미 나온 내용은 추출하지 마라.
- 아래 스키마의 PRIMARY KEY/FOREIGN KEY 관계로 당연히 유추 가능한 JOIN 조건은 추출하지 마라.
- 질문 하나에서만 등장하는 특정 행(row)의 값(특정 ID 숫자 등)은 추출하지 마라.
- 태그의 테이블/컬럼명은 반드시 스키마에 실제로 존재하는 정확한 이름을 써라.
- 아래 기존 KB에 이미 같은 내용이 있으면 생략해라. 반대되는 내용이 있으면, "상황"과 "예외"를
  더 구체적으로 나눠서 기존 것을 대체할 항목으로 만들어라.

### 스키마 (PK/FK 확인 및 정확한 테이블/컬럼명 확인용)
{schema_ddl}

### 기존 KB (중복/충돌 확인용)
{existing_kb_markdown}

### 이번 세션 질문별 evidence
{evidence_summary}

### 이번 세션 대화 기록
{transcript}

새로 추가할 항목이 없으면 "추가할 항목 없음"이라고만 답해라.
"""


def format_transcript_for_distill(transcripts: list[dict]) -> str:
    lines = []
    for t in transcripts:
        if len(t["turns"]) == 1 and t["turns"][0]["correct"]:
            continue
        lines.append(f"### 질문: {t['question']}")
        for turn in t["turns"]:
            if "hint" in turn:
                lines.append(f"- 사람 힌트: {turn['hint']}")
            lines.append(f"- 시도 {turn['attempt']} SQL: {turn['sql']} (정답 여부: {turn['correct']})")
        lines.append(f"- 최종 정답 SQL: {t['gold_sql']}")
        lines.append("")
    return "\n".join(lines) if lines else "(이번 배치에서 교정이 발생한 질문 없음)"


def load_evidence_map(db_id: str, batch: str) -> dict:
    path = SPLIT_DIR / f"{db_id}_{batch}.json"
    if not path.exists():
        return {}
    with open(path, encoding="utf-8") as f:
        questions = json.load(f)
    return {str(q["question_id"]): q.get("evidence", "") for q in questions}


def format_evidence_summary(transcripts: list[dict], evidence_map: dict) -> str:
    lines = []
    for t in transcripts:
        ev = evidence_map.get(str(t["question_id"]), "")
        if ev:
            lines.append(f"- 질문: {t['question']}\n  evidence: {ev}")
    return "\n".join(lines) if lines else "(evidence 없음)"


def extract_qe_deltas(transcript: str, evidence_summary: str, schema_ddl: str, existing_kb_markdown: str) -> str:
    prompt = QE_DISTILL_PROMPT.format(
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


# ---------------- 파싱 ----------------

def parse_kb_entries(markdown_text: str) -> list[dict]:
    entries = []
    blocks = re.split(r"(?=^## KB-)", markdown_text, flags=re.MULTILINE)
    for block in blocks:
        if not block.strip().startswith("## KB-"):
            continue
        situation = _extract_field(block, "상황")
        tags_raw = _extract_field(block, "태그")
        correction = _extract_field(block, "교정 내용")
        exception = _extract_field(block, "예외")
        if not correction:
            continue
        tags = [t.strip() for t in tags_raw.split(",") if t.strip()] if tags_raw else []
        entries.append({
            "situation": situation,
            "tags": tags,
            "correction": correction,
            "exception": exception if exception and exception != "없음" else "",
        })
    return entries


def _extract_field(block: str, field_name: str) -> str:
    m = re.search(rf"-\s*{re.escape(field_name)}\s*:\s*(.+)", block)
    return m.group(1).strip() if m else ""


# ---------------- Query Expansion ----------------

QUERY_EXPANSION_PROMPT = """주어진 질문을 SQL로 풀려면 어떤 테이블, 컬럼, SQL 함수/절이 필요할지
스키마를 참고해서 예측해라. 실제 스키마에 존재하는 정확한 테이블/컬럼명 위주로,
그리고 필요해 보이는 SQL 요소(JOIN, DISTINCT, GROUP BY, 집계함수, 날짜함수, 서브쿼리 등)도
같이 나열해라. 콤마로 구분된 키워드 목록만 출력해라. 설명 붙이지 마라.

### 스키마
{schema_ddl}

### 질문
{question}
{evidence_line}
"""


def predict_query_elements(question: str, evidence: str, schema_ddl: str) -> list[str]:
    evidence_line = f"evidence: {evidence}" if evidence else ""
    prompt = QUERY_EXPANSION_PROMPT.format(schema_ddl=schema_ddl, question=question, evidence_line=evidence_line)
    resp = llm._client.chat.completions.create(
        model=llm.MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0,
    )
    raw = resp.choices[0].message.content.strip()
    return [t.strip() for t in raw.split(",") if t.strip()]


# ---------------- 매칭 및 주입 ----------------

def select_entries_by_tags(entries: list[dict], predicted_elements: list[str]) -> list[dict]:
    pred_lower = [p.lower() for p in predicted_elements]
    selected = []
    for e in entries:
        tags_lower = [t.lower() for t in e["tags"]]
        hit = any(p in t or t in p for p in pred_lower for t in tags_lower)
        if hit:
            selected.append(e)
    return selected


def build_kb_text(selected: list[dict]) -> str:
    lines = []
    for e in selected:
        line = f"- {e['correction']}"
        if e["exception"]:
            line += f" (단, {e['exception']})"
        lines.append(line)
    return "\n".join(lines)


# ---------------- 평가 ----------------

def load_split(db_id: str, split_name: str) -> list[dict]:
    with open(SPLIT_DIR / f"{db_id}_{split_name}.json", encoding="utf-8") as f:
        return json.load(f)


def evaluate(db_id: str, schema_ddl: str, questions: list[dict], entries: list[dict]) -> tuple[float, dict]:
    correctness = {}
    for q in questions:
        if entries:
            predicted_elements = predict_query_elements(q["question"], q.get("evidence", ""), schema_ddl)
            selected = select_entries_by_tags(entries, predicted_elements)
            kb_text = build_kb_text(selected)
        else:
            kb_text = ""
        predicted = llm.generate_sql(q["question"], q.get("evidence", ""), schema_ddl, kb_text=kb_text)
        correctness[str(q["question_id"])] = int(db.check_correct(db_id, predicted, q["SQL"]))
    acc = sum(correctness.values()) / len(correctness) if correctness else 0.0
    return acc, correctness


def save_result(record: dict):
    RESULTS_DIR.mkdir(exist_ok=True)
    existing = []
    if QE_RESULTS_PATH.exists():
        with open(QE_RESULTS_PATH, encoding="utf-8") as f:
            existing = json.load(f)
    existing.append(record)
    with open(QE_RESULTS_PATH, "w", encoding="utf-8") as f:
        json.dump(existing, f, ensure_ascii=False, indent=2)


def main():
    for db_id in TARGET_DBS:
        print(f"\n{'#'*60}\n# {db_id} (Query Expansion + 구조화 태그: Raw -> R1 -> R2 -> R3)\n{'#'*60}")
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

                delta_text = extract_qe_deltas(transcript_text, evidence_summary, schema_ddl, kb_markdown)

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
            (KB_DIR / f"{db_id}_kb_qe_{round_name}.md").write_text(kb_markdown + "\n", encoding="utf-8")

            acc, correctness = evaluate(db_id, schema_ddl, test_qs, entries)
            delta = acc - raw_acc
            print(f"[{round_name}] {acc:.1%}  (Raw 대비 {delta:+.1%}p, 누적 항목 {len(entries)}개)")
            save_result({"db_id": db_id, "condition": round_name, "accuracy": acc, "correctness": correctness,
                         "n_entries": len(entries)})

    print("\n완료. results/round_results_qe.json, kb/*_kb_qe_*.md 확인하세요.")


if __name__ == "__main__":
    main()