## KB-001
- 상황: "질문: For the set of cards with "Ancestor's Chosen" in it, is there a Korean version of it?" 이 시도에서 foreign_data 테이블을 사용한 것이 잘못되었다.
- 태그: cards, name, JOIN, WRONG_TABLE
- 교정 내용: 오답: SELECT st.translation FROM cards c JOIN foreign_data fd ON c.uuid = fd.uuid WHERE c.name = 'Ancestor''s Chosen' AND fd.language = 'Korean' / 정답: SELECT IIF(SUM(CASE WHEN T2.language = 'Korean' AND T2.translation IS NOT NULL THEN 1 ELSE 0 END) > 0, 'YES', 'NO') FROM cards AS T1 INNER JOIN set_translations AS T2 ON T2.setCode = T1.setCode WHERE T1.name = 'Ancestor''s Chosen'

## KB-002
- 상황: "질문: Which card costs more converted mana, "Serra Angel" or "Shrine Keeper"?" 이 시도에서 convertedManaCost 컬럼을 SELECT에 포함시킨 것이 잘못되었다.
- 태그: cards, name, COLUMN_ORDER
- 교정 내용: 오답: SELECT name, convertedManaCost FROM cards WHERE name IN ('Serra Angel', 'Shrine Keeper') ORDER BY convertedManaCost DESC LIMIT 1 / 정답: SELECT name FROM cards WHERE name IN ('Serra Angel', 'Shrine Keeper') ORDER BY convertedManaCost DESC LIMIT 1

## KB-003
- 상황: "질문: Which of these artists have designed a card in the set Coldsnap, Jeremy Jarvis, Aaron Miller or Chippy?" 이 시도에서 setCode를 직접 사용한 것이 잘못되었다.
- 태그: cards, setCode, JOIN, WRONG_COLUMN
- 교정 내용: 오답: SELECT DISTINCT artist FROM cards WHERE setCode = 'Coldsnap' AND artist IN ('Jeremy Jarvis', 'Aaron Miller', 'Chippy') / 정답: SELECT T1.artist FROM cards AS T1 INNER JOIN sets AS T2 ON T2.code = T1.setCode WHERE (T2.name = 'Coldsnap' AND T1.artist = 'Chippy') OR (T2.name = 'Coldsnap' AND T1.artist = 'Aaron Miller') OR (T2.name = 'Coldsnap' AND T1.artist = 'Jeremy Jarvis') GROUP BY T1.artist

## KB-004
- 상황: "질문: How many unknown power cards contain info about the triggered ability" 이 시도에서 text 컬럼을 cards 테이블에서 사용한 것이 잘못되었다.
- 태그: cards, power, rulings, JOIN, WRONG_COLUMN
- 교정 내용: 오답: SELECT COUNT(*) FROM cards WHERE (power IS NULL OR power = '*') AND text LIKE '%triggered ability%' / 정답: SELECT Count(DISTINCT T1.id) FROM cards AS T1 INNER JOIN rulings AS T2 ON T1.uuid = T2.uuid WHERE (T1.power IS NULL OR T1.power = '*') AND T2.text LIKE '%triggered ability%'

## KB-005
- 상황: "질문: What are the borderless cards available without powerful foils?" 이 시도에서 SELECT에 모든 컬럼을 포함시킨 것이 잘못되었다.
- 태그: cards, borderColor, COLUMN_ORDER
- 교정 내용: 오답: SELECT * FROM cards WHERE borderColor = 'borderless' AND (cardKingdomFoilId IS NULL OR cardKingdomId IS NULL) / 정답: SELECT id FROM cards WHERE borderColor = 'borderless' AND (cardKingdomId IS NULL OR cardKingdomId IS NULL)

## KB-006
- 상황: "질문: Among the Artifact cards, which are black color and comes with foreign languague translation?" 이 시도에서 전체 컬럼을 SELECT한 것이 잘못되었다.
- 태그: cards, originalType, colors, foreign_data, COLUMN_ORDER
- 교정 내용: 오답: SELECT c.* FROM cards c JOIN foreign_data f ON c.uuid = f.uuid WHERE c.originalType = 'Artifact' AND c.colors = 'B' / 정답: SELECT DISTINCT T1.name FROM cards AS T1 INNER JOIN foreign_data AS T2 ON T1.uuid = T2.uuid WHERE T1.originalType = 'Artifact' AND T1.colors = 'B'

## KB-007
- 상황: "질문: Name the card and artist with the most ruling information. Also state if the card is a promotional printing." 이 시도에서 GROUP BY 조건이 잘못되었다.
- 태그: cards, rulings, isPromo, GROUP BY, AGGREGATION_LOGIC
- 교정 내용: 오답: SELECT c.name, c.artist, c.isPromo FROM cards c JOIN rulings r ON c.uuid = r.uuid GROUP BY c.uuid HAVING COUNT(r.uuid) = (SELECT MAX(rulings_count) FROM (SELECT COUNT(r.uuid) AS rulings_count FROM cards c JOIN rulings r ON c.uuid = r.uuid GROUP BY c.uuid)) / 정답: SELECT T1.name, T1.artist, T1.isPromo FROM cards AS T1 INNER JOIN rulings AS T2 ON T1.uuid = T2.uuid WHERE T1.isPromo = 1 AND T1.artist = (SELECT artist FROM cards WHERE isPromo = 1 GROUP BY artist HAVING COUNT(DISTINCT uuid) = (SELECT MAX(count_uuid) FROM ( SELECT COUNT(DISTINCT uuid) AS count_uuid FROM cards WHERE isPromo = 1 GROUP BY artist ))) LIMIT 1

## KB-008
- 상황: "질문: What's the Italian name of the set of cards with "Ancestor's Chosen" is in?" 이 시도에서 set_translations 테이블을 잘못 사용한 것이 잘못되었다.
- 태그: set_translations, setCode, JOIN, WRONG_TABLE
- 교정 내용: 오답: SELECT st.translation FROM set_translations st JOIN cards c ON st.setCode = c.setCode WHERE c.name = 'Ancestor''s Chosen' AND st.language = 'Italian' / 정답: SELECT translation FROM set_translations WHERE setCode IN ( SELECT setCode FROM cards WHERE name = 'Ancestor''s Chosen' ) AND language = 'Italian'

## KB-009
- 상황: "질문: What is the percentage of Story Spotlight cards that do not have a text box? List them by their ID." 이 시도에서 GROUP_CONCAT을 사용한 것이 잘못되었다.
- 태그: cards, isStorySpotlight, isTextless, AGGREGATION_LOGIC
- 교정 내용: 오답: SELECT (SUM(CASE WHEN isStorySpotlight = 1 AND isTextless = 0 THEN 1 ELSE 0 END) * 100.0 / COUNT(*)) AS percentage, GROUP_CONCAT(id) AS ids FROM cards / 정답: SELECT CAST(SUM(CASE WHEN T2.isTextless = 0 AND T2.isStorySpotlight = 1 THEN 1 ELSE 0 END) AS REAL) * 100 / COUNT(T1.id) FROM cards AS T1

## KB-010
- 상황: "질문: What percentage of cards without power are in French?" 이 시도에서 LEFT JOIN을 사용한 것이 잘못되었다.
- 태그: cards, power, foreign_data, JOIN, WRONG_TABLE
- 교정 내용: 오답: SELECT (COUNT(CASE WHEN f.language = 'French' THEN 1 END) * 100.0 / COUNT(*)) AS percentage FROM cards c LEFT JOIN foreign_data f ON c.uuid = f.uuid WHERE c.power IS NULL OR c.power = '*' / 정답: SELECT CAST(SUM(CASE WHEN T2.language = 'French' THEN 1 ELSE 0 END) AS REAL) * 100 / COUNT(T1.id) FROM cards AS T1 INNER JOIN foreign_data AS T2 ON T1.uuid = T2.uuid WHERE T1.power IS NULL OR T1.power = '*'
