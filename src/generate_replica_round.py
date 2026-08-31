"""
generate_replica_round.py

복제 DB 라운드용 데이터를 만드는 스크립트. 두 단계로 구성됨:

  1단계 - 복제 질문 생성: 원본 T1+T2+T3 문항(DB당 38~51개) 각각을 1:1로 변형한다.
    같은 SQL 로직/패턴(JOIN 구조, DISTINCT 필요 여부, 집계함수 종류, GROUP BY, 서브쿼리 등)은
    유지하되 실제 컬럼/조건/값/질문 문장은 다르게 - GPT-5.6 Terra로 생성.
    생성된 SQL은 (a) 실제 DB에 실행해서 에러 없는지, (b) gpt-4o-mini로 질문 의도와
    논리적으로 맞는지 검증하고, 검증 실패하면 재생성(최대 MAX_GEN_RETRIES회).

  2단계 - 교정 세션(피드백): 생성된 복제 질문들을 "라운드1의 고정된 최종 KB"
    (literal + 마스킹 + 임베딩 + 임계값 0.2, k 제한 없음, R3)로 먼저 풀어보고,
    틀리면 하연이 터미널에서 직접 자연어 힌트를 입력 -> 재시도 (run_experiment.py의
    get_human_hint 패턴과 동일, 정답 SQL은 화면에 참고용으로만 표시하고 LLM에는 안 줌).

이 스크립트는 "데이터 수집"만 담당하고 KB 축적 방법론과는 분리돼 있음. 여기서 저장하는
split_output/*_replica{n}.json, results/transcripts/*_replica{n}.json은 나중에 어떤
KB 구축 방식(literal, 일반화, 태그매칭, 임베딩 등)을 시도하든 그대로 재사용 가능함 -
기존 T1/T2/T3 transcript가 여러 build_kb_qe_*.py에서 재사용됐던 것과 같은 패턴.

라운드1 KB는 kb/{db_id}_kb_qe_literal_embed_threshold_R3.md를 그대로 읽어서 쓰고,
이 스크립트에서는 절대 안 건드림(재증류 없음).

이미 만들어진 split_output/results 파일이 있으면 기본적으로 재사용(재생성 안 함).
--regenerate로 강제 재생성 가능.

사용법 (반드시 실제 터미널에서 실행 - 교정 세션 중 힌트 입력 필요):
    python3 src/generate_replica_round.py --db thrombosis_prediction --replica 1
    python3 src/generate_replica_round.py --db formula_1 --replica 2
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import db_utils as db
import llm_utils as llm
from build_kb_qe import BATCHES, SPLIT_DIR, parse_kb_entries
from build_kb_qe_literal import build_kb_text_literal
from build_kb_qe_literal_embed import extract_schema_tokens, mask_text
from build_kb_qe_literal_embed_threshold import select_entries_by_embedding_topk_threshold

REPLICA_GEN_MODEL = "gpt-5.6-terra"
MAX_GEN_RETRIES = 3
MAX_HINTS_PER_QUESTION = 2  # 원본 run_experiment.py와 동일

NO_K_CAP = 10_000  # k에 이 값을 주면 사실상 "제한 없음" (KB 크기보다 항상 큼)
MIN_SIM = 0.2

KB_DIR = Path("kb")
SPLIT_DIR_OUT = Path("split_output")
TRANSCRIPTS_DIR = Path("results/transcripts")

ROUND1_KB_TEMPLATE = "{db_id}_kb_qe_literal_embed_threshold_R3.md"  # 고정, 절대 재증류 안 함


# ---------------- 1단계: 복제 질문 생성 ----------------

REPLICA_GEN_PROMPT = """당신은 Text-to-SQL 벤치마크용 새 문항을 만드는 어시스턴트입니다.
아래 원본 질문과 정답 SQL을 참고해서, 완전히 새로운 질문 + 정답 SQL 한 쌍을 만드세요.

요구사항:
- 같은 데이터베이스(동일 스키마, 동일 데이터)를 그대로 사용합니다. 스키마에 실제 존재하는
  테이블/컬럼명만 쓰세요.
- 원본과 똑같은 SQL 로직/패턴(JOIN 구조, DISTINCT 필요 여부, 집계함수 종류(COUNT/AVG/SUM 등),
  GROUP BY 여부, 서브쿼리 vs JOIN, 날짜 계산 방식 등)을 유지하되, 실제 사용하는 컬럼/조건/
  구체적인 값은 원본과 달라야 합니다.
- 질문 문장 자체도 원본 문장을 그대로 재사용하지 말고 새로 작성하세요.
- evidence(자연어 정의/값 인코딩 설명 등)가 필요하면 원본처럼 작성하고, 필요 없으면 빈
  문자열로 두세요.
- SQL은 그 자리에서 바로 실행 가능해야 합니다 (문법 오류 금지).

### 스키마
{schema_ddl}

### 원본 질문
{original_question}
### 원본 evidence
{original_evidence}
### 원본 정답 SQL
{original_sql}
{retry_feedback}
아래 JSON 형식으로만 답하세요. 다른 설명 붙이지 마세요:
{{"question": "...", "evidence": "...", "sql": "..."}}
"""

VERIFY_PROMPT = """아래 질문 + evidence + SQL이 서로 논리적으로 일치하는지 판단하세요.

질문: {question}
evidence: {evidence}
SQL: {sql}
SQL 실행 결과 (앞 5개 행): {result_preview}
SQL 실행 에러: {error}

이 SQL이 질문(및 evidence)의 의도를 정확하게 구현하고 있는지 판단해서, 아래 JSON
형식으로만 답하세요. 다른 설명 붙이지 마세요:
{{"valid": true 또는 false, "reason": "한 문장으로 짧게"}}
"""


def _parse_json_response(text: str) -> dict:
    text = text.strip()
    if text.startswith("```"):
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]
    return json.loads(text.strip())


def generate_one_replica(schema_ddl: str, original: dict) -> dict | None:
    """원본 질문 1개 -> 검증까지 통과한 복제 질문 1개. 실패하면 None."""
    retry_feedback = ""
    for attempt in range(1, MAX_GEN_RETRIES + 1):
        prompt = REPLICA_GEN_PROMPT.format(
            schema_ddl=schema_ddl,
            original_question=original["question"],
            original_evidence=original.get("evidence", ""),
            original_sql=original["SQL"],
            retry_feedback=retry_feedback,
        )
        resp = llm._client.chat.completions.create(
            model=REPLICA_GEN_MODEL,
            messages=[{"role": "user", "content": prompt}],
            # GPT-5.6은 Chat Completions에서 커스텀 temperature를 지원 안 함 (기본값 1만 가능)
        )
        try:
            gen = _parse_json_response(resp.choices[0].message.content)
            new_q, new_evidence, new_sql = gen["question"], gen.get("evidence", ""), gen["sql"]
        except Exception as e:
            retry_feedback = f"\n(이전 시도가 JSON 파싱에 실패했습니다: {e}. 반드시 지정된 JSON 형식으로만 답하세요.)\n"
            continue

        rows, err = db.execute_sql(original["db_id"], new_sql)
        result_preview = str(rows[:5]) if rows is not None else ""

        verify_resp = llm._client.chat.completions.create(
            model=llm.MODEL,
            messages=[{"role": "user", "content": VERIFY_PROMPT.format(
                question=new_q, evidence=new_evidence, sql=new_sql,
                result_preview=result_preview, error=err or "(없음)",
            )}],
            temperature=0,
        )
        try:
            verdict = _parse_json_response(verify_resp.choices[0].message.content)
        except Exception:
            verdict = {"valid": False, "reason": "검증 응답 파싱 실패"}

        if err is None and verdict.get("valid"):
            return {"question": new_q, "evidence": new_evidence, "SQL": new_sql}

        reason = err or verdict.get("reason", "알 수 없는 이유")
        print(f"    [재생성 {attempt}/{MAX_GEN_RETRIES}] 검증 실패: {reason}")
        retry_feedback = f"\n(이전 시도가 다음 이유로 거부됐습니다: {reason}. 이 문제를 피해서 다시 만드세요.)\n"

    return None


def load_original_questions(db_id: str) -> list[dict]:
    qs = []
    for batch in BATCHES:
        path = SPLIT_DIR / f"{db_id}_{batch}.json"
        with open(path, encoding="utf-8") as f:
            for q in json.load(f):
                q["db_id"] = db_id
                qs.append(q)
    return qs


def generate_replica_questions(db_id: str, replica: int, schema_ddl: str) -> list[dict]:
    out_path = SPLIT_DIR_OUT / f"{db_id}_replica{replica}.json"
    originals = load_original_questions(db_id)
    replicas = []

    print(f"복제 질문 생성 중: {len(originals)}개 원본 -> 복제{replica}")
    for i, orig in enumerate(originals, 1):
        new_q = generate_one_replica(schema_ddl, orig)
        if new_q is None:
            print(f"  [{i}/{len(originals)}] qid={orig['question_id']} -> 생성 실패, 건너뜀")
            continue
        new_q["question_id"] = f"{orig['question_id']}_rep{replica}"
        replicas.append(new_q)
        print(f"  [{i}/{len(originals)}] qid={orig['question_id']} -> {new_q['question_id']} 생성 완료")

        SPLIT_DIR_OUT.mkdir(exist_ok=True)
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(replicas, f, ensure_ascii=False, indent=2)  # 진행 중 저장 (중단 대비)

    print(f"완료: {len(replicas)}/{len(originals)}개 생성 성공, {out_path}에 저장")
    return replicas


# ---------------- 2단계: 교정 세션 (라운드1 고정 KB로 풀고, 틀리면 하연이 힌트) ----------------

def get_human_hint(question: str, evidence: str, gold_sql: str, predicted_sql: str) -> str:
    print("\n" + "=" * 60)
    print(f"[오답] 질문: {question}")
    if evidence:
        print(f"(evidence: {evidence})")
    print(f"LLM이 생성한 SQL:\n  {predicted_sql}")
    print(f"\n[참고용, LLM에게는 안 보여줌] Gold SQL:\n  {gold_sql}")
    print("=" * 60)
    hint = input("이 질문에 대한 자연어 힌트를 입력하세요 (SQL 작성 금지, Enter만 누르면 힌트 생략): ").strip()
    return hint


def load_round1_kb(db_id: str) -> list[dict]:
    kb_path = KB_DIR / ROUND1_KB_TEMPLATE.format(db_id=db_id)
    if not kb_path.exists():
        raise FileNotFoundError(
            f"{kb_path} 없음 - 먼저 build_kb_qe_literal_embed_threshold.py로 라운드1 KB를 만들어야 함"
        )
    entries = parse_kb_entries(kb_path.read_text(encoding="utf-8"))
    print(f"라운드1 KB 로드: {kb_path} ({len(entries)}개 엔트리, 고정, 재증류 안 함)")
    return entries


def run_correction_session(db_id: str, replica_questions: list[dict], round1_entries: list[dict],
                            schema_ddl: str, schema_tokens: list[str]) -> list[dict]:
    transcripts = []
    for i, q in enumerate(replica_questions, 1):
        print(f"\n--- {i}/{len(replica_questions)} (qid={q['question_id']}) ---")
        question, evidence, gold = q["question"], q.get("evidence", ""), q["SQL"]

        selected = select_entries_by_embedding_topk_threshold(
            round1_entries, question, schema_tokens, NO_K_CAP, MIN_SIM,
        )
        kb_text = build_kb_text_literal(selected)

        history = []
        predicted = llm.generate_sql(question, evidence, schema_ddl, kb_text)
        correct = db.check_correct(db_id, predicted, gold)
        turns = [{"attempt": 1, "sql": predicted, "correct": correct}]

        hint_count = 0
        while not correct and hint_count < MAX_HINTS_PER_QUESTION:
            hint = get_human_hint(question, evidence, gold, predicted)
            hint_count += 1
            if not hint:
                break
            history.append({"role": "assistant", "content": f"```sql\n{predicted}\n```"})
            history.append({"role": "user", "content": f"틀렸습니다. 힌트: {hint}\n다시 SQL을 작성해주세요."})
            predicted = llm.generate_sql(question, evidence, schema_ddl, kb_text, history=history)
            correct = db.check_correct(db_id, predicted, gold)
            turns.append({"attempt": hint_count + 1, "hint": hint, "sql": predicted, "correct": correct})

        status = "정답" if correct else "최종 오답"
        print(f"  -> {status}")
        transcripts.append({
            "question_id": q["question_id"], "question": question,
            "gold_sql": gold, "final_correct": correct, "turns": turns,
        })
    return transcripts


# ---------------- 메인 ----------------

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", required=True)
    parser.add_argument("--replica", type=int, choices=[1, 2], required=True)
    parser.add_argument("--regenerate", action="store_true", help="이미 있는 복제 질문 파일 무시하고 새로 생성")
    parser.add_argument("--recorrect", action="store_true", help="이미 있는 transcript 무시하고 교정 세션 새로 진행")
    args = parser.parse_args()

    schema_ddl = db.get_schema_ddl(args.db)
    schema_tokens = extract_schema_tokens(schema_ddl)

    split_path = SPLIT_DIR_OUT / f"{args.db}_replica{args.replica}.json"
    transcript_path = TRANSCRIPTS_DIR / f"{args.db}_replica{args.replica}.json"

    # 1단계
    if split_path.exists() and not args.regenerate:
        with open(split_path, encoding="utf-8") as f:
            replica_questions = json.load(f)
        print(f"기존 복제 질문 재사용: {split_path} ({len(replica_questions)}개, 재생성 안 함)")
    else:
        replica_questions = generate_replica_questions(args.db, args.replica, schema_ddl)

    # 2단계
    if transcript_path.exists() and not args.recorrect:
        print(f"기존 transcript 재사용: {transcript_path} (교정 세션 새로 안 함)")
        return

    round1_entries = load_round1_kb(args.db)
    print(f"\n교정 세션 시작 ({len(replica_questions)}문항). 틀리면 직접 힌트를 입력해줘.")
    transcripts = run_correction_session(args.db, replica_questions, round1_entries, schema_ddl, schema_tokens)

    TRANSCRIPTS_DIR.mkdir(parents=True, exist_ok=True)
    with open(transcript_path, "w", encoding="utf-8") as f:
        json.dump(transcripts, f, ensure_ascii=False, indent=2)

    n_correct = sum(t["final_correct"] for t in transcripts)
    print(f"\n완료. {transcript_path} 저장됨. ({n_correct}/{len(transcripts)}문항 최종 정답)")


if __name__ == "__main__":
    main()