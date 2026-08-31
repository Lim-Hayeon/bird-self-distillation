"""
build_kb_qe_literal_embed_threshold.py

build_kb_qe_literal_embed.py에서 발견된 문제를 고친 버전.

발견된 문제: top-k는 관련 있는 엔트리가 하나도 없어도 무조건 k개를 채워서 뽑음.
thrombosis_prediction 디버깅에서 실제로 확인됨 - PT/TG/GOT 관련 질문인데 KB에
그 검사항목을 다룬 지식이 아예 없어서(T1/T2/T3가 우연히 안 다뤘음), 그런데도
유사도 0.2~0.4짜리 무관한 엔트리 8개가 억지로 주입되고 있었음. 이게 thrombosis에서
Raw->R1->R2->R3가 계속 25.0%로 완전히 그대로였던 것과 연결되는 원인 중 하나로 추정됨
(무관한 노이즈가 매번 비슷한 정도로 섞여 들어가서 무의미한 영향만 준 것).

바뀐 것: select_entries_by_embedding_topk_threshold() - 코사인 유사도가 min_similarity
이상인 엔트리 중에서만 top-k를 뽑음. 기준을 넘는 게 하나도 없으면 빈 리스트를 반환해서
KB 없이(Raw와 동일한 프롬프트로) 생성하도록 함 - "관련 있는 게 없으면 억지로 채우지
말고 차라리 아무것도 안 주는" 전략.

나머지(literal distillation, literal 텍스트 주입, 평가 흐름, 마스킹)는
build_kb_qe_literal_embed.py와 100% 동일. 기존 파일들 전혀 안 건드림.

새 KB: kb/{db_id}_kb_qe_literal_embed_threshold_R1.md / _R2.md / _R3.md
새 결과: results/round_results_qe_literal_embed_threshold.json
  (레코드마다 "k", "min_similarity", "n_fallback_to_raw"(이번 라운드에서 기준 못 넘어서
  Raw로 대체된 문항 수) 포함)

사용법 (리포 루트에서):
    python3 src/build_kb_qe_literal_embed_threshold.py --k 8 --min-sim 0.5
    python3 src/build_kb_qe_literal_embed_threshold.py --k 8 --min-sim 0.4   # 기준 낮춰서도 비교
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
    BATCHES,
    BATCH_TO_ROUND,
    SPLIT_DIR,
    TRANSCRIPTS_DIR,
    format_transcript_for_distill,
    load_evidence_map,
    format_evidence_summary,
    parse_kb_entries,
)
from build_kb_qe_literal import (
    extract_qe_deltas_literal,
    build_kb_text_literal,
)
from build_kb_qe_literal_embed import (
    extract_schema_tokens,
    mask_text,
    get_embedding,
    cosine_similarity,
)

KB_DIR = Path("kb")
RESULTS_DIR = Path("results")


# ---------------- 검색: top-k + 최소 유사도 임계값 ----------------

def select_entries_by_embedding_topk_threshold(entries: list[dict], question: str,
                                                schema_tokens: list[str], k: int,
                                                min_similarity: float) -> list[dict]:
    q_masked = mask_text(question, schema_tokens)
    q_emb = get_embedding(q_masked)

    scored = []
    for e in entries:
        e_masked = mask_text(e["situation"], schema_tokens)
        e_emb = get_embedding(e_masked)
        sim = cosine_similarity(q_emb, e_emb)
        if sim >= min_similarity:
            scored.append((sim, e))
    scored.sort(key=lambda x: x[0], reverse=True)
    return [e for _, e in scored[:k]]


# ---------------- 평가 ----------------

def load_split(db_id: str, split_name: str) -> list[dict]:
    with open(SPLIT_DIR / f"{db_id}_{split_name}.json", encoding="utf-8") as f:
        return json.load(f)


def evaluate(db_id: str, schema_ddl: str, questions: list[dict], entries: list[dict],
             schema_tokens: list[str], k: int, min_similarity: float) -> tuple[float, dict, int]:
    correctness = {}
    n_fallback = 0
    for q in questions:
        if entries:
            selected = select_entries_by_embedding_topk_threshold(
                entries, q["question"], schema_tokens, k, min_similarity,
            )
            if not selected:
                n_fallback += 1
            kb_text = build_kb_text_literal(selected)
        else:
            kb_text = ""
        predicted = llm.generate_sql(q["question"], q.get("evidence", ""), schema_ddl, kb_text=kb_text)
        correctness[str(q["question_id"])] = int(db.check_correct(db_id, predicted, q["SQL"]))
    acc = sum(correctness.values()) / len(correctness) if correctness else 0.0
    return acc, correctness, n_fallback


def save_result(path: Path, record: dict):
    RESULTS_DIR.mkdir(exist_ok=True)
    existing = []
    if path.exists():
        with open(path, encoding="utf-8") as f:
            existing = json.load(f)
    existing.append(record)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(existing, f, ensure_ascii=False, indent=2)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--k", type=int, nargs="+", default=[8])
    parser.add_argument("--min-sim", type=float, nargs="+", default=[0.5],
                         help="이 유사도 미만인 엔트리는 후보에서 제외 (다 제외되면 Raw로 대체). "
                              "여러 개 주면 스윕 (예: --min-sim 0.2 0.3 0.4 0.5)")
    parser.add_argument("--rebuild", action="store_true",
                         help="kb/*.md가 이미 있어도 무시하고 처음부터 다시 증류함 (기본은 있으면 재사용)")
    args = parser.parse_args()

    results_path = RESULTS_DIR / "round_results_qe_literal_embed_threshold.json"

    for db_id in TARGET_DBS:
        print(f"\n{'#'*60}\n# {db_id} (literal + 임베딩 top-k + 임계값, k={args.k}, min_sim={args.min_sim})\n{'#'*60}")
        schema_ddl = db.get_schema_ddl(db_id)
        schema_tokens = extract_schema_tokens(schema_ddl)
        test_qs = load_split(db_id, "test")

        raw_acc, raw_correctness, _ = evaluate(db_id, schema_ddl, test_qs, [], schema_tokens, k=0, min_similarity=0)
        print(f"[Raw] {raw_acc:.1%}")
        save_result(results_path, {"db_id": db_id, "condition": "Raw", "k": None, "min_similarity": None,
                                    "accuracy": raw_acc, "correctness": raw_correctness})

        entries: list[dict] = []
        kb_markdown = ""
        kb_id_counter = 1

        for batch in BATCHES:
            round_name = BATCH_TO_ROUND[batch]
            kb_path = KB_DIR / f"{db_id}_kb_qe_literal_embed_threshold_{round_name}.md"

            if kb_path.exists() and not args.rebuild:
                kb_markdown = kb_path.read_text(encoding="utf-8")
                entries = parse_kb_entries(kb_markdown)
                print(f"  [{round_name}] 기존 KB 파일 재사용: {kb_path} ({len(entries)}개 엔트리, 재증류 안 함)")
            else:
                transcript_path = TRANSCRIPTS_DIR / f"{db_id}_{round_name}.json"

                if transcript_path.exists():
                    with open(transcript_path, encoding="utf-8") as f:
                        transcripts = json.load(f)
                    evidence_map = load_evidence_map(db_id, batch)
                    transcript_text = format_transcript_for_distill(transcripts)
                    evidence_summary = format_evidence_summary(transcripts, evidence_map)

                    delta_text = extract_qe_deltas_literal(transcript_text, evidence_summary, schema_ddl, kb_markdown)

                    if "추가할 항목 없음" not in delta_text:
                        renumbered_lines = []
                        for line in delta_text.splitlines():
                            if re.match(r"^## KB-", line):
                                renumbered_lines.append(f"## KB-{kb_id_counter:03d}")
                                kb_id_counter += 1
                            else:
                                renumbered_lines.append(line)
                        delta_text = "\n".join(renumbered_lines)
                        kb_markdown += ("\n\n" if kb_markdown else "") + delta_text
                        new_entries = parse_kb_entries(delta_text)
                        entries.extend(new_entries)
                        print(f"  [{round_name}] 새 항목 {len(new_entries)}개 추출 (누적 {len(entries)}개, 새로 증류함)")
                    else:
                        print(f"  [{round_name}] 새 항목 없음 (새로 증류함)")
                else:
                    print(f"  [경고] {transcript_path} 없음, 이 단계는 이전 상태 유지")

                KB_DIR.mkdir(exist_ok=True)
                kb_path.write_text(kb_markdown + "\n", encoding="utf-8")

            for k in args.k:
                for min_sim in args.min_sim:
                    acc, correctness, n_fallback = evaluate(
                        db_id, schema_ddl, test_qs, entries, schema_tokens, k, min_sim,
                    )
                    delta = acc - raw_acc
                    print(f"[{round_name} k={k} min_sim={min_sim}] {acc:.1%}  (Raw 대비 {delta:+.1%}p, "
                          f"{n_fallback}/{len(test_qs)}문항 Raw로 대체됨)")
                    save_result(results_path, {"db_id": db_id, "condition": round_name, "k": k,
                                                "min_similarity": min_sim, "accuracy": acc,
                                                "correctness": correctness, "n_entries": len(entries),
                                                "n_fallback_to_raw": n_fallback})

    print(f"\n완료. {results_path}, kb/*_kb_qe_literal_embed_threshold_*.md 확인하세요.")


if __name__ == "__main__":
    main()