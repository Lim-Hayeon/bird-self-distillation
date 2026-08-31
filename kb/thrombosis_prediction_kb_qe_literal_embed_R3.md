## KB-001
- 상황: "질문: List the patient ID, sex and birthday of patient with LDH beyond normal range." LDH beyond normal range를 고려하지 않고 중복된 환자 ID가 나올 수 있는 SQL을 작성했다.
- 태그: Patient, ID, Laboratory, LDH, MISSING_DISTINCT
- 교정 내용: 오답: SELECT Patient.ID, Patient.SEX, Patient.Birthday FROM Patient JOIN Laboratory ON Patient.ID = Laboratory.ID WHERE Laboratory.LDH > 500 / 정답: SELECT DISTINCT T1.ID, T1.SEX, T1.Birthday FROM Patient AS T1 INNER JOIN Laboratory AS T2 ON T1.ID = T2.ID WHERE T2.LDH > 500

## KB-002
- 상황: "질문: What is the average age of the male patient with high cholesterol?" 서브쿼리를 사용하여 중복된 환자 ID를 제거해버려 평균 계산이 잘못되었다.
- 태그: Patient, Birthday, Laboratory, T-CHO, AGGREGATION_LOGIC
- 교정 내용: 오답: SELECT AVG(strftime('%Y', 'now') - strftime('%Y', Birthday)) AS Average_Age FROM Patient WHERE SEX = 'M' AND ID IN ( SELECT ID FROM Laboratory WHERE `T-CHO` >= 250 ) / 정답: SELECT AVG(STRFTIME('%Y', date('NOW')) - STRFTIME('%Y', T1.Birthday)) FROM Patient AS T1 INNER JOIN Laboratory AS T2 ON T1.ID = T2.ID WHERE T2.`T-CHO` >= 250 AND T1.SEX = 'M'

## KB-003
- 상황: "질문: Among the patients who has a normal anti-scl70, how many of them are female and does not have any symptom?" SC170 컬럼을 잘못된 테이블에서 가져와서 SQL이 틀렸다.
- 태그: Patient, ID, Laboratory, SC170, WRONG_TABLE
- 교정 내용: 오답: SELECT COUNT(DISTINCT P.ID) FROM Patient P JOIN Examination E ON P.ID = E.ID WHERE P.SEX = 'F' AND E.Symptoms IS NULL AND E.SC170 IN ('negative', '0') / 정답: SELECT COUNT(DISTINCT T1.ID) FROM Patient AS T1 INNER JOIN Laboratory AS T2 ON T1.ID = T2.ID INNER JOIN Examination AS T3 ON T3.ID = T2.ID WHERE (T2.SC170 = 'negative' OR T2.SC170 = '0') AND T1.SEX = 'F' AND T3.Symptoms IS NULL

## KB-004
- 상황: "질문: Name the ID and age of patient with two or more laboratory examinations which show their hematoclit level exceeded the normal range." COUNT 조건을 잘못 설정하여 SQL이 틀렸다.
- 태그: Patient, ID, Laboratory, HCT, AGGREGATION_LOGIC
- 교정 내용: 오답: SELECT P.ID, (strftime('%Y', 'now') - strftime('%Y', P.Birthday)) AS age FROM Patient P JOIN Laboratory L ON P.ID = L.ID WHERE L.HCT >= 52 GROUP BY P.ID HAVING COUNT(L.ID) > 2 / 정답: SELECT DISTINCT T1.ID, STRFTIME('%Y', CURRENT_TIMESTAMP) - STRFTIME('%Y', T1.Birthday) FROM Patient AS T1 INNER JOIN Laboratory AS T2 ON T1.ID = T2.ID WHERE T1.ID IN ( SELECT ID FROM Laboratory WHERE HCT >= 52 GROUP BY ID HAVING COUNT(ID) >= 2 )

## KB-005
- 상황: "질문: Provide all ID, sex and birthday of patients whose urea nitrogen (UN) just within the borderline of passing?" DISTINCT를 사용하지 않아 중복된 환자 ID가 나올 수 있는 SQL을 작성했다.
- 태그: Patient, ID, Laboratory, UN, MISSING_DISTINCT
- 교정 내용: 오답: SELECT Patient.ID, Patient.SEX, Patient.Birthday FROM Patient JOIN Laboratory ON Patient.ID = Laboratory.ID WHERE Laboratory.UN = 29 / 정답: SELECT DISTINCT T1.ID, T1.SEX, T1.Birthday FROM Patient AS T1 INNER JOIN Laboratory AS T2 ON T1.ID = T2.ID WHERE T2.UN = 29

## KB-006
- 상황: "질문: What is the percentage of female patient were born after 1930?" 날짜 비교를 잘못하여 SQL이 틀렸다.
- 태그: Patient, Birthday, AGGREGATION_LOGIC, DATE_LOGIC
- 교정 내용: 오답: SELECT (COUNT(ID) * 100.0 / (SELECT COUNT(ID) FROM Patient WHERE SEX = 'F')) AS FemalePercentage FROM Patient WHERE Birthday > '1930-01-01' AND SEX = 'F' / 정답: SELECT CAST(SUM(CASE WHEN STRFTIME('%Y', Birthday) > '1930' THEN 1 ELSE 0 END) AS REAL) * 100 / COUNT(*) FROM Patient WHERE SEX = 'F'

## KB-007
- 상황: "질문: For patients with abnormal platelet level, state the number of patients with lower than normal range. How is it compare to the number of patients with higher than normal range?" 비교 기준을 잘못 설정하여 SQL이 틀렸다.
- 태그: Laboratory, PLT, AGGREGATION_LOGIC
- 교정 내용: 오답: SELECT SUM(CASE WHEN PLT < 100 THEN 1 ELSE 0 END) AS Lower_Than_Normal, SUM(CASE WHEN PLT > 400 THEN 1 ELSE 0 END) AS Higher_Than_Normal, (SUM(CASE WHEN PLT < 100 THEN 1 ELSE 0 END) - SUM(CASE WHEN PLT > 400 THEN 1 ELSE 0 END)) AS Difference FROM Laboratory WHERE PLT <= 100 OR PLT >= 400 / 정답: SELECT SUM(CASE WHEN T2.PLT <= 100 THEN 1 ELSE 0 END) - SUM(CASE WHEN T2.PLT >= 400 THEN 1 ELSE 0 END) FROM Patient AS T1 INNER JOIN Laboratory AS T2 ON T1.ID = T2.ID

## KB-008
- 상황: "질문: Was the patient with the number 57266's uric acid within a normal range?" 결과 형식이 잘못되어 SQL이 틀렸다.
- 태그: Patient, ID, Laboratory, UA, VALUE_ENCODING
- 교정 내용: 오답: SELECT CASE WHEN (SEX = 'M' AND UA <= 8.0) OR (SEX = 'F' AND UA <= 6.5) THEN 'No' ELSE 'Yes' END AS Is_UA_Normal FROM Patient JOIN Laboratory ON Patient.ID = Laboratory.ID WHERE Patient.ID = 57266 / 정답: SELECT CASE WHEN (T1.SEX = 'F' AND T2.UA > 6.5) OR (T1.SEX = 'M' AND T2.UA > 8.0) THEN true ELSE false END FROM Patient AS T1 INNER JOIN Laboratory AS T2 ON T1.ID = T2.ID WHERE T1.ID = 57266

## KB-009
- 상황: "질문: How many patients with a abnormal C-reactive protein don't have their data recorded?" 서브쿼리를 사용하여 SQL이 틀렸다.
- 태그: Patient, ID, Laboratory, CRP, JOIN_LOGIC
- 교정 내용: 오답: SELECT COUNT(*) FROM Patient WHERE Description IS NULL AND ID NOT IN (SELECT ID FROM Laboratory WHERE CRP = '+') / 정답: SELECT COUNT(*) FROM Patient JOIN Laboratory ON Patient.ID = Laboratory.ID WHERE Laboratory.CRP = '+' AND Patient.Description IS NULL

## KB-010
- 상황: "질문: What percentage of patients who were born in 1980 and were diagnosed with RA are women?" YEAR() 함수를 사용하여 SQL이 틀렸다.
- 태그: Patient, Birthday, Diagnosis, AGGREGATION_LOGIC
- 교정 내용: 오답: SELECT (SUM(CASE WHEN SEX = 'F' THEN 1 ELSE 0 END) * 100.0 / COUNT(*)) AS percentage FROM Patient WHERE YEAR(Birthday) = 1980 AND Diagnosis = 'RA' / 정답: SELECT CAST(SUM(CASE WHEN SEX = 'F' THEN 1 ELSE 0 END) AS REAL) * 100 / COUNT(ID) FROM Patient WHERE Diagnosis = 'RA' AND STRFTIME('%Y', Birthday) = '1980'

## KB-011
- 상황: "질문: Among the patients whose creatinine level is abnormal, how many of them aren't 70 yet?" COUNT(*)를 사용하여 SQL이 틀렸다.
- 태그: Patient, ID, Laboratory, CRE, AGGREGATION_LOGIC
- 교정 내용: 오답: SELECT COUNT(*) FROM Patient JOIN Laboratory ON Patient.ID = Laboratory.ID WHERE Laboratory.CRE >= 1.5 AND (STRFTIME('%Y', 'now') - STRFTIME('%Y', Patient.Birthday)) < 70 / 정답: SELECT COUNT(DISTINCT T1.ID) FROM Patient AS T1 INNER JOIN Laboratory AS T2 ON T1.ID = T2.ID WHERE T2.CRE >= 1.5 AND STRFTIME('%Y', Date('now')) - STRFTIME('%Y', T1.Birthday) < 70

## KB-012
- 상황: "질문: What are the patient's diagnosis for those who has lower red blood blood cell? State their ID and age." DISTINCT를 사용하지 않아 중복된 환자 ID가 나올 수 있는 SQL을 작성했다.
- 태그: Patient, ID, Laboratory, RBC, MISSING_DISTINCT
- 교정 내용: 오답: SELECT Patient.ID, (strftime('%Y', 'now') - strftime('%Y', Patient.Birthday)) AS Age, Patient.Diagnosis FROM Patient JOIN Laboratory ON Patient.ID = Laboratory.ID WHERE Laboratory.RBC < 3.5 / 정답: SELECT DISTINCT T1.Diagnosis, T1.ID , STRFTIME('%Y', CURRENT_TIMESTAMP) -STRFTIME('%Y', T1.Birthday) FROM Patient AS T1 INNER JOIN Laboratory AS T2 ON T1.ID = T2.ID WHERE T2.RBC < 3.5

## KB-013
- 상황: "질문: Among the patients with normal anti-SM, how many of them does not have thrombosis?" Examination 테이블을 잘못 사용하여 SQL이 틀렸다.
- 태그: Examination, Laboratory, SM, Thrombosis, JOIN_LOGIC
- 교정 내용: 오답: SELECT COUNT(DISTINCT P.ID) FROM Patient P JOIN Laboratory L ON P.ID = L.ID WHERE L.SM IN ('-', '+-') AND P.ID NOT IN (SELECT ID FROM Examination WHERE Thrombosis = 1) / 정답: SELECT COUNT(T1.ID) FROM Examination AS T1 INNER JOIN Laboratory AS T2 ON T1.ID = T2.ID WHERE T2.SM IN ('negative','0') AND T1.Thrombosis = 0

## KB-014
- 상황: "질문: List and group all patients by sex for total bilirubin (T-BIL) level not within the normal range." GROUP_CONCAT을 잘못 사용하여 SQL이 틀렸다.
- 태그: Patient, ID, Laboratory, T-BIL, AGGREGATION_LOGIC
- 교정 내용: 오답: SELECT SEX, GROUP_CONCAT(DISTINCT Patient.ID) AS PatientIDs FROM Patient JOIN Laboratory ON Patient.ID = Laboratory.ID WHERE `T-BIL` >= 2.0 GROUP BY SEX / 정답: SELECT T1.ID,T1.SEX FROM Patient AS T1 INNER JOIN Laboratory AS T2 ON T1.ID = T2.ID WHERE T2.`T-BIL` >= 2.0 GROUP BY T1.SEX,T1.ID

## KB-015
- 상황: "질문: Among the patients who has a normal level of anti-centromere and a normal level of anti-SSB, how many of them are male?" 잘못된 값 인코딩으로 SQL이 틀렸다.
- 태그: Patient, Laboratory, CENTROMEA, SSB, SEX, WRONG_COLUMN
- 교정 내용: 오답: SELECT COUNT(DISTINCT p.ID) AS MalePatients FROM Patient p JOIN Laboratory l ON p.ID = l.ID WHERE l.CENTROMEA IN ('-', '+-') AND l.SSB IN ('-', '+-') AND p.SEX = 'M' / 정답: SELECT COUNT(DISTINCT T1.ID) FROM Patient AS T1 INNER JOIN Laboratory AS T2 ON T1.ID = T2.ID WHERE T2.CENTROMEA IN ('negative', '0') AND T2.SSB IN ('negative', '0') AND T1.SEX = 'M'

## KB-016
- 상황: "질문: For the patients with a normal range of creatinine phosphokinase, how many of them have a positive measure of degree of coagulation?" DISTINCT를 사용하지 않아 중복된 환자 ID가 나올 수 있는 SQL을 작성했다.
- 태그: Patient, Laboratory, Examination, CPK, AGGREGATION_LOGIC
- 교정 내용: 오답: SELECT COUNT(DISTINCT p.ID) FROM Patient p JOIN Laboratory l ON p.ID = l.ID WHERE l.CPK < 250 AND (l.KCT = '+' OR l.RVVT = '+' OR l.LAC = '+') / 정답: SELECT COUNT(T1.ID) FROM Patient AS T1 INNER JOIN Laboratory AS T2 ON T1.ID = T2.ID INNER JOIN Examination AS T3 ON T1.ID = T3.ID WHERE T2.CPK < 250 AND (T3.KCT = '+' OR T3.RVVT = '+' OR T3.LAC = '+')

## KB-017
- 상황: "질문: How many underage patients were examined during the course of the three-year period from 1990 to 1993?" 연도 계산을 잘못하여 SQL이 틀렸다.
- 태그: Patient, Birthday, Examination, Examination Date, AGGREGATION_LOGIC, DATE_LOGIC
- 교정 내용: 오답: SELECT COUNT(DISTINCT p.ID) FROM Patient p JOIN Examination e ON p.ID = e.ID WHERE STRFTIME('%Y', p.Birthday) <= STRFTIME('%Y', '1993-12-31', '-18 years') AND STRFTIME('%Y', e.`Examination Date`) BETWEEN '1990' AND '1993' / 정답: SELECT COUNT(T1.ID) FROM Patient AS T1 INNER JOIN Examination AS T2 ON T1.ID = T2.ID WHERE STRFTIME('%Y', T2.`Examination Date`) BETWEEN '1990' AND '1993' AND STRFTIME('%Y', T2.`Examination Date`) - STRFTIME('%Y', T1.Birthday) < 18

## KB-018
- 상황: "질문: What number of patients with a degree of thrombosis level 2 and ANA pattern of only S, have a level of anti-Cardiolip in antibody (IgM) 20% higher than average?" 컬럼명을 잘못 사용하여 SQL이 틀렸다.
- 태그: Examination, Thrombosis, ANA Pattern, aCL IgM, AGGREGATION_LOGIC
- 교정 내용: 오답: SELECT COUNT(DISTINCT e.ID) FROM Examination e JOIN ( SELECT AVG(`aCL IgM`) * 1.2 AS avg_aCL_IgM FROM Examination ) avg_table ON e.`aCL IgM` > avg_table.avg_aCL_IgM WHERE e.Thrombosis = 2 AND e.ANA = 'S' / 정답: SELECT COUNT(*) FROM Examination WHERE Thrombosis = 2 AND `ANA Pattern` = 'S' AND `aCL IgM` > (SELECT AVG(`aCL IgM`) * 1.2 FROM Examination WHERE Thrombosis = 2 AND `ANA Pattern` = 'S')

## KB-019
- 상황: "질문: For the patient who was born on 1959/2/18, what is the decrease rate for his/her total cholesterol from November to December in 1981?" 서브쿼리를 잘못 사용하여 SQL이 틀렸다.
- 태그: Laboratory, T-CHO, AGGREGATION_LOGIC, DATE_LOGIC
- 교정 내용: 오답: SELECT (SUM(CASE WHEN Date LIKE '1981-11-%' THEN `T-CHO` ELSE 0 END) - SUM(CASE WHEN Date LIKE '1981-12-%' THEN `T-CHO` ELSE 0 END)) / NULLIF(SUM(CASE WHEN Date LIKE '1981-12-%' THEN `T-CHO` ELSE 0 END), 0) AS DecreaseRate FROM Laboratory WHERE ID IN (SELECT ID FROM Patient WHERE Birthday = '1959-02-18') / 정답: SELECT CAST((SUM(CASE WHEN T2.Date LIKE '1981-11-%' THEN T2.`T-CHO` ELSE 0 END) - SUM(CASE WHEN T2.Date LIKE '1981-12-%' THEN T2.`T-CHO` ELSE 0 END)) AS REAL) / SUM(CASE WHEN T2.Date LIKE '1981-12-%' THEN T2.`T-CHO` ELSE 0 END) FROM Patient AS T1 INNER JOIN Laboratory AS T2 ON T1.ID = T2.ID WHERE T1.Birthday = '1959-02-18'

## KB-020
- 상황: "질문: For the patient who was diagnosed with SLE on 1994/2/19, what was his/her anti-Cardiolipin antibody concentration status on 1993/11/12?" 결과 형식이 잘못되어 SQL이 틀렸다.
- 태그: Patient, Examination, Diagnosis, aCL IgA, aCL IgG, aCL IgM, VALUE_ENCODING
- 교정 내용: 오답: SELECT CASE WHEN `aCL IgM` IS NOT NULL THEN 'present' ELSE 'absent' END AS `aCL_IgM_Status` FROM Examination WHERE ID IN (SELECT ID FROM Patient WHERE Diagnosis = 'SLE' AND Description = '1994-02-19') AND `Examination Date` = '1993-11-12' / 정답: SELECT `aCL IgA`, `aCL IgG`, `aCL IgM` FROM Examination WHERE ID IN ( SELECT ID FROM Patient WHERE Diagnosis = 'SLE' AND Description = '1994-02-19' ) AND `Examination Date` = '1993-11-12'

## KB-021
- 상황: "질문: For the patients with an abnormal Ig M level, what is the most common disease they are diagnosed with?" 테이블을 잘못 조인하여 SQL이 틀렸다.
- 태그: Patient, Laboratory, Examination, IGM, AGGREGATION_LOGIC
- 교정 내용: 오답: SELECT Diagnosis FROM Laboratory JOIN Examination ON Laboratory.ID = Examination.ID WHERE IGM <= 40 OR IGM >= 400 GROUP BY Diagnosis ORDER BY COUNT(Diagnosis) DESC LIMIT 1 / 정답: SELECT T1.Diagnosis FROM Patient AS T1 INNER JOIN Laboratory AS T2 ON T1.ID = T2.ID WHERE T2.IGM NOT BETWEEN 40 AND 400 GROUP BY T1.Diagnosis ORDER BY COUNT(T1.Diagnosis) DESC LIMIT 1

## KB-022
- 상황: "질문: For laboratory examinations take in 1984, list all patients below 50 years old with normal platelet level." 날짜 계산을 잘못하여 SQL이 틀렸다.
- 태그: Patient, Laboratory, PLT, AGGREGATION_LOGIC, DATE_LOGIC
- 교정 내용: 오답: SELECT DISTINCT P.ID, P.SEX FROM Patient P JOIN Laboratory L ON P.ID = L.ID WHERE YEAR(L.Date) = '1984' AND (STRFTIME('%Y', 'now') - STRFTIME('%Y', P.Birthday)) < 50 AND L.PLT BETWEEN 100 AND 400 / 정답: SELECT DISTINCT T1.ID FROM Patient AS T1 INNER JOIN Laboratory AS T2 ON T1.ID = T2.ID WHERE T2.PLT BETWEEN 100 AND 400 AND STRFTIME('%Y', T2.Date) - STRFTIME('%Y', T1.Birthday) < 50 AND STRFTIME('%Y', T2.Date) = '1984'

## KB-023
- 상황: "질문: State the ID and age of patient with positive degree of coagulation." DISTINCT를 사용하지 않아 중복된 환자 ID가 나올 수 있는 SQL을 작성했다.
- 태그: Patient, Examination, RVVT, AGGREGATION_LOGIC
- 교정 내용: 오답: SELECT ID, (STRFTIME('%Y', 'now') - STRFTIME('%Y', Birthday)) AS Age FROM Examination JOIN Patient ON Examination.ID = Patient.ID WHERE RVVT = '+' / 정답: SELECT DISTINCT T1.ID, STRFTIME('%Y', CURRENT_TIMESTAMP) - STRFTIME('%Y', T1.Birthday) FROM Patient AS T1 INNER JOIN Examination AS T2 ON T1.ID = T2.ID WHERE T2.RVVT = '+'

## KB-024
- 상황: "질문: How many patients have a normal level of anti-ribonuclear protein and have been admitted to the hospital?" 조건을 잘못 설정하여 SQL이 틀렸다.
- 태그: Patient, Laboratory, RNP, Admission, AGGREGATION_LOGIC
- 교정 내용: 오답: SELECT COUNT(DISTINCT P.ID) FROM Patient P JOIN Laboratory L ON P.ID = L.ID WHERE (L.RNP = 'negative' OR L.RNP = '0') AND P.Admission = '+' / 정답: SELECT COUNT(DISTINCT T1.ID) FROM Patient AS T1 INNER JOIN Laboratory AS T2 ON T1.ID = T2.ID WHERE T2.RNP = 'negative' OR T2.RNP = '0' AND T1.Admission = '+'

## KB-025
- 상황: "질문: Are there more in-patient or outpatient who were male? What is the deviation in percentage?" 계산 방식이 잘못되어 SQL이 틀렸다.
- 태그: Patient, Admission, SEX, AGGREGATION_LOGIC
- 교정 내용: 오답: SELECT CASE WHEN COUNT(CASE WHEN Admission = '+' THEN ID END) > COUNT(CASE WHEN Admission = '-' THEN ID END) THEN 'in-patient' ELSE 'outpatient' END AS Type, ABS((COUNT(CASE WHEN Admission = '+' THEN ID END) - COUNT(CASE WHEN Admission = '-' THEN ID END)) * 100.0 / NULLIF(COUNT(CASE WHEN Admission = '-' THEN ID END), 0)) AS Percentage_Deviation FROM Patient WHERE SEX = 'M' / 정답: SELECT CAST(SUM(CASE WHEN Admission = '+' THEN 1 ELSE 0 END) AS REAL) * 100 / SUM(CASE WHEN Admission = '-' THEN 1 ELSE 0 END) FROM Patient WHERE SEX = 'M'

## KB-026
- 상황: "질문: How many patients with a normal Ig A level came to the hospital after 1990/1/1?" 테이블을 잘못 조인하여 SQL이 틀렸다.
- 태그: Patient, Laboratory, IGA, First Date, AGGREGATION_LOGIC, DATE_LOGIC
- 교정 내용: 오답: SELECT COUNT(*) FROM Laboratory JOIN Patient ON Laboratory.ID = Patient.ID WHERE IGA > 80 AND IGA < 500 AND STRFTIME('%Y', `First Date`) > '1990' / 정답: SELECT COUNT(T1.ID) FROM Patient AS T1 INNER JOIN Laboratory AS T2 ON T1.ID = T2.ID WHERE T2.IGA BETWEEN 80 AND 500 AND  strftime('%Y',  T1.`First Date`) > '1990'

## KB-027
- 상황: "질문: How many patients who were examined between 1987/7/6 and 1996/1/31 had a GPT level greater than 30 and an ALB level less than 4? List them by their ID." 조인 조건이 잘못되어 SQL이 틀렸다.
- 태그: Laboratory, GPT, ALB, AGGREGATION_LOGIC, DATE_LOGIC
- 교정 내용: 오답: SELECT DISTINCT L.ID FROM Laboratory L JOIN Examination E ON L.ID = E.ID WHERE L.Date BETWEEN '1987-07-06' AND '1996-01-31' AND L.GPT > 30 AND L.ALB < 4 / 정답: SELECT DISTINCT ID FROM Laboratory WHERE Date BETWEEN '1987-07-06' AND '1996-01-31' AND GPT > 30 AND ALB < 4
