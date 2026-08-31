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
