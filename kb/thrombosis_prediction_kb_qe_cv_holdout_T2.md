## KB-001
- 상황: 환자 단위로 리스트업할 때 중복을 피하기 위해 DISTINCT를 사용해야 하는 질문
- 태그: Patient, ID, SEX, Birthday, Laboratory, LDH, DISTINCT, JOIN_LOGIC
- 교정 내용: 처음에는 DISTINCT를 사용하지 않아 중복된 환자 정보가 나올 수 있었으나, DISTINCT를 추가하여 중복을 제거한 쿼리로 수정함.
- 예외: 없음

## KB-002
- 상황: 평균 계산 시 중복된 환자 ID를 세지 않기 위해 직접 조인하여 조건을 만족하는 검사 기록을 기준으로 평균을 내야 하는 질문
- 태그: Patient, Birthday, Laboratory, T-CHO, AVG, JOIN_LOGIC
- 교정 내용: 처음에는 서브쿼리를 사용하여 중복이 없어져서 틀렸으나, 직접 조인하여 조건을 만족하는 검사 기록을 기준으로 평균을 내는 쿼리로 수정함.
- 예외: 없음

## KB-003
- 상황: 특정 컬럼이 잘못된 테이블에서 조회되어 조인해야 하는 질문
- 태그: Patient, ID, SEX, Symptoms, Examination, SC170, Laboratory, JOIN_LOGIC
- 교정 내용: 처음에는 Examination 테이블에서 SC170을 조회했으나, Laboratory 테이블에서 조회해야 한다는 힌트를 받아 조인하여 수정함.
- 예외: 없음

## KB-004
- 상황: COUNT 조건을 잘못 사용하여 두 번 이상을 세는 질문
- 태그: Patient, ID, Birthday, Laboratory, HCT, COUNT, GROUP BY, HAVING
- 교정 내용: 처음에는 COUNT(L.ID) > 2로 잘못 작성했으나, COUNT(L.ID) >= 2로 수정하여 올바른 조건을 반영함.
- 예외: 없음

## KB-005
- 상황: 환자 리스트업 시 DISTINCT를 사용해야 하는 질문
- 태그: Patient, ID, SEX, Birthday, Laboratory, UN, DISTINCT, JOIN_LOGIC
- 교정 내용: 처음에는 DISTINCT를 사용하지 않아 중복된 환자 정보가 나올 수 있었으나, DISTINCT를 추가하여 중복을 제거한 쿼리로 수정함.
- 예외: 없음

## KB-006
- 상황: 날짜 비교 시 잘못된 방식으로 비교한 질문
- 태그: Patient, Birthday, SEX, COUNT, STRFTIME, AGGREGATION_LOGIC
- 교정 내용: 처음에는 Birthday를 직접 비교했으나, STRFTIME('%Y', Birthday)로 연도만 추출하여 비교하도록 수정함.
- 예외: 없음

## KB-007
- 상황: COUNT(*) 대신 DISTINCT를 사용해야 하는 질문
- 태그: Patient, ID, Laboratory, CRP, COUNT, JOIN_LOGIC
- 교정 내용: 처음에는 COUNT(*)를 사용했으나, COUNT(DISTINCT ID)로 수정하여 중복을 피하도록 함.
- 예외: 없음

## KB-008
- 상황: 날짜 비교 시 잘못된 함수 사용으로 인한 질문
- 태그: Patient, Birthday, SEX, COUNT, STRFTIME, AGGREGATION_LOGIC
- 교정 내용: 처음에는 YEAR() 함수를 사용했으나, STRFTIME('%Y', Birthday)로 수정하여 올바른 쿼리로 변경함.
- 예외: 없음

## KB-009
- 상황: COUNT(*) 대신 DISTINCT를 사용해야 하는 질문
- 태그: Patient, ID, Laboratory, CRE, COUNT, JOIN_LOGIC
- 교정 내용: 처음에는 COUNT(*)를 사용했으나, COUNT(DISTINCT Patient.ID)로 수정하여 중복을 피하도록 함.
- 예외: 없음

## KB-010
- 상황: 특정 연도에 검사받은 환자 중 나이를 계산할 때 검사 날짜를 기준으로 해야 하는 질문
- 태그: Patient, Birthday, Laboratory, Date, STRFTIME, AGGREGATION_LOGIC
- 교정 내용: 처음에는 현재 날짜를 기준으로 나이를 계산했으나, 검사 날짜를 기준으로 나이를 계산하도록 수정함.
- 예외: 없음

## KB-011
- 상황: 특정 컬럼이 잘못된 테이블에서 조회되어 조인해야 하는 질문
- 태그: Patient, ID, IGA, Laboratory, JOIN_LOGIC
- 교정 내용: 처음에는 Patient 테이블에서 IGA를 조회했으나, Laboratory 테이블에서 조회해야 한다는 힌트를 받아 조인하여 수정함.
- 예외: 없음

## KB-012
- 상황: 특정 조건을 만족하는 환자 수를 세는 질문에서 COUNT(*) 대신 DISTINCT를 사용해야 하는 경우
- 태그: Patient, ID, Laboratory, IGA, COUNT, JOIN_LOGIC
- 교정 내용: 처음에는 COUNT(*)를 사용했으나, COUNT(DISTINCT T1.ID)로 수정하여 중복을 피하도록 함.
- 예외: 없음

## KB-013
- 상황: 특정 조건을 만족하는 환자 수를 세는 질문에서 COUNT 조건을 잘못 사용한 경우
- 태그: Patient, ID, Admission, COUNT, AGGREGATION_LOGIC
- 교정 내용: 처음에는 COUNT(CASE WHEN Admission = '+' THEN ID END)로 잘못 작성했으나, COUNT(CASE WHEN Admission = '+' THEN 1 END)로 수정하여 올바른 조건을 반영함.
- 예외: 없음

## KB-014
- 상황: 특정 조건을 만족하는 환자 수를 세는 질문에서 GROUP BY를 사용해야 하는 경우
- 태그: Patient, ID, Admission, GROUP BY, AGGREGATION_LOGIC
- 교정 내용: 처음에는 GROUP BY를 사용하지 않아 중복된 환자 정보가 나올 수 있었으나, GROUP BY를 추가하여 중복을 제거한 쿼리로 수정함.
- 예외: 없음
