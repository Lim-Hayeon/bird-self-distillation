## KB-001
- 상황: 드라이버의 승리 수를 기준으로 가장 많은 승리를 기록한 드라이버의 이름, 국적, 최대 포인트를 구하는 질문
- 태그: drivers.forename, drivers.surname, driverStandings.wins, driverStandings.points, COUNT, GROUP BY, JOIN_LOGIC
- 교정 내용: 처음에는 드라이버의 이름을 합쳐서 반환했으나, 따로 반환해야 한다는 힌트를 받아 수정했다. 또한, "가장 많이 이긴 사람"을 찾는 방법을 MAX 서브쿼리에서 COUNT로 변경하여 올바른 결과를 도출했다.
- 예외: 없음

## KB-002
- 상황: 기록된 최상의 랩 타임과 해당 드라이버 및 레이스를 찾는 질문
- 태그: lapTimes.milliseconds, drivers.forename, drivers.surname, races.name, ORDER BY, LIMIT
- 교정 내용: 처음에는 MIN 서브쿼리를 사용하여 최상의 랩 타임을 찾으려 했으나, ORDER BY와 LIMIT를 사용하여 가장 빠른 랩 타임을 찾는 방식으로 수정했다.
- 예외: 없음

## KB-003
- 상황: 특정 조건을 만족하는 프랑스 드라이버의 수를 세는 질문
- 태그: drivers.nationality, lapTimes.time, COUNT, JOIN_LOGIC
- 교정 내용: 처음에는 milliseconds 컬럼을 사용했으나, 문자열 형식의 time 컬럼을 사용하여 초 단위로 변환해야 한다는 힌트를 받아 수정했다. 또한 DISTINCT를 제거하고 COUNT로 변경했다.
- 예외: 없음

## KB-004
- 상황: 가장 나이가 많은 드라이버의 국적을 찾는 질문
- 태그: drivers.dob, drivers.nationality, ORDER BY, LIMIT
- 교정 내용: 처음에는 dob가 NULL인 경우를 고려하지 않았으나, NULL 조건을 추가하여 수정했다.
- 예외: 없음

## KB-005
- 상황: 현재 가장 어린 드라이버의 전체 이름, 국적, 첫 레이스 이름을 찾는 질문
- 태그: drivers.forename, drivers.surname, drivers.nationality, races.name, ORDER BY, LIMIT
- 교정 내용: 처음에는 forename과 surname을 합쳐서 반환했으나, 따로 반환해야 한다는 힌트를 받아 수정했다. 또한, MAX 서브쿼리 대신 ORDER BY와 LIMIT를 사용하여 가장 어린 드라이버를 찾는 방식으로 변경했다.
- 예외: 없음

## KB-006
- 상황: 루이스 해밀턴이 가장 높은 순위를 기록한 레이스를 찾는 질문
- 태그: drivers.forename, drivers.surname, results.rank, races.name, JOIN_LOGIC
- 교정 내용: 처음에는 레이스의 이름, 날짜, 연도, 라운드를 모두 선택했으나, 레이스 이름만 선택해야 한다는 힌트를 받아 수정했다. 또한, ORDER BY 대신 rank = 1 조건으로 변경했다.
- 예외: 없음

## KB-007
- 상황: 포뮬러 1 레이스에서 가장 짧은 랩 타임을 기록한 드라이버를 찾는 질문
- 태그: lapTimes.time, drivers.forename, drivers.surname, MIN, ORDER BY, LIMIT
- 교정 내용: 처음에는 time을 문자열로 비교했으나, 초 단위로 변환하여 비교해야 한다는 힌트를 받아 수정했다. 또한, 드라이버별로 그룹핑하여 각자의 최소 기록을 구한 뒤 오름차순 정렬하여 20명을 뽑는 방식으로 변경했다.
- 예외: 없음

## KB-008
- 상황: 2009년 챔피언의 가장 빠른 랩 번호를 찾는 질문
- 태그: results.fastestLap, races.year, results.time, LIKE
- 교정 내용: 처음에는 챔피언 여부를 driverStandings 서브쿼리로 찾으려 했으나, results.time 컬럼이 특정 형식인 행만 걸러내는 조건으로 수정했다. 이후 챔피언 조건을 아예 빼고 year=2009이고 time이 그 형식인 행 전체를 반환하도록 변경했다.
- 예외: 없음

## KB-009
- 상황: 2010년 이후 해밀턴이 1위가 아닌 경우의 비율을 계산하는 질문
- 태그: driverStandings.position, drivers.surname, COUNT, JOIN_LOGIC
- 교정 내용: 처음에는 results 테이블을 사용했으나, driverStandings 테이블을 조인해야 한다는 힌트를 받아 수정했다. 또한, position 조건을 >1에서 <>1로 변경하고, CAST를 REAL로 수정했다.
- 예외: 없음

## KB-010
- 상황: 2008년 마리나 베이 스트리트 서킷에서 3차 예선에서 1위를 기록한 드라이버의 이름을 찾는 질문
- 태그: qualifying.q3, drivers.forename, drivers.surname, ORDER BY, LIMIT
- 교정 내용: 처음에는 3차 예선이 q3 컬럼이라는 것을 인지하지 못하고 position과 number 조건을 사용했으나, q3가 NULL이 아닌 행 중에서 시간을 초 단위로 변환하여 오름차순 정렬 후 1등만 뽑아야 한다는 힌트를 받아 수정했다.
- 예외: 없음

## KB-011
- 상황: 가장 어린 일본 드라이버의 나이와 이름을 찾는 질문
- 태그: drivers.nationality, drivers.dob, ORDER BY, LIMIT
- 교정 내용: 처음에는 age, forename, surname 순서로 반환해야 한다는 것을 인지하지 못하고 forename과 surname을 먼저 반환했으나, 순서를 변경하여 수정했다.
- 예외: 없음

## KB-012
- 상황: 2009년 스페인 그랑프리에서 가장 빠른 랩 속도를 찾는 질문
- 태그: results.fastestLapSpeed, races.name, races.year, ORDER BY, LIMIT
- 교정 내용: 처음에는 year 조건이 빠졌고, MAX() 대신 ORDER BY와 LIMIT를 사용해야 한다는 힌트를 받아 수정했다.
- 예외: 없음

## KB-013
- 상황: 가장 어린 드라이버의 첫 번째 예선 레이스의 연도, 이름, 날짜, 시간을 찾는 질문
- 태그: drivers.dob, races.year, races.name, races.date, races.time, ORDER BY, LIMIT, SUBQUERY_VS_JOIN
- 교정 내용: 처음에는 GROUP BY 방식으로 드라이버를 찾으려 했으나, 가장 어린 드라이버를 서브쿼리로 먼저 찾고 그 드라이버의 레이스를 정렬하여 1등을 뽑는 방식으로 수정했다. 또한, 드라이버 이름을 합치는 대신 레이스 이름을 사용해야 한다는 힌트를 받아 수정했다.
- 예외: 없음

## KB-014
- 상황: 1975년 이전 챔피언의 평균 시간을 초 단위로 구하는 질문
- 태그: results.positionOrder, races.year, results.time, AVG, JOIN_LOGIC, DATE_LOGIC
- 교정 내용: 처음에는 seasons 테이블을 조인하려 했으나, races.year를 직접 사용해야 한다는 힌트를 받아 수정했다. 또한, position 조건을 1에서 positionOrder = 1로 변경하고, 시간 형식에 맞게 문자열을 분리하여 초 단위로 변환해야 한다는 힌트를 받아 수정했다.
- 예외: 없음

## KB-015
- 상황: 캐나다 그랑프리에서 가장 많은 사고를 낸 드라이버의 사고 수를 찾는 질문
- 태그: results.statusId, races.name, COUNT, JOIN_LOGIC
- 교정 내용: 처음에는 raceId를 하나만 찾으려 했으나, 모든 해당 레이스를 포함해야 한다는 힌트를 받아 수정했다. 또한, 마지막 COUNT 조건을 전체 사고가 아닌 캐나다 그랑프리에서의 사고만 세야 한다는 힌트를 받아 수정했다.
- 예외: 없음

## KB-016
- 상황: 이탈리아 서킷의 가장 빠른 랩 기록을 찾는 질문
- 태그: results.FastestLapTime, circuits.country, MIN, JOIN_LOGIC
- 교정 내용: 처음에는 lapTimes.time을 사용하려 했으나, results.FastestLapTime을 사용해야 한다는 힌트를 받아 수정했다. 또한, 이탈리아 서킷 전체에서 가장 빠른 기록을 찾는 방식으로 변경했다.
- 예외: 없음

## KB-017
- 상황: 872번 레이스에서 경기를 마친 가장 어린 드라이버를 찾는 질문
- 태그: drivers.dob, results.time, ORDER BY, LIMIT
- 교정 내용: 처음에는 dob 컬럼을 SELECT에서 빼야 한다는 힌트를 받아 수정했다. forename과 surname만 반환해야 한다는 힌트를 받아 수정했다.
- 예외: 없음

## KB-018
- 상황: 2008년 캐나다 그랑프리 챔피언의 완주 시간을 찾는 질문
- 태그: results.time, races.year, races.name, LIKE
- 교정 내용: 처음에는 드라이버 이름을 포함해야 한다는 것을 인지하지 못하고 time 컬럼만 선택했으나, 챔피언을 판단하는 조건을 time 형식으로 변경해야 한다는 힌트를 받아 수정했다.
- 예외: 없음

## KB-019
- 상황: 영국 국적의 최대 포인트를 찾는 질문
- 태그: constructors.nationality, constructorStandings.points, MAX, JOIN_LOGIC
- 교정 내용: 처음에는 constructorResults 테이블을 사용하려 했으나, constructorStandings 테이블을 사용해야 한다는 힌트를 받아 수정했다.
- 예외: 없음

## KB-020
- 상황: 유럽 그랑프리에서 독일에서 개최된 비율을 계산하는 질문
- 태그: races.name, circuits.country, COUNT, JOIN_LOGIC, AGGREGATION_LOGIC
- 교정 내용: 처음에는 races 테이블에서 country 컬럼을 사용하려 했으나, circuits 테이블을 조인하여 country를 가져와야 한다는 힌트를 받아 수정했다. 또한, CAST를 REAL로 변경해야 한다는 힌트를 받아 수정했다.
- 예외: 없음

## KB-021
- 상황: 1971년에 태어난 드라이버 중 가장 빠른 랩 타임을 기록한 드라이버를 찾는 질문
- 태그: drivers.dob, results.fastestLapTime, JOIN_LOGIC
- 교정 내용: 처음에는 서브쿼리를 사용하려 했으나, drivers와 results를 직접 JOIN해야 한다는 힌트를 받아 수정했다.
- 예외: 없음

## KB-022
- 상황: 알렉스 유옹이 20위 이하로 주행한 레이스를 찾는 질문
- 태그: drivers.forename, drivers.surname, driverStandings.position, JOIN_LOGIC
- 교정 내용: 처음에는 results 테이블을 사용하려 했으나, driverStandings 테이블을 사용해야 한다는 힌트를 받아 수정했다. 또한, SELECT에서 레이스 이름만 반환해야 한다는 힌트를 받아 수정했다.
- 예외: 없음

## KB-023
- 상황: 45번 레이스에서 Q3 시간이 0:01:33인 드라이버의 약어 코드를 찾는 질문
- 태그: qualifying.q3, drivers.code, LIKE, JOIN_LOGIC
- 교정 내용: 처음에는 q3 시간이 '0:01:33' 형식으로 저장되어 있다고 잘못 인식했으나, 실제 형식에 맞게 LIKE 조건을 수정해야 한다는 힌트를 받아 수정했다.
- 예외: 없음

## KB-024
- 상황: 미국 국적의 드라이버 코드를 찾는 질문
- 태그: drivers.nationality, drivers.code
- 교정 내용: 처음에는 driverRef를 선택하려 했으나, code 컬럼을 선택해야 한다는 힌트를 받아 수정했다.
- 예외: 없음

## KB-025
- 상황: 2007년 캐나다 그랑프리에서 1위를 기록한 드라이버의 이름을 찾는 질문
- 태그: races.name, results.rank, drivers.driverRef, JOIN_LOGIC
- 교정 내용: 처음에는 year 조건을 results 테이블에서 찾으려 했으나, races 테이블에서 year를 가져와야 한다는 힌트를 받아 수정했다. 또한, position 조건을 rank로 변경해야 한다는 힌트를 받아 수정했다.
- 예외: 없음

## KB-026
- 상황: 2008년 중국 그랑프리에서 2위를 기록한 드라이버의 완주 시간을 찾는 질문
- 태그: results.rank, races.name, results.time, JOIN_LOGIC
- 교정 내용: 처음에는 position 조건을 사용했으나, rank 조건으로 변경해야 한다는 힌트를 받아 수정했다. 또한, SELECT할 time은 results.time이어야 한다는 힌트를 받아 수정했다.
- 예외: 없음

## KB-027
- 상황: 오스트리아에서 개최된 서킷의 위치와 좌표를 찾는 질문
- 태그: circuits.country, circuits.location, circuits.lat, circuits.lng, DISTINCT
- 교정 내용: 처음에는 DISTINCT 조건이 빠졌으나, 추가해야 한다는 힌트를 받아 수정했다.
- 예외: 없음
