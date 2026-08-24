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

## KB-013
- 상황: 가장 어린 드라이버의 첫 예선 레이스 연도, 이름, 날짜, 시간을 구하는 질문
- 태그: drivers.dob, races.year, races.name, races.date, races.time, ORDER BY, LIMIT, SUBQUERY_VS_JOIN
- 교정 내용: 처음에는 GROUP BY 방식으로 가장 어린 드라이버를 찾으려 했으나, 올바른 방법은 서브쿼리로 가장 어린 드라이버를 먼저 찾고 그 드라이버의 레이스를 정렬하여 1개만 뽑는 것이었다. SELECT에서 드라이버 이름을 합치지 않고 races.name을 사용해야 했다.
- 예외: 없음

## KB-014
- 상황: 1975년 이전 챔피언의 평균 시간을 구하는 질문
- 태그: results.positionOrder, races.year, results.time, AVG, GROUP BY, DATE_LOGIC
- 교정 내용: 처음에는 seasons 테이블을 조인하려 했으나, 올바른 방법은 races.year를 직접 사용해야 했다. position 조건을 1로 설정하는 대신 positionOrder = 1로 수정하고, 시간 형식에 맞게 문자열을 분리하여 초 단위로 변환해야 했다.
- 예외: 없음

## KB-015
- 상황: 캐나다 그랑프리에서 가장 많은 사고를 낸 드라이버의 사고 수를 구하는 질문
- 태그: results.statusId, races.name, COUNT, JOIN_LOGIC
- 교정 내용: 처음에는 raceId를 하나만 찾으려 했으나, 올바른 방법은 races 테이블을 조인하여 모든 해당 레이스를 포함해야 했다. 사고 수를 세는 COUNT 조건을 Canadian Grand Prix에서의 사고로 제한해야 했다.
- 예외: 없음

## KB-016
- 상황: 이탈리아 서킷의 랩 기록을 구하는 질문
- 태그: results.FastestLapTime, circuits.country, MIN, JOIN_LOGIC
- 교정 내용: 처음에는 lapTimes.time을 사용하려 했으나, 올바른 방법은 results.FastestLapTime을 사용하여 이탈리아 서킷 전체에서 가장 빠른 기록을 찾아야 했다.
- 예외: 없음

## KB-017
- 상황: 레이스 번호 872에서 경기를 마친 드라이버 중 가장 어린 드라이버를 구하는 질문
- 태그: drivers.dob, results.raceId, ORDER BY, LIMIT
- 교정 내용: 처음에는 dob 컬럼을 SELECT에 포함시키려 했으나, 올바른 방법은 forename과 surname만 반환해야 했다.
- 예외: 없음

## KB-018
- 상황: 2008년 캐나다 그랑프리 챔피언의 완주 시간을 구하는 질문
- 태그: results.time, races.year, races.name, LIKE
- 교정 내용: 처음에는 드라이버 이름을 SELECT하려 했으나, 올바른 방법은 time 컬럼만 SELECT하고, position 조건 대신 time 형식으로 챔피언을 판단해야 했다.
- 예외: 없음

## KB-019
- 상황: 영국 국적의 최대 포인트를 구하는 질문
- 태그: constructors.nationality, constructorStandings.points, MAX, JOIN_LOGIC
- 교정 내용: 처음에는 constructorResults 테이블을 조인하려 했으나, 올바른 방법은 constructorStandings 테이블을 조인해야 했다.
- 예외: 없음

## KB-020
- 상황: 유럽 그랑프리에서 독일에서 개최된 비율을 구하는 질문
- 태그: races.name, circuits.country, COUNT, JOIN_LOGIC, CAST
- 교정 내용: 처음에는 races 테이블에서 country 컬럼을 찾으려 했으나, 올바른 방법은 circuits 테이블을 조인하여 country를 가져와야 했다. COUNT를 REAL로 캐스팅해야 했다.
- 예외: 없음

## KB-021
- 상황: 1971년에 태어난 드라이버 중 가장 빠른 랩 타임을 기록한 드라이버를 구하는 질문
- 태그: drivers.dob, results.fastestLapTime, JOIN_LOGIC
- 교정 내용: 처음에는 서브쿼리를 사용하려 했으나, 올바른 방법은 drivers와 results를 직접 JOIN해야 했다.
- 예외: 없음

## KB-022
- 상황: 알렉스 유옹이 20위 이하로 주행한 레이스를 구하는 질문
- 태그: drivers.forename, drivers.surname, driverStandings.position, JOIN_LOGIC
- 교정 내용: 처음에는 results 테이블을 사용하려 했으나, 올바른 방법은 driverStandings 테이블을 조인해야 했다. SELECT에서 레이스 이름만 반환해야 했다.
- 예외: 없음

## KB-023
- 상황: 레이스 번호 45에서 Q3 시간이 0:01:33인 드라이버의 약어 코드를 구하는 질문
- 태그: qualifying.q3, drivers.code, LIKE, JOIN_LOGIC
- 교정 내용: 처음에는 q3 형식이 다르게 설정되어 있었으나, 올바른 방법은 q3가 '1:33%' 형식으로 저장되어 있다는 것을 반영해야 했다.
- 예외: 없음

## KB-024
- 상황: 미국 국적의 드라이버 코드를 구하는 질문
- 태그: drivers.nationality, drivers.code
- 교정 내용: 처음에는 driverRef를 SELECT하려 했으나, 올바른 방법은 code 컬럼을 SELECT해야 했다.
- 예외: 없음

## KB-025
- 상황: 2007년 캐나다 그랑프리에서 1위를 기록한 드라이버의 이름을 구하는 질문
- 태그: results.rank, races.year, races.name, JOIN_LOGIC
- 교정 내용: 처음에는 position 조건을 사용하려 했으나, 올바른 방법은 rank = 1로 판단해야 했다. SELECT에서 드라이버 이름을 포함해야 했다.
- 예외: 없음

## KB-026
- 상황: 2008년 중국 그랑프리에서 2위를 기록한 드라이버의 완주 시간을 구하는 질문
- 태그: results.rank, races.year, races.name, JOIN_LOGIC
- 교정 내용: 처음에는 position 조건을 사용하려 했으나, 올바른 방법은 rank = 2로 판단해야 했다. SELECT할 time은 results.time이어야 했다.
- 예외: 없음

## KB-027
- 상황: 오스트리아에서 개최된 서킷의 위치와 좌표를 구하는 질문
- 태그: circuits.country, circuits.location, circuits.lat, circuits.lng, DISTINCT
- 교정 내용: 처음에는 DISTINCT를 사용하지 않았으나, 올바른 방법은 DISTINCT를 추가해야 했다.
- 예외: 없음

## KB-028
- 상황: 2008년 호주 그랑프리에서 챔피언과 마지막으로 경기를 마친 드라이버의 속도 차이를 퍼센트로 구하는 질문
- 태그: results.time, races.year, races.name, SUBSTR, CAST, DATE_LOGIC
- 교정 내용: 처음에는 마지막 드라이버의 시간을 챔피언과 같은 방식으로 파싱하려 했으나, 올바른 방법은 마지막 드라이버의 시간에서 부호를 제외하고 전체를 초 단위로 변환해야 했다. 공식은 (격차시간 / (챔피언시간 + 격차시간)) * 100으로 수정했다.
- 예외: 없음

## KB-029
- 상황: 상위 3명의 가장 어린 드라이버 중 네덜란드 드라이버 수를 구하는 질문
- 태그: drivers.dob, drivers.nationality, COUNT, ORDER BY, LIMIT
- 교정 내용: 처음에는 드라이버의 코드를 반환하려 했으나, 올바른 방법은 nationality가 'Dutch'인 드라이버 수를 COUNT하여 반환해야 했다.
- 예외: 없음

## KB-030
- 상황: 가장 많은 포인트를 기록한 드라이버의 이름과 포인트를 구하는 질문
- 태그: driverStandings.points, drivers.forename, drivers.surname, ORDER BY, LIMIT
- 교정 내용: 처음에는 results 테이블을 사용하여 포인트를 SUM하려 했으나, 올바른 방법은 driverStandings 테이블을 사용하여 포인트를 직접 반환하고 내림차순 정렬하여 1명만 뽑아야 했다.
- 예외: 없음

## KB-031
- 상황: 291번 레이스에서 포인트가 0인 팀의 이름을 구하는 질문
- 태그: constructorStandings.points, constructors.name, JOIN_LOGIC
- 교정 내용: 처음에는 constructorResults 테이블을 사용하려 했으나, 올바른 방법은 constructorStandings 테이블을 사용하여 포인트가 0인 팀을 찾고 INNER JOIN으로 연결해야 했다.
- 예외: 없음

## KB-032
- 상황: 미하엘 슈마허의 가장 빠른 랩이 기록된 레이스의 이름과 연도를 구하는 질문
- 태그: lapTimes.milliseconds, races.name, races.year, JOIN_LOGIC, ORDER BY
- 교정 내용: 처음에는 results 테이블을 사용하려 했으나, 올바른 방법은 lapTimes 테이블을 사용하여 milliseconds 기준으로 오름차순 정렬해야 했다.
- 예외: 없음

## KB-033
- 상황: 폴 디 레스타가 853번 레이스에서 기록한 속도와 854번 레이스에서의 속도 차이를 퍼센트로 구하는 질문
- 태그: results.fastestLapSpeed, drivers.forename, drivers.surname, JOIN_LOGIC
- 교정 내용: 처음에는 드라이버 조건이 빠져 있었고, 단순히 빼기만 하지 말고 공식에 따라 계산해야 했다. 올바른 방법은 (853 값 - 854 값) / 853 값 * 100으로 수정했다.
- 예외: 없음

## KB-034
- 상황: 161번 레이스에서 0:01:27의 랩 타임을 기록한 드라이버의 웹사이트를 구하는 질문
- 태그: lapTimes.time, drivers.forename, drivers.surname, JOIN_LOGIC, DISTINCT
- 교정 내용: 처음에는 time 형식이 잘못되어 있었고, LIKE 조건을 수정해야 했다. 또한, 드라이버의 이름과 웹사이트를 함께 반환해야 했다.
- 예외: 없음

## KB-035
- 상황: 독일에서 개최된 레이스의 이름을 구하는 질문
- 태그: circuits.country, races.name, JOIN_LOGIC, DISTINCT
- 교정 내용: 처음에는 서브쿼리를 사용하려 했으나, 올바른 방법은 circuits와 races를 직접 JOIN하고 DISTINCT를 사용해야 했다.
- 예외: 없음

## KB-036
- 상황: 루이스 해밀턴의 2009년 말레이시아 그랑프리에서의 평균 랩 타임을 구하는 질문
- 태그: lapTimes.milliseconds, drivers.forename, drivers.surname, races.year, races.name, AVG, JOIN_LOGIC
- 교정 내용: 처음에는 year 조건이 빠져 있었으나, 올바른 방법은 races.year = 2009 조건을 추가해야 했다.
- 예외: 없음

## KB-037
- 상황: 903번 예선에서 0:01:54의 랩 타임을 기록한 드라이버의 번호를 구하는 질문
- 태그: qualifying.q3, drivers.number, JOIN_LOGIC
- 교정 내용: 처음에는 q3 형식이 잘못되어 있었고, LIKE 조건을 수정해야 했다.
- 예외: 없음
