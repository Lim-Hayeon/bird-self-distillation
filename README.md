# BIRD Self-Distillation

Text-to-SQL 자기증류(self-distillation) 연구: 인간 피드백으로 구축한 지식베이스(KB)를
반복적으로 축적할 때, 정확도가 라운드를 거듭할수록 실제로 지속 향상되는지(단조증가)를
검증하고, 이를 위한 자동 위험 신호 탐지 기반 자기교정 파이프라인을 구현한다.

- 벤치마크: [BIRD Mini-Dev](https://bird-bench.github.io/)
- 대상 DB: `thrombosis_prediction`, `formula_1`, `card_games`
- SQL 생성 모델: `gpt-4o-mini`
- 복제 문항 생성 모델: `GPT-5.6 Terra`

---

## 핵심 결과

| DB | 1단계 (KB 없음) | 3단계 (라운드1 KB → 복제DB1) | 5단계 (라운드1+복제1 KB → 복제DB2) |
|---|---|---|---|
| thrombosis_prediction | 26.3% | 70.2% (±6.6%) | **76.3%** (±2.6%) |
| formula_1 | 31.4% | 50.7% (±2.3%) | **56.7%** (±1.2%) |
| card_games | 32.5% | 63.6% (±4.6%) | **69.5%** (±3.2%) |

세 DB 모두에서 1→3→5단계 정확도의 단조증가를 확인했다(3~5회 반복 측정 평균, 괄호는 표준편차).

---

## 방법론 요약

1. **KB 저장 형식**: 규칙을 추상화하지 않고, 실제 질문·오답 SQL·정답 SQL을 그대로
   인용하는 literal 형식 채택 (4개 필드: 상황/태그/교정 내용/예외).
2. **KB 축적**: 원본(T1+T2+T3) → 복제DB1 → 복제DB2 순으로 인간 교정 세션을 거쳐
   KB를 누적. 축적 시 진짜 중복인 소그룹만 골라 병합하고 나머지 엔트리는 원문 그대로
   보존하는 2단계 정리(consolidation) 절차 적용.
3. **자기교정 파이프라인**: 질문마다 KB 없이 초안 SQL을 먼저 생성 → 위험 신호가
   탐지될 때만 관련 KB 지식을 참고해 자기교정 → 신호 없으면 초안 그대로 채택.
4. **위험 신호 자동 발견**: KB의 모든 오답→정답 SQL 쌍에서 토큰 등장·소멸 빈도를
   집계, 3회 이상 반복된 패턴만 신뢰.
5. **위험 신호 자동 적용**: 대부분 신호는 빈도 기반 탐지로 충분하나, 오판이 잦았던
   `DISTINCT`는 실제 DB 실행 결과(중복 행 여부)와 질문 evidence 텍스트를 근거로
   판단하도록 별도 설계.

자세한 설계 근거는 `src/evaluate_structural_match.py`의 각 함수 docstring 참고.

---

## 저장소 구조

```
bird-self-distillation/
├── data/mini_dev_data/          # BIRD Mini-Dev 원본 데이터 (직접 다운로드 필요)
├── split_output/                # T1/T2/T3/test 분할 및 복제DB1/2 문항
├── kb/                          # 라운드별 누적 KB (.md)
├── results/
│   ├── transcripts/             # 교정 세션 기록 (오답→힌트→정답)
│   └── round_results_*.json     # 평가 결과 로그
└── src/
    ├── (기반 인프라)
    │   ├── bird_split.py            # 원본 데이터 T1/T2/T3/test 분할
    │   ├── db_utils.py              # DB 스키마 조회, SQL 실행/채점
    │   ├── llm_utils.py             # gpt-4o-mini 호출 (SQL 생성)
    │   ├── run_experiment.py        # 최초 T1/T2/T3 교정 세션 실행
    │   └── analyze_results.py       # McNemar 검정 등 통계 분석
    │
    ├── (라운드1 KB 구축 — literal + 마스킹 + 임베딩 방식 확정까지의 단계)
    │   ├── build_kb_qe.py                        # QE 기반 distillation
    │   ├── build_kb_qe_literal.py                # literal 방식 도입
    │   ├── build_kb_qe_literal_embed.py           # + 마스킹/임베딩 검색
    │   └── build_kb_qe_literal_embed_threshold.py # + 임계값 (최종 "라운드1 KB" 산출)
    │
    ├── (복제DB 파이프라인 — 라운드1 → 복제1 → 복제2)
    │   ├── generate_replica_questions.py    # ① 복제 문항 생성 (GPT-5.6 + 검증)
    │   ├── correct_and_accumulate_replica.py # ② 교정 세션 + KB 자동 누적/정리
    │   └── evaluate_structural_match.py      # ③ 최종 평가 (자동 위험 신호 탐지)
    │
    └── report_signal_candidates.py  # KB 데이터 기반 위험 신호 후보 빈도표 출력
```

---

## 환경 설정

```bash
# Python 3.9.6+ (macOS: python3 사용, python 아님)
pip install openai python-dotenv

# 리포 루트에 .env 생성
echo "OPENAI_API_KEY=sk-..." > .env
```

BIRD Mini-Dev 데이터를 `data/mini_dev_data/`에 위치시킨다 (`mini_dev_sqlite.json`,
`dev_databases/{db_id}/{db_id}.sqlite`).

---

## 실행 순서

### 1) 원본 데이터 분할 및 라운드1 KB 구축

```bash
python3 src/bird_split.py
python3 src/run_experiment.py          # T1/T2/T3 교정 세션 (대화형, 힌트 입력 필요)
python3 src/build_kb_qe_literal_embed_threshold.py --db <db_id>   # 라운드1 KB 산출
```

정확한 옵션은 각 스크립트 상단 docstring 또는 `--help` 참고.

### 2) 복제DB 파이프라인 (DB당 반복)

```bash
# 복제DB1
python3 src/generate_replica_questions.py --db <db_id> --replica 1
python3 src/correct_and_accumulate_replica.py --db <db_id> --replica 1   # 대화형, 오답 시 힌트 입력

# 복제DB2 (라운드1+복제1 KB 기반)
python3 src/generate_replica_questions.py --db <db_id> --replica 2
python3 src/correct_and_accumulate_replica.py --db <db_id> --replica 2   # 대화형
```

### 3) 최종 평가

```bash
# 3단계: 라운드1 KB → 복제DB1
python3 src/evaluate_structural_match.py --db <db_id> --kb-through 0 --eval-on replica1 --repeat 5 --auto

# 5단계: 라운드1+복제1 KB → 복제DB2
python3 src/evaluate_structural_match.py --db <db_id> --kb-through 1 --eval-on replica2 --repeat 5 --auto
```

`--auto`: KB 데이터 기반 자동 위험 신호 탐지(최종 채택 방법론). 생략 시 수동 정의 6개
신호 버전으로 동작.

### 4) 위험 신호 후보 확인 (선택)

```bash
python3 src/report_signal_candidates.py --db <db_id>
```

KB에 누적된 오답→정답 쌍에서 자동 집계된 토큰 빈도표를 출력한다.

---

## 참고

- 대상 DB별 지배적 오류 유형: thrombosis_prediction(날짜 함수 오용, DISTINCT 누락),
  formula_1(MAX↔ORDER BY 패턴, 시간 문자열 파싱), card_games(다양하고 분산된 오류 유형).
- `--auto`(자동 탐지)는 formula_1에서 수동 규칙 버전(63.3%)보다 낮은 성능(56.7%)을
  보였다 — 해당 DB의 지배적 오류가 실행/텍스트 근거만으로 포착하기 어려운 유형이기 때문.
