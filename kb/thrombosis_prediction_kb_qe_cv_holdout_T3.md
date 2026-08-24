## KB-001
- 상황: 환자 단위로 리스트업할 때 중복을 피하기 위해 DISTINCT를 사용해야 하는 질문
- 태그: Patient, ID, SEX, Birthday, Laboratory, UN, DISTINCT, WRONG_COLUMN
- 교정 내용: 처음에는 DISTINCT 없이 환자 정보를 조회하여 중복이 발생했으나, DISTINCT를 추가하여 중복을 제거한 결과가 맞는 쿼리가 되었다.
- 예외: 없음

## KB-002
- 상황: 평균 계산 시 중복된 환자 기록을 피하기 위해 직접 조인하여 계산해야 하는 질문
- 태그: Patient, Birthday, Laboratory, T-CHO, AVG, JOIN_LOGIC
- 교정 내용: 처음에는 서브쿼리를 사용하여 환자 ID만 걸러내어 중복이 없어져서 틀렸으나, 직접 조인하여 조건을 만족하는 검사 기록을 기준으로 평균을 계산하여 올바른 쿼리가 되었다.
- 예외: 없음

## KB-003
- 상황: 특정 컬럼이 잘못된 테이블에서 조회되어 오류가 발생한 질문
- 태그: Patient, ID, SEX, Symptoms, Examination, SC170, Laboratory, JOIN_LOGIC, WRONG_TABLE
- 교정 내용: 처음에는 Examination 테이블에서 SC170을 조회했으나, Laboratory 테이블에서 조회해야 하므로 조인을 추가하여 올바른 쿼리가 되었다.
- 예외: 없음

## KB-004
- 상황: COUNT 조건을 잘못 설정하여 결과가 틀린 질문
- 태그: Patient, ID, Birthday, Laboratory, HCT, COUNT, GROUP BY, AGGREGATION_LOGIC
- 교정 내용: 처음에는 COUNT(L.ID) > 2로 설정했으나, COUNT(L.ID) >= 2로 수정하여 올바른 쿼리가 되었다.
- 예외: 없음

## KB-005
- 상황: 환자 리스트업 시 DISTINCT를 사용해야 하는 질문
- 태그: Patient, ID, SEX, Birthday, Laboratory, UN, DISTINCT, WRONG_COLUMN
- 교정 내용: 처음에는 DISTINCT 없이 환자 정보를 조회하여 중복이 발생했으나, DISTINCT를 추가하여 중복을 제거한 결과가 맞는 쿼리가 되었다.
- 예외: 없음

## KB-006
- 상황: 날짜 비교 시 잘못된 방식으로 비교하여 오류가 발생한 질문
- 태그: Patient, Birthday, SEX, STRFTIME, AGGREGATION_LOGIC, DATE_LOGIC
- 교정 내용: 처음에는 Birthday를 직접 비교했으나, STRFTIME('%Y', Birthday)로 연도만 추출하여 비교하여 올바른 쿼리가 되었다.
- 예외: 없음

## KB-007
- 상황: COUNT(*) 대신 DISTINCT를 사용해야 하는 질문
- 태그: Patient, ID, Laboratory, CRP, COUNT, JOIN_LOGIC
- 교정 내용: 처음에는 COUNT(*)로 환자 수를 셌으나, COUNT(DISTINCT ID)로 수정하여 중복을 피한 올바른 쿼리가 되었다.
- 예외: 없음

## KB-008
- 상황: 날짜 비교 시 잘못된 함수 사용으로 오류가 발생한 질문
- 태그: Patient, Birthday, SEX, STRFTIME, AGGREGATION_LOGIC, DATE_LOGIC
- 교정 내용: 처음에는 YEAR() 함수를 사용했으나, STRFTIME('%Y', Birthday)로 수정하여 올바른 쿼리가 되었다.
- 예외: 없음

## KB-009
- 상황: 특정 컬럼의 순서가 잘못되어 결과가 틀린 질문
- 태그: Patient, ID, Diagnosis, Laboratory, Date, WRONG_COLUMN
- 교정 내용: 처음에는 SELECT 순서가 L.Date, P.Diagnosis로 되어 있었으나, P.Diagnosis, L.Date로 수정하여 올바른 쿼리가 되었다.
- 예외: 없음

## KB-010
- 상황: 중복된 환자 기록을 피하기 위해 DISTINCT를 사용해야 하는 질문
- 태그: Patient, ID, Diagnosis, Laboratory, RBC, DISTINCT, AGGREGATION_LOGIC
- 교정 내용: 처음에는 DISTINCT 없이 환자 정보를 조회하여 중복이 발생했으나, DISTINCT를 추가하여 중복을 제거한 결과가 맞는 쿼리가 되었다.
- 예외: 없음

## KB-011
- 상황: 서브쿼리 대신 직접 조인하여 조건을 만족해야 하는 질문
- 태그: Examination, Laboratory, SM, Thrombosis, COUNT, JOIN_LOGIC
- 교정 내용: 처음에는 NOT IN 서브쿼리를 사용했으나, Examination 테이블에서 Thrombosis = 0 조건으로 직접 조인하여 올바른 쿼리가 되었다.
- 예외: 없음

## KB-012
- 상황: GROUP BY 시 컬럼 순서가 잘못되어 결과가 틀린 질문
- 태그: Patient, ID, Laboratory, T-BIL, GROUP BY, WRONG_COLUMN
- 교정 내용: 처음에는 SEX, ID로 GROUP BY 하였으나, ID, SEX로 수정하여 올바른 쿼리가 되었다.
- 예외: 없음

## KB-013
- 상황: 특정 컬럼의 값이 잘못된 인코딩으로 조회되어 오류가 발생한 질문
- 태그: Patient, SEX, Laboratory, CENTROMEA, SSB, WRONG_COLUMN
- 교정 내용: 처음에는 CENTROMEA와 SSB를 '-'/'+-'로 조회했으나, 'negative'/'0'으로 수정하여 올바른 쿼리가 되었다.
- 예외: 없음

## KB-014
- 상황: DISTINCT 대신 COUNT를 사용해야 하는 질문
- 태그: Patient, ID, Laboratory, CPK, COUNT, AGGREGATION_LOGIC
- 교정 내용: 처음에는 COUNT(DISTINCT p.ID)로 설정했으나, COUNT(p.ID)로 수정하여 올바른 쿼리가 되었다.
- 예외: 없음
