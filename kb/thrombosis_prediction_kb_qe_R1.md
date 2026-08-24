## KB-001
- 상황: 환자 단위로 리스트업할 때 중복을 방지하기 위해 DISTINCT를 사용해야 하는 경우
- 태그: Patient, ID, SEX, Birthday, Laboratory, LDH, DISTINCT, JOIN_LOGIC
- 교정 내용: 처음에는 DISTINCT를 사용하지 않아 중복된 환자 정보가 나올 수 있었으나, DISTINCT를 추가하여 중복을 제거한 결과가 맞는 쿼리가 되었다.
- 예외: 없음

## KB-002
- 상황: 평균 계산 시 중복된 환자 기록을 방지하기 위해 직접 조인하여 조건을 만족하는 검사 기록을 기준으로 평균을 내야 하는 경우
- 태그: Patient, Birthday, Laboratory, T-CHO, AVG, JOIN_LOGIC
- 교정 내용: 처음에는 서브쿼리를 사용하여 환자 ID만 걸러내어 중복이 없어져서 틀렸으나, 직접 조인하여 조건을 만족하는 검사 기록을 기준으로 평균을 내는 쿼리로 수정하여 올바른 결과를 얻었다.
- 예외: 없음

## KB-003
- 상황: 특정 컬럼이 다른 테이블에 있을 때, 해당 테이블도 함께 조인해야 하는 경우
- 태그: Patient, ID, SEX, Symptoms, Laboratory, SC170, JOIN_LOGIC
- 교정 내용: 처음에는 SC170 컬럼이 Examination 테이블에 있다고 잘못 판단하여 쿼리가 틀렸으나, Laboratory 테이블에 있는 SC170을 사용하여 올바른 쿼리로 수정하였다.
- 예외: 없음

## KB-004
- 상황: COUNT 조건을 설정할 때, "두 번 이상"을 정확히 표현하기 위해 COUNT >= 2로 계산해야 하는 경우
- 태그: Patient, ID, Birthday, Laboratory, HCT, COUNT, GROUP BY, HAVING
- 교정 내용: 처음에는 COUNT(ID) > 2로 잘못 작성하였으나, COUNT(ID) >= 2로 수정하여 올바른 쿼리를 작성하였다.
- 예외: 없음

## KB-005
- 상황: 환자 리스트업 시 DISTINCT를 사용해야 하는 경우
- 태그: Patient, ID, SEX, Birthday, Laboratory, UN, DISTINCT, JOIN_LOGIC
- 교정 내용: 처음에는 DISTINCT를 사용하지 않아 중복된 환자 정보가 나올 수 있었으나, DISTINCT를 추가하여 중복을 제거한 결과가 맞는 쿼리가 되었다.
- 예외: 없음

## KB-006
- 상황: 날짜 비교 시 STRFTIME을 사용하여 연도만 추출하여 비교해야 하는 경우
- 태그: Patient, Birthday, SEX, COUNT, Description
- 교정 내용: 처음에는 Birthday를 직접 비교하여 잘못된 쿼리가 되었으나, STRFTIME('%Y', Birthday)로 연도만 추출하여 비교하는 쿼리로 수정하여 올바른 결과를 얻었다.
- 예외: 없음

## KB-007
- 상황: COUNT를 사용할 때 DISTINCT를 사용하여 중복을 방지해야 하는 경우
- 태그: Patient, Laboratory, CRE, COUNT, JOIN_LOGIC
- 교정 내용: 처음에는 COUNT(*)를 사용하여 중복된 환자 수를 세었으나, COUNT(DISTINCT ID)로 수정하여 중복을 방지한 올바른 쿼리를 작성하였다.
- 예외: 없음
