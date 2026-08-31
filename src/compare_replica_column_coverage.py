"""
compare_replica_column_coverage.py

구조(JOIN 수, 조건절 수 등)는 복제DB1=복제DB2로 완전히 같다는 게 이미 확인됐는데도
정답률이 크게 다른 이유를 확인하기 위한 스크립트. 가설: 라운드1 KB가 특정 컬럼들
(예: LDH, HGB 등 자주 다룬 검사항목)은 잘 커버하는데 다른 컬럼(예: 드물게 나온 항목)은
거의 안 다뤄서, "그 라운드에서 우연히 어떤 컬럼이 많이 뽑혔느냐"에 따라 정답률이
크게 갈릴 수 있다.

라운드1 KB 텍스트(상황+교정 내용)에 실제로 언급되는 스키마 컬럼/테이블을 모으고,
복제DB1/복제DB2 각각의 gold SQL이 그 "커버된" 컬럼만 쓰는지, 아니면 KB가 한 번도
언급 안 한 컬럼을 쓰는 문항이 있는지 센다.

사용법:
    python3 src/compare_replica_column_coverage.py --db thrombosis_prediction
    python3 src/compare_replica_column_coverage.py   # 3개 DB 전체
"""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from pathlib import Path

import db_utils as db
from build_kb_qe import TARGET_DBS
from build_kb_qe_literal_embed import extract_schema_tokens
from correct_and_accumulate_replica import load_round1_kb

SPLIT_DIR_OUT = Path("split_output")


def find_tokens_in_text(text: str, schema_tokens: list[str]) -> set[str]:
    found = set()
    for tok in schema_tokens:
        if len(tok) < 2:
            continue
        if re.search(r"\b" + re.escape(tok) + r"\b", text, re.IGNORECASE):
            found.add(tok)
    return found


def analyze_db(db_id: str):
    schema_ddl = db.get_schema_ddl(db_id)
    schema_tokens = extract_schema_tokens(schema_ddl)

    entries, _ = load_round1_kb(db_id)
    covered = set()
    for e in entries:
        covered |= find_tokens_in_text(e["situation"] + " " + e["correction"], schema_tokens)

    print(f"\n{'='*60}\n{db_id}\n{'='*60}")
    print(f"라운드1 KB가 언급하는 컬럼/테이블 ({len(covered)}개):")
    print(f"  {sorted(covered)}")

    for replica_n in [1, 2]:
        path = SPLIT_DIR_OUT / f"{db_id}_replica{replica_n}.json"
        if not path.exists():
            print(f"\n[복제DB{replica_n}] 파일 없음, 건너뜀")
            continue
        with open(path, encoding="utf-8") as f:
            questions = json.load(f)

        col_counter = Counter()
        n_uncovered_q = 0
        uncovered_examples = []
        for q in questions:
            used = find_tokens_in_text(q["SQL"], schema_tokens)
            for c in used:
                col_counter[c] += 1
            uncovered = used - covered
            if uncovered:
                n_uncovered_q += 1
                uncovered_examples.append((q["question_id"], sorted(uncovered)))

        print(f"\n[복제DB{replica_n}] {len(questions)}문항")
        print(f"  KB가 한 번도 안 다룬 컬럼을 쓰는 문항: {n_uncovered_q}/{len(questions)} "
              f"({n_uncovered_q/len(questions):.1%})")
        if uncovered_examples:
            print("  예시(최대 8개):")
            for qid, cols in uncovered_examples[:8]:
                print(f"    [{qid}] 미커버 컬럼: {cols}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", choices=TARGET_DBS, default=None)
    args = parser.parse_args()
    dbs = [args.db] if args.db else TARGET_DBS
    for db_id in dbs:
        analyze_db(db_id)


if __name__ == "__main__":
    main()