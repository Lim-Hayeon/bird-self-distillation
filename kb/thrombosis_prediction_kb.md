
## Round: R1
- 환자 리스트업할 땐 DISTINCT를 써야 중복이 생기지 않는다.
- 평균 계산할 때는 조건을 만족하는 검사기록을 기준으로 해야 하며, 서브쿼리(IN) 대신 조인을 사용해야 한다.
- COUNT를 사용할 때 "두 번 이상"은 COUNT >= 2로 계산해야 한다.
- 날짜 비교할 땐 Birthday를 STRFTIME('%Y', Birthday)로 연도만 뽑아서 비교해야 한다.
- 결과를 true/false로 반환해야 할 때는 문자열 대신 boolean 값을 사용해야 한다.
- 서브쿼리(IN) 대신 Laboratory와 직접 JOIN해서 COUNT해야 한다.

## Round: R2
- Diagnosis와 Date의 SELECT 순서는 Diagnosis 먼저, Date를 그 다음에 오도록 해야 한다.
- DISTINCT를 사용해야 중복을 제거할 수 있으며, SELECT 순서는 Diagnosis, ID, Age 순으로 바꿔야 한다.
- SM 컬럼의 정상 값은 'negative'와 '0'으로 저장되어 있으므로, 이를 기준으로 조건을 설정해야 한다. 서브쿼리 대신 직접 조인하여 조건을 확인해야 한다.
- Patient 테이블은 필요 없고, Examination과 Laboratory만 조인하여 COUNT해야 하며, DISTINCT는 사용하지 말아야 한다.
- SELECT 순서는 ID, SEX로 바꿔야 하며, GROUP BY는 SEX, ID로 해야 한다.
- CENTROMEA와 SSB의 정상 값은 'negative'와 '0'으로 저장되어 있으므로, 이를 기준으로 조건을 설정해야 한다.
- KCT, RVVT, LAC는 Examination 테이블에 있으므로, 해당 테이블을 조인해야 하며, DISTINCT는 사용하지 말아야 한다.

## Round: R3
- 나이를 계산할 땐 검사 날짜 기준으로 생년을 빼야 하며, DISTINCT는 사용하지 말아야 한다.
- 평균 계산할 땐 조건을 만족하는 행들만 기준으로 삼아야 하며, COUNT는 DISTINCT를 사용하지 말고 COUNT(*)로 해야 한다.
- 특정 컬럼의 값을 판단할 땐, 해당 컬럼을 직접 반환해야 하며, CASE 문을 사용하지 말아야 한다.
- 날짜 비교할 땐 STRFTIME('%Y', ...)를 사용해야 하며, 연도 비교는 '>' 또는 '<'로 해야 한다.
- 조건을 연결할 땐 괄호 없이 AND, OR를 사용하여 이어 써야 한다.
