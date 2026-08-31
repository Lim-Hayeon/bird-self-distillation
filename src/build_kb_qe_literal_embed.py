"""
build_kb_qe_literal_embed.py

build_kb_qe_literal.py에서 검색 방식만 통째로 교체한 버전.

기존: predict_query_elements(QE) + select_entries_by_tags(태그 아무거나 1개 겹치면 OR로 선택)
이번: 임베딩 기반 top-k 검색 + masking

바뀐 이유: 태그 매칭(OR)은 과검색(77~100%)의 직접 원인이었음. 검색을 손보기로 하면서,
DAIL-SQL / XiYan-SQL 등 최신 Text-to-SQL 논문들이 few-shot 예시 검색에 실제로 쓰는
"Masked Question Similarity(MQS)" 방식을 채택함:
  - 질문을 그대로 임베딩하면 테이블명/컬럼명/구체적 값 같은 그 상황에만 해당하는 디테일이
    유사도 계산에 노이즈로 끼어들어서 검색 품질을 떨어뜨림 (예: LDH 질문과 CPK 질문은
    구조가 똑같아도 컬럼명이 달라서 raw 임베딩 유사도가 낮게 나올 수 있음)
  - 그래서 임베딩하기 전에 질문에서 스키마 토큰(테이블/컬럼명), 문자열 리터럴, 숫자를
    [SCHEMA]/[STR]/[NUM] 같은 플레이스홀더로 마스킹해서 "질문의 구조"만 남긴 다음
    그 마스킹된 텍스트로 유사도를 잰다.
  - literal KB의 상황(situation) 필드는 원본 질문을 그대로 인용하고 있어서
    (질문: "..." 형태), 이 마스킹+임베딩 비교가 자연스럽게 적용됨.

동작:
  1. 스키마 DDL에서 테이블/컬럼명을 추출 (extract_schema_tokens)
  2. 질문과 각 KB 엔트리의 situation을 마스킹 (mask_text)
  3. 둘 다 임베딩(OpenAI text-embedding-3-small)해서 코사인 유사도로 top-k만 선택
  4. 선택된 엔트리를 build_kb_qe_literal.build_kb_text_literal()로 그대로 주입

임베딩은 마스킹된 텍스트를 키로 캐싱해서, 같은 질문/같은 엔트리가 여러 라운드·여러 k값에
걸쳐 재사용될 때 중복 API 호출을 피함 (k를 여러 개 스윕해도 임베딩은 한 번만 계산됨,
바뀌는 건 top-k 자르는 기준뿐이라 SQL 생성 호출만 k별로 새로 필요함).

기존 kb/*.md, results/round_results*.json, build_kb_qe.py, build_kb_qe_literal.py는
전혀 안 건드림.

새 KB: kb/{db_id}_kb_qe_literal_embed_R1.md / _R2.md / _R3.md
새 결과: results/round_results_qe_literal_embed.json (레코드마다 "k" 필드 포함)

사용법 (리포 루트에서):
    python3 src/build_kb_qe_literal_embed.py --k 8                 # k=8 하나만 먼저
    python3 src/build_kb_qe_literal_embed.py --k 5 7 9 11          # k 스윕 (시간 오래 걸림)
"""

from __future__ import annotations

import argparse
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
)
from build_kb_qe_literal import (
    extract_qe_deltas_literal,
    build_kb_text_literal,
)

KB_DIR = Path("kb")
RESULTS_DIR = Path("results")
EMBEDDING_MODEL = "text-embedding-3-small"

_embedding_cache: dict[str, list[float]] = {}


# ---------------- 스키마 토큰 추출 (테이블/컬럼명 마스킹용) ----------------

_SQL_KEYWORDS_SKIP = {
    "PRIMARY", "FOREIGN", "KEY", "CONSTRAINT", "UNIQUE", "CHECK", "REFERENCES",
    "NOT", "NULL", "DEFAULT", "AUTOINCREMENT",
}


def extract_schema_tokens(schema_ddl: str) -> list[str]:
    """CREATE TABLE DDL 텍스트에서 테이블명 + 컬럼명을 뽑는다 (마스킹 대상 토큰)."""
    tokens: set[str] = set()

    for m in re.finditer(r'CREATE\s+TABLE\s+["`\[]?([A-Za-z_][\w]*)["`\]]?\s*\(', schema_ddl, re.IGNORECASE):
        tokens.add(m.group(1))

    for block in re.finditer(
        r'CREATE\s+TABLE\s+["`\[]?[\w]+["`\]]?\s*\((.*)\)\s*$',
        schema_ddl, re.IGNORECASE | re.DOTALL,
    ):
        body = block.group(1)
        # 단순 콤마 분리 (컬럼 정의 안에 괄호가 중첩되는 경우는 드물어서 근사치로 충분)
        depth = 0
        parts, current = [], []
        for ch in body:
            if ch == "(":
                depth += 1
            elif ch == ")":
                depth -= 1
            if ch == "," and depth == 0:
                parts.append("".join(current))
                current = []
            else:
                current.append(ch)
        parts.append("".join(current))

        for part in parts:
            part = part.strip()
            m = re.match(r'["`\[]?([A-Za-z_][\w\-]*)["`\]]?\s+', part)
            if m:
                name = m.group(1)
                if name.upper() not in _SQL_KEYWORDS_SKIP:
                    tokens.add(name)

    return sorted(tokens, key=len, reverse=True)  # 긴 토큰 먼저 치환해야 부분 중첩 문제가 줄어듦


# ---------------- 마스킹 ----------------

def mask_text(text: str, schema_tokens: list[str]) -> str:
    masked = text
    for tok in schema_tokens:
        if len(tok) < 2:
            continue
        masked = re.sub(r"\b" + re.escape(tok) + r"\b", "[SCHEMA]", masked, flags=re.IGNORECASE)
    masked = re.sub(r"'[^']*'|\"[^\"]*\"", "[STR]", masked)
    masked = re.sub(r"\b\d+\.?\d*\b", "[NUM]", masked)
    return masked


# ---------------- 임베딩 + 코사인 유사도 ----------------

def get_embedding(text: str) -> list[float]:
    if text not in _embedding_cache:
        resp = llm._client.embeddings.create(model=EMBEDDING_MODEL, input=text)
        _embedding_cache[text] = resp.data[0].embedding
    return _embedding_cache[text]


def cosine_similarity(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = sum(x * x for x in a) ** 0.5
    norm_b = sum(x * x for x in b) ** 0.5
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


def select_entries_by_embedding_topk(entries: list[dict], question: str,
                                      schema_tokens: list[str], k: int) -> list[dict]:
    q_masked = mask_text(question, schema_tokens)
    q_emb = get_embedding(q_masked)

    scored = []
    for e in entries:
        e_masked = mask_text(e["situation"], schema_tokens)
        e_emb = get_embedding(e_masked)
        sim = cosine_similarity(q_emb, e_emb)
        scored.append((sim, e))
    scored.sort(key=lambda x: x[0], reverse=True)
    return [e for _, e in scored[:k]]


# ---------------- 평가 (build_kb_qe_literal.py와 동일 흐름) ----------------

def load_split(db_id: str, split_name: str) -> list[dict]:
    with open(SPLIT_DIR / f"{db_id}_{split_name}.json", encoding="utf-8") as f:
        return json.load(f)


def evaluate(db_id: str, schema_ddl: str, questions: list[dict], entries: list[dict],
             schema_tokens: list[str], k: int) -> tuple[float, dict]:
    correctness = {}
    for q in questions:
        if entries:
            selected = select_entries_by_embedding_topk(entries, q["question"], schema_tokens, k)
            kb_text = build_kb_text_literal(selected)
        else:
            kb_text = ""
        predicted = llm.generate_sql(q["question"], q.get("evidence", ""), schema_ddl, kb_text=kb_text)
        correctness[str(q["question_id"])] = int(db.check_correct(db_id, predicted, q["SQL"]))
    acc = sum(correctness.values()) / len(correctness) if correctness else 0.0
    return acc, correctness


def save_result(path: Path, record: dict):
    RESULTS_DIR.mkdir(exist_ok=True)
    existing = []
    if path.exists():
        with open(path, encoding="utf-8") as f:
            existing = json.load(f)
    existing.append(record)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(existing, f, ensure_ascii=False, indent=2)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--k", type=int, nargs="+", default=[8],
                         help="top-k 값 (여러 개 주면 스윕, 예: --k 5 7 9 11)")
    args = parser.parse_args()

    results_path = RESULTS_DIR / "round_results_qe_literal_embed.json"

    for db_id in TARGET_DBS:
        print(f"\n{'#'*60}\n# {db_id} (literal + 임베딩 top-k 검색, k={args.k}: Raw -> R1 -> R2 -> R3)\n{'#'*60}")
        schema_ddl = db.get_schema_ddl(db_id)
        schema_tokens = extract_schema_tokens(schema_ddl)
        print(f"스키마 토큰 {len(schema_tokens)}개 추출 (마스킹 대상)")
        test_qs = load_split(db_id, "test")

        raw_acc, raw_correctness = evaluate(db_id, schema_ddl, test_qs, [], schema_tokens, k=0)
        print(f"[Raw] {raw_acc:.1%}")
        save_result(results_path, {"db_id": db_id, "condition": "Raw", "k": None,
                                    "accuracy": raw_acc, "correctness": raw_correctness})

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
                    print(f"  [{round_name}] 새 항목 {len(new_entries)}개 추출 (누적 {len(entries)}개)")
                else:
                    print(f"  [{round_name}] 새 항목 없음")
            else:
                print(f"  [경고] {transcript_path} 없음, 이 단계는 이전 상태 유지")

            KB_DIR.mkdir(exist_ok=True)
            (KB_DIR / f"{db_id}_kb_qe_literal_embed_{round_name}.md").write_text(kb_markdown + "\n", encoding="utf-8")

            for k in args.k:
                acc, correctness = evaluate(db_id, schema_ddl, test_qs, entries, schema_tokens, k)
                delta = acc - raw_acc
                print(f"[{round_name} k={k}] {acc:.1%}  (Raw 대비 {delta:+.1%}p)")
                save_result(results_path, {"db_id": db_id, "condition": round_name, "k": k,
                                            "accuracy": acc, "correctness": correctness,
                                            "n_entries": len(entries)})

    print(f"\n완료. {results_path}, kb/*_kb_qe_literal_embed_*.md 확인하세요.")


if __name__ == "__main__":
    main()