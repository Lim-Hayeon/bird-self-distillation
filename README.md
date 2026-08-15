# bird-self-distillation

BIRD Mini-Dev 기반 Text-to-SQL self-distillation 파일럿 실험.
세션 중 발생한 교정(correction)을 LLM이 스스로 markdown knowledge base로 추출하고,
다음 세션(라운드)에 주입했을 때 정확도가 누적 향상되는지 검증한다.

## 폴더 구조

```
bird-self-distillation/
├── data/               # BIRD Mini-Dev 원본 질문 파일 (gitignore, 용량 큼)
├── results/            # baseline 채점 결과, 라운드별 평가 결과
├── split_output/        # Test/T1/T2/T3 분할 결과 (db_id별)
├── kb/                  # 라운드별 누적 knowledge base (KB_v1.md, KB_v2.md, ...)
└── src/
    └── bird_split.py    # DB별 Test/T1/T2/T3 층화추출 스크립트
```

## 대상 DB (3개)

| db_id | 전체 | Test | T1 | T2 | T3 |
|---|---|---|---|---|---|
| thrombosis_prediction | 50 | 12 | 13 | 13 | 12 |
| formula_1 | 66 | 15 | 17 | 17 | 17 |
| card_games | 52 | 12 | 14 | 13 | 13 |

## 실행 순서

1. `data/`에 BIRD Mini-Dev 질문 파일 배치 (기존 `bird-text2sql` 리포에서 복사)
2. `results/`에 이전 baseline 채점 결과 배치 (`{question_id: 0/1}` 형태 JSON)
3. `python3 src/bird_split.py` → `split_output/`에 DB별 4개 파일 생성
4. (다음 단계) T1 baseline 실행 → 오답에 힌트 제공 → self-distillation 프롬프트로 KB_v1 생성 → Test set 재평가

## 참고

기존 연구(`Lim-Hayeon/bird-text2sql`)의 self-correction, semantic layer 실험에서
이어지는 다음 단계. 정적 지식 주입(semantic layer)과 달리, 이번 실험은 지식 생성 자체를
LLM이 세션 대화에서 자동 추출(self-distillation)하는 것이 핵심 차이점.