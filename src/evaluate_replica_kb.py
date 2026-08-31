"""
evaluate_replica_kb.py  (3/3)

이미 쌓인 KB(1,2번 스크립트로 만들어진 것)를 가지고 정답률만 확인하는 스크립트.
여기가 "검색/주입 방식(마스킹/임베딩/k/임계값)을 바꿔가며 재실험"하는 자리 -
--k, --min-sim을 바꿔서 몇 번이고 다시 돌려도 됨(사람 개입 없음, KB 내용도 안 바뀜).

KB 자체(어떤 질문에서 어떤 correction이 나왔는지, literal 내용이 뭔지)는 여기서 절대
새로 안 만듦 - correct_and_accumulate_replica.py가 이미 저장해둔 transcript들을 다시
distill(같은 literal 방식, 고정)해서 그대로 재구성만 함. 즉 이 스크립트를 다시 돌려도
"내용"은 항상 똑같고, 바뀌는 건 검색 파라미터뿐.

--relevance-filter: 임베딩+임계값/k는 "재현율 우선"으로 넉넉하게(coarse_k=20) 후보를
뽑고, 그 위에 gpt-4o-mini로 "이 지식이 이 질문에 실제로 적용 가능한가"를 판단해서
한 번 더 걸러낸다. 지금까지 시도한 것(태그매칭, 임베딩 top-k, 임계값)은 전부 "유사도
숫자" 기반 필터였는데, 이건 "판단" 기반 필터라 질적으로 다름 - KB가 커질수록 유사도만
으로는 진짜 관련 있는 것과 표면적으로만 비슷한 것을 못 가르는 문제(예: GOT/GPT처럼
마스킹으로 안 잡히는 유사 컬럼)를 직접 겨냥함.

--kb-through로 어느 시점의 누적 KB를 쓸지 고르고, --eval-on으로 그 KB를 무엇에
적용해서 정답률을 잴지 고름:
  --kb-through 0 --eval-on replica1  : 라운드1 KB로 복제DB1 풀기
  --kb-through 1 --eval-on replica2  : 라운드1+복제DB1 KB로 복제DB2 풀기
  --kb-through 2 --eval-on test      : 최종 누적 KB로 원본 BIRD Test set 최종 검증

매번 실제로 새로 LLM 호출해서 다시 풀어봄 (교정 세션 때의 1차 시도 결과를 재활용하지
않음) - 검색 파라미터를 바꿔서 실험하는 게 목적이라 항상 새로 평가해야 의미가 있음.

사용법 (자동 - 힌트 입력 없음):
    python3 src/evaluate_replica_kb.py --db thrombosis_prediction --kb-through 0 --eval-on replica1
    python3 src/evaluate_replica_kb.py --db thrombosis_prediction --kb-through 1 --eval-on replica2
    python3 src/evaluate_replica_kb.py --db thrombosis_prediction --kb-through 2 --eval-on test
    # 검색 파라미터 바꿔서 재실험 예시:
    python3 src/evaluate_replica_kb.py --db thrombosis_prediction --kb-through 1 --eval-on replica2 --k 8 --min-sim 0.3
    # LLM 관련성 판단 필터 켜서 실험:
    python3 src/evaluate_replica_kb.py --db thrombosis_prediction --kb-through 1 --eval-on replica2 --relevance-filter
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import db_utils as db
import llm_utils as llm
from build_kb_qe import TARGET_DBS, SPLIT_DIR, predict_query_elements, select_entries_by_tags
from build_kb_qe_literal import build_kb_text_literal
from build_kb_qe_literal_embed import extract_schema_tokens
from build_kb_qe_literal_embed_threshold import select_entries_by_embedding_topk_threshold
from correct_and_accumulate_replica import build_accumulated_kb, SPLIT_DIR_OUT


def select_entries_hybrid(entries: list[dict], question: str, evidence: str,
                           schema_tokens: list[str], schema_ddl: str,
                           k: int, min_sim: float) -> list[dict]:
    """임베딩(마스킹+코사인유사도) OR 태그매칭(QE로 예측한 SQL요소가 태그와 겹침) 합집합.
    둘 다 순수 규칙 기반 - QE는 "질문을 분석해 필요 요소를 예측"하는 1회 호출이지,
    "이 후보가 맞는지 판단"하는 관련성 필터와는 성격이 다름(후보별 판단 없음)."""
    embed_selected = select_entries_by_embedding_topk_threshold(entries, question, schema_tokens, k, min_sim)

    predicted_elements = predict_query_elements(question, evidence, schema_ddl)
    tag_selected = select_entries_by_tags(entries, predicted_elements)

    combined = list(embed_selected)
    seen = {id(e) for e in embed_selected}
    for e in tag_selected:
        if id(e) not in seen:
            combined.append(e)
            seen.add(id(e))
    return combined

RESULTS_PATH = Path("results/round_results_replica_eval.json")

DEFAULT_NO_K_CAP = 10_000
DEFAULT_MIN_SIM = 0.2
RELEVANCE_FILTER_COARSE_K = 100  # KB 크기(현재 최대 51개)보다 항상 크게 - 사실상 min_sim만 적용됨.
                                   # 예전엔 20이었는데, formula_1(42개 엔트리)에서 21등 밖으로
                                   # 밀린 엔트리가 LLM 판단 단계에 아예 도달 못하는 버그였음.


RELEVANCE_FILTER_PROMPT = """아래 질문에 대해 SQL을 생성하려고 합니다. 후보로 뽑힌 과거
교정 지식들 중 실제로 이 질문에 적용 가능한 것만 골라내려고 합니다.

질문: {question}
evidence: {evidence}

후보 지식 목록:
{candidates_numbered}

각 번호가 이 질문의 SQL을 정확히 작성하는 데 조금이라도 도움이 될 수 있는지
판단하세요. SQL 하나에는 보통 여러 요소(어느 테이블을 쓸지, JOIN을 어떻게 할지,
DISTINCT가 필요한지, 집계 함수를 어떻게 쓸지, 값을 어떻게 인코딩할지, 날짜를
어떻게 계산할지 등)가 동시에 들어갑니다. 한 질문에 "제일 잘 맞는 것 딱 하나"만
고르지 말고, **이 SQL을 구성하는 여러 요소 각각에 대해 도움이 될 수 있는 지식을
전부** true로 표시하세요 - 서로 다른 이유로 여러 개가 동시에 true인 경우가 흔합니다.
애매하면 포함(true)시키는 쪽으로 판단하세요 - 관련 있는 걸 놓치는 것보다 여분으로
주는 게 낫습니다.

아래 JSON 형식으로만 답하세요, 다른 설명 없이. 키는 후보 번호(문자열), 값은 true/false:
{{"1": true, "2": false, ...}}
"""


def _parse_json_loose(text: str) -> dict:
    text = text.strip()
    if text.startswith("```"):
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]
    return json.loads(text.strip())


def select_entries_relevance_filtered(entries: list[dict], question: str, evidence: str,
                                       schema_tokens: list[str], min_sim: float) -> list[dict]:
    """1단계(임베딩, 재현율 우선) -> 2단계(LLM 판단, 정밀도 확보)."""
    coarse = select_entries_by_embedding_topk_threshold(
        entries, question, schema_tokens, RELEVANCE_FILTER_COARSE_K, min_sim,
    )
    if not coarse:
        return []

    candidates_numbered = "\n".join(
        f"{i+1}. {e['situation']} => {e['correction']}" for i, e in enumerate(coarse)
    )
    prompt = RELEVANCE_FILTER_PROMPT.format(
        question=question, evidence=evidence, candidates_numbered=candidates_numbered,
    )
    resp = llm._client.chat.completions.create(
        model=llm.MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0,
    )
    try:
        verdict = _parse_json_loose(resp.choices[0].message.content)
    except Exception:
        return coarse  # 파싱 실패하면 안전하게 필터 없이 coarse 그대로 사용

    return [e for i, e in enumerate(coarse) if verdict.get(str(i + 1), True)]


def select_entries_llm_only(entries: list[dict], question: str, evidence: str) -> list[dict]:
    """마스킹/임베딩 전혀 안 씀 - KB 전체를 LLM한테 그대로 보여주고 관련 있는 것만 직접
    고르게 함. KB가 크지 않을 때(지금 34~51개) 충분히 실용적인, 훨씬 단순한 대안."""
    if not entries:
        return []
    candidates_numbered = "\n".join(
        f"{i+1}. {e['situation']} => {e['correction']}" for i, e in enumerate(entries)
    )
    prompt = RELEVANCE_FILTER_PROMPT.format(
        question=question, evidence=evidence, candidates_numbered=candidates_numbered,
    )
    resp = llm._client.chat.completions.create(
        model=llm.MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0,
    )
    try:
        verdict = _parse_json_loose(resp.choices[0].message.content)
    except Exception:
        return entries  # 파싱 실패하면 안전하게 전체 반환

    return [e for i, e in enumerate(entries) if verdict.get(str(i + 1), True)]


def load_eval_questions(db_id: str, eval_on: str) -> list[dict]:
    if eval_on == "test":
        path = SPLIT_DIR / f"{db_id}_test.json"
    else:  # "replica1" or "replica2"
        path = SPLIT_DIR_OUT / f"{db_id}_{eval_on}.json"
    if not path.exists():
        raise FileNotFoundError(f"{path} 없음")
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def evaluate(db_id: str, schema_ddl: str, questions: list[dict], entries: list[dict],
             schema_tokens: list[str], k: int, min_sim: float,
             relevance_filter: bool = False, llm_only: bool = False, hybrid: bool = False) -> tuple[float, dict, list[int]]:
    correctness = {}
    n_selected_list = []
    for q in questions:
        evidence = q.get("evidence", "")
        if llm_only:
            selected = select_entries_llm_only(entries, q["question"], evidence)
        elif relevance_filter:
            selected = select_entries_relevance_filtered(entries, q["question"], evidence, schema_tokens, min_sim)
        elif hybrid:
            selected = select_entries_hybrid(entries, q["question"], evidence, schema_tokens, schema_ddl, k, min_sim)
        else:
            selected = select_entries_by_embedding_topk_threshold(entries, q["question"], schema_tokens, k, min_sim)
        n_selected_list.append(len(selected))
        kb_text = build_kb_text_literal(selected)
        predicted = llm.generate_sql(q["question"], evidence, schema_ddl, kb_text=kb_text)
        correctness[str(q["question_id"])] = int(db.check_correct(db_id, predicted, q["SQL"]))
    acc = sum(correctness.values()) / len(correctness) if correctness else 0.0
    return acc, correctness, n_selected_list


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
    parser.add_argument("--kb-through", type=int, choices=[0, 1, 2], required=True,
                         help="0=라운드1 KB만, 1=+복제DB1, 2=+복제DB1+복제DB2")
    parser.add_argument("--eval-on", required=True, choices=["replica1", "replica2", "test"],
                         help="이 KB를 무엇에 적용해서 정답률을 잴지")
    parser.add_argument("--k", type=int, default=DEFAULT_NO_K_CAP)
    parser.add_argument("--min-sim", type=float, default=DEFAULT_MIN_SIM)
    parser.add_argument("--relevance-filter", action="store_true",
                         help="임베딩(재현율 우선, coarse_k=100)으로 후보를 넓게 뽑은 뒤 "
                              "gpt-4o-mini로 실제 적용 가능한지 판단해서 한 번 더 거름. "
                              "켜면 --k는 무시됨.")
    parser.add_argument("--llm-only", action="store_true",
                         help="마스킹/임베딩을 아예 안 씀 - KB 전체를 gpt-4o-mini한테 그대로 "
                              "보여주고 관련 있는 것만 직접 고르게 함. --k, --min-sim, "
                              "--relevance-filter 다 무시됨. KB가 크지 않을 때(지금 규모) "
                              "쓸 수 있는 제일 단순한 방식.")
    parser.add_argument("--hybrid", action="store_true",
                         help="임베딩(마스킹+코사인유사도) OR 태그매칭(QE 예측+태그겹침)의 "
                              "합집합. 순수 규칙 기반(후보별 LLM 판단 없음) - 임베딩이 놓치는 "
                              "컬럼명 불일치 케이스를 태그의 구조적 유사성(JOIN/DISTINCT 등)이 "
                              "보완해줄 수 있는지 테스트용.")
    parser.add_argument("--repeat", type=int, default=1,
                         help="같은 조건을 몇 번 반복할지 - API 비결정성 노이즈와 진짜 차이를 "
                              "구분하려면 1보다 크게(예: 3~5) 주는 걸 권장")
    args = parser.parse_args()

    schema_ddl = db.get_schema_ddl(args.db)
    schema_tokens = extract_schema_tokens(schema_ddl)

    entries, _ = build_accumulated_kb(args.db, schema_ddl, args.kb_through)
    print(f"KB(라운드1+복제DB{args.kb_through}까지 누적): {len(entries)}개 엔트리")

    questions = load_eval_questions(args.db, args.eval_on)
    if args.llm_only:
        mode_desc = "llm-only (마스킹/임베딩 없음, LLM이 전체 KB를 직접 판단)"
    elif args.relevance_filter:
        mode_desc = "relevance-filter (임베딩 재현율 + LLM 정밀도)"
    elif args.hybrid:
        mode_desc = f"hybrid (임베딩 OR 태그매칭, k={args.k}, min_sim={args.min_sim})"
    else:
        mode_desc = f"k={args.k}, min_sim={args.min_sim}"
    print(f"평가 대상: {args.eval_on} ({len(questions)}문항), {mode_desc}, repeat={args.repeat}")

    accs = []
    for run_i in range(1, args.repeat + 1):
        acc, correctness, n_selected_list = evaluate(
            args.db, schema_ddl, questions, entries, schema_tokens, args.k, args.min_sim,
            relevance_filter=args.relevance_filter, llm_only=args.llm_only, hybrid=args.hybrid,
        )
        avg_selected = sum(n_selected_list) / len(n_selected_list) if n_selected_list else 0
        accs.append(acc)
        print(f"  [run {run_i}/{args.repeat}] 정답률: {acc:.1%}  (평균 선택 엔트리 {avg_selected:.1f}개/{len(entries)}개)")

        save_result({
            "db_id": args.db, "kb_through": args.kb_through, "eval_on": args.eval_on,
            "k": args.k, "min_similarity": args.min_sim, "relevance_filter": args.relevance_filter,
            "llm_only": args.llm_only, "hybrid": args.hybrid,
            "run": run_i, "accuracy": acc, "correctness": correctness, "n_kb_entries": len(entries),
        })

    mean_acc = sum(accs) / len(accs)
    if len(accs) > 1:
        variance = sum((a - mean_acc) ** 2 for a in accs) / (len(accs) - 1)
        std_acc = variance ** 0.5
        print(f"\n{args.repeat}회 평균: {mean_acc:.1%}  (표준편차 ±{std_acc:.1%}, 범위 {min(accs):.1%}~{max(accs):.1%})")
    else:
        print(f"\n정답률: {mean_acc:.1%}  (--repeat 1보다 크게 주면 평균/표준편차도 같이 나옴)")

    print(f"완료. {RESULTS_PATH}에 저장됨.")


if __name__ == "__main__":
    main()