## KB-001
- 상황: 가장 많이 이긴 드라이버의 이름, 국적, 최대 포인트를 구하는 질문
- 태그: drivers.forename, drivers.surname, driverStandings.wins, driverStandings.points, COUNT, GROUP BY, JOIN_LOGIC
- 교정 내용: 처음에는 드라이버의 이름을 합쳐서 반환하고, 가장 많이 이긴 드라이버를 MAX 서브쿼리로 찾으려 했으나, 올바른 방법은 wins가 1 이상인 드라이버를 COUNT하여 내림차순 정렬 후 1명만 뽑는 것이었다. GROUP BY도 forename, surname, nationality로 수정했다.
- 예외: 없음

## KB-002
- 상황: 기록된 최상의 랩 타임과 해당 드라이버 및 레이스를 구하는 질문
- 태그: lapTimes.milliseconds, drivers.forename, drivers.surname, races.name, ORDER BY, LIMIT
- 교정 내용: 처음에는 MIN 서브쿼리로 최상의 랩 타임을 찾으려 했으나, 올바른 방법은 milliseconds로 ORDER BY하여 가장 빠른 랩 타임을 찾는 것이었다. milliseconds 값을 SELECT에 포함시켜야 했다.
- 예외: 없음

## KB-003
- 상황: 2분 이하의 랩 타임을 기록한 프랑스 드라이버 수를 구하는 질문
- 태그: drivers.nationality, lapTimes.milliseconds, lapTimes.time, COUNT, JOIN_LOGIC
- 교정 내용: 처음에는 milliseconds 컬럼을 사용하여 120000 미만을 체크했으나, 올바른 방법은 time 컬럼을 사용하여 초 단위로 변환한 후 비교하는 것이었다. DISTINCT를 빼고 COUNT를 사용해야 했다.
- 예외: 없음

## KB-004
- 상황: 가장 나이가 많은 드라이버의 국적을 구하는 질문
- 태그: drivers.dob, drivers.nationality, ORDER BY, LIMIT
- 교정 내용: 처음에는 dob로 오름차순 정렬하여 LIMIT 1을 사용했으나, NULL 값이 있을 수 있어 dob IS NOT NULL 조건을 추가해야 했다.
- 예외: 없음

## KB-005
- 상황: 현재 가장 어린 레이서의 이름, 국적, 첫 레이스 이름을 구하는 질문
- 태그: drivers.forename, drivers.surname, drivers.nationality, driverStandings.raceId, ORDER BY, LIMIT
- 교정 내용: 처음에는 forename과 surname을 합쳐서 반환하고, results 테이블을 조인했으나, 올바른 방법은 forename과 surname을 따로 반환하고 driverStandings 테이블을 조인해야 했다. MAX 서브쿼리 대신 ORDER BY로 가장 어린 드라이버를 찾았다.
- 예외: 없음

## KB-006
- 상황: 루이스 해밀턴이 가장 높은 순위를 기록한 레이스를 구하는 질문
- 태그: results.rank, drivers.forename, drivers.surname, races.name, JOIN_LOGIC
- 교정 내용: 처음에는 레이스 이름, 날짜, 연도, 라운드를 SELECT했으나, 올바른 방법은 레이스 이름만 SELECT하고 rank = 1 조건으로 필터링해야 했다.
- 예외: 없음

## KB-007
- 상황: 포뮬러 1 레이스에서 가장 짧은 랩 타임을 기록한 드라이버를 구하는 질문
- 태그: lapTimes.time, drivers.forename, drivers.surname, MIN, ORDER BY, GROUP BY
- 교정 내용: 처음에는 time을 직접 비교했으나, 올바른 방법은 time을 초 단위로 변환하여 비교해야 했다. 드라이버별로 그룹핑하여 각자의 최소 기록을 구한 뒤 오름차순 정렬하여 20명을 뽑아야 했다.
- 예외: 없음

## KB-008
- 상황: 2009년 챔피언의 가장 빠른 랩 번호를 구하는 질문
- 태그: results.fastestLap, races.year, results.time, LIKE
- 교정 내용: 처음에는 챔피언 여부를 서브쿼리로 찾으려 했으나, 올바른 방법은 year = 2009이고 time이 특정 형식인 행을 반환하는 것이었다.
- 예외: 없음

## KB-009
- 상황: 2010년 이후 해밀턴이 1위가 아닌 경우의 비율을 구하는 질문
- 태그: driverStandings.position, drivers.surname, COUNT, JOIN_LOGIC
- 교정 내용: 처음에는 results 테이블을 조인하고 position 조건을 >1로 설정했으나, 올바른 방법은 driverStandings 테이블을 조인하고 position 조건을 <>1로 설정해야 했다. COUNT를 REAL로 캐스팅해야 했다.
- 예외: 없음

## KB-010
- 상황: 2008년 마리나 베이 스트리트 서킷에서 3번째 예선에서 1위를 기록한 레이서의 이름을 구하는 질문
- 태그: qualifying.q3, drivers.forename, drivers.surname, ORDER BY, LIMIT
- 교정 내용: 처음에는 position과 number 조건을 사용했으나, 올바른 방법은 q3가 NULL이 아닌 행 중에서 q3 시간을 초 단위로 변환하여 오름차순 정렬 후 1등만 뽑아야 했다.
- 예외: 없음

## KB-011
- 상황: 가장 어린 일본 드라이버의 나이와 이름을 구하는 질문
- 태그: drivers.nationality, drivers.dob, ORDER BY, LIMIT
- 교정 내용: 처음에는 나이를 마지막에 반환했으나, 올바른 방법은 나이를 첫 번째로 반환하고 forename과 surname을 그 뒤에 배치해야 했다.
- 예외: 없음

## KB-012
- 상황: 2009년 스페인 그랑프리에서 가장 빠른 랩 스피드를 구하는 질문
- 태그: results.fastestLapSpeed, races.name, races.year, ORDER BY, LIMIT
- 교정 내용: 처음에는 year 조건이 빠졌고, MAX() 대신 ORDER BY로 가장 빠른 랩 스피드를 찾는 것이었다.
- 예외: 없음
