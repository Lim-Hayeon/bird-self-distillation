"""
correct_and_accumulate_replica.py  (2/3)

복제 질문(1번 스크립트로 이미 생성돼있어야 함)을 "그 시점까지 누적된 KB"로 먼저
풀어보고, 틀리면 하연이 터미널에서 직접 자연어 힌트를 입력 -> 재시도
(run_experiment.py의 get_human_hint 패턴과 동일, 정답 SQL은 화면에 참고용으로만
표시하고 LLM에는 안 줌). 세션이 끝나면 그 transcript를 바로 distill해서
(gpt-4o-mini, literal 방식 - 지금까지 쓰던 것) KB에 자동으로 누적/저장한다.
그리고 매 라운드가 끝날 때마다 중복 정리(consolidate_kb)를 자동으로 거친다 -
같은 근본 패턴(예: 컬럼만 다른 DISTINCT 오류)이 여러 개로 중복 저장돼 있으면
병합하고, 진짜 중복이 없으면 원본을 그대로 둔다(불필요한 재작성 노이즈 방지).
consolidate_kb.py 실험에서 진짜 중복이 있을 때 병합이 확실히 도움된다는 게
확인됐음(+5.3pp, 완벽 재현) - 없을 때는 정확히 0.0%p로 손해가 없다는 것도 확인됨.

--replica 값에 따라 세션에 쓰는 KB가 다름:
  --replica 1: 라운드1 KB 그대로 (literal+마스킹+임베딩+임계값0.2, k제한없음, R3)
  --replica 2: 라운드1+복제DB1 누적 KB (복제DB1이 이미 이 스크립트로 처리돼있어야 함)

중요: 이 스크립트에서 교정 세션 중 검색/주입 방식(마스킹+임베딩+min_sim=0.2+k제한없음)은
고정값이다. 나중에 이 방식을 바꾸고 싶어도 이미 진행한 교정 세션(하연의 힌트)은 그
당시 방식 기준으로 나온 것이라 다시 할 수 없음 - 검색 방식을 바꿔서 실험하고 싶으면
evaluate_replica_kb.py(3번 스크립트)를 쓸 것 (거긴 사람 개입 없이 재실행 가능).

이미 transcript(results/transcripts/{db}_replica{n}.json)가 있으면 교정 세션은
건너뛰고(재사용) distillation만 (안 돼있으면) 진행. --recorrect로 교정 세션 강제 재진행.

결과:
  results/transcripts/{db}_replica{n}.json  (교정 세션 기록)
  kb/{db}_kb_qe_replica_R{n+1}.md           (그 시점까지 누적된 KB 전체 텍스트)

사용법 (반드시 실제 터미널에서 실행 - 힌트 입력 필요, 이미 다 돼있으면 자동으로 스킵):
    python3 src/correct_and_accumulate_replica.py --db thrombosis_prediction --replica 1
    python3 src/correct_and_accumulate_replica.py --db thrombosis_prediction --replica 2
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

import db_utils as db
import llm_utils as llm
from build_kb_qe import (
    TARGET_DBS,
    parse_kb_entries,
    format_transcript_for_distill,
    load_evidence_map,
    format_evidence_summary,
)
from build_kb_qe_literal import extract_qe_deltas_literal, build_kb_text_literal
from build_kb_qe_literal_embed import extract_schema_tokens
from build_kb_qe_literal_embed_threshold import select_entries_by_embedding_topk_threshold

KB_DIR = Path("kb")
SPLIT_DIR_OUT = Path("split_output")
TRANSCRIPTS_DIR = Path("results/transcripts")

ROUND1_KB_TEMPLATE = "{db_id}_kb_qe_literal_embed_threshold_R3.md"  # 고정, 절대 재증류 안 함
MAX_HINTS_PER_QUESTION = 2  # 원본 run_experiment.py와 동일

# 교정 세션에서 쓰는 검색/주입 방식 - 고정값 (evaluate_replica_kb.py에서만 바꿔서 실험함)
NO_K_CAP = 10_000
MIN_SIM = 0.2


# ---------------- KB 정리 (중복 병합) ----------------
# consolidate_kb.py 실험에서 확인됨: 진짜 중복이 있으면 병합이 도움됨(+5.3pp). 근데
# "KB 전체를 통째로 다시 쓰게" 시켰더니, 병합 대상이 아닌 엔트리까지 매번 다시 쓰이면서
# 미묘하게 훼손되는 문제가 반복 관찰됨 (예: "Thrombosis는 Examination 테이블에 있다"는
# 사실이 흐려지거나, 날짜 기준점(now vs 특정 이벤트 날짜) 조건이 뒤섞임) - 프롬프트를
# 두 번 다르게 강화해도 똑같은 실패가 재발해서, 프롬프트 문구 문제가 아니라 "전체
# 재작성" 구조 자체가 위험하다고 판단함.
#
# 그래서 2단계로 분리함:
#   1단계: 진짜 중복인 엔트리들의 "번호"만 찾음 (내용 자체는 절대 안 건드림)
#   2단계: 그 소그룹만 따로 병합. 그룹에 안 뽑힌 엔트리는 원문 그대로, 한 글자도
#          안 바뀐 채로 보존됨 - 이러면 애초에 병합 대상이 아니었던 사실/조건부 규칙이
#          "전체 재작성" 와중에 실수로 훼손될 위험이 구조적으로 사라짐.

IDENTIFY_DUPLICATES_PROMPT = """아래 KB 엔트리 목록에서, 컬럼/테이블명/구체값만 다르고
나머지 SQL 로직과 적용 조건이 완전히 동일한 "진짜 중복" 그룹을 찾으세요.

**주의: 적용 조건이 조금이라도 다르면 절대 같은 그룹으로 묶지 마세요.** 예:
- "DISTINCT를 써야 하는 경우"와 "DISTINCT를 쓰면 안 되는 경우"는 겉보기에 비슷해도
  정반대 조건이라 다른 그룹입니다.
- "현재 날짜(now) 기준 나이 계산"과 "특정 이벤트 날짜 기준 나이 계산"은 다른 그룹입니다.
- 필요한 SELECT 컬럼 목록이 다르면 다른 그룹입니다.
"컬럼/테이블 이름만 바꾸면 완전히 똑같은 상황"인 것만 그룹으로 묶고, 애매하면 그룹에
넣지 마세요.

### KB 엔트리 목록 (번호. 상황 | 교정 내용 | 예외)
{numbered_entries}

아래 JSON 형식으로만 답하세요, 다른 설명 없이. 각 그룹은 진짜 중복인 번호(정수)들의
리스트입니다(반드시 2개 이상). 진짜 중복이 하나도 없으면 빈 리스트를 반환하세요:
{{"groups": [[3, 7], [12, 15, 19]]}}
"""

MERGE_GROUP_PROMPT = """아래는 서로 진짜 중복(컬럼/테이블명만 다르고 나머지 로직과
적용 조건은 완전히 동일)이라고 판단된 KB 엔트리들입니다. 하나로 병합하세요.

병합 규칙:
- 대표적인 literal 예시 1~2개만 남기고, 상황 설명에 "이 패턴이 다른 컬럼(예: X, Y,
  Z)에서도 관찰됨"을 덧붙이세요.
- 원래 있던 사실 정보(어느 테이블에 있는지, 정확한 컬럼명 등)는 절대 왜곡하지 말고
  원문 그대로 유지하세요.

### 병합 대상 엔트리들
{group_entries_text}

아래 형식으로 병합된 엔트리 하나만 정확히 이렇게 출력하세요, 다른 설명 없이:
## KB-001
- 상황: ...
- 태그: ...
- 교정 내용: ...
- 예외: ...
"""


def _parse_json_loose(text: str) -> dict:
    text = text.strip()
    if text.startswith("```"):
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]
    return json.loads(text.strip())


def consolidate_kb(kb_markdown: str, current_entries: list[dict]) -> tuple[list[dict], str]:
    """1단계: 진짜 중복인 엔트리 '번호'만 찾음 (내용 안 건드림).
    2단계: 그 그룹만 따로 병합. 그룹에 안 뽑힌 엔트리는 원문 그대로 보존됨."""
    if len(current_entries) < 2:
        return current_entries, kb_markdown

    numbered = "\n".join(
        f"{i}. {e['situation']} | {e['correction']} | 예외: {e['exception'] or '없음'}"
        for i, e in enumerate(current_entries, start=1)
    )
    resp = llm._client.chat.completions.create(
        model=llm.MODEL,
        messages=[{"role": "user", "content": IDENTIFY_DUPLICATES_PROMPT.format(numbered_entries=numbered)}],
        temperature=0,
    )
    try:
        result = _parse_json_loose(resp.choices[0].message.content)
        groups = [[int(x) for x in g] for g in result.get("groups", []) if len(g) >= 2]
    except Exception:
        return current_entries, kb_markdown  # 파싱 실패 - 안전하게 원본 유지

    if not groups:
        return current_entries, kb_markdown  # 진짜 중복 없음 - 원본 그대로

    grouped_indices = {i for g in groups for i in g}
    new_entries = [e for i, e in enumerate(current_entries, start=1) if i not in grouped_indices]

    for group in groups:
        group_entries = [current_entries[i - 1] for i in group if 1 <= i <= len(current_entries)]
        if len(group_entries) < 2:
            new_entries.extend(group_entries)
            continue
        group_text = "\n\n".join(
            f"- 상황: {e['situation']}\n  교정 내용: {e['correction']}\n  예외: {e['exception'] or '없음'}"
            for e in group_entries
        )
        merge_resp = llm._client.chat.completions.create(
            model=llm.MODEL,
            messages=[{"role": "user", "content": MERGE_GROUP_PROMPT.format(group_entries_text=group_text)}],
            temperature=0,
        )
        merged = parse_kb_entries(merge_resp.choices[0].message.content.strip())
        if merged:
            new_entries.append(merged[0])
        else:
            new_entries.extend(group_entries)  # 파싱 실패 - 안전하게 병합 전 상태로 되돌림

    blocks = []
    for i, e in enumerate(new_entries, start=1):
        blocks.append(
            f"## KB-{i:03d}\n- 상황: {e['situation']}\n- 태그: {', '.join(e['tags'])}\n"
            f"- 교정 내용: {e['correction']}\n- 예외: {e['exception'] or '없음'}"
        )
    new_markdown = "\n\n".join(blocks)

    return new_entries, new_markdown


# ---------------- KB 로드/누적 (round1 고정 + 복제 라운드 distill) ----------------

def load_round1_kb(db_id: str) -> tuple[list[dict], str]:
    kb_path = KB_DIR / ROUND1_KB_TEMPLATE.format(db_id=db_id)
    if not kb_path.exists():
        raise FileNotFoundError(
            f"{kb_path} 없음 - 먼저 build_kb_qe_literal_embed_threshold.py로 라운드1 KB를 만들어야 함"
        )
    markdown = kb_path.read_text(encoding="utf-8")
    entries = parse_kb_entries(markdown)
    return entries, markdown


def distill_from_replica(db_id: str, replica_n: int, schema_ddl: str,
                          kb_markdown: str, kb_id_counter: int) -> tuple[list[dict], str, int]:
    batch = f"replica{replica_n}"
    transcript_path = TRANSCRIPTS_DIR / f"{db_id}_{batch}.json"
    with open(transcript_path, encoding="utf-8") as f:
        transcripts = json.load(f)

    evidence_map = load_evidence_map(db_id, batch)  # split_output/{db}_replica{n}.json 그대로 재사용됨
    transcript_text = format_transcript_for_distill(transcripts)
    evidence_summary = format_evidence_summary(transcripts, evidence_map)

    delta_text = extract_qe_deltas_literal(transcript_text, evidence_summary, schema_ddl, kb_markdown)

    if "추가할 항목 없음" in delta_text:
        return [], kb_markdown, kb_id_counter

    renumbered = []
    for line in delta_text.splitlines():
        if re.match(r"^## KB-", line):
            renumbered.append(f"## KB-{kb_id_counter:03d}")
            kb_id_counter += 1
        else:
            renumbered.append(line)
    delta_text = "\n".join(renumbered)
    new_markdown = kb_markdown + ("\n\n" if kb_markdown else "") + delta_text
    new_entries = parse_kb_entries(delta_text)
    return new_entries, new_markdown, kb_id_counter


def build_accumulated_kb(db_id: str, schema_ddl: str, through_replica: int) -> tuple[list[dict], str]:
    """라운드1 KB에서 시작해서 복제DB1..through_replica까지 순서대로 distill해서 누적하고,
    매 라운드 끝에 중복 정리(consolidate_kb)를 거침.

    각 라운드 결과(distill+정리까지 끝난 상태)는 kb/{db}_kb_qe_replica_R{n+1}.md에
    캐싱됨 - 이미 있으면 재계산(distill/정리 재호출) 없이 그대로 읽어서 씀. 이래야
    이 함수를 여러 번 호출해도(②의 correction session, ③의 evaluate, consolidate_kb.py
    등) 매번 다른 KB가 나오는 일이 없음 (distill/정리 둘 다 LLM 호출이라 매번 다시
    하면 API 비결정성 때문에 호출할 때마다 결과가 달라짐).

    through_replica=0 이면 라운드1 KB 그대로 (변화 없음, 정리도 안 함, 캐싱도 없음
    - 라운드1 파일 자체가 이미 고정 캐시임).
    이미 만들어둔 kb/*_replica_R{n}.md를 지우면 그 라운드부터 강제로 다시 계산됨."""
    entries, kb_markdown = load_round1_kb(db_id)
    kb_id_counter = len(entries) + 1
    for replica_n in range(1, through_replica + 1):
        cache_path = KB_DIR / f"{db_id}_kb_qe_replica_R{replica_n + 1}.md"
        if cache_path.exists():
            kb_markdown = cache_path.read_text(encoding="utf-8")
            entries = parse_kb_entries(kb_markdown)
            kb_id_counter = len(entries) + 1
            continue  # 캐시에서 불러왔으니 이 라운드는 재계산 안 함

        transcript_path = TRANSCRIPTS_DIR / f"{db_id}_replica{replica_n}.json"
        if not transcript_path.exists():
            raise FileNotFoundError(
                f"{transcript_path} 없음 - correct_and_accumulate_replica.py --db {db_id} "
                f"--replica {replica_n} 먼저 실행"
            )
        new_entries, kb_markdown, kb_id_counter = distill_from_replica(
            db_id, replica_n, schema_ddl, kb_markdown, kb_id_counter,
        )
        entries = entries + new_entries

        n_before = len(entries)
        entries, kb_markdown = consolidate_kb(kb_markdown, entries)
        if len(entries) != n_before:
            print(f"  [복제DB{replica_n} 이후 KB 정리] 중복 병합됨: {n_before}개 -> {len(entries)}개")
            kb_id_counter = len(entries) + 1  # 병합으로 번호가 다시 매겨졌으니 카운터도 갱신
        else:
            print(f"  [복제DB{replica_n} 이후 KB 정리] 병합할 중복 없음 ({n_before}개 유지)")

        KB_DIR.mkdir(exist_ok=True)
        cache_path.write_text(kb_markdown + "\n", encoding="utf-8")  # 다음부터는 이 파일 재사용됨
    return entries, kb_markdown


# ---------------- 교정 세션 ----------------

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


def run_correction_session(db_id: str, replica_questions: list[dict], current_entries: list[dict],
                            schema_ddl: str, schema_tokens: list[str]) -> list[dict]:
    transcripts = []
    for i, q in enumerate(replica_questions, 1):
        print(f"\n--- {i}/{len(replica_questions)} (qid={q['question_id']}) ---")
        question, evidence, gold = q["question"], q.get("evidence", ""), q["SQL"]

        selected = select_entries_by_embedding_topk_threshold(
            current_entries, question, schema_tokens, NO_K_CAP, MIN_SIM,
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
    parser.add_argument("--db", required=True, choices=TARGET_DBS)
    parser.add_argument("--replica", type=int, choices=[1, 2], required=True)
    parser.add_argument("--recorrect", action="store_true", help="이미 있는 transcript 무시하고 교정 세션 새로 진행")
    args = parser.parse_args()

    schema_ddl = db.get_schema_ddl(args.db)
    schema_tokens = extract_schema_tokens(schema_ddl)

    split_path = SPLIT_DIR_OUT / f"{args.db}_replica{args.replica}.json"
    if not split_path.exists():
        raise FileNotFoundError(
            f"{split_path} 없음 - generate_replica_questions.py --db {args.db} "
            f"--replica {args.replica} 먼저 실행"
        )
    with open(split_path, encoding="utf-8") as f:
        replica_questions = json.load(f)

    transcript_path = TRANSCRIPTS_DIR / f"{args.db}_replica{args.replica}.json"
    if transcript_path.exists() and not args.recorrect:
        print(f"기존 transcript 재사용: {transcript_path} (교정 세션 새로 안 함)")
        with open(transcript_path, encoding="utf-8") as f:
            transcripts = json.load(f)
    else:
        through_replica = args.replica - 1  # replica=1 -> 라운드1만, replica=2 -> 라운드1+복제DB1
        current_entries, _ = build_accumulated_kb(args.db, schema_ddl, through_replica)
        label = "라운드1 KB" if through_replica == 0 else f"라운드1+복제DB{through_replica} 누적 KB"
        print(f"교정 세션에 사용할 KB: {label} ({len(current_entries)}개 엔트리)")

        print(f"\n교정 세션 시작 ({len(replica_questions)}문항). 틀리면 직접 힌트를 입력해줘.")
        transcripts = run_correction_session(args.db, replica_questions, current_entries, schema_ddl, schema_tokens)

        TRANSCRIPTS_DIR.mkdir(parents=True, exist_ok=True)
        with open(transcript_path, "w", encoding="utf-8") as f:
            json.dump(transcripts, f, ensure_ascii=False, indent=2)

    n_first_try = sum(1 for t in transcripts if t["turns"][0]["correct"])
    n_final = sum(t["final_correct"] for t in transcripts)
    print(f"\n[복제DB{args.replica} 정답률] 1차 시도 {n_first_try}/{len(transcripts)} "
          f"({n_first_try/len(transcripts):.1%})  |  최종(힌트 포함) {n_final}/{len(transcripts)} "
          f"({n_final/len(transcripts):.1%})")

    # 세션 끝나자마자 바로 distillation + KB 누적 저장
    print(f"\nKB 누적 중 (복제DB{args.replica}에서 distill) ...")
    entries, kb_markdown = build_accumulated_kb(args.db, schema_ddl, args.replica)
    kb_out_path = KB_DIR / f"{args.db}_kb_qe_replica_R{args.replica + 1}.md"
    KB_DIR.mkdir(exist_ok=True)
    kb_out_path.write_text(kb_markdown + "\n", encoding="utf-8")
    print(f"완료. 누적 KB {len(entries)}개 엔트리, {kb_out_path}에 저장됨.")


if __name__ == "__main__":
    main()