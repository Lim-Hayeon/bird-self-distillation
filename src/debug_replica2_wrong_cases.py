"""
debug_replica2_wrong_cases.py

evaluate_structural_match.py(라운드1+복제DB1 KB, 구조검사 방식)로 복제DB2를 풀어서
여전히 틀린 문항들을 골라, 예측 SQL / gold SQL / evidence / 각각 실행 결과를 나란히
보여준다. 목적: 모델이 진짜 틀린 건지, gold SQL 자체가 evidence랑 안 맞거나 이상한
(데이터셋 결함) 건지 사람이 직접 판단하기 위함.

사용법:
    python3 src/debug_replica2_wrong_cases.py --db thrombosis_prediction
"""

from __future__ import annotations

import argparse

import db_utils as db
import llm_utils as llm
from build_kb_qe import TARGET_DBS
from build_kb_qe_literal import build_kb_text_literal
from correct_and_accumulate_replica import build_accumulated_kb
from evaluate_structural_match import (
    get_schema_columns,
    select_by_structural_risk,
    load_eval_questions,
    DEFAULT_K,
)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", required=True, choices=TARGET_DBS)
    parser.add_argument("--k", type=int, default=DEFAULT_K)
    args = parser.parse_args()

    schema_ddl = db.get_schema_ddl(args.db)
    schema_columns = get_schema_columns(schema_ddl)

    entries, _ = build_accumulated_kb(args.db, schema_ddl, through_replica=1)
    print(f"KB(라운드1+복제DB1): {len(entries)}개 엔트리\n")

    questions = load_eval_questions(args.db, "replica2")

    n_wrong = 0
    for q in questions:
        question, evidence, gold = q["question"], q.get("evidence", ""), q["SQL"]

        draft_sql = llm.generate_sql(question, evidence, schema_ddl, kb_text="")
        selected = select_by_structural_risk(entries, draft_sql, schema_columns, args.k, question=question)

        if not selected:
            predicted = draft_sql
        else:
            kb_text = build_kb_text_literal(selected)
            history = [
                {"role": "assistant", "content": f"```sql\n{draft_sql}\n```"},
                {"role": "user", "content": "아래 참고 지식을 보고 이 SQL에 문제가 없는지 검토하고, "
                                             "필요하면 정확하게 다시 작성해주세요."},
            ]
            predicted = llm.generate_sql(question, evidence, schema_ddl, kb_text, history=history)

        correct = db.check_correct(args.db, predicted, gold)
        if correct:
            continue

        n_wrong += 1
        pred_rows, pred_err = db.execute_sql(args.db, predicted)
        gold_rows, gold_err = db.execute_sql(args.db, gold)

        print(f"{'='*70}\n[{q['question_id']}] {question}")
        if evidence:
            print(f"  evidence: {evidence}")
        print(f"\n  draft SQL: {draft_sql}")
        if selected:
            print(f"  매칭된 KB 엔트리 {len(selected)}개: {[e['situation'][:50] for e in selected]}")
        print(f"  최종 예측 SQL: {predicted}")
        print(f"  gold SQL: {gold}")
        if pred_err:
            print(f"  예측 SQL 실행 에러: {pred_err}")
        if gold_err:
            print(f"  gold SQL 실행 에러: {gold_err}  <- 데이터셋 자체 문제 가능성")
        if not pred_err and not gold_err:
            print(f"  예측 결과(앞 3개): {pred_rows[:3]}")
            print(f"  gold 결과(앞 3개): {gold_rows[:3]}")
        print()

    print(f"\n총 {len(questions)}문항 중 {n_wrong}개 틀림")


if __name__ == "__main__":
    main()