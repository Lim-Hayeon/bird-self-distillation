"""
debug_structural_detection.py

evaluate_structural_match.py가 formula_1에서 매칭 0개만 낸 이유를 확인한다.
실제 스키마 파싱 결과와, 실제 draft SQL 몇 개에 대한 탐지 결과를 그대로 보여준다.

사용법:
    python3 src/debug_structural_detection.py --db formula_1 --n 5
"""

from __future__ import annotations

import argparse

import db_utils as db
import llm_utils as llm
from build_kb_qe import TARGET_DBS
from evaluate_structural_match import (
    get_schema_columns,
    detect_table_column_mismatches,
    detect_missing_distinct_risk,
)
from evaluate_case_bank import load_eval_questions


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", required=True, choices=TARGET_DBS)
    parser.add_argument("--n", type=int, default=5)
    args = parser.parse_args()

    schema_ddl = db.get_schema_ddl(args.db)
    print("=" * 70)
    print("실제 스키마 DDL (앞부분)")
    print("=" * 70)
    print(schema_ddl[:1000])
    print("...(생략)..." if len(schema_ddl) > 1000 else "")

    cols = get_schema_columns(schema_ddl)
    print(f"\n{'='*70}\n파싱된 테이블 수: {len(cols)}\n{'='*70}")
    for t, c in cols.items():
        print(f"  {t} ({len(c)}개 컬럼): {sorted(c)[:10]}{' ...' if len(c) > 10 else ''}")

    questions = load_eval_questions(args.db, "replica1")[: args.n]
    print(f"\n{'='*70}\ndraft SQL {len(questions)}개 탐지 테스트\n{'='*70}")
    for q in questions:
        draft = llm.generate_sql(q["question"], q.get("evidence", ""), schema_ddl, kb_text="")
        mismatches = detect_table_column_mismatches(draft, cols)
        distinct_risk = detect_missing_distinct_risk(draft)
        print(f"\n[{q['question_id']}] {q['question'][:60]}")
        print(f"  draft SQL: {draft}")
        print(f"  테이블-컬럼 불일치: {mismatches}")
        print(f"  JOIN인데 DISTINCT 없음: {distinct_risk}")


if __name__ == "__main__":
    main()