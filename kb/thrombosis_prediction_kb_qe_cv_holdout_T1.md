## KB-001
- 상황: 환자의 진단과 실험실 검사 날짜를 조회할 때, SELECT 순서가 잘못된 경우
- 태그: Patient, Diagnosis, Laboratory, Date, COLUMN_ORDER
- 교정 내용: 처음에는 SELECT 순서가 잘못되어 L.Date, P.Diagnosis로 작성되었으나, P.Diagnosis, L.Date로 수정하여 올바른 순서로 변경되었다.
- 예외: 없음

## KB-002
- 상황: 적혈구 수치가 낮은 환자의 진단과 ID, 나이를 조회할 때, DISTINCT와 컬럼 순서가 잘못된 경우
- 태그: Patient, Diagnosis, Laboratory, RBC, COLUMN_ORDER, MISSING_DISTINCT
- 교정 내용: 처음에는 DISTINCT가 빠지고, 컬럼 순서가 잘못되어 Patient.Diagnosis, Patient.ID, Age로 작성되었으나, DISTINCT를 추가하고 순서를 Diagnosis, ID, Age로 수정하여 올바르게 변경되었다.
- 예외: 없음

## KB-003
- 상황: 정상 anti-SM을 가진 환자 중에서 혈전증이 없는 환자의 수를 조회할 때, 서브쿼리 대신 조인으로 변경해야 하는 경우
- 태그: Examination, Thrombosis, Laboratory, SM, JOIN_LOGIC
- 교정 내용: 처음에는 NOT IN 서브쿼리를 사용했으나, Examination 테이블과 Laboratory 테이블을 조인하여 E.Thrombosis = 0 조건으로 직접 세어야 한다는 힌트를 받아 수정하였다.
- 예외: 없음

## KB-004
- 상황: 총 빌리루빈 수치가 정상 범위를 벗어난 환자를 성별로 그룹화할 때, GROUP_CONCAT 대신 단순 GROUP BY를 사용해야 하는 경우
- 태그: Patient, Laboratory, T-BIL, GROUP BY, MISSING_DISTINCT
- 교정 내용: 처음에는 GROUP_CONCAT을 사용했으나, 단순히 ID와 SEX를 SELECT하여 SEX, ID로 GROUP BY 해야 한다는 힌트를 받아 수정하였다.
- 예외: 없음

## KB-005
- 상황: 정상 anti-centromere 및 anti-SSB 수치를 가진 남성 환자의 수를 조회할 때, 값 인코딩이 잘못된 경우
- 태그: Patient, SEX, Laboratory, CENTROMEA, SSB, VALUE_ENCODING
- 교정 내용: 처음에는 CENTROMEA와 SSB를 '-'/'+-'로 잘못 작성했으나, 'negative'/'0'으로 수정하여 올바르게 변경되었다.
- 예외: 없음

## KB-006
- 상황: 정상 범위의 크레아티닌 인산화효소를 가진 환자 중에서 응고 정도가 양성인 환자의 수를 조회할 때, DISTINCT가 잘못 사용된 경우
- 태그: Patient, Laboratory, CPK, KCT, RVVT, LAC, JOIN_LOGIC, MISSING_DISTINCT
- 교정 내용: 처음에는 DISTINCT를 사용했으나, Examination 테이블과 조인하여 COUNT(p.ID)로 수정하여 올바르게 변경되었다.
- 예외: 없음

## KB-007
- 상황: 미성년 환자의 수를 특정 연도 범위 내에서 조회할 때, 나이 계산 방식이 잘못된 경우
- 태그: Patient, Birthday, Examination, Examination Date, DATE_LOGIC, MISSING_DISTINCT
- 교정 내용: 처음에는 나이를 고정된 1993년 기준으로 계산했으나, Examination Date 연도에서 Birthday 연도의 차이를 계산해야 한다는 힌트를 받아 수정하였다. DISTINCT는 필요 없었다.
- 예외: 없음

## KB-008
- 상황: 특정 혈전증 수준과 ANA 패턴을 가진 환자의 수를 조회할 때, 평균 계산 방식이 잘못된 경우
- 태그: Examination, Thrombosis, ANA Pattern, aCL IgM, AGGREGATION_LOGIC, MISSING_DISTINCT
- 교정 내용: 처음에는 전체 평균을 사용했으나, Thrombosis=2와 ANA Pattern='S' 조건에 맞는 환자들만의 평균을 계산해야 한다는 힌트를 받아 수정하였다. DISTINCT는 필요 없었다.
- 예외: 없음

## KB-009
- 상황: 특정 환자의 총 콜레스테롤 감소율을 계산할 때, 서브쿼리 대신 조인으로 변경해야 하는 경우
- 태그: Patient, Laboratory, T-CHO, JOIN_LOGIC, AGGREGATION_LOGIC
- 교정 내용: 처음에는 서브쿼리를 사용했으나, Patient와 Laboratory를 조인하여 직접 계산해야 한다는 힌트를 받아 수정하였다.
- 예외: 없음

## KB-010
- 상황: 특정 진단을 받은 환자의 항체 농도 상태를 조회할 때, 반환할 컬럼이 잘못된 경우
- 태그: Patient, Examination, Diagnosis, aCL IgA, aCL IgG, aCL IgM, COLUMN_ORDER
- 교정 내용: 처음에는 항체 상태를 'present'/'absent'로 판단했으나, aCL IgA, aCL IgG, aCL IgM 값을 그대로 반환해야 한다는 힌트를 받아 수정하였다.
- 예외: 없음

## KB-011
- 상황: 비정상 IgM 수치를 가진 환자의 가장 흔한 진단을 조회할 때, 조인 테이블이 잘못된 경우
- 태그: Patient, Laboratory, Examination, IGM, JOIN_LOGIC
- 교정 내용: 처음에는 Examination 테이블을 사용했으나, Diagnosis는 Patient 테이블에 있어야 한다는 힌트를 받아 수정하였다.
- 예외: 없음

## KB-012
- 상황: 특정 연도에 검사받은 환자의 수를 조회할 때, 나이 계산 방식이 잘못된 경우
- 태그: Patient, Laboratory, Date, Birthday, DATE_LOGIC, MISSING_DISTINCT
- 교정 내용: 처음에는 현재 시각을 기준으로 나이를 계산했으나, 검사 날짜를 기준으로 계산해야 한다는 힌트를 받아 수정하였다. DISTINCT는 필요 없었다.
- 예외: 없음

## KB-013
- 상황: 입원 환자와 외래 환자의 비율을 계산할 때, 비율 계산 방식이 잘못된 경우
- 태그: Patient, Admission, SEX, AGGREGATION_LOGIC
- 교정 내용: 처음에는 입원 환자와 외래 환자의 수를 비교하여 텍스트로 판단했으나, 비율을 계산하여 반환해야 한다는 힌트를 받아 수정하였다.
- 예외: 없음

## KB-014
- 상황: 특정 IgA 수치 범위 내의 환자 수를 조회할 때, 테이블 조인과 조건이 잘못된 경우
- 태그: Patient, Laboratory, IGA, First Date, JOIN_LOGIC, AGGREGATION_LOGIC
- 교정 내용: 처음에는 Laboratory 테이블을 사용하지 않고 Patient 테이블에서 IGA를 조회했으나, Laboratory와 조인하여 조건을 수정해야 한다는 힌트를 받아 수정하였다.
- 예외: 없음

## KB-015
- 상황: 특정 기간 내에 검사받은 환자의 수를 조회할 때, 조인 테이블이 잘못된 경우
- 태그: Laboratory, Date, GPT, ALB, JOIN_LOGIC
- 교정 내용: 처음에는 Examination 테이블을 조인했으나, Laboratory 테이블만 사용해야 한다는 힌트를 받아 수정하였다.
- 예외: 없음
