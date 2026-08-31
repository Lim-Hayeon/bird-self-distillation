"""
evaluate_structural_match.py

evaluate_self_correct.py(초안 SQL vs 오답SQL 임베딩)가 별로 안 통했던 이유: "DISTINCT
하나 빠진 것" 같은 작은 차이가 SQL 텍스트 전체의 "느낌"에 묻혀서 임베딩이 못 잡아냄.
그래서 임베딩을 버리고, **결정론적으로(파싱해서 확실하게) 두 가지 구조적 위험 신호를
직접 탐지**하는 방식으로 바꿈:

  1. 테이블-컬럼 불일치 (WRONG_TABLE 계열) - 이 프로젝트 내내 제일 자주, 제일 끈질기게
     재발했던 버그(예: Thrombosis를 Patient 테이블 컬럼인 것처럼 씀, 실제로는 Examination
     테이블 컬럼). draft SQL에서 "별칭.컬럼" 참조를 다 뽑아서, 그 별칭이 매핑된 실제
     테이블에 그 컬럼이 진짜 있는지 스키마와 직접 대조 - 애매함 없이 Yes/No로 확정됨.
  2. JOIN은 있는데 DISTINCT가 없음 (MISSING_DISTINCT 계열 위험 신호) - 두 번째로 흔했던
     패턴.

이 두 신호로 위험이 감지되면, 그 구체적인 컬럼명(1번) 또는 DISTINCT 관련 태그(2번)를
"직접 언급하는" KB 엔트리를 찾아서(부분 문자열 매칭, 임베딩 아님) 참고 지식으로 준다.
아무 위험도 안 감지되면 draft를 그대로 씀 - 불필요한 개입 방지.

KB 소스는 correct_and_accumulate_replica.py의 build_accumulated_kb를 그대로 재사용
(라운드1 고정 + 안전한 중복 정리 포함). 다른 평가 스크립트들은 전혀 안 건드림.

사용법:
    python3 src/evaluate_structural_match.py --db formula_1 --kb-through 0 --eval-on replica1 --repeat 3
    python3 src/evaluate_structural_match.py --db formula_1 --kb-through 1 --eval-on replica2 --repeat 3
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

import db_utils as db
import llm_utils as llm
from build_kb_qe import TARGET_DBS, SPLIT_DIR
from build_kb_qe_literal import build_kb_text_literal
from correct_and_accumulate_replica import build_accumulated_kb, SPLIT_DIR_OUT

RESULTS_PATH = Path("results/round_results_structural_match.json")
DEFAULT_K = 2

_SQL_KEYWORDS_SKIP = {"PRIMARY", "FOREIGN", "KEY", "CONSTRAINT", "UNIQUE", "CHECK",
                      "REFERENCES", "NOT", "NULL", "DEFAULT", "AUTOINCREMENT"}
_ALIAS_SKIP_WORDS = {"ON", "WHERE", "INNER", "LEFT", "RIGHT", "OUTER", "JOIN",
                     "GROUP", "ORDER", "BY", "AND", "OR", "AS", "SELECT", "FROM"}


def get_schema_columns(schema_ddl: str) -> dict[str, set[str]]:
    tables: dict[str, set[str]] = {}
    blocks = re.split(r"(?=CREATE\s+TABLE)", schema_ddl, flags=re.IGNORECASE)
    for block in blocks:
        m = re.match(r'\s*CREATE\s+TABLE\s+["`\[]?([A-Za-z_]\w*)["`\]]?\s*\(', block, re.IGNORECASE)
        if not m:
            continue
        table_name = m.group(1)

        start = m.end()  # 여는 '(' 바로 다음 위치
        depth = 1
        i = start
        while i < len(block) and depth > 0:
            if block[i] == "(":
                depth += 1
            elif block[i] == ")":
                depth -= 1
            i += 1
        body = block[start:i - 1]  # 대응하는 닫는 ')' 직전까지 (다른 테이블 안 섞임)

        depth2 = 0
        parts, current = [], []
        for ch in body:
            if ch == "(":
                depth2 += 1
            elif ch == ")":
                depth2 -= 1
            if ch == "," and depth2 == 0:
                parts.append("".join(current))
                current = []
            else:
                current.append(ch)
        parts.append("".join(current))

        columns = set()
        for part in parts:
            part = part.strip()
            cm = re.match(r'["`\[]?([A-Za-z_][\w\-]*)["`\]]?\s+', part)
            if cm and cm.group(1).upper() not in _SQL_KEYWORDS_SKIP:
                columns.add(cm.group(1))
        tables[table_name] = columns
    return tables


def extract_table_aliases(sql: str, valid_tables: set[str]) -> dict[str, str]:
    aliases: dict[str, str] = {}
    for m in re.finditer(
        r'\b(?:FROM|JOIN)\s+["`\[]?(\w+)["`\]]?(?:\s+AS)?\s*([A-Za-z_]\w*)?',
        sql, re.IGNORECASE,
    ):
        table_raw, alias_raw = m.group(1), m.group(2)
        table = next((t for t in valid_tables if t.upper() == table_raw.upper()), None)
        if not table:
            continue
        aliases[table] = table
        if alias_raw and alias_raw.upper() not in _ALIAS_SKIP_WORDS and alias_raw.upper() != table.upper():
            aliases[alias_raw] = table
    return aliases


def detect_table_column_mismatches(sql: str, schema_columns: dict[str, set[str]]) -> list[tuple[str, str]]:
    aliases = extract_table_aliases(sql, set(schema_columns.keys()))
    mismatches = []
    for m in re.finditer(r"\b([A-Za-z_]\w*)\.([A-Za-z_][\w\-]*)\b", sql):
        alias, col = m.group(1), m.group(2)
        if alias not in aliases:
            continue
        table = aliases[alias]
        valid_cols_upper = {c.upper() for c in schema_columns.get(table, set())}
        if col.upper() not in valid_cols_upper:
            mismatches.append((table, col))
    return mismatches


FIXED_ERROR_CATEGORIES = {
    "WRONG_TABLE", "WRONG_COLUMN", "MISSING_DISTINCT", "EXTRA_DISTINCT",
    "DATE_LOGIC", "AGGREGATION_LOGIC", "VALUE_ENCODING", "JOIN_LOGIC",
    "COLUMN_ORDER", "SUBQUERY_VS_JOIN",
}


def get_active_error_categories(entries: list[dict]) -> dict[str, int]:
    """이 DB의 KB에 실제로 등장하는 오류유형 태그와 엔트리 수 - 내가 눈으로 훑어서
    찾은 게 아니라, distillation 때 이미 분류해둔 카테고리를 그대로 집계한 것.
    이게 '이 DB에서 실제로 어떤 종류의 실수가 나는지'를 보여주는 데이터 기반 체크리스트."""
    counts: dict[str, int] = {}
    for e in entries:
        for t in e["tags"]:
            t_upper = t.upper()
            if t_upper in FIXED_ERROR_CATEGORIES:
                counts[t_upper] = counts.get(t_upper, 0) + 1
    return counts


def extract_mentioned_columns(text: str, schema_columns: dict[str, set[str]]) -> set[str]:
    all_columns = {c for cols in schema_columns.values() for c in cols}
    mentioned = set()
    for col in all_columns:
        if len(col) < 2:
            continue
        if re.search(r"\b" + re.escape(col) + r"\b", text, re.IGNORECASE):
            mentioned.add(col)
    return mentioned


# ==================== 자동 diff 기반 탐지 (사람이 미리 정한 카테고리 없음) ====================
# 아래 6개 결정론적 탐지기(테이블불일치/DISTINCT양방향/YEAR/SELECT*/Yes-No질문)는 전부
# 실제 오답 사례를 사람이 직접 읽고 하나씩 발견해서 손으로 만든 것 - 이러면 아직 못 본
# 새로운 버그 유형은 매번 사람이 또 찾아야 함. 그래서 "KB의 모든 오답→정답 쌍에서
# 정확히 뭐가 바뀌었는지"를 기계적으로 뽑아내고, 그 변화 패턴 자체를 범용 신호로 쓰는
# 방식을 별도로 구현함(select_by_auto_diff) - 카테고리를 사람이 미리 정의할 필요가 없어짐.

_GENERIC_SQL_WORDS = {
    "SELECT", "FROM", "WHERE", "AND", "OR", "ON", "AS", "JOIN", "INNER", "LEFT",
    "RIGHT", "OUTER", "NOT", "NULL", "IN", "LIKE", "BETWEEN", "IS", "THEN", "ELSE",
    "END", "WHEN", "ASC", "DESC", "LIMIT", "ALL", "EXISTS", "ANY", "UNION", "WITH",
    "BY", "GROUP", "ORDER", "CASE",
}


def extract_signal_tokens(sql: str) -> set[str]:
    """SQL에서 '이 교정이 실제로 뭘 바꿨는지'를 나타내는 의미있는 토큰만 추출.
    SELECT/FROM/WHERE 같은 어디에나 있는 보일러플레이트는 제외 - 함수 호출 이름
    (DISTINCT, COUNT, STRFTIME, YEAR, IIF, CAST 등), GROUP BY/ORDER BY 여부,
    SELECT * 패턴만 신호로 씀."""
    tokens = set()
    for m in re.finditer(r"\b([A-Z_][A-Z0-9_]*)\s*\(", sql.upper()):
        name = m.group(1)
        if name not in _GENERIC_SQL_WORDS:
            tokens.add(name)
    if re.search(r"\bDISTINCT\b", sql, re.IGNORECASE):
        tokens.add("DISTINCT")
    if re.search(r"\bGROUP\s+BY\b", sql, re.IGNORECASE):
        tokens.add("GROUP_BY")
    if re.search(r"\bORDER\s+BY\b", sql, re.IGNORECASE):
        tokens.add("ORDER_BY")
    if re.search(r"SELECT\s+(?:\w+\.)?\*", sql, re.IGNORECASE):
        tokens.add("SELECT_STAR")
    return tokens


def compute_signal_diff(correction: str) -> tuple[set[str], set[str]]:
    """반환: (added, removed) - 정답에서 새로 생긴 신호 토큰, 오답에서 없어진 신호 토큰.
    형식이 안 맞으면 (빈 집합, 빈 집합)."""
    if "/ 정답:" not in correction:
        return set(), set()
    wrong_part, right_part = correction.split("/ 정답:", 1)
    wrong_tokens = extract_signal_tokens(wrong_part)
    right_tokens = extract_signal_tokens(right_part)
    return right_tokens - wrong_tokens, wrong_tokens - right_tokens


def is_pure_structural_fix(correction: str, schema_columns: dict[str, set[str]]) -> bool:
    """오답과 정답이 언급하는 스키마 컬럼이 완전히 같으면(문법/함수만 바뀌고 컬럼은 그대로)
    - 이런 경우는 어떤 구체적 컬럼이든 상관없이 일반적으로 적용 가능한 교훈이라 컬럼
    겹침 요구 없이 매칭 가능(예: YEAR->STRFTIME, SELECT *->특정컬럼는 대상 컬럼이
    달라도 항상 같은 교훈)."""
    if "/ 정답:" not in correction:
        return False
    wrong_part, right_part = correction.split("/ 정답:", 1)
    wrong_cols = extract_mentioned_columns(wrong_part, schema_columns)
    right_cols = extract_mentioned_columns(right_part, schema_columns)
    return wrong_cols == right_cols


MIN_AUTO_SIGNAL_COUNT = 3  # 같은 토큰 diff가 이 정도는 반복돼야 "진짜 패턴"으로 신뢰


def query_shape_signature(sql: str) -> bool:
    """대충의 쿼리 '형태' 지문 - 지금은 집계함수(COUNT/SUM/AVG/MAX/MIN)가 SELECT 절에
    있는지만 봄. card_games에서 'COUNT(*) 안에 DISTINCT를 넣을지'가 일반 SELECT 목록의
    DISTINCT 빠뜨림과 완전히 다른 판단이라는 게 확인됐는데, 이걸 'COUNT는 예외'라고
    사람이 콕 집어 규칙을 넣는 대신 '같은 쿼리 형태끼리만 서로 비교 가능하다'는 일반
    원칙으로 일반화함 - draft와 KB 사례가 이 지문이 다르면 diff 신호를 안 믿음."""
    select_clause = re.split(r"\bFROM\b", sql, maxsplit=1, flags=re.IGNORECASE)[0]
    return bool(re.search(r"\b(COUNT|SUM|AVG|MAX|MIN)\s*\(", select_clause, re.IGNORECASE))


def select_by_auto_diff(entries: list[dict], draft_sql: str, schema_columns: dict[str, set[str]],
                         k: int) -> list[dict]:
    """카테고리를 사람이 미리 정의하지 않고, KB 데이터에서 직접 위험 신호를 뽑아냄.
    두 방향을 대칭적으로 봄:
      (a) draft가 어떤 교정의 '제거됐어야 할 토큰'(예: YEAR(, SELECT *, 불필요한 DISTINCT)을
          여전히 갖고 있는 경우
      (b) draft에 어떤 교정이 '새로 추가했던 토큰'(예: 빠뜨린 DISTINCT)이 아예 없는 경우
    각각 이 KB에서 최소 MIN_AUTO_SIGNAL_COUNT번 이상 반복되는 패턴일 때만 신뢰(우연한
    1회성 매칭 방지). draft와 KB 사례의 쿼리 형태(집계 여부)가 같을 때만 비교 가능하다고
    봄(query_shape_signature). 순수 문법 교정(컬럼 안 바뀜)이거나 SELECT_STAR면 컬럼
    겹침 없이, 아니면 컬럼 겹침을 요구."""
    draft_tokens = extract_signal_tokens(draft_sql)
    draft_columns = extract_mentioned_columns(draft_sql, schema_columns)
    draft_shape = query_shape_signature(draft_sql)

    removed_counts: dict[str, int] = {}
    added_counts: dict[str, int] = {}
    for e in entries:
        added, removed = compute_signal_diff(e["correction"])
        for tok in removed:
            removed_counts[tok] = removed_counts.get(tok, 0) + 1
        for tok in added:
            added_counts[tok] = added_counts.get(tok, 0) + 1

    selected: list[dict] = []
    seen = set()
    for e in entries:
        if len(selected) >= k:
            break
        if "/ 정답:" not in e["correction"]:
            continue
        wrong_part, _ = e["correction"].split("/ 정답:", 1)
        if query_shape_signature(wrong_part) != draft_shape:
            continue  # 집계 여부(쿼리 형태)가 다르면 이 사례는 지금 draft와 비교 불가

        added, removed = compute_signal_diff(e["correction"])
        matched_removed = removed & draft_tokens
        matched_added = added - draft_tokens

        removed_ok = bool(matched_removed) and any(
            removed_counts.get(tok, 0) >= MIN_AUTO_SIGNAL_COUNT for tok in matched_removed)
        added_ok = bool(matched_added) and any(
            added_counts.get(tok, 0) >= MIN_AUTO_SIGNAL_COUNT for tok in matched_added)
        if not removed_ok and not added_ok:
            continue

        if removed_ok and (is_pure_structural_fix(e["correction"], schema_columns) or "SELECT_STAR" in matched_removed):
            # 강한 신호(제거돼야 할 게 draft에 여전히 있음) + 순수 구조 교정일 때만
            # 컬럼 겹침 없이 허용. '추가돼야 할 게 없다'는 약한 신호(added_ok)는
            # 항상 컬럼 겹침을 요구함 - 안 그러면 완전히 무관한 사례가 "그냥 draft에
            # 없으니까"라는 이유만으로 걸려드는 문제가 실제로 확인됨.
            selected.append(e)
            seen.add(id(e))
        elif removed_ok or added_ok:
            entry_columns = extract_mentioned_columns(e["situation"] + " " + e["correction"], schema_columns)
            if draft_columns & entry_columns:
                selected.append(e)
                seen.add(id(e))

    return selected[:k]



def detect_select_star_risk(sql: str) -> bool:
    """SELECT * 나 별칭.* 패턴 - card_games KB에서 이 패턴이 나올 때마다(3번 확인) 항상
    더 적은 구체적 컬럼으로 교정됐음. 어떤 구체적 컬럼이냐와 무관하게 "SELECT * 자체가
    항상 문제"라는 일반적인 교훈이라 컬럼 겹침 없이도 안전하게 매칭 가능."""
    return bool(re.search(r"SELECT\s+(?:\w+\.)?\*", sql, re.IGNORECASE))


def detect_extra_distinct_risk(sql: str) -> bool:
    """DISTINCT가 draft에 있음 - '빠뜨림'의 반대 방향. card_games KB에 "불필요하게
    DISTINCT를 썼다"는 교정 사례가 여러 개 있는 게 확인됨(missing만 잡던 기존 탐지의
    사각지대)."""
    return "DISTINCT" in sql.upper()


def count_extra_distinct_fix_entries(entries: list[dict]) -> int:
    """오답엔 DISTINCT 있고 정답엔 없는(불필요한 DISTINCT를 뺀) 엔트리 개수."""
    count = 0
    for e in entries:
        correction = e["correction"]
        if "/ 정답:" in correction:
            wrong_part, right_part = correction.split("/ 정답:", 1)
            if "DISTINCT" in wrong_part.upper() and "DISTINCT" not in right_part.upper():
                count += 1
    return count


MIN_DISTINCT_FIX_COUNT = 3  # 이 정도는 있어야 "이 DB에서 진짜 흔한 패턴"으로 신뢰함


def count_distinct_fix_entries(entries: list[dict]) -> int:
    """오답엔 DISTINCT 없고 정답엔 있는 엔트리가 KB에 몇 개나 있는지. card_games에서
    이 숫자가 1~2개뿐인데도 개입해서 오히려 정답을 망가뜨리는 게 확인돼서, 이 신호를
    쓸지 말지 자체를 이 개수로 게이팅함(1~2개는 우연일 수 있음, 여러 개면 진짜 패턴)."""
    count = 0
    for e in entries:
        correction = e["correction"]
        if "/ 정답:" in correction:
            wrong_part, right_part = correction.split("/ 정답:", 1)
            if "DISTINCT" in right_part.upper() and "DISTINCT" not in wrong_part.upper():
                count += 1
    return count


def detect_missing_distinct_risk(sql: str) -> bool:
    upper = sql.upper()
    return "JOIN" in upper and "DISTINCT" not in upper


def is_count_only_query(sql: str) -> bool:
    """SELECT 절이 COUNT(...) 위주인지 - DISTINCT를 COUNT() 안에 넣을지는 '무엇을 세고
    싶은가'(개체 수 vs 행 수)의 의미적 문제라, 일반 SELECT 목록에 DISTINCT를 빠뜨린 것
    (중복 행이 그냥 눈에 보이는 문제)과는 판단 기준이 완전히 다름. 실제로 card_games에서
    COUNT(*) 쿼리에 DISTINCT를 잘못 추가해서 정답을 크게 틀리게 만드는 사례가 반복
    확인돼서, 이 경우는 missing-DISTINCT 체크에서 아예 제외함."""
    select_clause = re.split(r"\bFROM\b", sql, maxsplit=1, flags=re.IGNORECASE)[0]
    return bool(re.search(r"\bCOUNT\s*\(", select_clause, re.IGNORECASE))


def detect_year_function_risk(sql: str) -> bool:
    """SQLite엔 YEAR() 함수가 없음 - 이 함수를 쓰면 100% 확실히 실행 자체가 안 되는 버그.
    실제 오답 사례에서 KB에 이미 STRFTIME 교정 지식이 있었는데도 이 신호가 없어서
    못 찾았던 게 확인돼서 추가함."""
    return bool(re.search(r"\bYEAR\s*\(", sql, re.IGNORECASE))


_YES_NO_QUESTION_PATTERNS = [
    r"^Do(es)?\b", r"^Were\b", r"^Was\b", r"^Is\b", r"^Are\s+there\b",
    r"\bindicating whether\b",
]


def detect_yes_no_question_risk(question: str) -> bool:
    """질문 자체가 존재여부(Yes/No)를 묻는 패턴인지 - 처음으로 draft SQL이 아니라
    '질문 문장'을 보는 탐지기. 'Do any...', 'Were the...', 'indicating whether...' 같은
    질문은 이 DB에서 IIF(조건, 'YES', 'NO') 형태로 답해야 하는 경우가 있었음(465, 469
    확인됨) - draft가 실제 값을 나열하거나 boolean/count로 답하면 틀림."""
    return any(re.search(p, question, re.IGNORECASE) for p in _YES_NO_QUESTION_PATTERNS)


def count_yes_no_fix_entries(entries: list[dict]) -> int:
    """정답에 IIF(...,'YES'...) 패턴을 쓰는 엔트리가 KB에 몇 개나 있는지 - 이것도
    검증 없이 매칭시키면 위험하므로 개수로 게이팅."""
    count = 0
    for e in entries:
        correction_upper = e["correction"].upper()
        if "IIF" in correction_upper and "'YES'" in correction_upper:
            count += 1
    return count


def select_by_structural_risk(entries: list[dict], draft_sql: str, schema_columns: dict[str, set[str]],
                               k: int, question: str = "") -> list[dict]:
    """1단계(결정론적 - 확실할 때만): 테이블-컬럼 불일치 / DISTINCT 위험 / YEAR() 위험 /
    존재여부(Yes-No) 질문 패턴. 2단계(일반화된 폴백 - 카테고리 상관없이): draft SQL이
    실제로 언급하는 컬럼과 KB 엔트리가 언급하는 컬럼이 겹치면 후보로 - VALUE_ENCODING,
    AGGREGATION_LOGIC처럼 전용 구조 탐지기가 없는 카테고리도 이걸로 커버됨. 1단계에서
    이미 뽑힌 건 제외하고, 1단계 결과가 항상 먼저 채워지므로 확실한 신호가 약한 신호에
    밀리지 않음."""
    selected: list[dict] = []
    seen = set()

    mismatches = detect_table_column_mismatches(draft_sql, schema_columns)
    for _, col in mismatches:
        for e in entries:
            if id(e) in seen:
                continue
            text = e["situation"] + " " + e["correction"]
            if re.search(r"\b" + re.escape(col) + r"\b", text, re.IGNORECASE):
                selected.append(e)
                seen.add(id(e))

    if (detect_missing_distinct_risk(draft_sql) and not is_count_only_query(draft_sql)
            and count_distinct_fix_entries(entries) >= MIN_DISTINCT_FIX_COUNT):
        # 태그 이름(MISSING_DISTINCT)이 아니라 교정 내용 텍스트를 직접 봄 - distillation이
        # 이런 케이스를 AGGREGATION_LOGIC 등 다른 태그로 잘못 분류하는 경우가 실제로
        # 확인됨(formula_1: "DISTINCT를 빠뜨렸다"는 상황인데 태그는 AGGREGATION_LOGIC).
        # 추가로: DISTINCT 사례 풀 안에서도 draft와 컬럼이 겹치는 것만 매칭 - 겹침 없이
        # "그냥 아무 DISTINCT 예시나" 매칭시키면 무관한 질문에 계속 같은 예시가 끼어들어서
        # 오히려 정답을 망가뜨리는 게 card_games에서 실제로 확인됨.
        draft_columns_distinct = extract_mentioned_columns(draft_sql, schema_columns)
        for e in entries:
            if id(e) in seen:
                continue
            correction = e["correction"]
            if "/ 정답:" not in correction:
                continue
            wrong_part, right_part = correction.split("/ 정답:", 1)
            if "DISTINCT" not in right_part.upper() or "DISTINCT" in wrong_part.upper():
                continue
            entry_columns = extract_mentioned_columns(e["situation"] + " " + correction, schema_columns)
            if draft_columns_distinct & entry_columns:
                selected.append(e)
                seen.add(id(e))

    if detect_select_star_risk(draft_sql):
        # SELECT * 자체가 일반적인 교훈(구체적 컬럼만 골라 써라)이라 컬럼 겹침 요구 없이
        # 매칭 - card_games에서 이 패턴이 항상 같은 방향으로 교정된 게 확인됨(신뢰도 높음).
        for e in entries:
            if id(e) in seen:
                continue
            correction = e["correction"]
            if "/ 정답:" not in correction:
                continue
            wrong_part, right_part = correction.split("/ 정답:", 1)
            if detect_select_star_risk(wrong_part) and not detect_select_star_risk(right_part):
                selected.append(e)
                seen.add(id(e))

    if (detect_extra_distinct_risk(draft_sql) and not is_count_only_query(draft_sql)
            and count_extra_distinct_fix_entries(entries) >= MIN_DISTINCT_FIX_COUNT):
        # "빠뜨림"의 반대 방향(불필요하게 DISTINCT를 씀) - 이것도 컬럼 겹침 요구.
        draft_columns_extra = extract_mentioned_columns(draft_sql, schema_columns)
        for e in entries:
            if id(e) in seen:
                continue
            correction = e["correction"]
            if "/ 정답:" not in correction:
                continue
            wrong_part, right_part = correction.split("/ 정답:", 1)
            if "DISTINCT" not in wrong_part.upper() or "DISTINCT" in right_part.upper():
                continue
            entry_columns = extract_mentioned_columns(e["situation"] + " " + correction, schema_columns)
            if draft_columns_extra & entry_columns:
                selected.append(e)
                seen.add(id(e))

    if detect_year_function_risk(draft_sql):
        for e in entries:
            if id(e) in seen:
                continue
            text = (e["situation"] + " " + e["correction"]).upper()
            if "YEAR(" in text:  # 그 엔트리 자체가 YEAR() 실수를 다룬 것만 - STRFTIME은
                selected.append(e)  # 너무 흔해서(다른 이유의 날짜 수정에도 등장) 과매칭 위험
                seen.add(id(e))

    if (question and detect_yes_no_question_risk(question)
            and count_yes_no_fix_entries(entries) >= MIN_DISTINCT_FIX_COUNT):
        # 질문 문장 패턴('Do any...', 'Were...', 'indicating whether...')이 존재여부를
        # 묻는 것이면, IIF(...,'YES'...) 패턴으로 답한 사례를 참고시킴. draft SQL이
        # 아니라 질문 텍스트를 보는 첫 탐지기.
        for e in entries:
            if id(e) in seen:
                continue
            correction_upper = e["correction"].upper()
            if "IIF" in correction_upper and "'YES'" in correction_upper:
                selected.append(e)
                seen.add(id(e))

    # 폴백(컬럼 겹침)은 확실한 신호(테이블불일치/DISTINCT/YEAR)가 하나라도 이미 있을 때만
    # "보충용"으로 씀. 확실한 신호가 하나도 없으면 폴백 자체를 아예 안 씀 - 애매한 것만으로
    # 개입시키면 멀쩡한 draft를 오히려 망가뜨리는 게 실제로 확인됨
    # (formula_1: 857_rep2, 990_rep2 - 원래 맞는 draft에 무관한 조건이 추가돼서 틀어짐).
    if selected and len(selected) < k:
        draft_columns = extract_mentioned_columns(draft_sql, schema_columns)
        for e in entries:
            if id(e) in seen or len(selected) >= k:
                continue
            text = e["situation"] + " " + e["correction"]
            entry_columns = extract_mentioned_columns(text, schema_columns)
            overlap = draft_columns & entry_columns
            if len(overlap) >= 2:
                selected.append(e)
                seen.add(id(e))

    return selected[:k]


def load_eval_questions(db_id: str, eval_on: str) -> list[dict]:
    if eval_on == "test":
        path = SPLIT_DIR / f"{db_id}_test.json"
    else:
        path = SPLIT_DIR_OUT / f"{db_id}_{eval_on}.json"
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def evaluate(db_id: str, schema_ddl: str, questions: list[dict], entries: list[dict],
             schema_columns: dict[str, set[str]], k: int,
             use_auto_diff: bool = False) -> tuple[float, dict, list[int], float]:
    correctness = {}
    n_selected_list = []
    n_draft_correct = 0

    for q in questions:
        evidence = q.get("evidence", "")

        draft_sql = llm.generate_sql(q["question"], evidence, schema_ddl, kb_text="")
        if db.check_correct(db_id, draft_sql, q["SQL"]):
            n_draft_correct += 1

        if use_auto_diff:
            selected = select_by_auto_diff(entries, draft_sql, schema_columns, k)
        else:
            selected = select_by_structural_risk(entries, draft_sql, schema_columns, k, question=q["question"])
        n_selected_list.append(len(selected))

        if not selected:
            predicted = draft_sql
        else:
            kb_text = build_kb_text_literal(selected)
            history = [
                {"role": "assistant", "content": f"```sql\n{draft_sql}\n```"},
                {"role": "user", "content": "아래 참고 지식을 보고 이 SQL에 문제가 없는지 검토하고, "
                                             "필요하면 정확하게 다시 작성해주세요."},
            ]
            predicted = llm.generate_sql(q["question"], evidence, schema_ddl, kb_text, history=history)

        correctness[str(q["question_id"])] = int(db.check_correct(db_id, predicted, q["SQL"]))

    acc = sum(correctness.values()) / len(correctness) if correctness else 0.0
    draft_acc = n_draft_correct / len(questions) if questions else 0.0
    return acc, correctness, n_selected_list, draft_acc


def save_result(record: dict):
    RESULTS_PATH.parent.mkdir(exist_ok=True)
    existing = []
    if RESULTS_PATH.exists():
        with open(RESULTS_PATH, encoding="utf-8") as f:
            existing = json.load(f)
    existing.append(record)
    with open(RESULTS_PATH, "w", encoding="utf-8") as f:
        json.dump(existing, f, ensure_ascii=False, indent=2)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", required=True, choices=TARGET_DBS)
    parser.add_argument("--kb-through", type=int, choices=[0, 1, 2], required=True)
    parser.add_argument("--eval-on", required=True, choices=["replica1", "replica2", "test"])
    parser.add_argument("--k", type=int, default=DEFAULT_K)
    parser.add_argument("--repeat", type=int, default=1)
    parser.add_argument("--auto", action="store_true",
                         help="6개 손으로 만든 탐지기 대신, KB의 오답->정답 diff에서 "
                              "자동으로 위험 신호를 뽑아내는 select_by_auto_diff 사용 "
                              "(카테고리를 사람이 미리 정의 안 함)")
    args = parser.parse_args()

    schema_ddl = db.get_schema_ddl(args.db)
    schema_columns = get_schema_columns(schema_ddl)

    entries, _ = build_accumulated_kb(args.db, schema_ddl, args.kb_through)
    print(f"KB(라운드1+복제DB{args.kb_through}까지 누적): {len(entries)}개 엔트리")

    active_categories = get_active_error_categories(entries)
    print(f"이 KB에 실제로 등장하는 오류유형 (데이터 기반, 눈으로 고른 게 아님):")
    for cat, count in sorted(active_categories.items(), key=lambda x: -x[1]):
        print(f"  {cat}: {count}개 엔트리")

    questions = load_eval_questions(args.db, args.eval_on)
    mode_desc = "auto-diff(자동)" if args.auto else "structural(6개 손탐지기)"
    print(f"평가 대상: {args.eval_on} ({len(questions)}문항), k={args.k}, {mode_desc}, repeat={args.repeat}")

    accs = []
    draft_accs = []
    for run_i in range(1, args.repeat + 1):
        acc, correctness, n_selected_list, draft_acc = evaluate(
            args.db, schema_ddl, questions, entries, schema_columns, args.k,
            use_auto_diff=args.auto,
        )
        avg_selected = sum(n_selected_list) / len(n_selected_list) if n_selected_list else 0
        accs.append(acc)
        draft_accs.append(draft_acc)
        print(f"  [run {run_i}/{args.repeat}] 최종 정답률: {acc:.1%}  "
              f"(1차 시도(KB없음) 정답률: {draft_acc:.1%}, 평균 매칭 엔트리 {avg_selected:.1f}개)")
        save_result({
            "db_id": args.db, "kb_through": args.kb_through, "eval_on": args.eval_on,
            "k": args.k, "run": run_i, "accuracy": acc, "draft_accuracy": draft_acc,
            "correctness": correctness, "n_kb_entries": len(entries),
        })

    mean_acc = sum(accs) / len(accs)
    mean_draft = sum(draft_accs) / len(draft_accs)
    if len(accs) > 1:
        variance = sum((a - mean_acc) ** 2 for a in accs) / (len(accs) - 1)
        std = variance ** 0.5
        print(f"\n{args.repeat}회 평균: 최종 {mean_acc:.1%} (±{std:.1%})  |  1차시도(KB없음) 평균 {mean_draft:.1%}")
    else:
        print(f"\n최종 정답률: {mean_acc:.1%}  |  1차시도(KB없음): {mean_draft:.1%}")
    print(f"완료. {RESULTS_PATH}에 저장됨.")


if __name__ == "__main__":
    main()