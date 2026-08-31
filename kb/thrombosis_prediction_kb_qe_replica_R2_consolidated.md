## KB-001
- 상황: "질문: List the patient ID, sex and birthday of patient with LDH beyond normal range." LDH beyond normal range를 고려하지 않아 중복된 환자 정보가 발생할 수 있다.
- 태그: Patient, ID, JOIN, MISSING_DISTINCT
- 교정 내용: 오답: SELECT Patient.ID, Patient.SEX, Patient.Birthday FROM Patient JOIN Laboratory ON Patient.ID = Laboratory.ID WHERE Laboratory.LDH > 500 / 정답: SELECT DISTINCT T1.ID, T1.SEX, T1.Birthday FROM Patient AS T1 INNER JOIN Laboratory AS T2 ON T1.ID = T2.ID WHERE T2.LDH > 500

## KB-002
- 상황: "질문: What is the average age of the male patient with high cholesterol?" 서브쿼리로 인해 중복된 환자 수가 계산되어 평균이 잘못 나올 수 있다.
- 태그: Patient, Birthday, Laboratory, T-CHO, JOIN, AGGREGATION_LOGIC
- 교정 내용: 오답: SELECT AVG(strftime('%Y', 'now') - strftime('%Y', Birthday)) AS Average_Age FROM Patient WHERE SEX = 'M' AND ID IN ( SELECT ID FROM Laboratory WHERE `T-CHO` >= 250 ) / 정답: SELECT AVG(STRFTIME('%Y', date('NOW')) - STRFTIME('%Y', T1.Birthday)) FROM Patient AS T1 INNER JOIN Laboratory AS T2 ON T1.ID = T2.ID WHERE T2.`T-CHO` >= 250 AND T1.SEX = 'M'

## KB-003
- 상황: "질문: Among the patients who has a normal anti-scl70, how many of them are female and does not have any symptom?" SC170 컬럼이 잘못된 테이블에서 참조되어 오류가 발생했다.
- 태그: Patient, SEX, Examination, Symptoms, Laboratory, SC170, JOIN, WRONG_TABLE
- 교정 내용: 오답: SELECT COUNT(DISTINCT P.ID) FROM Patient P JOIN Examination E ON P.ID = E.ID WHERE P.SEX = 'F' AND E.Symptoms IS NULL AND E.SC170 IN ('negative', '0') / 정답: SELECT COUNT(DISTINCT T1.ID) FROM Patient AS T1 INNER JOIN Laboratory AS T2 ON T1.ID = T2.ID INNER JOIN Examination AS T3 ON T3.ID = T2.ID WHERE (T2.SC170 = 'negative' OR T2.SC170 = '0') AND T1.SEX = 'F' AND T3.Symptoms IS NULL

## KB-004
- 상황: "질문: Name the ID and age of patient with two or more laboratory examinations which show their hematocrit level exceeded the normal range." COUNT 조건이 잘못 설정되어 오류가 발생했다.
- 태그: Patient, Birthday, Laboratory, HCT, JOIN, AGGREGATION_LOGIC
- 교정 내용: 오답: SELECT P.ID, (strftime('%Y', 'now') - strftime('%Y', P.Birthday)) AS age FROM Patient P JOIN Laboratory L ON P.ID = L.ID WHERE L.HCT >= 52 GROUP BY P.ID HAVING COUNT(L.ID) > 2 / 정답: SELECT DISTINCT T1.ID, STRFTIME('%Y', CURRENT_TIMESTAMP) - STRFTIME('%Y', T1.Birthday) FROM Patient AS T1 INNER JOIN Laboratory AS T2 ON T1.ID = T2.ID WHERE T1.ID IN ( SELECT ID FROM Laboratory WHERE HCT >= 52 GROUP BY ID HAVING COUNT(ID) >= 2 )

## KB-005
- 상황: "질문: Provide all ID, sex and birthday of patients whose urea nitrogen (UN) just within the borderline of passing?" DISTINCT가 누락되어 중복된 환자 정보가 발생할 수 있다.
- 태그: Patient, ID, SEX, Birthday, Laboratory, UN, JOIN, MISSING_DISTINCT
- 교정 내용: 오답: SELECT Patient.ID, Patient.SEX, Patient.Birthday FROM Patient JOIN Laboratory ON Patient.ID = Laboratory.ID WHERE Laboratory.UN = 29 / 정답: SELECT DISTINCT T1.ID, T1.SEX, T1.Birthday FROM Patient AS T1 INNER JOIN Laboratory AS T2 ON T1.ID = T2.ID WHERE T2.UN = 29

## KB-006
- 상황: "질문: What is the percentage of female patient were born after 1930?" 날짜 비교 방식이 잘못되어 오류가 발생했다.
- 태그: Patient, Birthday, SEX, AGGREGATION_LOGIC
- 교정 내용: 오답: SELECT (COUNT(ID) * 100.0 / (SELECT COUNT(ID) FROM Patient WHERE SEX = 'F')) AS FemalePercentage FROM Patient WHERE Birthday > '1930-01-01' AND SEX = 'F' / 정답: SELECT CAST(SUM(CASE WHEN STRFTIME('%Y', Birthday) > '1930' THEN 1 ELSE 0 END) AS REAL) * 100 / COUNT(*) FROM Patient WHERE SEX = 'F'

## KB-007
- 상황: "질문: For patients with abnormal platelet level, state the number of patients with lower than normal range. How is it compare to the number of patients with higher than normal range?" 비교 기준이 잘못 설정되어 오류가 발생했다.
- 태그: Laboratory, PLT, AGGREGATION_LOGIC
- 교정 내용: 오답: SELECT SUM(CASE WHEN PLT < 100 THEN 1 ELSE 0 END) AS Lower_Than_Normal, SUM(CASE WHEN PLT > 400 THEN 1 ELSE 0 END) AS Higher_Than_Normal, (SUM(CASE WHEN PLT < 100 THEN 1 ELSE 0 END) - SUM(CASE WHEN PLT > 400 THEN 1 ELSE 0 END)) AS Difference FROM Laboratory WHERE PLT <= 100 OR PLT >= 400 / 정답: SELECT SUM(CASE WHEN T2.PLT <= 100 THEN 1 ELSE 0 END) - SUM(CASE WHEN T2.PLT >= 400 THEN 1 ELSE 0 END) FROM Patient AS T1 INNER JOIN Laboratory AS T2 ON T1.ID = T2.ID

## KB-008
- 상황: "질문: Was the patient with the number 57266's uric acid within a normal range?" 결과 형식이 잘못되어 오류가 발생했다.
- 태그: Patient, Laboratory, UA, JOIN, VALUE_ENCODING
- 교정 내용: 오답: SELECT CASE WHEN (SEX = 'M' AND UA <= 8.0) OR (SEX = 'F' AND UA <= 6.5) THEN 'No' ELSE 'Yes' END AS Is_UA_Normal FROM Patient JOIN Laboratory ON Patient.ID = Laboratory.ID WHERE Patient.ID = 57266 / 정답: SELECT CASE WHEN (T1.SEX = 'F' AND T2.UA > 6.5) OR (T1.SEX = 'M' AND T2.UA > 8.0) THEN true ELSE false END FROM Patient AS T1 INNER JOIN Laboratory AS T2 ON T1.ID = T2.ID WHERE T1.ID = 57266

## KB-009
- 상황: "질문: How many patients with a abnormal C-reactive protein don't have their data recorded?" 서브쿼리 대신 JOIN을 사용해야 하는 오류가 발생했다.
- 태그: Patient, Laboratory, CRP, Description, JOIN, WRONG_TABLE
- 교정 내용: 오답: SELECT COUNT(*) FROM Patient WHERE Description IS NULL AND ID NOT IN (SELECT ID FROM Laboratory WHERE CRP = '+') / 정답: SELECT COUNT(*) FROM Patient JOIN Laboratory ON Patient.ID = Laboratory.ID WHERE Laboratory.CRP = '+' AND Patient.Description IS NULL

## KB-010
- 상황: "질문: What percentage of patients who were born in 1980 and were diagnosed with RA are women?" YEAR() 함수가 없어서 오류가 발생했다.
- 태그: Patient, Birthday, SEX, Diagnosis, AGGREGATION_LOGIC
- 교정 내용: 오답: SELECT (SUM(CASE WHEN SEX = 'F' THEN 1 ELSE 0 END) * 100.0 / COUNT(*)) AS percentage FROM Patient WHERE YEAR(Birthday) = 1980 AND Diagnosis = 'RA' / 정답: SELECT CAST(SUM(CASE WHEN SEX = 'F' THEN 1 ELSE 0 END) AS REAL) * 100 / COUNT(ID) FROM Patient WHERE Diagnosis = 'RA' AND STRFTIME('%Y', Birthday) = '1980'

## KB-011
- 상황: "질문: Among the patients whose creatinine level is abnormal, how many of them aren't 70 yet?" COUNT(*) 대신 COUNT(DISTINCT ID)를 사용해야 하는 오류가 발생했다.
- 태그: Patient, Laboratory, CRE, Birthday, JOIN, AGGREGATION_LOGIC
- 교정 내용: 오답: SELECT COUNT(*) FROM Patient JOIN Laboratory ON Patient.ID = Laboratory.ID WHERE Laboratory.CRE >= 1.5 AND (STRFTIME('%Y', 'now') - STRFTIME('%Y', Patient.Birthday)) < 70 / 정답: SELECT COUNT(DISTINCT T1.ID) FROM Patient AS T1 INNER JOIN Laboratory AS T2 ON T1.ID = T2.ID WHERE T2.CRE >= 1.5 AND STRFTIME('%Y', Date('now')) - STRFTIME('%Y', T1.Birthday) < 70

## KB-012
- 상황: "질문: For the patients with a normal range of creatinine phosphokinase, how many of them have a positive measure of degree of coagulation?" 잘못된 테이블 조인으로 인해 오류가 발생했다.
- 태그: Patient, Laboratory, Examination, CPK, KCT, RVVT, LAC, JOIN, WRONG_TABLE
- 교정 내용: 오답: SELECT COUNT(DISTINCT p.ID) FROM Patient p JOIN Laboratory l ON p.ID = l.ID WHERE l.CPK < 250 AND (l.KCT = '+' OR l.RVVT = '+' OR l.LAC = '+') / 정답: SELECT COUNT(T1.ID) FROM Patient AS T1 INNER JOIN Laboratory AS T2 ON T1.ID = T2.ID INNER JOIN Examination AS T3 ON T1.ID = T3.ID WHERE T2.CPK < 250 AND (T3.KCT = '+' OR T3.RVVT = '+' OR T3.LAC = '+')

## KB-013
- 상황: "질문: For laboratory examinations take in 1984, list all patients below 50 years old with normal platelet level." YEAR() 대신 STRFTIME('%Y', ...) 써야 해. 그리고 나이는 현재 시각이 아니라 검사 날짜(Date) 기준으로 계산해야 해. SELECT는 ID만, SEX는 빼.
- 태그: Patient, Laboratory, PLT, Date, JOIN, AGGREGATION_LOGIC
- 교정 내용: 오답: SELECT DISTINCT P.ID, P.SEX FROM Patient P JOIN Laboratory L ON P.ID = L.ID WHERE YEAR(L.Date) = '1984' AND (STRFTIME('%Y', 'now') - STRFTIME('%Y', P.Birthday)) < 50 AND L.PLT BETWEEN 100 AND 400 / 정답: SELECT DISTINCT T1.ID FROM Patient AS T1 INNER JOIN Laboratory AS T2 ON T1.ID = T2.ID WHERE T2.PLT BETWEEN 100 AND 400 AND STRFTIME('%Y', T2.Date) - STRFTIME('%Y', T1.Birthday) < 50 AND STRFTIME('%Y', T2.Date) = '1984'

## KB-014
- 상황: "질문: State the ID and age of patient with positive degree of coagulation." DISTINCT 빠졌어.
- 태그: Patient, Examination, RVVT, JOIN, AGGREGATION_LOGIC
- 교정 내용: 오답: SELECT ID, (STRFTIME('%Y', 'now') - STRFTIME('%Y', Birthday)) AS Age FROM Examination JOIN Patient ON Examination.ID = Patient.ID WHERE RVVT = '+' / 정답: SELECT DISTINCT T1.ID, STRFTIME('%Y', CURRENT_TIMESTAMP) - STRFTIME('%Y', T1.Birthday) FROM Patient AS T1 INNER JOIN Examination AS T2 ON T1.ID = T2.ID WHERE T2.RVVT = '+'

## KB-015
- 상황: "질문: How many patients have a normal level of anti-ribonuclear protein and have been admitted to the hospital?" 괄호 빼봐. RNP 조건 두 개를 OR로, 그 뒤에 AND Admission 조건을 그냥 이어 써.
- 태그: Patient, Laboratory, RNP, Admission, JOIN, AGGREGATION_LOGIC
- 교정 내용: 오답: SELECT COUNT(DISTINCT P.ID) FROM Patient P JOIN Laboratory L ON P.ID = L.ID WHERE (L.RNP = 'negative' OR L.RNP = '0') AND P.Admission = '+' / 정답: SELECT COUNT(DISTINCT T1.ID) FROM Patient AS T1 INNER JOIN Laboratory AS T2 ON T1.ID = T2.ID WHERE T2.RNP = 'negative' OR T2.RNP = '0' AND T1.Admission = '+'

## KB-016
- 상황: "질문: Are there more in-patient or outpatient who were male? What is the deviation in percentage?" 어느 쪽이 많은지 텍스트로 판단하지 말고, 그냥 in-patient 비율을 outpatient 비율로 나눈 값(퍼센트)만 반환해. CASE, ABS, NULLIF 다 필요 없어.
- 태그: Patient, Admission, SEX, AGGREGATION_LOGIC
- 교정 내용: 오답: SELECT CASE WHEN COUNT(CASE WHEN Admission = '+' THEN ID END) > COUNT(CASE WHEN Admission = '-' THEN ID END) THEN 'in-patient' ELSE 'outpatient' END AS Type, ABS((COUNT(CASE WHEN Admission = '+' THEN ID END) - COUNT(CASE WHEN Admission = '-' THEN ID END)) * 100.0 / NULLIF(COUNT(CASE WHEN Admission = '-' THEN ID END), 0)) AS Percentage_Deviation FROM Patient WHERE SEX = 'M' / 정답: SELECT CAST(SUM(CASE WHEN Admission = '+' THEN 1 ELSE 0 END) AS REAL) * 100 / SUM(CASE WHEN Admission = '-' THEN 1 ELSE 0 END) FROM Patient WHERE SEX = 'M'

## KB-017
- 상황: "질문: How many patients with a normal Ig A level came to the hospital after 1990/1/1?" IGA는 Patient가 아니라 Laboratory 테이블에 있어. Laboratory랑 조인해야 하고, 연도 비교는 >=가 아니라 >로 써야 해.
- 태그: Patient, Laboratory, IGA, `First Date`, JOIN, AGGREGATION_LOGIC
- 교정 내용: 오답: SELECT COUNT(*) FROM Patient WHERE IGA > 80 AND IGA < 500 AND STRFTIME('%Y', `First Date`) >= '1990' / 정답: SELECT COUNT(T1.ID) FROM Patient AS T1 INNER JOIN Laboratory AS T2 ON T1.ID = T2.ID WHERE T2.IGA BETWEEN 80 AND 500 AND  strftime('%Y',  T1.`First Date`) > '1990'

## KB-018
- 상황: "질문: How many patients who were examined between 1987/7/6 and 1996/1/31 had a GPT level greater than 30 and an ALB level less than 4? List them by their ID." Examination 조인은 필요 없어. Laboratory 하나만 써도 돼.
- 태그: Laboratory, GPT, ALB, Date, AGGREGATION_LOGIC
- 교정 내용: 오답: SELECT DISTINCT L.ID FROM Laboratory L JOIN Examination E ON L.ID = E.ID WHERE L.Date BETWEEN '1987-07-06' AND '1996-01-31' AND L.GPT > 30 AND L.ALB < 4 / 정답: SELECT DISTINCT ID FROM Laboratory WHERE Date BETWEEN '1987-07-06' AND '1996-01-31' AND GPT > 30 AND ALB < 4

## KB-029
- 상황: "질문: List the diagnosis, patient ID, and age of patients whose hemoglobin level is below 10." DISTINCT가 누락되어 중복된 환자 정보가 발생할 수 있다.
- 태그: Patient, Diagnosis, Laboratory, HGB, JOIN, MISSING_DISTINCT
- 교정 내용: 오답: SELECT P.Diagnosis, P.ID, (STRFTIME('%Y', 'now') - STRFTIME('%Y', P.Birthday)) AS Age FROM Patient P JOIN Laboratory L ON P.ID = L.ID WHERE L.HGB < 10 / 정답: SELECT DISTINCT T1.Diagnosis, T1.ID, STRFTIME('%Y', CURRENT_TIMESTAMP) - STRFTIME('%Y', T1.Birthday) FROM Patient AS T1 INNER JOIN Laboratory AS T2 ON T1.ID = T2.ID WHERE T2.HGB < 10

## KB-030
- 상황: "질문: How many patients with a GOT level greater than 40 have thrombosis?" Thrombosis 컬럼이 잘못된 테이블에서 참조되어 오류가 발생했다.
- 태그: Patient, Thrombosis, Laboratory, GOT, JOIN, WRONG_TABLE
- 교정 내용: 오답: SELECT COUNT(*) FROM Patient P JOIN Laboratory L ON P.ID = L.ID WHERE L.GOT > 40 AND P.Thrombosis = 1 / 정답: SELECT COUNT(T1.ID) FROM Examination AS T1 INNER JOIN Laboratory AS T2 ON T1.ID = T2.ID WHERE T2.GOT > 40 AND T1.Thrombosis = 1

## KB-031
- 상황: "질문: List the diagnoses of patients whose aspartate aminotransferase (GOT) level is above the normal limit, ordered from oldest to youngest by birth date." DISTINCT가 누락되어 중복된 환자 정보가 발생할 수 있다.
- 태그: Patient, Diagnosis, Laboratory, GOT, JOIN, MISSING_DISTINCT
- 교정 내용: 오답: SELECT P.Diagnosis FROM Patient P JOIN Laboratory L ON P.ID = L.ID WHERE L.GOT > 40 ORDER BY P.Birthday ASC / 정답: SELECT DISTINCT T1.Diagnosis FROM Patient AS T1 INNER JOIN Laboratory AS T2 ON T1.ID = T2.ID WHERE T2.GOT > 40 ORDER BY T1.Birthday ASC

## KB-032
- 상황: "질문: Among patients with a serum uric acid level below 7.0, how many have a detectable result for at least one anticardiolipin antibody class?" aCL IgG/IgM/IgA 컬럼이 잘못된 테이블에서 참조되어 오류가 발생했다.
- 태그: Patient, Laboratory, Examination, UA, JOIN, WRONG_TABLE
- 교정 내용: 오답: SELECT COUNT(DISTINCT T1.ID) FROM Patient AS T1 INNER JOIN Laboratory AS T2 ON T1.ID = T2.ID WHERE T2.UA < 7.0 AND (T2.`aCL IgG` > 0 OR T2.`aCL IgM` > 0 OR T2.`aCL IgA` > 0) / 정답: SELECT COUNT(T1.ID) FROM Patient AS T1 INNER JOIN Laboratory AS T2 ON T1.ID = T2.ID INNER JOIN Examination AS T3 ON T1.ID = T3.ID WHERE T2.UA < 7.0 AND (T3.`aCL IgG` > 0 OR T3.`aCL IgM` > 0 OR T3.`aCL IgA` > 0)

## KB-033
- 상황: "질문: What is the rate of decrease in triglyceride levels for female patients from October 1981 to November 1981?" 나눗셈 전에 분자를 REAL로 형변환해야 해.
- 태그: Patient, Laboratory, TG, Date, JOIN, VALUE_ENCODING
- 교정 내용: 오답: SELECT (SUM(CASE WHEN T1.SEX = 'F' AND T2.Date LIKE '1981-10-%' THEN T2.TG ELSE 0 END) - SUM(CASE WHEN T1.SEX = 'F' AND T2.Date LIKE '1981-11-%' THEN T2.TG ELSE 0 END)) / NULLIF(SUM(CASE WHEN T1.SEX = 'F' AND T2.Date LIKE '1981-11-%' THEN T2.TG ELSE 0 END), 0) AS Rate_of_Decrease FROM Patient AS T1 INNER JOIN Laboratory AS T2 ON T1.ID = T2.ID WHERE T1.SEX = 'F' / 정답: SELECT CAST((SUM(CASE WHEN T2.Date LIKE '1981-10-%' THEN T2.TG ELSE 0 END) - SUM(CASE WHEN T2.Date LIKE '1981-11-%' THEN T2.TG ELSE 0 END)) AS REAL) / SUM(CASE WHEN T2.Date LIKE '1981-11-%' THEN T2.TG ELSE 0 END) FROM Patient AS T1 INNER JOIN Laboratory AS T2 ON T1.ID = T2.ID WHERE T1.SEX = 'F'

## KB-034
- 상황: "질문: How many patients first visited the hospital after 1995 and had a platelet count within the normal range?" 날짜 비교 방식이 잘못되어 오류가 발생했다.
- 태그: Patient, Laboratory, PLT, `First Date`, JOIN, DATE_LOGIC
- 교정 내용: 오답: SELECT COUNT(*) FROM Patient AS T1 INNER JOIN Laboratory AS T2 ON T1.ID = T2.ID WHERE T1.`First Date` > '1995-01-01' AND T2.PLT > 150 AND T2.PLT < 400 / 정답: SELECT COUNT(T1.ID) FROM Patient AS T1 INNER JOIN Laboratory AS T2 ON T1.ID = T2.ID WHERE T2.PLT BETWEEN 150 AND 400 AND strftime('%Y', T1.`First Date`) > '1995'
