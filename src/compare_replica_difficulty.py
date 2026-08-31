"""
compare_replica_difficulty.py

복제DB1과 복제DB2의 gold SQL을 구조적으로(조인 수, 서브쿼리 여부, 집계함수, 조건절
개수 등) 비교해서, 정말로 난이도 차이가 있는지 LLM 판단 없이 순수 텍스트 분석으로
확인한다. (지금까지 나온 정답률 차이로 "어려웠을 것"이라고 추측만 했었는데, 이건
그 추측 자체를 검증하는 것.)

사용법:
    python3 src/compare_replica_difficulty.py --db thrombosis_prediction
    python3 src/compare_replica_difficulty.py          # 3개 DB 전체
"""

from __future__ import annotations

import argparse
import json
import re
import statistics
from pathlib import Path

from build_kb_qe import TARGET_DBS

SPLIT_DIR_OUT = Path("split_output")


def analyze_sql(sql: str) -> dict:
    upper = sql.upper()
    return {
        "n_joins": len(re.findall(r"\bJOIN\b", upper)),
        "has_subquery": upper.count("SELECT") > 1,
        "has_distinct": "DISTINCT" in upper,
        "has_groupby": "GROUP BY" in upper,
        "has_orderby": "ORDER BY" in upper,
        "has_aggregate": bool(re.search(r"\b(COUNT|SUM|AVG|MAX|MIN)\s*\(", upper)),
        "has_date_func": bool(re.search(r"STRFTIME|DATE\(", upper)),
        "has_case": "CASE" in upper,
        "n_conditions": len(re.findall(r"\bAND\b|\bOR\b", upper)),
        "sql_length": len(sql),
    }


def summarize(sqls: list[str]) -> dict:
    analyses = [analyze_sql(s) for s in sqls]
    n = len(analyses)
    if n == 0:
        return {}
    summary = {"n": n}
    for key in ["n_joins", "n_conditions", "sql_length"]:
        vals = [a[key] for a in analyses]
        summary[key] = {"mean": statistics.mean(vals), "median": statistics.median(vals)}
    for key in ["has_subquery", "has_distinct", "has_groupby", "has_orderby", "has_aggregate", "has_case", "has_date_func"]:
        summary[key] = sum(a[key] for a in analyses) / n
    return summary


def print_comparison(db_id: str, summary1: dict, summary2: dict):
    print(f"\n{'='*60}\n{db_id}\n{'='*60}")
    print(f"{'지표':30s} {'복제DB1':>12s} {'복제DB2':>12s}")
    print(f"{'문항 수':30s} {summary1['n']:>12d} {summary2['n']:>12d}")
    for key, label in [("n_joins", "평균 JOIN 수"), ("n_conditions", "평균 조건절(AND/OR) 수"),
                        ("sql_length", "평균 SQL 길이(문자)")]:
        v1, v2 = summary1[key]["mean"], summary2[key]["mean"]
        diff = v2 - v1
        print(f"{label:30s} {v1:>12.2f} {v2:>12.2f}   (차이: {diff:+.2f})")
    for key, label in [("has_subquery", "서브쿼리 있는 비율"), ("has_distinct", "DISTINCT 쓰는 비율"),
                        ("has_groupby", "GROUP BY 쓰는 비율"), ("has_orderby", "ORDER BY 쓰는 비율"),
                        ("has_aggregate", "집계함수 쓰는 비율"), ("has_case", "CASE문 쓰는 비율"),
                        ("has_date_func", "날짜함수 쓰는 비율")]:
        v1, v2 = summary1[key], summary2[key]
        diff = v2 - v1
        print(f"{label:30s} {v1:>11.1%} {v2:>11.1%}   (차이: {diff:+.1%}p)")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", choices=TARGET_DBS, default=None)
    args = parser.parse_args()

    dbs = [args.db] if args.db else TARGET_DBS
    for db_id in dbs:
        path1 = SPLIT_DIR_OUT / f"{db_id}_replica1.json"
        path2 = SPLIT_DIR_OUT / f"{db_id}_replica2.json"
        if not path1.exists() or not path2.exists():
            print(f"[{db_id}] 복제DB1/2 파일 없음, 건너뜀")
            continue
        with open(path1, encoding="utf-8") as f:
            sqls1 = [q["SQL"] for q in json.load(f)]
        with open(path2, encoding="utf-8") as f:
            sqls2 = [q["SQL"] for q in json.load(f)]

        summary1 = summarize(sqls1)
        summary2 = summarize(sqls2)
        print_comparison(db_id, summary1, summary2)


if __name__ == "__main__":
    main()