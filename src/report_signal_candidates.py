"""
report_signal_candidates.py

evaluate_structural_match.py의 6개 위험 신호는 실제 오답 사례를 사람이 하나하나 읽으며
발견한 것 - 이게 "새 DB마다 사람이 다시 찾아야 한다"는 재현성 문제로 지적됨.

근데 "발견" 자체는 자동화할 수 있다: KB의 모든 오답->정답 쌍에서 어떤 토큰이 가장
자주 "정답에서만 생기는지/오답에서만 사라지는지"를 빈도로 집계하면, 사람이 사례를
하나하나 안 읽어도 "이 DB에서 반복되는 패턴 후보"가 순위표로 바로 나온다.

이 스크립트는 이 "빈도 집계 기반 발견"이 실제로 우리가 오늘 사람이 발견한 신호들
(YEAR, SELECT_STAR, DISTINCT)을 상위권에 올려주는지 검증한다 - 검증되면, 앞으로
새 DB에서는 "사례 읽기" 대신 "이 순위표 보고 안전조건만 확인"하는 준자동 절차로
방법론을 재서술할 수 있다.

사용법:
    python3 src/report_signal_candidates.py --db thrombosis_prediction
    python3 src/report_signal_candidates.py --db formula_1
    python3 src/report_signal_candidates.py --db card_games
"""

from __future__ import annotations

import argparse
from collections import Counter

import db_utils as db
from build_kb_qe import TARGET_DBS
from correct_and_accumulate_replica import build_accumulated_kb
from evaluate_structural_match import compute_signal_diff


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", required=True, choices=TARGET_DBS)
    parser.add_argument("--top-n", type=int, default=10)
    args = parser.parse_args()

    schema_ddl = db.get_schema_ddl(args.db)
    entries, _ = build_accumulated_kb(args.db, schema_ddl, through_replica=1)
    print(f"KB(라운드1+복제DB1): {len(entries)}개 엔트리\n")

    added_counter: Counter[str] = Counter()
    removed_counter: Counter[str] = Counter()
    examples: dict[str, str] = {}

    for e in entries:
        added, removed = compute_signal_diff(e["correction"])
        for tok in added:
            added_counter[tok] += 1
            examples.setdefault(f"added:{tok}", e["situation"][:70])
        for tok in removed:
            removed_counter[tok] += 1
            examples.setdefault(f"removed:{tok}", e["situation"][:70])

    print(f"{'='*70}\n[오답에서 사라진 토큰 - '이걸 없애야 한다'는 패턴] Top {args.top_n}\n{'='*70}")
    for tok, count in removed_counter.most_common(args.top_n):
        print(f"  {tok:20s} {count:3d}회   예: {examples.get(f'removed:{tok}', '')}")

    print(f"\n{'='*70}\n[정답에서 새로 생긴 토큰 - '이걸 추가해야 한다'는 패턴] Top {args.top_n}\n{'='*70}")
    for tok, count in added_counter.most_common(args.top_n):
        print(f"  {tok:20s} {count:3d}회   예: {examples.get(f'added:{tok}', '')}")


if __name__ == "__main__":
    main()