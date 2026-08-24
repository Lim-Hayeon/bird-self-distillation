## KB-001
- 상황: 드라이버의 생년이 1971년인 경우, 가장 빠른 랩 타임을 기록한 드라이버의 ID와 코드를 찾고자 할 때
- 태그: drivers, driverId, code, results, fastestLapTime, JOIN_LOGIC
- 교정 내용: 처음에는 서브쿼리(IN)를 사용하여 드라이버를 찾으려 했으나, 직접 JOIN을 통해 드라이버와 결과를 연결해야 한다는 것을 알게 되었다.
- 예외: 없음

## KB-002
- 상황: 특정 레이스에서 1위 드라이버의 이름과 함께 그 드라이버의 핸드폰 번호를 찾고자 할 때
- 태그: results, driverId, rank, drivers, forename, surname, JOIN_LOGIC
- 교정 내용: 처음에는 position을 사용하여 1위를 찾으려 했으나, rank를 사용해야 한다는 것을 알게 되었다. 또한, SELECT에 forename과 surname을 추가해야 한다.
- 예외: 없음

## KB-003
- 상황: 특정 레이스에서 2위 드라이버의 완주 시간을 찾고자 할 때
- 태그: results, time, rank, races, name, year, JOIN_LOGIC
- 교정 내용: 처음에는 position을 사용하여 2위를 찾으려 했으나, rank를 사용해야 한다는 것을 알게 되었다. 또한, SELECT할 time은 results.time이어야 한다.
- 예외: 없음

## KB-004
- 상황: 오스트리아에서 개최된 서킷의 위치와 좌표를 찾고자 할 때
- 태그: circuits, location, lat, lng, DISTINCT
- 교정 내용: 처음에는 DISTINCT를 사용하지 않아 중복된 결과가 나올 수 있었으나, DISTINCT를 추가하여 중복을 제거해야 한다는 것을 알게 되었다.
- 예외: 없음

## KB-005
- 상황: 2008년 호주 그랑프리에서 챔피언과 마지막으로 결승을 마친 드라이버의 시간 차이를 백분율로 계산하고자 할 때
- 태그: results, time, positionOrder, races, year, JOIN_LOGIC, DATE_LOGIC, AGGREGATION_LOGIC
- 교정 내용: 처음에는 last_driver.time을 챔피언과 같은 방식으로 파싱하려 했으나, 격차시간을 올바르게 계산하기 위해 last_driver.time을 부호를 제외한 전체 숫자로 변환해야 한다는 것을 알게 되었다. 또한, 최종 퍼센트 값 하나만 반환해야 하며, 공식은 (격차시간 / (챔피언시간 + 격차시간)) * 100으로 수정해야 했다.
- 예외: 없음

## KB-006
- 상황: 상위 3명의 젊은 드라이버 중 네덜란드 국적의 드라이버 수를 세고자 할 때
- 태그: drivers, dob, nationality, COUNT, AGGREGATION_LOGIC
- 교정 내용: 처음에는 code를 포함하여 SELECT하려 했으나, nationality가 'Dutch'인 드라이버 수만 COUNT하여 반환해야 한다는 것을 알게 되었다.
- 예외: 없음

## KB-007
- 상황: 포인트가 가장 많은 드라이버의 이름과 포인트를 찾고자 할 때
- 태그: driverStandings, drivers, forename, surname, points, JOIN_LOGIC, AGGREGATION_LOGIC
- 교정 내용: 처음에는 results 테이블을 사용하여 SUM으로 포인트를 합산하려 했으나, driverStandings 테이블을 사용하고 points 값을 그대로 내림차순 정렬하여 1등만 뽑아야 한다는 것을 알게 되었다.
- 예외: 없음

## KB-008
- 상황: 특정 레이스에서 0 포인트를 기록한 팀의 이름을 찾고자 할 때
- 태그: constructorStandings, constructors, points, raceId, JOIN_LOGIC
- 교정 내용: 처음에는 constructorResults 테이블을 사용하려 했으나, constructorStandings 테이블을 사용하고 INNER JOIN으로 points=0이면서 raceId=291인 조건으로 수정해야 한다는 것을 알게 되었다.
- 예외: 없음

## KB-009
- 상황: 마이클 슈마허가 가장 빠른 랩을 기록한 레이스의 이름과 연도를 찾고자 할 때
- 태그: lapTimes, races, drivers, milliseconds, JOIN_LOGIC
- 교정 내용: 처음에는 results 테이블을 사용하려 했으나, lapTimes 테이블을 조인하고 milliseconds 기준으로 오름차순 정렬해야 한다는 것을 알게 되었다.
- 예외: 없음

## KB-010
- 상황: 특정 레이스에서 드라이버의 랩 타임을 찾고자 할 때
- 태그: lapTimes, time, raceId, drivers, url, JOIN_LOGIC, DISTINCT
- 교정 내용: 처음에는 time 형식을 '0:01:27'로 잘못 파싱하려 했으나, '1:27%'로 수정해야 한다는 것을 알게 되었다. 또한, url뿐만 아니라 forename, surname도 SELECT해야 하며 DISTINCT를 추가해야 한다.
- 예외: 없음

## KB-011
- 상황: 독일에서 개최된 레이스의 이름을 찾고자 할 때
- 태그: races, circuits, country, JOIN_LOGIC, DISTINCT
- 교정 내용: 처음에는 서브쿼리(IN)를 사용하려 했으나, circuits와 races를 직접 JOIN하고 DISTINCT를 사용해야 한다는 것을 알게 되었다.
- 예외: 없음

## KB-012
- 상황: 특정 드라이버의 평균 랩 타임을 찾고자 할 때
- 태그: lapTimes, milliseconds, drivers, races, year, JOIN_LOGIC
- 교정 내용: 처음에는 year 조건이 빠져 있었으나, races.year = 2009 조건을 추가해야 한다는 것을 알게 되었다.
- 예외: 없음

## KB-013
- 상황: 특정 레이스에서 드라이버의 Q3 결과를 찾고자 할 때
- 태그: qualifying, q3, raceId, drivers, JOIN_LOGIC
- 교정 내용: 처음에는 q3 형식을 '0:01:54'로 잘못 파싱하려 했으나, '1:54%'로 수정해야 한다는 것을 알게 되었다.
- 예외: 없음
