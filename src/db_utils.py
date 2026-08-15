"""
db_utils.py
SQLite DB 스키마 추출 + SQL 실행 + execution accuracy 비교 유틸.

BIRD 표준 디렉토리 구조 가정:
    data/dev_databases/{db_id}/{db_id}.sqlite
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

DBS_ROOT = Path("data/mini_dev_data/dev_databases")

# 쿼리 하나가 너무 오래 걸리는 것을 막기 위한 안전장치 (progress handler 호출 횟수 기준)
MAX_PROGRESS_STEPS = 5_000_000


def get_db_path(db_id: str) -> Path:
    return DBS_ROOT / db_id / f"{db_id}.sqlite"


def get_schema_ddl(db_id: str) -> str:
    """sqlite_master에서 CREATE TABLE 문들을 모아 스키마 DDL 텍스트로 반환."""
    db_path = get_db_path(db_id)
    conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    try:
        cur = conn.cursor()
        cur.execute("SELECT sql FROM sqlite_master WHERE type='table' AND sql IS NOT NULL")
        rows = cur.fetchall()
        return "\n\n".join(r[0] for r in rows)
    finally:
        conn.close()


def execute_sql(db_id: str, sql: str):
    """
    SQL을 읽기 전용으로 실행하고 (rows, error) 튜플을 반환한다.
    - 성공 시: (list[tuple], None)
    - 실패/타임아웃 시: (None, "에러 메시지")
    LLM이 생성한 SQL이 DROP/UPDATE 등을 포함해도 read-only 연결이라 실제 DB는 변경되지 않는다.
    """
    db_path = get_db_path(db_id)
    conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    steps = {"n": 0}

    def _progress_handler():
        steps["n"] += 1
        return 1 if steps["n"] > MAX_PROGRESS_STEPS else 0

    conn.set_progress_handler(_progress_handler, 1000)

    try:
        cur = conn.cursor()
        cur.execute(sql)
        rows = cur.fetchall()
        return rows, None
    except sqlite3.Error as e:
        return None, str(e)
    finally:
        conn.close()


def _normalize_row(row) -> tuple:
    """비교 시 타입 차이(1 vs 1.0 vs '1')로 인한 오탐을 줄이기 위해 값을 문자열로 정규화."""
    return tuple("" if v is None else str(v) for v in row)


def results_match(pred_rows, gold_rows) -> bool:
    """execution accuracy 비교: 순서 무시, 각 행의 값 구성만 비교 (BIRD 표준 방식의 단순화 버전)."""
    if pred_rows is None or gold_rows is None:
        return False
    pred_set = sorted(_normalize_row(r) for r in pred_rows)
    gold_set = sorted(_normalize_row(r) for r in gold_rows)
    return pred_set == gold_set


def check_correct(db_id: str, predicted_sql: str, gold_sql: str) -> bool:
    """predicted_sql과 gold_sql을 각각 실행해서 결과가 일치하는지 판정."""
    pred_rows, pred_err = execute_sql(db_id, predicted_sql)
    if pred_err is not None:
        return False
    gold_rows, gold_err = execute_sql(db_id, gold_sql)
    if gold_err is not None:
        # gold SQL 자체가 에러나면 데이터 문제이니 별도로 확인 필요 (조용히 오답 처리하지 않고 예외 발생)
        raise RuntimeError(f"[{db_id}] gold SQL 실행 실패: {gold_err}\nSQL: {gold_sql}")
    return results_match(pred_rows, gold_rows)