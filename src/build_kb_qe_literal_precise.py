"""
build_kb_qe_literal_precise.py

build_kb_qe_literal.py에서 안 건드렸던 마지막 변수(검색 정밀도)까지 같이 손본 버전.

지금까지 확인된 것:
  - literal 내용(원본 질문+오답/정답 SQL)은 self-consistency를 26.3% -> 78.9%까지 끌어올림
  - 근데 검색은 여전히 원본 그대로라 과검색 100% (매번 KB 전체가 주입됨)
  - Test set에서는 이게 DB마다 다르게 작용함 (card_games +41.7%p, thrombosis -8.3%p)
    -> 무관한 literal 예시들이 노이즈로 섞여서 들어가는 게 변동성의 원인일 가능성

이 버전에서 바뀐 것: select_entries_by_tags()의 "태그 1개만 겹쳐도 선택" 로직을
select_entries_by_tags_precise()로 교체해서 "태그가 min_overlap개 이상 겹쳐야 선택"
하도록 바꿈. 나머지(literal distillation, literal 텍스트 주입, 평가 흐름)는
build_kb_qe_literal.py와 100% 동일.

기존 파일들은 전혀 안 건드림. build_kb_qe_literal.py의 함수(extract_qe_deltas_literal,
build_kb_text_literal)를 그대로 재사용.

새 KB: kb/{db_id}_kb_qe_literal_precise_R1.md / _R2.md / _R3.md
새 결과: results/round_results_qe_literal_precise.json

사용법 (리포 루트에서):
    python3 src/build_kb_qe_literal_precise.py
    python3 src/build_kb_qe_literal_precise.py --min-overlap 3   # 더 엄격하게 하고 싶으면
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
    predict_query_elements,
)
from build_kb_qe_literal import (
    extract_qe_deltas_literal,
    build_kb_text_literal,
)

KB_DIR = Path("kb")
RESULTS_DIR = Path("results")


# ---------------- 검색: 태그 겹침 개수 임계값 적용 ----------------

def select_entries_by_tags_precise(entries: list[dict], predicted_elements: list[str],
                                    min_overlap: int = 2) -> list[dict]:
    """기존 select_entries_by_tags와 인터페이스는 동일하되, 태그가 min_overlap개
    이상 겹쳐야 선택한다 (기존엔 1개만 겹쳐도 선택 -> 과검색의 원인이었음)."""
    pred_lower = [p.lower() for p in predicted_elements]
    selected = []
    for e in entries:
        tags_lower = [t.lower() for t in e["tags"]]
        n_overlap = sum(
            1 for t in tags_lower if any(p in t or t in p for p in pred_lower)
        )
        if n_overlap >= min_overlap:
            selected.append(e)
    return selected


# ---------------- 평가 (build_kb_qe_literal.py와 동일 로직) ----------------

def load_split(db_id: str, split_name: str) -> list[dict]:
    with open(SPLIT_DIR / f"{db_id}_{split_name}.json", encoding="utf-8") as f:
        return json.load(f)


def evaluate(db_id: str, schema_ddl: str, questions: list[dict], entries: list[dict],
             min_overlap: int) -> tuple[float, dict, list[int]]:
    correctness = {}
    n_selected_list = []
    for q in questions:
        if entries:
            predicted_elements = predict_query_elements(q["question"], q.get("evidence", ""), schema_ddl)
            selected = select_entries_by_tags_precise(entries, predicted_elements, min_overlap)
            n_selected_list.append(len(selected))
            kb_text = build_kb_text_literal(selected)
        else:
            kb_text = ""
        predicted = llm.generate_sql(q["question"], q.get("evidence", ""), schema_ddl, kb_text=kb_text)
        correctness[str(q["question_id"])] = int(db.check_correct(db_id, predicted, q["SQL"]))
    acc = sum(correctness.values()) / len(correctness) if correctness else 0.0
    return acc, correctness, n_selected_list


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
    parser.add_argument("--min-overlap", type=int, default=2,
                         help="검색에서 엔트리를 선택하려면 최소 몇 개의 태그가 겹쳐야 하는지")
    args = parser.parse_args()

    results_path = RESULTS_DIR / f"round_results_qe_literal_precise_overlap{args.min_overlap}.json"

    for db_id in TARGET_DBS:
        print(f"\n{'#'*60}\n# {db_id} (literal + 검색정밀화 min_overlap={args.min_overlap}: Raw -> R1 -> R2 -> R3)\n{'#'*60}")
        schema_ddl = db.get_schema_ddl(db_id)
        test_qs = load_split(db_id, "test")

        raw_acc, raw_correctness, _ = evaluate(db_id, schema_ddl, test_qs, [], args.min_overlap)
        print(f"[Raw] {raw_acc:.1%}")
        save_result(results_path, {"db_id": db_id, "condition": "Raw", "accuracy": raw_acc,
                                    "correctness": raw_correctness})

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
            (KB_DIR / f"{db_id}_kb_qe_literal_precise_{round_name}.md").write_text(kb_markdown + "\n", encoding="utf-8")

            acc, correctness, n_selected_list = evaluate(db_id, schema_ddl, test_qs, entries, args.min_overlap)
            delta = acc - raw_acc
            avg_selected = sum(n_selected_list) / len(n_selected_list) if n_selected_list else 0
            avg_ratio = avg_selected / len(entries) if entries else 0
            print(f"[{round_name}] {acc:.1%}  (Raw 대비 {delta:+.1%}p, 누적 항목 {len(entries)}개, "
                  f"평균 선택 {avg_selected:.1f}개={avg_ratio:.0%})")
            save_result(results_path, {"db_id": db_id, "condition": round_name, "accuracy": acc,
                                        "correctness": correctness, "n_entries": len(entries),
                                        "avg_selected_ratio": avg_ratio})

    print(f"\n완료. {results_path}, kb/*_kb_qe_literal_precise_*.md 확인하세요.")
    print("round_results_qe.json(원본), round_results_qe_literal.json(literal만)이랑")
    print("db_id/condition 기준으로 셋 다 나란히 비교하면 됨.")


if __name__ == "__main__":
    main()