
## Round: R1
- '가장 많이 이긴 사람'을 찾을 때는 wins >= 1인 행 개수를 COUNT하여 내림차순 정렬 후 1명만 뽑아야 함.
- milliseconds 값 대신 time 컬럼을 사용하여 초 단위로 변환해야 함.
- dob가 NULL인 행이 있을 수 있으므로 dob IS NOT NULL 조건을 추가해야 함.
- forename과 surname은 합치지 말고 따로 반환해야 함.
- "3rd qualifying"은 q3 컬럼을 의미하므로 q3가 NULL이 아닌 행 중에서 시간을 초 단위로 변환하여 오름차순 정렬 후 1등만 뽑아야 함.
- position 조건은 >1이 아니라 <>1(1이 아닌 경우)로 써야 함.

## Round: R2
- '가장 어린 드라이버'를 찾을 때는 서브쿼리로 먼저 드라이버를 찾고, 그 드라이버의 레이스를 정렬하여 1등을 뽑아야 함.
- '챔피언'을 판단할 때는 position 대신 positionOrder = 1로 써야 하며, 시간 형식에 맞게 문자열을 분리하여 초 단위로 변환해야 함.
- 'Canadian Grand Prix'의 사고 수를 세려면 raceId를 직접 JOIN하여 모든 해당 레이스를 포함해야 하며, 사고 수는 해당 레이스에서만 세야 함.
- '이탈리아 서킷'의 가장 빠른 기록을 찾을 때는 lapTimes.time 대신 results.FastestLapTime을 사용하고, 전체에서 가장 빠른 기록 1개만 반환해야 함.
- 드라이버의 생년월일(dob)은 SELECT에서 제외해야 하며, 이름과 성만 반환해야 함.
- 'American' 국적의 드라이버를 찾을 때는 driverRef 대신 code 컬럼을 SELECT해야 함.
- 'Canadian Grand Prix'의 챔피언을 찾을 때는 time 컬럼을 SELECT하고, position 대신 time 형식으로 챔피언을 판단해야 함.
- 'AustChineseralian Grand Prix'의 2위 드라이버의 finish time을 찾을 때는 position 대신 rank = 2로 판단해야 하며, results.time을 SELECT해야 함.
- 'Austria'에서 열린 서킷의 위치와 좌표를 찾을 때는 DISTINCT를 추가해야 함.

## Round: R3
- '챔피언'의 시간은 H:MM:SS.mmm 형식이고, 나머지 순위의 시간은 격차 형식이므로, 격차 시간을 파싱할 때는 부호를 제외한 전체를 초 단위로 변환해야 함.
- '가장 어린 드라이버'를 찾을 때는 nationality를 COUNT하여 반환해야 하며, 드라이버의 생년월일(dob)로 정렬 후 상위 3명만 고려해야 함.
- '가장 많은 포인트를 얻은 드라이버'를 찾을 때는 driverStandings 테이블을 사용하고, SUM으로 합산하지 말고 points 값을 그대로 내림차순 정렬하여 1명만 뽑아야 함.
- '0 포인트'를 가진 constructor를 찾을 때는 constructorStandings 테이블을 사용하고, INNER JOIN으로 조건을 설정해야 하며, points=0이면서 raceId=291인 조건을 추가해야 함.
- '가장 빠른 랩'을 찾을 때는 lapTimes 테이블을 사용하고, fastestLapTime이 아닌 milliseconds 기준으로 오름차순 정렬해야 함.
- 'Q3의 랩 타임'을 찾을 때는 q3 형식이 '0:01:54'가 아니라 '1:54%'로 저장되어 있으므로, LIKE 조건을 수정해야 함.
- '서킷이 독일에 있는 레이스'를 찾을 때는 서브쿼리 대신 circuits와 races를 직접 JOIN하고 DISTINCT를 사용해야 함.
- '특정 레이스의 평균 랩 타임'을 구할 때는 year 조건을 추가해야 함.
