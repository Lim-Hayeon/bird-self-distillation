"""
analyze_results.py
results/round_results.json을 읽어서 DB별 Raw vs R1/R2/R3 정확도와
McNemar 정확검정(exact test) p-value를 계산해 표로 출력한다.

외부 통계 라이브러리 불필요 (math.comb만 사용).

사용법:
    python3 src/analyze_results.py
"""

from __future__ import annotations

import json
from math import comb
from pathlib import Path

RESULTS_PATH = Path("results/round_results.json")


def mcnemar_exact_p(b: int, c: int) -> float:
    """
    부호검정 기반 정확 McNemar 양측검정 p-value.
    b: raw=오답 -> round=정답 으로 바뀐 개수 (개선)
    c: raw=정답 -> round=오답 으로 바뀐 개수 (악화)
    """
    n = b + c
    if n == 0:
        return 1.0
    k = min(b, c)
    p = sum(comb(n, i) for i in range(0, k + 1)) * 2 / (2 ** n)
    return min(p, 1.0)


def compare(raw_correctness: dict, round_correctness: dict) -> dict:
    """두 조건의 문항별 정오답 딕셔너리를 비교해 McNemar 표(b, c)와 p-value 계산."""
    b = c = same_correct = same_wrong = 0
    for qid, raw_val in raw_correctness.items():
        round_val = round_correctness.get(qid)
        if round_val is None:
            continue  # 두 조건에 공통으로 없는 문항은 제외
        if raw_val == 0 and round_val == 1:
            b += 1
        elif raw_val == 1 and round_val == 0:
            c += 1
        elif raw_val == 1 and round_val == 1:
            same_correct += 1
        else:
            same_wrong += 1
    p = mcnemar_exact_p(b, c)
    return {"b_improved": b, "c_worsened": c, "same_correct": same_correct, "same_wrong": same_wrong, "p_value": p}


def main():
    if not RESULTS_PATH.exists():
        print(f"[에러] {RESULTS_PATH} 가 없습니다. run_experiment.py를 먼저 실행하세요.")
        return

    with open(RESULTS_PATH, encoding="utf-8") as f:
        records = json.load(f)

    by_db = {}
    for r in records:
        by_db.setdefault(r["db_id"], {})[r["condition"]] = r

    for db_id, conditions in by_db.items():
        print(f"\n{'='*60}\n{db_id}\n{'='*60}")
        if "Raw" not in conditions:
            print("  [경고] Raw 조건 결과가 없어 비교 불가")
            continue
        raw = conditions["Raw"]
        print(f"  Raw: {raw['accuracy']:.1%}")

        for round_name in ["R1", "R2", "R3"]:
            if round_name not in conditions:
                continue
            rnd = conditions[round_name]
            stat = compare(raw["correctness"], rnd["correctness"])
            sig = "*" if stat["p_value"] < 0.05 else ""
            print(f"  {round_name}: {rnd['accuracy']:.1%}  "
                  f"(Raw 대비 {rnd['accuracy']-raw['accuracy']:+.1%}p, "
                  f"개선 {stat['b_improved']} / 악화 {stat['c_worsened']}, "
                  f"McNemar p={stat['p_value']:.4f}{sig})")


if __name__ == "__main__":
    main()