"""
run_experiment.py
Self-distillation 실험 메인 파이프라인.

DB별로:
  1) Test set에 Raw(KB 없음) baseline 평가
  2) T1 배치: 문제 시도 -> 틀리면 사람이 자연어 힌트 제공(정답 SQL 노출 금지) -> 재시도
     -> 배치 종료 후 self-distillation으로 KB_v1 생성 -> Test set 재평가
  3) T2, T3도 동일하게 반복 (KB 누적)

실행 중 틀린 문제마다 터미널에서 힌트를 직접 입력해야 하므로, 반드시 실제 터미널에서 실행할 것
(자동화된 러너/노트북 셀 일괄실행 X).

사용법:
    python3 src/run_experiment.py
"""

from __future__ import annotations

import json
from pathlib import Path

import db_utils as db
import llm_utils as llm

TARGET_DBS = ["thrombosis_prediction", "formula_1", "card_games"]
ROUNDS = [("R1", "T1"), ("R2", "T2"), ("R3", "T3")]
MAX_HINTS_PER_QUESTION = 2  # 힌트를 최대 몇 번까지 줄지

SPLIT_DIR = Path("split_output")
KB_DIR = Path("kb")
RESULTS_DIR = Path("results")
TRANSCRIPTS_DIR = Path("results/transcripts")


def load_split(db_id: str, split_name: str) -> list[dict]:
    path = SPLIT_DIR / f"{db_id}_{split_name}.json"
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def load_kb(db_id: str) -> str:
    path = KB_DIR / f"{db_id}_kb.md"
    if path.exists():
        return path.read_text(encoding="utf-8")
    return ""


def append_kb(db_id: str, round_name: str, delta_text: str) -> str:
    """새 delta를 KB 파일에 append하고, 합쳐진 전체 KB 텍스트를 반환."""
    KB_DIR.mkdir(exist_ok=True)
    path = KB_DIR / f"{db_id}_kb.md"
    existing = load_kb(db_id)

    if "추가할 항목 없음" in delta_text:
        section = f"\n## Round: {round_name}\n(추가된 항목 없음)\n"
    else:
        section = f"\n## Round: {round_name}\n{delta_text}\n"

    updated = existing + section
    path.write_text(updated, encoding="utf-8")
    return updated


def get_human_hint(question: str, evidence: str, gold_sql: str, predicted_sql: str) -> str:
    """틀린 문제에 대해 사람이 자연어 힌트를 입력하도록 요청 (정답 SQL은 화면에만 참고용으로 표시, LLM에는 전달 안 됨)."""
    print("\n" + "=" * 60)
    print(f"[오답] 질문: {question}")
    if evidence:
        print(f"(기존 evidence: {evidence})")
    print(f"LLM이 생성한 SQL:\n  {predicted_sql}")
    print(f"\n[참고용, LLM에게는 안 보여줌] Gold SQL:\n  {gold_sql}")
    print("=" * 60)
    hint = input("이 질문에 대한 자연어 힌트를 입력하세요 (SQL 작성 금지, Enter만 누르면 힌트 생략): ").strip()
    return hint


def run_correction_round(db_id: str, batch_questions: list[dict], kb_text: str,
                          schema_ddl: str, round_name: str) -> tuple[str, list[dict]]:
    """한 라운드(T1/T2/T3)의 교정 대화를 진행하고, self-distillation으로 KB를 갱신."""
    transcripts = []

    for i, q in enumerate(batch_questions, 1):
        print(f"\n--- [{round_name}] {i}/{len(batch_questions)} (qid={q['question_id']}) ---")
        history = []
        predicted = llm.generate_sql(q["question"], q.get("evidence", ""), schema_ddl, kb_text)
        correct = db.check_correct(db_id, predicted, q["SQL"])
        turns = [{"attempt": 1, "sql": predicted, "correct": correct}]

        hint_count = 0
        while not correct and hint_count < MAX_HINTS_PER_QUESTION:
            hint = get_human_hint(q["question"], q.get("evidence", ""), q["SQL"], predicted)
            hint_count += 1
            if not hint:
                break  # 힌트 생략하면 이 질문은 여기서 종료
            history.append({"role": "assistant", "content": f"```sql\n{predicted}\n```"})
            history.append({"role": "user", "content": f"틀렸습니다. 힌트: {hint}\n다시 SQL을 작성해주세요."})
            predicted = llm.generate_sql(q["question"], q.get("evidence", ""), schema_ddl, kb_text, history=history)
            correct = db.check_correct(db_id, predicted, q["SQL"])
            turns.append({"attempt": hint_count + 1, "hint": hint, "sql": predicted, "correct": correct})

        status = "정답" if correct else "최종 오답"
        print(f"  -> {status}")
        transcripts.append({
            "question_id": q["question_id"],
            "question": q["question"],
            "gold_sql": q["SQL"],
            "final_correct": correct,
            "turns": turns,
        })

    # self-distillation: 이번 배치 대화 기록에서 KB delta 추출
    transcript_text = format_transcripts(transcripts)
    print(f"\n[{round_name}] self-distillation 진행 중 (LLM에게 KB 추가 항목 추출 요청)...")
    delta = llm.extract_kb_deltas(transcript_text, existing_kb=kb_text)
    updated_kb = append_kb(db_id, round_name, delta)
    print(f"[{round_name}] KB 업데이트 완료. 새로 추가된 항목:\n{delta}")

    TRANSCRIPTS_DIR.mkdir(parents=True, exist_ok=True)
    with open(TRANSCRIPTS_DIR / f"{db_id}_{round_name}.json", "w", encoding="utf-8") as f:
        json.dump(transcripts, f, ensure_ascii=False, indent=2)

    return updated_kb, transcripts


def format_transcripts(transcripts: list[dict]) -> str:
    """대화 기록을 self-distillation 프롬프트에 넣을 텍스트로 변환. 틀렸다가 힌트로 고쳐진 것 위주로 구성."""
    lines = []
    for t in transcripts:
        if len(t["turns"]) == 1 and t["turns"][0]["correct"]:
            continue  # 처음부터 맞은 건 교정 없음, distillation 대상 아님
        lines.append(f"### 질문: {t['question']}")
        for turn in t["turns"]:
            if "hint" in turn:
                lines.append(f"- 사람 힌트: {turn['hint']}")
            lines.append(f"- 시도 {turn['attempt']} SQL: {turn['sql']} (정답 여부: {turn['correct']})")
        lines.append(f"- 최종 정답 SQL: {t['gold_sql']}")
        lines.append("")
    return "\n".join(lines) if lines else "(이번 배치에서 교정이 발생한 질문 없음)"


def evaluate_batch(db_id: str, questions: list[dict], kb_text: str, schema_ddl: str) -> tuple[float, dict]:
    """KB를 주입한 상태로 one-shot 평가 (힌트 없음). {question_id: 0/1} 딕셔너리와 정확도 반환."""
    correctness = {}
    for q in questions:
        predicted = llm.generate_sql(q["question"], q.get("evidence", ""), schema_ddl, kb_text)
        correctness[str(q["question_id"])] = int(db.check_correct(db_id, predicted, q["SQL"]))
    acc = sum(correctness.values()) / len(correctness) if correctness else 0.0
    return acc, correctness


def save_result(record: dict):
    RESULTS_DIR.mkdir(exist_ok=True)
    path = RESULTS_DIR / "round_results.json"
    existing = []
    if path.exists():
        with open(path, encoding="utf-8") as f:
            existing = json.load(f)
    existing.append(record)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(existing, f, ensure_ascii=False, indent=2)


def main():
    for db_id in TARGET_DBS:
        print(f"\n{'#'*60}\n# {db_id}\n{'#'*60}")
        schema_ddl = db.get_schema_ddl(db_id)
        test_qs = load_split(db_id, "test")

        # 1) Raw baseline
        print(f"\n[Raw] Test set 평가 중 ({len(test_qs)}문항, KB 없음)...")
        raw_acc, raw_correctness = evaluate_batch(db_id, test_qs, kb_text="", schema_ddl=schema_ddl)
        print(f"[Raw] 정확도: {raw_acc:.1%}")
        save_result({"db_id": db_id, "condition": "Raw", "accuracy": raw_acc, "correctness": raw_correctness})

        # 2) R1/R2/R3 라운드
        kb_text = ""
        for round_name, batch_name in ROUNDS:
            batch_qs = load_split(db_id, batch_name)
            kb_text, _ = run_correction_round(db_id, batch_qs, kb_text, schema_ddl, round_name)

            print(f"\n[{round_name}] Test set 재평가 중 ({len(test_qs)}문항, KB 적용)...")
            acc, correctness = evaluate_batch(db_id, test_qs, kb_text, schema_ddl)
            print(f"[{round_name}] 정확도: {acc:.1%} (Raw 대비 {acc - raw_acc:+.1%}p)")
            save_result({"db_id": db_id, "condition": round_name, "accuracy": acc, "correctness": correctness})

    print("\n모든 DB 실험 완료. results/round_results.json 확인하세요.")


if __name__ == "__main__":
    main()