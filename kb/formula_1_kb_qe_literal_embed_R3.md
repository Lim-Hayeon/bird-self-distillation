## KB-001
- 상황: "질문: Name the driver with the most winning. Mention his nationality and what is his maximum point scores." 처음에 MAX와 COUNT를 잘못 사용했다.
- 태그: drivers, forename, surname, nationality, driverStandings, points, wins, AGGREGATION_LOGIC
- 교정 내용: 오답: SELECT d.forename || ' ' || d.surname AS driver_name, d.nationality, MAX(ds.points) AS max_points FROM drivers d JOIN driverStandings ds ON d.driverId = ds.driverId GROUP BY d.driverId HAVING MAX(ds.wins) = (SELECT MAX(wins) FROM driverStandings) / 정답: SELECT T1.forename, T1.surname, T1.nationality, MAX(T2.points) FROM drivers AS T1 INNER JOIN driverStandings AS T2 ON T2.driverId = T1.driverId WHERE T2.wins >= 1 GROUP BY T1.forename, T1.surname, T1.nationality ORDER BY COUNT(T2.wins) DESC LIMIT 1

## KB-002
- 상황: "질문: What is the best lap time recorded? List the driver and race with such recorded lap time." 처음에 MIN을 서브쿼리로 잘못 사용했다.
- 태그: lapTimes, milliseconds, drivers, forename, surname, races, name, AGGREGATION_LOGIC, SUBQUERY_VS_JOIN
- 교정 내용: 오답: SELECT d.forename, d.surname, r.name FROM lapTimes lt JOIN drivers d ON lt.driverId = d.driverId JOIN races r ON lt.raceId = r.raceId WHERE lt.milliseconds = (SELECT MIN(milliseconds) FROM lapTimes) / 정답: SELECT T2.milliseconds, T1.forename, T1.surname, T3.name FROM drivers AS T1 INNER JOIN lapTimes AS T2 ON T1.driverId = T2.driverId INNER JOIN races AS T3 ON T2.raceId = T3.raceId ORDER BY T2.milliseconds ASC LIMIT 1

## KB-003
- 상황: "질문: How many French drivers who obtain the laptime less than 02:00.00?" 처음에 milliseconds 컬럼을 잘못 사용했다.
- 태그: drivers, nationality, lapTimes, time, AGGREGATION_LOGIC, VALUE_ENCODING
- 교정 내용: 오답: SELECT COUNT(DISTINCT d.driverId) FROM drivers d JOIN lapTimes lt ON d.driverId = lt.driverId WHERE d.nationality = 'French' AND lt.milliseconds < 120000 / 정답: SELECT COUNT(T1.driverId) FROM drivers AS T1 INNER JOIN lapTimes AS T2 on T1.driverId = T2.driverId WHERE T1.nationality = 'French' AND (CAST(SUBSTR(T2.time, 1, 2) AS INTEGER) * 60 + CAST(SUBSTR(T2.time, 4, 2) AS INTEGER) + CAST(SUBSTR(T2.time, 7, 2) AS REAL) / 1000) < 120

## KB-004
- 상황: "질문: Which country is the oldest driver from?" 처음에 NULL 조건을 빼먹었다.
- 태그: drivers, dob, nationality, COLUMN_ORDER, VALUE_ENCODING
- 교정 내용: 오답: SELECT nationality FROM drivers ORDER BY dob ASC LIMIT 1 / 정답: SELECT nationality FROM drivers WHERE dob IS NOT NULL ORDER BY dob ASC LIMIT 1

## KB-005
- 상황: "질문: As of the present, what is the full name of the youngest racer? Indicate her nationality and the name of the race to which he/she first joined." 처음에 MAX를 서브쿼리로 잘못 사용했다.
- 태그: drivers, forename, surname, nationality, races, name, dob, AGGREGATION_LOGIC, SUBQUERY_VS_JOIN
- 교정 내용: 오답: SELECT d.forename || ' ' || d.surname AS full_name, d.nationality, r.name AS first_race FROM drivers d JOIN results res ON d.driverId = res.driverId JOIN races r ON res.raceId = r.raceId WHERE d.dob = (SELECT MAX(dob) FROM drivers) LIMIT 1 / 정답: SELECT T1.forename, T1.surname, T1.nationality, T3.name FROM drivers AS T1 INNER JOIN driverStandings AS T2 on T1.driverId = T2.driverId INNER JOIN races AS T3 on T2.raceId = T3.raceId ORDER BY JULIANDAY(T1.dob) DESC LIMIT 1

## KB-006
- 상황: "질문: In which Formula_1 race did Lewis Hamilton rank the highest?" 처음에 ORDER BY를 잘못 사용했다.
- 태그: results, drivers, races, rank, AGGREGATION_LOGIC, JOIN_LOGIC
- 교정 내용: 오답: SELECT r.name, r.date, r.year, r.round FROM results res JOIN drivers d ON res.driverId = d.driverId JOIN races r ON res.raceId = r.raceId WHERE d.forename = 'Lewis' AND d.surname = 'Hamilton' ORDER BY res.rank ASC LIMIT 1 / 정답: SELECT name FROM races WHERE raceId IN ( SELECT raceId FROM results WHERE rank = 1 AND driverId = ( SELECT driverId FROM drivers WHERE forename = 'Lewis' AND surname = 'Hamilton' ) )

## KB-007
- 상황: "질문: Which top 20 driver created the shortest lap time ever record in a Formula_1 race? Please give them full names." 처음에 time을 잘못 비교했다.
- 태그: lapTimes, time, drivers, forename, surname, AGGREGATION_LOGIC, VALUE_ENCODING
- 교정 내용: 오답: SELECT d.forename || ' ' || d.surname AS full_name FROM lapTimes lt JOIN drivers d ON lt.driverId = d.driverId WHERE lt.time = (SELECT MIN(time) FROM lapTimes) LIMIT 20 / 정답: WITH lap_times_in_seconds AS (SELECT driverId, (CASE WHEN SUBSTR(time, 1, INSTR(time, ':') - 1) <> '' THEN CAST(SUBSTR(time, 1, INSTR(time, ':') - 1) AS REAL) * 60 ELSE 0 END + CASE WHEN SUBSTR(time, INSTR(time, ':') + 1, INSTR(time, '.') - INSTR(time, ':') - 1) <> '' THEN CAST(SUBSTR(time, INSTR(time, ':') + 1, INSTR(time, '.') - INSTR(time, ':') - 1) AS REAL) ELSE 0 END + CASE WHEN SUBSTR(time, INSTR(time, '.') + 1) <> '' THEN CAST(SUBSTR(time, INSTR(time, '.') + 1) AS REAL) / 1000 ELSE 0 END) AS time_in_seconds FROM lapTimes) SELECT T2.forename, T2.surname, T1.driverId FROM (SELECT driverId, MIN(time_in_seconds) AS min_time_in_seconds FROM lap_times_in_seconds GROUP BY driverId) AS T1 INNER JOIN drivers AS T2 ON T1.driverId = T2.driverId ORDER BY T1.min_time_in_seconds ASC LIMIT 20

## KB-008
- 상황: "질문: What is the fastest lap number of the champion in 2009?" 처음에 챔피언 조건을 잘못 사용했다.
- 태그: results, fastestLap, races, year, AGGREGATION_LOGIC, VALUE_ENCODING
- 교정 내용: 오답: SELECT fastestLap FROM results WHERE raceId IN (SELECT raceId FROM races WHERE year = 2009) AND driverId = (SELECT driverId FROM driverStandings WHERE raceId IN (SELECT raceId FROM races WHERE year = 2009) ORDER BY points DESC LIMIT 1) / 정답: SELECT T1.fastestLap FROM results AS T1 INNER JOIN races AS T2 on T1.raceId = T2.raceId WHERE T2.year = 2009 AND T1.time LIKE '_:%:__.___'

## KB-009
- 상황: "질문: Calculate the percentage whereby Hamilton was not at the 1st track of the the f1 circuit since 2010." 처음에 position 조건을 잘못 사용했다.
- 태그: driverStandings, results, drivers, races, AGGREGATION_LOGIC, VALUE_ENCODING
- 교정 내용: 오답: SELECT (COUNT(CASE WHEN position > 1 THEN 1 END) * 100.0 / COUNT(*)) AS percentage FROM results JOIN drivers ON results.driverId = drivers.driverId JOIN races ON results.raceId = races.raceId WHERE drivers.surname = 'Hamilton' AND races.year >= 2010 / 정답: SELECT CAST(COUNT(CASE WHEN T2.position <> 1 THEN T2.position END) AS REAL) * 100 / COUNT(T2.driverStandingsId) FROM races AS T1 INNER JOIN driverStandings AS T2 ON T2.raceId = T1.raceId INNER JOIN drivers AS T3 ON T3.driverId = T2.driverId WHERE T3.surname = 'Hamilton' AND T1.year >= 2010

## KB-010
- 상황: "질문: What is full name of the racer who ranked 1st in the 3rd qualifying race held in the Marina Bay Street Circuit in 2008?" 처음에 position과 number 조건을 잘못 사용했다.
- 태그: qualifying, races, drivers, forename, surname, AGGREGATION_LOGIC, VALUE_ENCODING
- 교정 내용: 오답: SELECT d.forename || ' ' || d.surname AS full_name FROM qualifying q JOIN races r ON q.raceId = r.raceId JOIN drivers d ON q.driverId = d.driverId JOIN circuits c ON r.circuitId = c.circuitId WHERE r.year = 2008 AND c.name = 'Marina Bay Street Circuit' AND q.position = 1 AND q.number = 3 / 정답: SELECT T2.forename, T2.surname FROM qualifying AS T1 INNER JOIN drivers AS T2 on T1.driverId = T2.driverId INNER JOIN races AS T3 ON T1.raceid = T3.raceid WHERE q3 IS NOT NULL AND T3.year = 2008 AND T3.circuitId IN ( SELECT circuitId FROM circuits WHERE name = 'Marina Bay Street Circuit' ) ORDER BY CAST(SUBSTR(q3, 1, INSTR(q3, ':') - 1) AS INTEGER) * 60 + CAST(SUBSTR(q3, INSTR(q3, ':') + 1, INSTR(q3, '.') - INSTR(q3, ':') - 1) AS REAL) + CAST(SUBSTR(q3, INSTR(q3, '.') + 1) AS REAL) / 1000 ASC LIMIT 1

## KB-011
- 상황: "질문: How old is the youngest Japanese driver? What is his name?" 처음에 컬럼 순서를 잘못 사용했다.
- 태그: drivers, dob, nationality, AGGREGATION_LOGIC, VALUE_ENCODING
- 교정 내용: 오답: SELECT forename, surname, (strftime('%Y', 'now') - strftime('%Y', dob)) AS age FROM drivers WHERE nationality = 'Japanese' ORDER BY dob DESC LIMIT 1 / 정답: SELECT STRFTIME('%Y', CURRENT_TIMESTAMP) - STRFTIME('%Y', dob), forename , surname FROM drivers WHERE nationality = 'Japanese' ORDER BY dob DESC LIMIT 1

## KB-012
- 상황: "질문: What was the fastest lap speed among all drivers in the 2009 Spanish Grand Prix?" 처음에 year 조건을 빼먹었다.
- 태그: results, fastestLapSpeed, races, AGGREGATION_LOGIC, VALUE_ENCODING
- 교정 내용: 오답: SELECT MAX(fastestLapSpeed) FROM results JOIN races ON results.raceId = races.raceId WHERE races.name = 'Spanish Grand Prix' AND fastestLapSpeed IS NOT NULL / 정답: SELECT T2.fastestLapSpeed FROM races AS T1 INNER JOIN results AS T2 ON T2.raceId = T1.raceId WHERE T1.name = 'Spanish Grand Prix' AND T1.year = 2009 AND T2.fastestLapSpeed IS NOT NULL ORDER BY T2.fastestLapSpeed DESC LIMIT 1

## KB-013
- 상황: "질문: On what year did the youngest driver had his first qualifying race? Also state the name, date and time of the race." 처음에 드라이버 이름을 잘못 사용했다.
- 태그: races, name, date, time, drivers, dob, JOIN_LOGIC
- 교정 내용: 오답: SELECT races.year, drivers.forename || ' ' || drivers.surname AS name, races.date, races.time FROM races JOIN qualifying ON races.raceId = qualifying.raceId JOIN drivers ON qualifying.driverId = drivers.driverId WHERE drivers.driverId = (SELECT driverId FROM drivers WHERE dob IS NOT NULL ORDER BY dob DESC LIMIT 1) ORDER BY races.date ASC LIMIT 1 / 정답: SELECT T3.year, T3.name, T3.date, T3.time FROM qualifying AS T1 INNER JOIN drivers AS T2 on T1.driverId = T2.driverId INNER JOIN races AS T3 on T1.raceId = T3.raceId WHERE T1.driverId = ( SELECT driverId FROM drivers ORDER BY dob DESC LIMIT 1 ) ORDER BY T3.date ASC LIMIT 1

## KB-014
- 상황: "질문: What is the average time in seconds of champion for each year, before year 1975?" 처음에 year 조건을 잘못 사용했다.
- 태그: results, time, year, AGGREGATION_LOGIC, VALUE_ENCODING
- 교정 내용: 오답: SELECT s.year, AVG(strftime('%s', r.time)) AS average_time_seconds FROM results r JOIN races ra ON r.raceId = ra.raceId JOIN seasons s ON ra.year = s.year WHERE r.position = 1 AND r.time IS NOT NULL AND s.year < 1975 GROUP BY s.year / 정답: WITH time_in_seconds AS ( SELECT T2.year, T2.raceId, T1.positionOrder, CASE WHEN T1.positionOrder = 1 THEN (CAST(SUBSTR(T1.time, 1, 1) AS REAL) * 3600) + (CAST(SUBSTR(T1.time, 3, 2) AS REAL) * 60) + CAST(SUBSTR(T1.time, 6,2) AS REAL ) + CAST(SUBSTR(T1.time, 9) AS REAL)/1000 ELSE 0 END AS time_seconds FROM results AS T1 INNER JOIN races AS T2 ON T1.raceId = T2.raceId WHERE T1.time IS NOT NULL ), champion_time AS ( SELECT year, raceId, time_seconds FROM time_in_seconds WHERE positionOrder = 1 ) SELECT year, AVG(time_seconds) FROM champion_time WHERE year < 1975 GROUP BY year HAVING AVG(time_seconds) IS NOT NULL

## KB-015
- 상황: "질문: How many accidents did the driver who had the highest number accidents in the Canadian Grand Prix have?" 처음에 raceId를 잘못 사용했다.
- 태그: results, accidents, races, statusId, AGGREGATION_LOGIC, JOIN_LOGIC
- 교정 내용: 오답: SELECT COUNT(*) AS accident_count FROM results WHERE driverId = ( SELECT driverId FROM results WHERE raceId = ( SELECT raceId FROM races WHERE name = 'Canadian Grand Prix' ) AND statusId = 3 GROUP BY driverId ORDER BY COUNT(*) DESC LIMIT 1 ) AND statusId = 3 / 정답: SELECT COUNT(T1.driverId) FROM results AS T1 INNER JOIN races AS T2 on T1.raceId = T2.raceId INNER JOIN status AS T3 on T1.statusId = T3.statusId WHERE T3.statusId = 3 AND T2.name = 'Canadian Grand Prix' GROUP BY T1.driverId ORDER BY COUNT(T1.driverId) DESC LIMIT 1

## KB-016
- 상황: "질문: Please list the lap records for the circuits in Italy." 처음에 lapTimes.time을 잘못 사용했다.
- 태그: results, fastestLapTime, circuits, AGGREGATION_LOGIC, VALUE_ENCODING
- 교정 내용: 오답: SELECT r.circuitId, MIN(l.time) AS lapRecord FROM lapTimes l JOIN races r ON l.raceId = r.raceId JOIN circuits c ON r.circuitId = c.circuitId WHERE c.country = 'Italy' GROUP BY r.circuitId / 정답: WITH fastest_lap_times AS (SELECT T1.raceId, T1.FastestLapTime, (CAST(SUBSTR(T1.FastestLapTime, 1, INSTR(T1.FastestLapTime, ':') - 1) AS REAL) * 60) + (CAST(SUBSTR(T1.FastestLapTime, INSTR(T1.FastestLapTime, ':') + 1, INSTR(T1.FastestLapTime, '.') - INSTR(T1.FastestLapTime, ':') - 1) AS REAL)) + (CAST(SUBSTR(T1.FastestLapTime, INSTR(T1.FastestLapTime, '.') + 1) AS REAL) / 1000) as time_in_seconds FROM results AS T1 WHERE T1.FastestLapTime IS NOT NULL ) SELECT T1.FastestLapTime as lap_record FROM results AS T1 INNER JOIN races AS T2 on T1.raceId = T2.raceId INNER JOIN circuits AS T3 on T2.circuitId = T3.circuitId INNER JOIN (SELECT MIN(fastest_lap_times.time_in_seconds) as min_time_in_seconds FROM fastest_lap_times INNER JOIN races AS T2 on fastest_lap_times.raceId = T2.raceId INNER JOIN circuits AS T3 on T2.circuitId = T3.circuitId WHERE T3.country = 'Italy' ) AS T4 ON (CAST(SUBSTR(T1.FastestLapTime, 1, INSTR(T1.FastestLapTime, ':') - 1) AS REAL) * 60) + (CAST(SUBSTR(T1.FastestLapTime, INSTR(T1.FastestLapTime, ':') + 1, INSTR(T1.FastestLapTime, '.') - INSTR(T1.FastestLapTime, ':') - 1) AS REAL)) + (CAST(SUBSTR(T1.FastestLapTime, INSTR(T1.FastestLapTime, '.') + 1) AS REAL) / 1000) = T4.min_time_in_seconds LIMIT 1

## KB-017
- 상황: "질문: For all the drivers who finished the game in race No. 872, who is the youngest?" 처음에 SELECT에서 dob를 잘못 사용했다.
- 태그: drivers, results, dob, AGGREGATION_LOGIC, VALUE_ENCODING
- 교정 내용: 오답: SELECT forename, surname, dob FROM drivers JOIN results ON drivers.driverId = results.driverId WHERE results.raceId = 872 AND results.time IS NOT NULL ORDER BY dob DESC LIMIT 1 / 정답: SELECT T1.forename, T1.surname FROM drivers AS T1 INNER JOIN results AS T2 ON T2.driverId = T1.driverId WHERE T2.raceId = 872 AND T2.time IS NOT NULL ORDER BY T1.dob DESC LIMIT 1

## KB-018
- 상황: "질문: Who is the champion of the Canadian Grand Prix in 2008? Indicate his finish time." 처음에 position 조건을 잘못 사용했다.
- 태그: results, races, time, AGGREGATION_LOGIC, VALUE_ENCODING
- 교정 내용: 오답: SELECT d.forename, d.surname, r.time FROM results r JOIN races ra ON r.raceId = ra.raceId JOIN drivers d ON r.driverId = d.driverId WHERE ra.year = 2008 AND ra.name = 'Canadian Grand Prix' AND r.position = 1 / 정답: SELECT T1.time FROM results AS T1 INNER JOIN races AS T2 ON T1.raceId = T2.raceId WHERE T2.name = 'Canadian Grand Prix' AND T2.year = 2008 AND T1.time LIKE '_:%:__.___'

## KB-019
- 상황: "질문: What are the maximum points of British constructors?" 처음에 constructorResults 테이블을 잘못 사용했다.
- 태그: constructors, constructorStandings, points, AGGREGATION_LOGIC, VALUE_ENCODING
- 교정 내용: 오답: SELECT MAX(points) AS max_points FROM constructors JOIN constructorResults ON constructors.constructorId = constructorResults.constructorId WHERE constructors.nationality = 'British' / 정답: SELECT MAX(T1.points) FROM constructorStandings AS T1 INNER JOIN constructors AS T2 on T1.constructorId = T2.constructorId WHERE T2.nationality = 'British'

## KB-020
- 상황: "질문: Among all European Grand Prix races, what is the percentage of the races were hosted in Germany?" 처음에 country 조건을 잘못 사용했다.
- 태그: races, circuits, AGGREGATION_LOGIC, VALUE_ENCODING
- 교정 내용: 오답: SELECT (COUNT(CASE WHEN country = 'Germany' THEN 1 END) * 100.0 / COUNT(*)) AS percentage FROM races WHERE name = 'European Grand Prix' / 정답: SELECT CAST(COUNT(CASE WHEN T1.country = 'Germany' THEN T2.circuitID END) AS REAL) * 100 / COUNT(T2.circuitId) FROM circuits AS T1 INNER JOIN races AS T2 ON T2.circuitID = T1.circuitId WHERE T2.name = 'European Grand Prix'

## KB-021
- 상황: "질문: Which drivers who were born in 1971 and has the fastest lap time on the race? Give id and code of these drivers." 처음에 서브쿼리를 잘못 사용했다.
- 태그: drivers, results, dob, fastestLapTime, AGGREGATION_LOGIC, JOIN_LOGIC
- 교정 내용: 오답: SELECT driverId, code FROM drivers WHERE strftime('%Y', dob) = '1971' AND driverId IN (SELECT driverId FROM results WHERE fastestLapTime IS NOT NULL) / 정답: SELECT T2.driverId, T2.code FROM results AS T1 INNER JOIN drivers AS T2 on T1.driverId = T2.driverId WHERE STRFTIME('%Y', T2.dob) = '1971' AND T1.fastestLapTime IS NOT NULL

## KB-022
- 상황: "질문: Which race was Alex Yoong in when he was in track number less than 20?" 처음에 results 테이블을 잘못 사용했다.
- 태그: driverStandings, races, drivers, AGGREGATION_LOGIC, VALUE_ENCODING
- 교정 내용: 오답: SELECT r.name, r.date FROM results res JOIN races r ON res.raceId = r.raceId JOIN drivers d ON res.driverId = d.driverId WHERE d.forename = 'Alex' AND d.surname = 'Yoong' AND res.position < 20 / 정답: SELECT T1.name FROM races AS T1 INNER JOIN driverStandings AS T2 ON T2.raceId = T1.raceId INNER JOIN drivers AS T3 ON T3.driverId = T2.driverId WHERE T3.forename = 'Alex' AND T3.surname = 'Yoong' AND T2.position < 20

## KB-023
- 상황: "질문: In the race No. 45, for the driver who had the Q3 time as 0:01:33, what is his abbreviated code?" 처음에 q3 조건을 잘못 사용했다.
- 태그: qualifying, drivers, AGGREGATION_LOGIC, VALUE_ENCODING
- 교정 내용: 오답: SELECT d.code FROM drivers d JOIN qualifying q ON d.driverId = q.driverId WHERE q.raceId = 45 AND q.q3 LIKE '0:01:33%' / 정답: SELECT T2.code FROM qualifying AS T1 INNER JOIN drivers AS T2 ON T2.driverId = T1.driverId WHERE T1.raceId = 45 AND T1.q3 LIKE '1:33%'

## KB-024
- 상황: "질문: List out the code for drivers who have nationality in American." 처음에 driverRef를 잘못 사용했다.
- 태그: drivers, nationality, AGGREGATION_LOGIC, VALUE_ENCODING
- 교정 내용: 오답: SELECT driverRef FROM drivers WHERE nationality = 'American' / 정답: SELECT code FROM drivers WHERE nationality = 'American'

## KB-025
- 상황: "질문: Which driver ranked the first in the Canadian Grand Prix in 2007? Please give his reference name." 처음에 year 조건을 잘못 사용했다.
- 태그: results, drivers, races, AGGREGATION_LOGIC, VALUE_ENCODING
- 교정 내용: 오답: SELECT d.driverRef FROM results r JOIN drivers d ON r.driverId = d.driverId JOIN races ra ON r.raceId = ra.raceId WHERE ra.name = 'Canadian Grand Prix' AND r.position = 1 AND r.year = 2007 / 정답: SELECT T3.forename, T3.surname, T3.driverRef FROM races AS T1 INNER JOIN results AS T2 ON T2.raceId = T1.raceId INNER JOIN drivers AS T3 ON T3.driverId = T2.driverId WHERE T1.name = 'Canadian Grand Prix' AND T2.rank = 1 AND T1.year = 2007

## KB-026
- 상황: "질문: What's the finish time for the driver who ranked second in 2008's AustChineseralian Grand Prix?" 처음에 position 조건을 잘못 사용했다.
- 태그: results, races, AGGREGATION_LOGIC, VALUE_ENCODING
- 교정 내용: 오답: SELECT r.time FROM results res JOIN races r ON res.raceId = r.raceId WHERE r.name = 'Chinese Grand Prix' AND r.year = 2008 AND res.position = 2 / 정답: SELECT T1.time FROM results AS T1 INNER JOIN races AS T2 on T1.raceId = T2.raceId WHERE T1.rank = 2 AND T2.name = 'Chinese Grand Prix' AND T2.year = 2008

## KB-027
- 상황: "질문: How many times the circuits were held in Austria? Please give their location and coordinates." 처음에 DISTINCT를 빼먹었다.
- 태그: circuits, location, lat, lng, AGGREGATION_LOGIC, VALUE_ENCODING
- 교정 내용: 오답: SELECT location, lat, lng FROM circuits WHERE country = 'Austria' / 정답: SELECT DISTINCT location, lat, lng FROM circuits WHERE country = 'Austria'

## KB-028
- 상황: "질문: How much faster in percentage is the champion than the driver who finished the race last in the 2008 Australian Grand Prix?" 처음에 last_driver.time을 챔피언과 같은 방식으로 파싱했다.
- 태그: results, time, AGGREGATION_LOGIC, VALUE_ENCODING
- 교정 내용: 오답: SELECT (CAST(SUBSTR(last_driver.time, 1, 2) AS INTEGER) * 3600 + CAST(SUBSTR(last_driver.time, 4, 2) AS INTEGER) * 60 + CAST(SUBSTR(last_driver.time, 7, 2) AS INTEGER) + CAST(SUBSTR(last_driver.time, 10, 3) AS INTEGER) / 1000) AS last_driver_time, ... / 정답: WITH time_in_seconds AS ( SELECT T1.positionOrder, CASE WHEN T1.positionOrder = 1 THEN (CAST(SUBSTR(T1.time, 1, 1) AS REAL) * 3600) + (CAST(SUBSTR(T1.time, 3, 2) AS REAL) * 60) + CAST(SUBSTR(T1.time, 6) AS REAL) ELSE CAST(SUBSTR(T1.time, 2) AS REAL) END AS time_seconds FROM results AS T1 INNER JOIN races AS T2 ON T1.raceId = T2.raceId WHERE T2.name = 'Australian Grand Prix' AND T1.time IS NOT NULL AND T2.year = 2008 ), champion_time AS ( SELECT time_seconds FROM time_in_seconds WHERE positionOrder = 1), last_driver_incremental AS ( SELECT time_seconds FROM time_in_seconds WHERE positionOrder = (SELECT MAX(positionOrder) FROM time_in_seconds) ) SELECT (CAST((SELECT time_seconds FROM last_driver_incremental) AS REAL) * 100) / (SELECT time_seconds + (SELECT time_seconds FROM last_driver_incremental) FROM champion_time)

## KB-029
- 상황: "질문: State code numbers of top 3 yougest drivers. How many Netherlandic drivers among them?" 처음에 code를 포함시켰다.
- 태그: drivers, nationality, dob, AGGREGATION_LOGIC, VALUE_ENCODING
- 교정 내용: 오답: SELECT code, COUNT(CASE WHEN nationality = 'Dutch' THEN 1 END) AS netherlandic_count FROM ( SELECT d.code, d.dob FROM drivers d WHERE d.dob IS NOT NULL ORDER BY d.dob DESC LIMIT 3) AS youngest_drivers GROUP BY code / 정답: SELECT COUNT(*) FROM ( SELECT T1.nationality FROM drivers AS T1 ORDER BY JULIANDAY(T1.dob) DESC LIMIT 3) AS T3 WHERE T3.nationality = 'Dutch'

## KB-030
- 상황: "질문: Please list the constructor names with 0 points at race 291." 처음에 constructorResults 테이블을 잘못 사용했다.
- 태그: constructors, constructorStandings, points, AGGREGATION_LOGIC, VALUE_ENCODING
- 교정 내용: 오답: SELECT c.name FROM constructors c LEFT JOIN constructorResults cr ON c.constructorId = cr.constructorId AND cr.raceId = 291 WHERE cr.points = 0 OR cr.points IS NULL / 정답: SELECT T2.name FROM constructorStandings AS T1 INNER JOIN constructors AS T2 on T1.constructorId = T2.constructorId WHERE T1.points = 0 AND T1.raceId = 291

## KB-031
- 상황: "질문: State the race and year of race in which Michael Schumacher had his fastest lap." 처음에 results 테이블을 잘못 사용했다.
- 태그: results, lapTimes, drivers, AGGREGATION_LOGIC, VALUE_ENCODING
- 교정 내용: 오답: SELECT r.name, r.year FROM results res JOIN races r ON res.raceId = r.raceId JOIN drivers d ON res.driverId = d.driverId WHERE d.forename = 'Michael' AND d.surname = 'Schumacher' ORDER BY res.fastestLapTime ASC LIMIT 1 / 정답: SELECT T1.name, T1.year FROM races AS T1 INNER JOIN lapTimes AS T2 ON T2.raceId = T1.raceId INNER JOIN drivers AS T3 ON T3.driverId = T2.driverId WHERE T3.forename = 'Michael' AND T3.surname = 'Schumacher' ORDER BY T2.milliseconds ASC LIMIT 1

## KB-032
- 상황: "질문: Paul di Resta was in the No. 853 race, what percent faster did he finish in the 853rd race than the next race for the fastest lap speed?" 처음에 driverId 조건을 빼먹었다.
- 태그: results, drivers, AGGREGATION_LOGIC, VALUE_ENCODING
- 교정 내용: 오답: SELECT ((SELECT fastestLapSpeed FROM results WHERE raceId = 853 AND driverId = (SELECT driverId FROM drivers WHERE forename = 'Paul' AND surname = 'di Resta')) - (SELECT fastestLapSpeed FROM results WHERE raceId = 854)) AS percent_faster / 정답: SELECT (SUM(IIF(T2.raceId = 853, T2.fastestLapSpeed, 0)) - SUM(IIF(T2.raceId = 854, T2.fastestLapSpeed, 0))) * 100 / SUM(IIF(T2.raceId = 853, T2.fastestLapSpeed, 0)) FROM drivers AS T1 INNER JOIN results AS T2 ON T2.driverId = T1.driverId WHERE T1.forename = 'Paul' AND T1.surname = 'di Resta'

## KB-033
- 상황: "질문: Who was the player that got the lap time of 0:01:27 in the race No. 161? Show his introduction website." 처음에 time 형식을 잘못 사용했다.
- 태그: lapTimes, drivers, AGGREGATION_LOGIC, VALUE_ENCODING
- 교정 내용: 오답: SELECT d.url FROM lapTimes lt JOIN drivers d ON lt.driverId = d.driverId WHERE lt.raceId = 161 AND lt.time LIKE '0:01:27%' / 정답: SELECT DISTINCT T2.forename, T2.surname, T2.url FROM lapTimes AS T1 INNER JOIN drivers AS T2 ON T2.driverId = T1.driverId WHERE T1.raceId = 161 AND T1.time LIKE '1:27%'

## KB-034
- 상황: "질문: Please give the name of the race held on the circuits in Germany." 처음에 서브쿼리를 잘못 사용했다.
- 태그: races, circuits, AGGREGATION_LOGIC, VALUE_ENCODING
- 교정 내용: 오답: SELECT name FROM races WHERE circuitId IN (SELECT circuitId FROM circuits WHERE country = 'Germany') / 정답: SELECT DISTINCT T2.name FROM circuits AS T1 INNER JOIN races AS T2 ON T2.circuitID = T1.circuitId WHERE T1.country = 'Germany'

## KB-035
- 상황: "질문: What is the average lap time for Lewis Hamilton in the 2009 Malaysian Grand Prix?" 처음에 year 조건을 빼먹었다.
- 태그: lapTimes, drivers, races, AGGREGATION_LOGIC, VALUE_ENCODING
- 교정 내용: 오답: SELECT AVG(lapTimes.milliseconds) AS average_lap_time FROM lapTimes JOIN races ON lapTimes.raceId = races.raceId JOIN drivers ON lapTimes.driverId = drivers.driverId WHERE drivers.forename = 'Lewis' AND drivers.surname = 'Hamilton' AND races.name = 'Malaysian Grand Prix' / 정답: SELECT AVG(T2.milliseconds) FROM races AS T1 INNER JOIN lapTimes AS T2 ON T2.raceId = T1.raceId INNER JOIN drivers AS T3 ON T3.driverId = T2.driverId WHERE T3.forename = 'Lewis' AND T3.surname = 'Hamilton' AND T1.year = 2009 AND T1.name = 'Malaysian Grand Prix'

## KB-036
- 상황: "질문: What is his number of the driver who finished 0:01:54 in the Q3 of qualifying race No.903?" 처음에 q3 형식을 잘못 사용했다.
- 태그: qualifying, drivers, AGGREGATION_LOGIC, VALUE_ENCODING
- 교정 내용: 오답: SELECT d.number FROM qualifying q JOIN drivers d ON q.driverId = d.driverId WHERE q.raceId = 903 AND q.q3 LIKE '0:01:54%' / 정답: SELECT T2.number FROM qualifying AS T1 INNER JOIN drivers AS T2 ON T2.driverId = T1.driverId WHERE T1.raceId = 903 AND T1.q3 LIKE '1:54%'
