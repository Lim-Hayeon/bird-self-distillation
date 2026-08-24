## KB-001
- 상황: 드라이버의 승리 수를 기준으로 가장 많은 승리를 기록한 드라이버의 이름, 국적, 최대 포인트를 구하는 질문
- 태그: drivers.forename, drivers.surname, driverStandings.nationality, driverStandings.points, driverStandings.wins, COUNT, GROUP BY
- 교정 내용: 처음에는 드라이버의 이름을 합쳐서 반환했으나, 따로 반환해야 한다는 힌트를 받아 수정했다. 또한, "가장 많이 이긴 사람"을 MAX 서브쿼리로 찾는 대신, wins가 1 이상인 행의 개수를 COUNT하여 내림차순 정렬 후 1명만 뽑는 방식으로 변경했다.
- 예외: 없음

## KB-002
- 상황: 기록된 최상의 랩 타임과 해당 드라이버 및 레이스를 구하는 질문
- 태그: lapTimes.milliseconds, drivers.forename, drivers.surname, races.name, ORDER BY, LIMIT
- 교정 내용: 처음에는 MIN 서브쿼리로 최상의 랩 타임을 찾으려 했으나, 힌트를 받아 milliseconds 값을 SELECT에 포함시키고 ORDER BY로 정렬하여 LIMIT 1로 수정했다.
- 예외: 없음

## KB-003
- 상황: 특정 조건을 만족하는 프랑스 드라이버의 수를 구하는 질문
- 태그: drivers.nationality, lapTimes.time, COUNT, CAST, SUBSTR
- 교정 내용: 처음에는 milliseconds 컬럼을 사용했으나, 힌트를 받아 time 컬럼을 사용하여 초 단위로 변환한 후 COUNT로 수정했다. DISTINCT를 빼고 COUNT(*)로 변경했다.
- 예외: 없음

## KB-004
- 상황: 가장 나이가 많은 드라이버의 국적을 구하는 질문
- 태그: drivers.nationality, drivers.dob, ORDER BY, LIMIT
- 교정 내용: 처음에는 dob가 NULL인 행을 고려하지 않았으나, 힌트를 받아 dob IS NOT NULL 조건을 추가하여 수정했다.
- 예외: 없음

## KB-005
- 상황: 현재 가장 어린 드라이버의 전체 이름, 국적, 첫 레이스 이름을 구하는 질문
- 태그: drivers.forename, drivers.surname, drivers.nationality, races.name, ORDER BY, LIMIT
- 교정 내용: 처음에는 forename과 surname을 합쳐서 반환했으나, 따로 반환해야 한다는 힌트를 받아 수정했다. 또한, MAX 서브쿼리 대신 ORDER BY로 가장 어린 드라이버를 찾도록 변경했다.
- 예외: 없음

## KB-006
- 상황: 루이스 해밀턴이 가장 높은 순위를 기록한 레이스를 구하는 질문
- 태그: results.rank, drivers.forename, drivers.surname, races.name, WHERE
- 교정 내용: 처음에는 모든 레이스 정보를 SELECT했으나, 힌트를 받아 race name만 SELECT하도록 수정하고, ORDER BY/LIMIT 대신 rank = 1 조건으로 필터링했다.
- 예외: 없음

## KB-007
- 상황: 포뮬러 1 레이스에서 가장 짧은 랩 타임을 기록한 드라이버의 이름을 구하는 질문
- 태그: lapTimes.time, drivers.forename, drivers.surname, MIN, ORDER BY, LIMIT
- 교정 내용: 처음에는 time을 문자열로 비교했으나, 힌트를 받아 콜론/점 기준으로 분/초/밀리초를 분리하여 초 단위로 변환한 후 비교하도록 수정했다. 드라이버별로 그룹핑하여 각자의 최소 기록을 구한 뒤 오름차순 정렬하여 20명을 뽑도록 변경했다.
- 예외: 없음

## KB-008
- 상황: 2009년 챔피언의 가장 빠른 랩 번호를 구하는 질문
- 태그: results.fastestLap, races.year, results.time, LIKE
- 교정 내용: 처음에는 챔피언 여부를 driverStandings 서브쿼리로 찾으려 했으나, 힌트를 받아 results.time 컬럼이 특정 형식인 행만 걸러내는 조건으로 수정했다.
- 예외: 없음

## KB-009
- 상황: 2010년 이후 해밀턴이 1위가 아닌 경우의 비율을 계산하는 질문
- 태그: driverStandings.position, drivers.surname, COUNT, CAST
- 교정 내용: 처음에는 results 테이블을 사용했으나, 힌트를 받아 driverStandings 테이블을 조인하도록 수정했다. position 조건을 >1에서 <>1로 변경하고, CAST를 REAL로 수정했다.
- 예외: 없음

## KB-010
- 상황: 2008년 마리나 베이 스트리트 서킷에서 3차 예선에서 1위를 기록한 드라이버의 이름을 구하는 질문
- 태그: qualifying.q3, drivers.forename, drivers.surname, ORDER BY, LIMIT
- 교정 내용: 처음에는 position과 number 조건을 사용했으나, 힌트를 받아 q3가 NULL이 아닌 행 중에서 q3 시간을 초 단위로 변환하여 오름차순 정렬 후 1등만 뽑도록 수정했다.
- 예외: 없음

## KB-011
- 상황: 가장 어린 일본 드라이버의 나이와 이름을 구하는 질문
- 태그: drivers.nationality, drivers.dob, STRFTIME, ORDER BY, LIMIT
- 교정 내용: 처음에는 나이, 이름 순서로 반환했으나, 힌트를 받아 age, forename, surname 순서로 변경했다.
- 예외: 없음

## KB-012
- 상황: 2009년 스페인 그랑프리에서 모든 드라이버의 가장 빠른 랩 속도를 구하는 질문
- 태그: results.fastestLapSpeed, races.name, races.year, ORDER BY, LIMIT
- 교정 내용: 처음에는 year 조건이 빠졌고, MAX() 대신 ORDER BY로 수정해야 한다는 힌트를 받아 수정했다.
- 예외: 없음

## KB-013
- 상황: 2008년 호주 그랑프리에서 챔피언과 마지막으로 경기를 마친 드라이버의 시간 차이를 백분율로 계산하는 질문
- 태그: results.time, results.positionOrder, CAST, SUBSTR, AGGREGATION_LOGIC, DATE_LOGIC
- 교정 내용: 처음에는 마지막 드라이버의 시간을 챔피언과 같은 방식으로 파싱했으나, 힌트를 받아 마지막 드라이버의 시간은 챔피언의 시간과의 격차로 계산해야 한다는 점을 반영하여 수정했다. 또한, 최종 퍼센트 값만 반환하도록 SELECT 문을 간소화했다.
- 예외: 없음

## KB-014
- 상황: 상위 3명의 가장 어린 드라이버 중 네덜란드 드라이버의 수를 구하는 질문
- 태그: drivers.dob, drivers.nationality, COUNT, ORDER BY
- 교정 내용: 처음에는 드라이버의 코드를 반환하려 했으나, 힌트를 받아 nationality가 'Dutch'인 드라이버 수만 COUNT하여 반환하도록 수정했다.
- 예외: 없음

## KB-015
- 상황: 가장 많은 포인트를 기록한 드라이버의 이름과 포인트를 구하는 질문
- 태그: driverStandings.points, drivers.forename, drivers.surname, ORDER BY
- 교정 내용: 처음에는 results 테이블을 사용하여 SUM으로 포인트를 합산하려 했으나, 힌트를 받아 driverStandings 테이블을 사용하고, 포인트를 그대로 내림차순 정렬하여 1등만 뽑도록 수정했다.
- 예외: 없음

## KB-016
- 상황: 291번 레이스에서 포인트가 0인 팀의 이름을 구하는 질문
- 태그: constructorStandings.points, constructors.name, INNER JOIN
- 교정 내용: 처음에는 constructorResults 테이블을 사용하려 했으나, 힌트를 받아 constructorStandings 테이블을 사용하고, INNER JOIN으로 포인트가 0이면서 raceId가 291인 조건으로 수정했다.
- 예외: 없음

## KB-017
- 상황: 미하엘 슈마허가 가장 빠른 랩을 기록한 레이스의 이름과 연도를 구하는 질문
- 태그: lapTimes.milliseconds, races.name, races.year, ORDER BY
- 교정 내용: 처음에는 results 테이블을 사용하려 했으나, 힌트를 받아 lapTimes 테이블을 조인하고, fastestLapTime 대신 milliseconds 기준으로 오름차순 정렬하도록 수정했다.
- 예외: 없음

## KB-018
- 상황: 폴 디 레스타가 853번 레이스에서 가장 빠른 랩 속도보다 854번 레이스에서 얼마나 더 빨리 완주했는지 비율을 구하는 질문
- 태그: results.fastestLapSpeed, drivers.forename, drivers.surname, AGGREGATION_LOGIC
- 교정 내용: 처음에는 단순히 두 값을 빼는 방식으로 계산하려 했으나, 힌트를 받아 비율을 계산하는 공식을 적용하여 수정했다.
- 예외: 없음

## KB-019
- 상황: 161번 레이스에서 0:01:27의 랩 타임을 기록한 드라이버의 이름과 웹사이트를 구하는 질문
- 태그: lapTimes.time, drivers.forename, drivers.surname, DISTINCT
- 교정 내용: 처음에는 time 형식이 '0:01:27'로 되어 있다고 가정했으나, 힌트를 받아 '1:27%'로 수정하고, DISTINCT를 추가하여 드라이버의 이름과 웹사이트를 함께 반환하도록 수정했다.
- 예외: 없음

## KB-020
- 상황: 독일 서킷에서 열린 레이스의 이름을 구하는 질문
- 태그: circuits.country, races.name, INNER JOIN, DISTINCT
- 교정 내용: 처음에는 서브쿼리를 사용하려 했으나, 힌트를 받아 circuits와 races를 직접 JOIN하고 DISTINCT를 사용하여 수정했다.
- 예외: 없음

## KB-021
- 상황: 2009년 말레이시아 그랑프리에서 루이스 해밀턴의 평균 랩 타임을 구하는 질문
- 태그: lapTimes.milliseconds, drivers.forename, drivers.surname, races.year, AGGREGATION_LOGIC
- 교정 내용: 처음에는 year 조건이 빠졌으나, 힌트를 받아 2009년 조건을 추가하여 수정했다.
- 예외: 없음

## KB-022
- 상황: 903번 예선에서 0:01:54의 Q3 랩 타임을 기록한 드라이버의 번호를 구하는 질문
- 태그: qualifying.q3, drivers.number, LIKE
- 교정 내용: 처음에는 q3 형식이 '0:01:54'로 되어 있다고 가정했으나, 힌트를 받아 '1:54%'로 수정하여 드라이버 번호를 반환하도록 수정했다.
- 예외: 없음
