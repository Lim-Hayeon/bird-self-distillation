"""
build_kb_qe_cv.py
build_kb_qe.py의 방식(Query Expansion + 구조화 태그 + 상황/교정내용/예외 템플릿)을
3-Fold Cross-Validation으로 검증한다. T1/T2/T3를 돌아가며 held-out 평가셋으로 써서
표본을 (DB당 39개 -> 최대 3배)로 늘려 통계적 검정력을 확보한다.

힌트 재입력 없음 - 이미 저장된 results/transcripts/*.json만 재사용.
build_kb_qe.py의 추출/검색 함수를 그대로 재사용 (import만, 수정 없음).
기존 kb/*.md, results/round_results*.json은 전혀 안 건드림.

Fold 구성 (DB별 3개):
  Fold(held-out=T1): KB는 T2+T3 transcript로만 생성 -> T1에 대해 평가
  Fold(held-out=T2): KB는 T1+T3 transcript로만 생성 -> T2에 대해 평가
  Fold(held-out=T3): KB는 T1+T2 transcript로만 생성 -> T3에 대해 평가

결과: kb/{db_id}_kb_qe_cv_holdout_{fold}.md, results/round_results_qe_cv.json

비용: 3-Fold CV라 build_kb_qe.py 전체 실행보다 distillation 호출은 비슷하고,
Query Expansion+평가 호출이 held-out 3세트(원래 Test 대신 T1/T2/T3 각각) 만큼 늘어남.

사용법 (리포 루트에서):
    python3 src/build_kb_qe_cv.py
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import db_utils as db
import llm_utils as llm
from analyze_results import mcnemar_exact_p
from build_kb_qe import (
    format_transcript_for_distill,
    load_evidence_map,
    format_evidence_summary,
    extract_qe_deltas,
    parse_kb_entries,
    predict_query_elements,
    select_entries_by_tags,
    build_kb_text,
)

TARGET_DBS = ["thrombosis_prediction", "formula_1", "card_games"]
FOLDS = ["T1", "T2", "T3"]
BATCH_TO_ROUND = {"T1": "R1", "T2": "R2", "T3": "R3"}

SPLIT_DIR = Path("split_output")
TRANSCRIPTS_DIR = Path("results/transcripts")
KB_DIR = Path("kb")
RESULTS_DIR = Path("results")
QE_CV_RESULTS_PATH = RESULTS_DIR / "round_results_qe_cv.json"


def build_kb_for_fold(db_id: str, schema_ddl: str, train_batches: list[str]) -> tuple[list[dict], str]:
    entries: list[dict] = []
    kb_markdown = ""
    kb_id_counter = 1

    for batch in train_batches:
        round_name = BATCH_TO_ROUND[batch]
        transcript_path = TRANSCRIPTS_DIR / f"{db_id}_{round_name}.json"
        if not transcript_path.exists():
            print(f"    [경고] {transcript_path} 없음, 건너뜀")
            continue

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

    return entries, kb_markdown


def load_split(db_id: str, split_name: str) -> list[dict]:
    with open(SPLIT_DIR / f"{db_id}_{split_name}.json", encoding="utf-8") as f:
        return json.load(f)


def evaluate(db_id: str, schema_ddl: str, questions: list[dict], entries: list[dict] | None) -> dict:
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
    return correctness


def save_result(record: dict):
    RESULTS_DIR.mkdir(exist_ok=True)
    existing = []
    if QE_CV_RESULTS_PATH.exists():
        with open(QE_CV_RESULTS_PATH, encoding="utf-8") as f:
            existing = json.load(f)
    existing.append(record)
    with open(QE_CV_RESULTS_PATH, "w", encoding="utf-8") as f:
        json.dump(existing, f, ensure_ascii=False, indent=2)


def main():
    grand_pooled_raw: dict = {}
    grand_pooled_qe: dict = {}

    for db_id in TARGET_DBS:
        print(f"\n{'#'*60}\n# {db_id} (QE 방식, 3-Fold CV)\n{'#'*60}")
        schema_ddl = db.get_schema_ddl(db_id)

        pooled_raw: dict = {}
        pooled_qe: dict = {}

        for held_out in FOLDS:
            train_batches = [b for b in FOLDS if b != held_out]
            print(f"\n  -- Fold: held-out={held_out}, train={train_batches} --")

            entries, kb_markdown = build_kb_for_fold(db_id, schema_ddl, train_batches)
            KB_DIR.mkdir(exist_ok=True)
            (KB_DIR / f"{db_id}_kb_qe_cv_holdout_{held_out}.md").write_text(kb_markdown + "\n", encoding="utf-8")
            print(f"     KB 항목 {len(entries)}개 생성")

            held_out_qs = load_split(db_id, held_out)

            raw_correctness = evaluate(db_id, schema_ddl, held_out_qs, None)
            qe_correctness = evaluate(db_id, schema_ddl, held_out_qs, entries)

            raw_acc = sum(raw_correctness.values()) / len(raw_correctness)
            qe_acc = sum(qe_correctness.values()) / len(qe_correctness)
            print(f"     Raw: {raw_acc:.1%}  |  QE-KB: {qe_acc:.1%}  (held-out {len(held_out_qs)}문항)")

            save_result({"db_id": db_id, "fold": held_out, "condition": "Raw",
                         "accuracy": raw_acc, "correctness": raw_correctness})
            save_result({"db_id": db_id, "fold": held_out, "condition": "QEKB",
                         "accuracy": qe_acc, "correctness": qe_correctness, "n_entries": len(entries)})

            for qid, v in raw_correctness.items():
                key = f"{held_out}:{qid}"
                pooled_raw[key] = v
                grand_pooled_raw[f"{db_id}:{key}"] = v
            for qid, v in qe_correctness.items():
                key = f"{held_out}:{qid}"
                pooled_qe[key] = v
                grand_pooled_qe[f"{db_id}:{key}"] = v

        b = c = 0
        for key in pooled_raw:
            rv, qv = pooled_raw[key], pooled_qe.get(key)
            if qv is None:
                continue
            if rv == 0 and qv == 1:
                b += 1
            elif rv == 1 and qv == 0:
                c += 1
        p = mcnemar_exact_p(b, c)
        n = len(pooled_raw)
        raw_pool_acc = sum(pooled_raw.values()) / n
        qe_pool_acc = sum(pooled_qe.values()) / n
        print(f"\n  >> {db_id} 3-Fold 풀링 (N={n}): Raw {raw_pool_acc:.1%} vs QE-KB {qe_pool_acc:.1%}"
              f" | 개선 {b} / 악화 {c} | McNemar p={p:.4f}"
              f" {'(유의미)' if p < 0.05 else '(아직 유의미하지 않음)'}")

    b = c = 0
    for key in grand_pooled_raw:
        rv, qv = grand_pooled_raw[key], grand_pooled_qe.get(key)
        if qv is None:
            continue
        if rv == 0 and qv == 1:
            b += 1
        elif rv == 1 and qv == 0:
            c += 1
    p = mcnemar_exact_p(b, c)
    n = len(grand_pooled_raw)
    print(f"\n{'='*60}\n전체 3개 DB 통합 풀링 (N={n}): 개선 {b} / 악화 {c} | McNemar p={p:.4f}"
          f" {'(유의미)' if p < 0.05 else '(아직 유의미하지 않음)'}\n{'='*60}")

    print("\n완료. results/round_results_qe_cv.json, kb/*_kb_qe_cv_holdout_*.md 확인하세요.")


if __name__ == "__main__":
    main()