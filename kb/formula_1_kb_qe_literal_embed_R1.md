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
