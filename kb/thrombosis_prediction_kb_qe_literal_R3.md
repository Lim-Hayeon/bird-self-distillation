## KB-001
- 상황: "질문: List the patient ID, sex and birthday of patient with LDH beyond normal range." LDH beyond normal range를 고려할 때 DISTINCT를 사용하지 않아 중복된 환자 정보가 나올 수 있다.
- 태그: Patient, ID, SEX, Birthday, Laboratory, LDH, DISTINCT, JOIN_LOGIC
- 교정 내용: 오답: SELECT Patient.ID, Patient.SEX, Patient.Birthday FROM Patient JOIN Laboratory ON Patient.ID = Laboratory.ID WHERE Laboratory.LDH > 500 / 정답: SELECT DISTINCT T1.ID, T1.SEX, T1.Birthday FROM Patient AS T1 INNER JOIN Laboratory AS T2 ON T1.ID = T2.ID WHERE T2.LDH > 500

## KB-002
- 상황: "질문: What is the average age of the male patient with high cholesterol?" 평균 계산 시 서브쿼리로 환자 ID를 걸러내면 중복이 없어져서 틀린다.
- 태그: Patient, ID, SEX, Birthday, Laboratory, T-CHO, AVG, JOIN_LOGIC
- 교정 내용: 오답: SELECT AVG(strftime('%Y', 'now') - strftime('%Y', Birthday)) AS Average_Age FROM Patient WHERE SEX = 'M' AND ID IN ( SELECT ID FROM Laboratory WHERE `T-CHO` >= 250 ) / 정답: SELECT AVG(STRFTIME('%Y', date('NOW')) - STRFTIME('%Y', T1.Birthday)) FROM Patient AS T1 INNER JOIN Laboratory AS T2 ON T1.ID = T2.ID WHERE T2.`T-CHO` >= 250 AND T1.SEX = 'M'

## KB-003
- 상황: "질문: Among the patients who has a normal anti-scl70, how many of them are female and does not have any symptom?" SC170 컬럼이 Examination이 아니라 Laboratory 테이블에 있어 조인해야 한다.
- 태그: Patient, ID, SEX, Symptoms, Laboratory, SC170, COUNT, JOIN_LOGIC
- 교정 내용: 오답: SELECT COUNT(DISTINCT P.ID) FROM Patient P JOIN Examination E ON P.ID = E.ID WHERE P.SEX = 'F' AND E.Symptoms IS NULL AND E.SC170 IN ('negative', '0') / 정답: SELECT COUNT(DISTINCT T1.ID) FROM Patient AS T1 INNER JOIN Laboratory AS T2 ON T1.ID = T2.ID INNER JOIN Examination AS T3 ON T3.ID = T2.ID WHERE (T2.SC170 = 'negative' OR T2.SC170 = '0') AND T1.SEX = 'F' AND T3.Symptoms IS NULL

## KB-004
- 상황: "질문: Name the ID and age of patient with two or more laboratory examinations which show their hematoclit level exceeded the normal range." "두 번 이상"은 COUNT >= 2로 계산해야 한다.
- 태그: Patient, ID, Birthday, Laboratory, HCT, COUNT, JOIN_LOGIC
- 교정 내용: 오답: SELECT P.ID, (strftime('%Y', 'now') - strftime('%Y', P.Birthday)) AS age FROM Patient P JOIN Laboratory L ON P.ID = L.ID WHERE L.HCT >= 52 GROUP BY P.ID HAVING COUNT(L.ID) > 2 / 정답: SELECT DISTINCT T1.ID, STRFTIME('%Y', CURRENT_TIMESTAMP) - STRFTIME('%Y', T1.Birthday) FROM Patient AS T1 INNER JOIN Laboratory AS T2 ON T1.ID = T2.ID WHERE T1.ID IN ( SELECT ID FROM Laboratory WHERE HCT >= 52 GROUP BY ID HAVING COUNT(ID) >= 2 )

## KB-005
- 상황: "질문: Provide all ID, sex and birthday of patients whose urea nitrogen (UN) just within the borderline of passing?" 환자 리스트업할 땐 DISTINCT를 써야 한다.
- 태그: Patient, ID, SEX, Birthday, Laboratory, UN, DISTINCT, JOIN_LOGIC
- 교정 내용: 오답: SELECT Patient.ID, Patient.SEX, Patient.Birthday FROM Patient JOIN Laboratory ON Patient.ID = Laboratory.ID WHERE Laboratory.UN = 29 / 정답: SELECT DISTINCT T1.ID, T1.SEX, T1.Birthday FROM Patient AS T1 INNER JOIN Laboratory AS T2 ON T1.ID = T2.ID WHERE T2.UN = 29

## KB-006
- 상황: "질문: What is the percentage of female patient were born after 1930?" 날짜 비교할 땐 Birthday를 STRFTIME('%Y', Birthday)로 연도만 뽑아서 비교해야 한다.
- 태그: Patient, ID, SEX, Birthday, COUNT, AVG, JOIN_LOGIC
- 교정 내용: 오답: SELECT (COUNT(ID) * 100.0 / (SELECT COUNT(ID) FROM Patient WHERE SEX = 'F')) AS FemalePercentage FROM Patient WHERE Birthday > '1930-01-01' AND SEX = 'F' / 정답: SELECT CAST(SUM(CASE WHEN STRFTIME('%Y', Birthday) > '1930' THEN 1 ELSE 0 END) AS REAL) * 100 / COUNT(*) FROM Patient WHERE SEX = 'F'

## KB-007
- 상황: "질문: For patients with abnormal platelet level, state the number of patients with lower than normal range. How is it compare to the number of patients with higher than normal range?" 비교 기준을 <, > 대신 <=, >= 로 써야 하고, 결과는 두 값의 차이(SUBTRACT) 하나만 컬럼으로 반환해야 한다.
- 태그: Laboratory, PLT, COUNT, JOIN_LOGIC
- 교정 내용: 오답: SELECT SUM(CASE WHEN PLT < 100 THEN 1 ELSE 0 END) AS Lower_Than_Normal, SUM(CASE WHEN PLT > 400 THEN 1 ELSE 0 END) AS Higher_Than_Normal, (SUM(CASE WHEN PLT < 100 THEN 1 ELSE 0 END) - SUM(CASE WHEN PLT > 400 THEN 1 ELSE 0 END)) AS Difference FROM Laboratory WHERE PLT <= 100 OR PLT >= 400 / 정답: SELECT SUM(CASE WHEN T2.PLT <= 100 THEN 1 ELSE 0 END) - SUM(CASE WHEN T2.PLT >= 400 THEN 1 ELSE 0 END) FROM Patient AS T1 INNER JOIN Laboratory AS T2 ON T1.ID = T2.ID

## KB-008
- 상황: "질문: Was the patient with the number 57266's uric acid within a normal range?" 결과는 'Yes'/'No' 같은 문자열 말고 true/false로 반환해야 한다.
- 태그: Patient, ID, SEX, Laboratory, UA, BOOLEAN, JOIN_LOGIC
- 교정 내용: 오답: SELECT CASE WHEN (SEX = 'M' AND UA <= 8.0) OR (SEX = 'F' AND UA <= 6.5) THEN 'No' ELSE 'Yes' END AS Is_UA_Normal FROM Patient JOIN Laboratory ON Patient.ID = Laboratory.ID WHERE Patient.ID = 57266 / 정답: SELECT CASE WHEN (T1.SEX = 'F' AND T2.UA > 6.5) OR (T1.SEX = 'M' AND T2.UA > 8.0) THEN true ELSE false END FROM Patient AS T1 INNER JOIN Laboratory AS T2 ON T1.ID = T2.ID WHERE T1.ID = 57266

## KB-009
- 상황: "질문: How many patients with a abnormal C-reactive protein don't have their data recorded?" CRP='+' 조건은 포함이야. NOT IN 쓰지 말고 CRP='+'인 환자 중에서 Description이 NULL인 사람을 세야 한다.
- 태그: Patient, ID, Description, Laboratory, CRP, COUNT, JOIN_LOGIC
- 교정 내용: 오답: SELECT COUNT(*) FROM Patient WHERE Description IS NULL AND ID NOT IN (SELECT ID FROM Laboratory WHERE CRP = '+') / 정답: SELECT COUNT(*) FROM Patient JOIN Laboratory ON Patient.ID = Laboratory.ID WHERE Laboratory.CRP = '+' AND Patient.Description IS NULL

## KB-010
- 상황: "질문: What percentage of patients who were born in 1980 and were diagnosed with RA are women?" SQLite엔 YEAR() 함수가 없어 STRFTIME('%Y', Birthday) = '1980'으로 써야 한다.
- 태그: Patient, ID, SEX, Birthday, Diagnosis, COUNT, AVG, JOIN_LOGIC
- 교정 내용: 오답: SELECT (SUM(CASE WHEN SEX = 'F' THEN 1 ELSE 0 END) * 100.0 / COUNT(*)) AS percentage FROM Patient WHERE YEAR(Birthday) = 1980 AND Diagnosis = 'RA' / 정답: SELECT CAST(SUM(CASE WHEN SEX = 'F' THEN 1 ELSE 0 END) AS REAL) * 100 / COUNT(ID) FROM Patient WHERE Diagnosis = 'RA' AND STRFTIME('%Y', Birthday) = '1980'

## KB-011
- 상황: "질문: Among the patients whose creatinine level is abnormal, how many of them aren't 70 yet?" 환자 수 셀 땐 COUNT(*) 말고 COUNT(DISTINCT ID) 써야 한다.
- 태그: Patient, ID, Birthday, Laboratory, CRE, COUNT, JOIN_LOGIC
- 교정 내용: 오답: SELECT COUNT(*) FROM Patient JOIN Laboratory ON Patient.ID = Laboratory.ID WHERE Laboratory.CRE >= 1.5 AND (STRFTIME('%Y', 'now') - STRFTIME('%Y', Patient.Birthday)) < 70 / 정답: SELECT COUNT(DISTINCT T1.ID) FROM Patient AS T1 INNER JOIN Laboratory AS T2 ON T1.ID = T2.ID WHERE T2.CRE >= 1.5 AND STRFTIME('%Y', Date('now')) - STRFTIME('%Y', T1.Birthday) < 70

## KB-012
- 상황: "질문: What are the patient's diagnosis for those who has lower red blood blood cell? State their ID and age." DISTINCT가 빠졌고, 컬럼 순서도 Diagnosis, ID, Age 순으로 바꿔야 한다.
- 태그: Patient, ID, Diagnosis, Birthday, Laboratory, RBC, DISTINCT, JOIN_LOGIC
- 교정 내용: 오답: SELECT Patient.ID, (strftime('%Y', 'now') - strftime('%Y', Patient.Birthday)) AS Age, Patient.Diagnosis FROM Patient JOIN Laboratory ON Patient.ID = Laboratory.ID WHERE Laboratory.RBC < 3.5 / 정답: SELECT DISTINCT T1.Diagnosis, T1.ID , STRFTIME('%Y', CURRENT_TIMESTAMP) -STRFTIME('%Y', T1.Birthday) FROM Patient AS T1 INNER JOIN Laboratory AS T2 ON T1.ID = T2.ID WHERE T2.RBC < 3.5

## KB-013
- 상황: "질문: Among the patients with normal anti-SM, how many of them does not have thrombosis?" SM 컬럼은 'negative'/'0'/'1'로 저장돼 있어. normal anti-SM은 SM IN ('negative', '0')로 써야 해. 그리고 NOT IN 서브쿼리 말고, Examination 테이블에서 Thrombosis = 0 조건으로 직접 조인해서 세야 한다.
- 태그: Patient, ID, SM, Thrombosis, Examination, COUNT, JOIN_LOGIC
- 교정 내용: 오답: SELECT COUNT(DISTINCT P.ID) FROM Patient P JOIN Laboratory L ON P.ID = L.ID WHERE L.SM IN ('-', '+-') AND P.ID NOT IN (SELECT ID FROM Examination WHERE Thrombosis = 1) / 정답: SELECT COUNT(T1.ID) FROM Examination AS T1 INNER JOIN Laboratory AS T2 ON T1.ID = T2.ID WHERE T2.SM IN ('negative','0') AND T1.Thrombosis = 0

## KB-014
- 상황: "질문: List and group all patients by sex for total bilirubin (T-BIL) level not within the normal range." GROUP_CONCAT 쓰지 말고 그냥 ID, SEX 컬럼만 SELECT해서 SEX, ID로 GROUP BY 해.
- 태그: Patient, ID, SEX, Laboratory, T-BIL, GROUP BY, JOIN_LOGIC
- 교정 내용: 오답: SELECT SEX, GROUP_CONCAT(DISTINCT Patient.ID) AS PatientIDs FROM Patient JOIN Laboratory ON Patient.ID = Laboratory.ID WHERE `T-BIL` >= 2.0 GROUP BY SEX / 정답: SELECT T1.ID,T1.SEX FROM Patient AS T1 INNER JOIN Laboratory AS T2 ON T1.ID = T2.ID WHERE T2.`T-BIL` >= 2.0 GROUP BY T1.SEX,T1.ID

## KB-015
- 상황: "질문: Among the patients who has a normal level of anti-centromere and a normal level of anti-SSB, how many of them are male?" CENTROMEA랑 SSB도 '-'/'+-' 말고 'negative'/'0'으로 값이 저장돼 있어. SM 컬럼이랑 똑같은 인코딩이야.
- 태그: Patient, ID, SEX, Laboratory, CENTROMEA, SSB, COUNT, JOIN_LOGIC
- 교정 내용: 오답: SELECT COUNT(DISTINCT p.ID) AS MalePatients FROM Patient p JOIN Laboratory l ON p.ID = l.ID WHERE l.CENTROMEA IN ('-', '+-') AND l.SSB IN ('-', '+-') AND p.SEX = 'M' / 정답: SELECT COUNT(DISTINCT T1.ID) FROM Patient AS T1 INNER JOIN Laboratory AS T2 ON T1.ID = T2.ID WHERE T2.CENTROMEA IN ('negative', '0') AND T2.SSB IN ('negative', '0') AND T1.SEX = 'M'

## KB-016
- 상황: "질문: For the patients with a normal range of creatinine phosphokinase, how many of them have a positive measure of degree of coagulation?" KCT, RVVT, LAC는 Laboratory가 아니라 Examination 테이블에 있어. Examination도 조인해야 하고, DISTINCT는 빼야 해.
- 태그: Patient, ID, Laboratory, Examination, CPK, COUNT, JOIN_LOGIC
- 교정 내용: 오답: SELECT COUNT(DISTINCT p.ID) FROM Patient p JOIN Laboratory l ON p.ID = l.ID WHERE l.CPK < 250 AND (l.KCT = '+' OR l.RVVT = '+' OR l.LAC = '+') / 정답: SELECT COUNT(T1.ID) FROM Patient AS T1 INNER JOIN Laboratory AS T2 ON T1.ID = T2.ID INNER JOIN Examination AS T3 ON T1.ID = T3.ID WHERE T2.CPK < 250 AND (T3.KCT = '+' OR T3.RVVT = '+' OR T3.LAC = '+')

## KB-017
- 상황: "질문: How many underage patients were examined during the course of the three-year period from 1990 to 1993?" 처음에 나이를 고정된 1993년 기준으로 계산하여 틀렸다.
- 태그: Patient, ID, Birthday, Examination, `Examination Date`, COUNT, JOIN_LOGIC
- 교정 내용: 오답: SELECT COUNT(DISTINCT p.ID) FROM Patient p JOIN Examination e ON p.ID = e.ID WHERE STRFTIME('%Y', p.Birthday) <= STRFTIME('%Y', '1993-12-31', '-18 years') AND STRFTIME('%Y', e.`Examination Date`) BETWEEN '1990' AND '1993' / 정답: SELECT COUNT(T1.ID) FROM Patient AS T1 INNER JOIN Examination AS T2 ON T1.ID = T2.ID WHERE STRFTIME('%Y', T2.`Examination Date`) BETWEEN '1990' AND '1993' AND STRFTIME('%Y', T2.`Examination Date`) - STRFTIME('%Y', T1.Birthday) < 18

## KB-018
- 상황: "질문: What number of patients with a degree of thrombosis level 2 and ANA pattern of only S, have a level of anti-Cardiolip in antibody (IgM) 20% higher than average?" 처음에 ANA 컬럼명을 잘못 사용하여 틀렸다.
- 태그: Examination, Thrombosis, `ANA Pattern`, `aCL IgM`, COUNT, JOIN_LOGIC
- 교정 내용: 오답: SELECT COUNT(DISTINCT e.ID) FROM Examination e JOIN ( SELECT AVG(`aCL IgM`) * 1.2 AS avg_aCL_IgM FROM Examination ) avg_table ON e.`aCL IgM` > avg_table.avg_aCL_IgM WHERE e.Thrombosis = 2 AND e.ANA = 'S' / 정답: SELECT COUNT(*) FROM Examination WHERE Thrombosis = 2 AND `ANA Pattern` = 'S' AND `aCL IgM` > (SELECT AVG(`aCL IgM`) * 1.2 FROM Examination WHERE Thrombosis = 2 AND `ANA Pattern` = 'S')

## KB-019
- 상황: "질문: For the patient who was born on 1959/2/18, what is the decrease rate for his/her total cholesterol from November to December in 1981?" 처음에 NULLIF를 사용하여 틀렸다.
- 태그: Patient, Birthday, Laboratory, `T-CHO`, COUNT, JOIN_LOGIC
- 교정 내용: 오답: SELECT (SUM(CASE WHEN Date LIKE '1981-11-%' THEN `T-CHO` ELSE 0 END) - SUM(CASE WHEN Date LIKE '1981-12-%' THEN `T-CHO` ELSE 0 END)) / NULLIF(SUM(CASE WHEN Date LIKE '1981-12-%' THEN `T-CHO` ELSE 0 END), 0) AS DecreaseRate FROM Laboratory WHERE ID IN (SELECT ID FROM Patient WHERE Birthday = '1959-02-18') / 정답: SELECT CAST((SUM(CASE WHEN T2.Date LIKE '1981-11-%' THEN T2.`T-CHO` ELSE 0 END) - SUM(CASE WHEN T2.Date LIKE '1981-12-%' THEN T2.`T-CHO` ELSE 0 END)) AS REAL) / SUM(CASE WHEN T2.Date LIKE '1981-12-%' THEN T2.`T-CHO` ELSE 0 END) FROM Patient AS T1 INNER JOIN Laboratory AS T2 ON T1.ID = T2.ID WHERE T1.Birthday = '1959-02-18'

## KB-020
- 상황: "질문: For the patients with an abnormal Ig M level, what is the most common disease they are diagnosed with?" 처음에 Diagnosis 컬럼을 잘못된 테이블에서 가져와서 틀렸다.
- 태그: Patient, ID, Diagnosis, Laboratory, IGM, COUNT, JOIN_LOGIC
- 교정 내용: 오답: SELECT Diagnosis FROM Laboratory JOIN Examination ON Laboratory.ID = Examination.ID WHERE IGM <= 40 OR IGM >= 400 GROUP BY Diagnosis ORDER BY COUNT(Diagnosis) DESC LIMIT 1 / 정답: SELECT T1.Diagnosis FROM Patient AS T1 INNER JOIN Laboratory AS T2 ON T1.ID = T2.ID WHERE T2.IGM NOT BETWEEN 40 AND 400 GROUP BY T1.Diagnosis ORDER BY COUNT(T1.Diagnosis) DESC LIMIT 1

## KB-021
- 상황: "질문: For laboratory examinations take in 1984, list all patients below 50 years old with normal platelet level." 처음에 YEAR() 함수를 사용하여 틀렸다.
- 태그: Patient, ID, Birthday, Laboratory, PLT, COUNT, JOIN_LOGIC
- 교정 내용: 오답: SELECT DISTINCT P.ID, P.SEX FROM Patient P JOIN Laboratory L ON P.ID = L.ID WHERE YEAR(L.Date) = '1984' AND (STRFTIME('%Y', 'now') - STRFTIME('%Y', P.Birthday)) < 50 AND L.PLT BETWEEN 100 AND 400 / 정답: SELECT DISTINCT T1.ID FROM Patient AS T1 INNER JOIN Laboratory AS T2 ON T1.ID = T2.ID WHERE T2.PLT BETWEEN 100 AND 400 AND STRFTIME('%Y', T2.Date) - STRFTIME('%Y', T1.Birthday) < 50 AND STRFTIME('%Y', T2.Date) = '1984'

## KB-022
- 상황: "질문: State the ID and age of patient with positive degree of coagulation." 처음에 DISTINCT가 빠져서 틀렸다.
- 태그: Patient, ID, Birthday, Examination, RVVT, COUNT, JOIN_LOGIC
- 교정 내용: 오답: SELECT ID, (STRFTIME('%Y', 'now') - STRFTIME('%Y', Birthday)) AS Age FROM Examination JOIN Patient ON Examination.ID = Patient.ID WHERE RVVT = '+' / 정답: SELECT DISTINCT T1.ID, STRFTIME('%Y', CURRENT_TIMESTAMP) - STRFTIME('%Y', T1.Birthday) FROM Patient AS T1 INNER JOIN Examination AS T2 ON T1.ID = T2.ID WHERE T2.RVVT = '+'

## KB-023
- 상황: "질문: How many patients have a normal level of anti-ribonuclear protein and have been admitted to the hospital?" 처음에 괄호를 잘못 사용하여 틀렸다.
- 태그: Patient, ID, Admission, Laboratory, RNP, COUNT, JOIN_LOGIC
- 교정 내용: 오답: SELECT COUNT(DISTINCT P.ID) FROM Patient P JOIN Laboratory L ON P.ID = L.ID WHERE (L.RNP = 'negative' OR L.RNP = '0') AND P.Admission = '+' / 정답: SELECT COUNT(DISTINCT T1.ID) FROM Patient AS T1 INNER JOIN Laboratory AS T2 ON T1.ID = T2.ID WHERE T2.RNP = 'negative' OR T2.RNP = '0' AND T1.Admission = '+'

## KB-024
- 상황: "질문: Are there more in-patient or outpatient who were male? What is the deviation in percentage?" 처음에 CASE 문을 사용하여 틀렸다.
- 태그: Patient, ID, Admission, SEX, COUNT, AVG, JOIN_LOGIC
- 교정 내용: 오답: SELECT CASE WHEN COUNT(CASE WHEN Admission = '+' THEN ID END) > COUNT(CASE WHEN Admission = '-' THEN ID END) THEN 'in-patient' ELSE 'outpatient' END AS Type, ABS((COUNT(CASE WHEN Admission = '+' THEN ID END) - COUNT(CASE WHEN Admission = '-' THEN ID END)) * 100.0 / NULLIF(COUNT(CASE WHEN Admission = '-' THEN ID END), 0)) AS Percentage_Deviation FROM Patient WHERE SEX = 'M' / 정답: SELECT CAST(SUM(CASE WHEN Admission = '+' THEN 1 ELSE 0 END) AS REAL) * 100 / SUM(CASE WHEN Admission = '-' THEN 1 ELSE 0 END) FROM Patient WHERE SEX = 'M'

## KB-025
- 상황: "질문: How many patients with a normal Ig A level came to the hospital after 1990/1/1?" 처음에 IGA 조건을 잘못 사용하여 틀렸다.
- 태그: Patient, ID, Laboratory, IGA, COUNT, JOIN_LOGIC
- 교정 내용: 오답: SELECT COUNT(*) FROM Laboratory JOIN Patient ON Laboratory.ID = Patient.ID WHERE IGA > 80 AND IGA < 500 AND STRFTIME('%Y', `First Date`) >= '1990' / 정답: SELECT COUNT(T1.ID) FROM Patient AS T1 INNER JOIN Laboratory AS T2 ON T1.ID = T2.ID WHERE T2.IGA BETWEEN 80 AND 500 AND strftime('%Y', T1.`First Date`) > '1990'

## KB-026
- 상황: "질문: How many patients who were examined between 1987/7/6 and 1996/1/31 had a GPT level greater than 30 and an ALB level less than 4? List them by their ID." 처음에 Examination 테이블을 조인하여 틀렸다.
- 태그: Laboratory, ID, GPT, ALB, COUNT, JOIN_LOGIC
- 교정 내용: 오답: SELECT DISTINCT L.ID FROM Laboratory L JOIN Examination E ON L.ID = E.ID WHERE L.Date BETWEEN '1987-07-06' AND '1996-01-31' AND L.GPT > 30 AND L.ALB < 4 / 정답: SELECT DISTINCT ID FROM Laboratory WHERE Date BETWEEN '1987-07-06' AND '1996-01-31' AND GPT > 30 AND ALB < 4
