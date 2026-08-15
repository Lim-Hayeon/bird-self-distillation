"""
bird_split.py
BIRD Mini-Dev 질문을 DB별로 Test / T1 / T2 / T3로 층화추출 분할한다.
층화 기준: mini-dev가 기본 제공하는 difficulty 라벨(simple/moderate/challenging)
          (각 그룹의 난이도 구성비가 전체 난이도 구성비와 비슷하게 유지되도록 함)

baseline을 먼저 돌릴 필요 없음 - difficulty는 문제 자체에 딸린 정적 메타데이터.

사용법:
    python3 bird_split.py

출력:
    split_output/{db_id}_test.json
    split_output/{db_id}_T1.json
    split_output/{db_id}_T2.json
    split_output/{db_id}_T3.json
"""

from __future__ import annotations

import json
import random
from collections import defaultdict
from pathlib import Path

random.seed(42)  # 재현성 고정

# ---------------- 설정 (경로 확인 후 수정) ----------------
QUESTIONS_PATH = "data/mini_dev_data/mini_dev_sqlite.json"
DIFFICULTY_FIELD = "difficulty"                # TODO: 실제 필드 이름이 다르면 수정 (보통 simple/moderate/challenging)
OUTPUT_DIR = Path("split_output")

TARGET_DBS = ["thrombosis_prediction", "formula_1", "card_games"]

# db_id: {"test": n, "T1": n, "T2": n, "T3": n}
SPLIT_SIZES = {
    "thrombosis_prediction": {"test": 12, "T1": 13, "T2": 13, "T3": 12},
    "formula_1":             {"test": 15, "T1": 17, "T2": 17, "T3": 17},
    "card_games":            {"test": 12, "T1": 14, "T2": 13, "T3": 13},
}


def load_questions(path: str) -> list[dict]:
    """BIRD Mini-Dev 질문 파일 로드. 각 항목은 최소
    {"question_id": ..., "db_id": ..., "question": ..., "SQL": ..., "difficulty": ...} 형태를 기대함."""
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def stratified_split_by_difficulty(questions: list[dict], sizes: dict) -> dict:
    """
    questions를 sizes에 지정된 개수만큼 "test", "T1", "T2", "T3" 그룹으로 나누되,
    각 그룹의 difficulty 구성비가 전체 difficulty 구성비와 비슷하게 유지되도록
    층화추출한다. 그룹 크기는 sizes에 지정된 값과 정확히 일치시키는 것을 우선한다.
    """
    total = len(questions)
    size_sum = sum(sizes.values())
    if size_sum != total:
        print(f"  [경고] 분할 크기 합({size_sum}) != 전체 문항 수({total}). "
              f"남거나 모자란 만큼은 사용되지 않거나 오류가 날 수 있습니다.")

    # difficulty별로 풀 구성 + 셔플
    pools = defaultdict(list)
    for q in questions:
        pools[q.get(DIFFICULTY_FIELD, "unknown")].append(q)
    for lst in pools.values():
        random.shuffle(lst)

    overall_ratio = {d: len(lst) / total for d, lst in pools.items()} if total else {}
    categories = list(pools.keys())
    group_names = list(sizes.keys())

    result = {}
    for name in group_names:
        target = sizes[name]

        # 1) 전체 난이도 비율 기준으로 반올림 배정 (남은 풀 넘지 않게 clamp)
        counts = {d: min(round(overall_ratio[d] * target), len(pools[d])) for d in categories}

        # 2) 목표 개수(target)에 정확히 맞도록 1개씩 순서대로 보정
        diff_amt = target - sum(counts.values())
        i = 0
        while diff_amt != 0 and i < 10000:
            d = categories[i % len(categories)]
            if diff_amt > 0 and counts[d] < len(pools[d]):
                counts[d] += 1
                diff_amt -= 1
            elif diff_amt < 0 and counts[d] > 0:
                counts[d] -= 1
                diff_amt += 1
            i += 1
        if diff_amt != 0:
            print(f"  [경고] {name} 배정이 목표({target})에 못 미침 (부족 {diff_amt}개). "
                  f"특정 난이도 문항이 부족한 것일 수 있습니다.")

        # 3) 실제로 풀에서 뽑아내기 (뽑은 만큼 풀에서 제거해 다음 그룹과 안 겹치게)
        group = []
        for d, n in counts.items():
            group.extend(pools[d][:n])
            pools[d] = pools[d][n:]
        random.shuffle(group)
        result[name] = group

    return result


def main():
    OUTPUT_DIR.mkdir(exist_ok=True)
    all_questions = load_questions(QUESTIONS_PATH)

    for db_id in TARGET_DBS:
        db_questions = [q for q in all_questions if q["db_id"] == db_id]
        dist = defaultdict(int)
        for q in db_questions:
            dist[q.get(DIFFICULTY_FIELD, "unknown")] += 1
        dist_str = ", ".join(f"{d}={n}" for d, n in dist.items())
        print(f"\n=== {db_id}: 전체 {len(db_questions)}문항 (난이도 분포: {dist_str}) ===")

        splits = stratified_split_by_difficulty(db_questions, SPLIT_SIZES[db_id])

        for split_name, items in splits.items():
            split_dist = defaultdict(int)
            for q in items:
                split_dist[q.get(DIFFICULTY_FIELD, "unknown")] += 1
            split_dist_str = ", ".join(f"{d}={n}" for d, n in split_dist.items())
            print(f"  {split_name}: {len(items)}개 ({split_dist_str})")

            out_path = OUTPUT_DIR / f"{db_id}_{split_name}.json"
            with open(out_path, "w", encoding="utf-8") as f:
                json.dump(items, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    main()