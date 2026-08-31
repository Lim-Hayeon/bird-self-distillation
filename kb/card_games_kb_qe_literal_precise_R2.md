## KB-001
- 상황: "질문: For the set of cards with "Ancestor's Chosen" in it, is there a Korean version of it?" 이 시도에서 foreign_data 테이블을 사용했으나 set_translations 테이블을 사용해야 했다.
- 태그: cards, name, set_translations, JOIN_LOGIC
- 교정 내용: 오답: SELECT st.translation FROM cards c JOIN foreign_data fd ON c.uuid = fd.uuid WHERE c.name = 'Ancestor''s Chosen' AND fd.language = 'Korean' / 정답: SELECT IIF(SUM(CASE WHEN T2.language = 'Korean' AND T2.translation IS NOT NULL THEN 1 ELSE 0 END) > 0, 'YES', 'NO') FROM cards AS T1 INNER JOIN set_translations AS T2 ON T2.setCode = T1.setCode WHERE T1.name = 'Ancestor''s Chosen'

## KB-002
- 상황: "질문: Which card costs more converted mana, "Serra Angel" or "Shrine Keeper"?" 이 시도에서 convertedManaCost 컬럼을 SELECT에 포함시켰으나 name만 SELECT해야 했다.
- 태그: cards, name, COLUMN_ORDER
- 교정 내용: 오답: SELECT name, convertedManaCost FROM cards WHERE name IN ('Serra Angel', 'Shrine Keeper') ORDER BY convertedManaCost DESC LIMIT 1 / 정답: SELECT name FROM cards WHERE name IN ('Serra Angel', 'Shrine Keeper') ORDER BY convertedManaCost DESC LIMIT 1

## KB-003
- 상황: "질문: Which of these artists have designed a card in the set Coldsnap, Jeremy Jarvis, Aaron Miller or Chippy?" 이 시도에서 cards.setCode를 직접 사용했으나 sets 테이블과 조인하여 sets.name을 사용해야 했다.
- 태그: cards, setCode, sets, JOIN_LOGIC
- 교정 내용: 오답: SELECT DISTINCT artist FROM cards WHERE setCode = 'Coldsnap' AND artist IN ('Jeremy Jarvis', 'Aaron Miller', 'Chippy') / 정답: SELECT T1.artist FROM cards AS T1 INNER JOIN sets AS T2 ON T2.code = T1.setCode WHERE (T2.name = 'Coldsnap' AND T1.artist = 'Chippy') OR (T2.name = 'Coldsnap' AND T1.artist = 'Aaron Miller') OR (T2.name = 'Coldsnap' AND T1.artist = 'Jeremy Jarvis') GROUP BY T1.artist

## KB-004
- 상황: "질문: How many unknown power cards contain info about the triggered ability" 이 시도에서 text 컬럼을 cards 테이블에서 가져오려 했으나 rulings 테이블에서 가져와야 했다.
- 태그: cards, power, rulings, JOIN_LOGIC
- 교정 내용: 오답: SELECT COUNT(*) FROM cards WHERE (power IS NULL OR power = '*') AND text LIKE '%triggered ability%' / 정답: SELECT Count(DISTINCT T1.id) FROM cards AS T1 INNER JOIN rulings AS T2 ON T1.uuid = T2.uuid WHERE (T1.power IS NULL OR T1.power = '*') AND T2.text LIKE '%triggered ability%'

## KB-005
- 상황: "질문: What are the borderless cards available without powerful foils?" 이 시도에서 SELECT에 모든 컬럼을 포함시켰으나 id 컬럼만 반환해야 했다.
- 태그: cards, borderColor, COLUMN_ORDER
- 교정 내용: 오답: SELECT * FROM cards WHERE borderColor = 'borderless' AND (cardKingdomFoilId IS NULL OR cardKingdomId IS NULL) / 정답: SELECT id FROM cards WHERE borderColor = 'borderless' AND (cardKingdomId IS NULL OR cardKingdomId IS NULL)

## KB-006
- 상황: "질문: Among the Artifact cards, which are black color and comes with foreign languague translation?" 이 시도에서 전체 컬럼을 SELECT했으나 name 컬럼만 SELECT해야 했다.
- 태그: cards, originalType, foreign_data, COLUMN_ORDER
- 교정 내용: 오답: SELECT c.* FROM cards c JOIN foreign_data f ON c.uuid = f.uuid WHERE c.originalType = 'Artifact' AND c.colors = 'B' / 정답: SELECT DISTINCT T1.name FROM cards AS T1 INNER JOIN foreign_data AS T2 ON T1.uuid = T2.uuid WHERE T1.originalType = 'Artifact' AND T1.colors = 'B'

## KB-007
- 상황: "질문: Name the card and artist with the most ruling information. Also state if the card is a promotional printing." 이 시도에서 카드 단위로 그룹핑했으나 artist 단위로 그룹핑해야 했다.
- 태그: cards, rulings, isPromo, AGGREGATION_LOGIC
- 교정 내용: 오답: SELECT c.name, c.artist, c.isPromo FROM cards c JOIN rulings r ON c.uuid = r.uuid GROUP BY c.uuid HAVING COUNT(r.uuid) = (SELECT MAX(rulings_count) FROM (SELECT COUNT(r.uuid) AS rulings_count FROM cards c JOIN rulings r ON c.uuid = r.uuid GROUP BY c.uuid)) / 정답: SELECT T1.name, T1.artist, T1.isPromo FROM cards AS T1 INNER JOIN rulings AS T2 ON T1.uuid = T2.uuid WHERE T1.isPromo = 1 AND T1.artist = (SELECT artist FROM cards WHERE isPromo = 1 GROUP BY artist HAVING COUNT(DISTINCT uuid) = (SELECT MAX(count_uuid) FROM ( SELECT COUNT(DISTINCT uuid) AS count_uuid FROM cards WHERE isPromo = 1 GROUP BY artist ))) LIMIT 1

## KB-008
- 상황: "질문: What's the Italian name of the set of cards with "Ancestor's Chosen" is in?" 이 시도에서 set_translations 테이블을 잘못 사용했으나 올바른 서브쿼리를 사용해야 했다.
- 태그: set_translations, cards, SUBQUERY_VS_JOIN
- 교정 내용: 오답: SELECT st.translation FROM set_translations st JOIN cards c ON st.setCode = c.setCode WHERE c.name = 'Ancestor''s Chosen' AND st.language = 'Italian' / 정답: SELECT translation FROM set_translations WHERE setCode IN ( SELECT setCode FROM cards WHERE name = 'Ancestor''s Chosen' ) AND language = 'Italian'

## KB-009
- 상황: "질문: What is the percentage of Story Spotlight cards that do not have a text box? List them by their ID." 이 시도에서 GROUP_CONCAT으로 id 리스트를 반환하려 했으나 퍼센트 값 하나만 SELECT해야 했다.
- 태그: cards, isStorySpotlight, isTextless, AGGREGATION_LOGIC
- 교정 내용: 오답: SELECT (SUM(CASE WHEN isStorySpotlight = 1 AND isTextless = 0 THEN 1 ELSE 0 END) * 100.0 / COUNT(*)) AS percentage, GROUP_CONCAT(id) AS ids FROM cards / 정답: SELECT CAST(SUM(CASE WHEN T2.isTextless = 0 AND T2.isStorySpotlight = 1 THEN 1 ELSE 0 END) AS REAL) * 100 / COUNT(T1.id) FROM cards AS T1

## KB-010
- 상황: "질문: What percentage of cards without power are in French?" 이 시도에서 LEFT JOIN을 사용했으나 INNER JOIN을 사용해야 했다.
- 태그: cards, power, foreign_data, JOIN_LOGIC
- 교정 내용: 오답: SELECT (COUNT(CASE WHEN f.language = 'French' THEN 1 END) * 100.0 / COUNT(*)) AS percentage FROM cards c LEFT JOIN foreign_data f ON c.uuid = f.uuid WHERE c.power IS NULL OR c.power = '*' / 정답: SELECT CAST(SUM(CASE WHEN T2.language = 'French' THEN 1 ELSE 0 END) AS REAL) * 100 / COUNT(T1.id) FROM cards AS T1 INNER JOIN foreign_data AS T2 ON T1.uuid = T2.uuid WHERE T1.power IS NULL OR T1.power = '*'

## KB-011
- 상황: "질문: Indicates the number of cards with pre-modern format, ruling text "This is a triggered mana ability." that do not have multiple faces." 이 시도에서 cards.otherFaceIds를 사용했으나 cards.side를 사용해야 했다.
- 태그: legalities, rulings, cards, side, AGGREGATION_LOGIC
- 교정 내용: 오답: SELECT COUNT(DISTINCT uuid) FROM legalities JOIN rulings ON legalities.uuid = rulings.uuid JOIN cards ON rulings.uuid = cards.uuid WHERE legalities.format = 'premodern' AND rulings.text = 'This is a triggered mana ability.' AND cards.otherFaceIds IS NULL / 정답: SELECT COUNT(T1.id) FROM cards AS T1 INNER JOIN legalities AS T2 ON T1.uuid = T2.uuid INNER JOIN rulings AS T3 ON T1.uuid = T3.uuid WHERE T2.format = 'premodern' AND T3.text = 'This is a triggered mana ability.' AND T1.Side IS NULL

## KB-012
- 상황: "질문: Which foreign language used by "A Pedra Fellwar"?" 이 시도에서 foreign_data.uuid를 사용했으나 foreign_data.name을 직접 사용해야 했다.
- 태그: foreign_data, cards, JOIN_LOGIC
- 교정 내용: 오답: SELECT language FROM foreign_data WHERE uuid = (SELECT uuid FROM cards WHERE name = 'A Pedra Fellwar') / 정답: SELECT DISTINCT language FROM foreign_data WHERE name = 'A Pedra Fellwar'

## KB-013
- 상황: "질문: What is the Italian flavor text of the card "Ancestor's Chosen"?" 이 시도에서 foreign_data.name을 사용했으나 cards.name을 사용해야 했다.
- 태그: foreign_data, cards, JOIN_LOGIC
- 교정 내용: 오답: SELECT flavorText FROM foreign_data WHERE language = 'Italian' AND name = 'Ancestor''s Chosen' / 정답: SELECT T2.flavorText FROM cards AS T1 INNER JOIN foreign_data AS T2 ON T2.uuid = T1.uuid WHERE T1.name = 'Ancestor''s Chosen' AND T2.language = 'Italian'

## KB-014
- 상황: "질문: Lists all types of cards in German." 이 시도에서 DISTINCT를 사용했으나 제거해야 했다.
- 태그: cards, subtypes, supertypes, COLUMN_ORDER
- 교정 내용: 오답: SELECT DISTINCT subtypes, supertypes FROM cards JOIN foreign_data ON cards.uuid = foreign_data.uuid WHERE foreign_data.language = 'German' AND (subtypes IS NOT NULL OR supertypes IS NOT NULL) / 정답: SELECT T1.subtypes, T1.supertypes FROM cards AS T1 INNER JOIN foreign_data AS T2 ON T1.uuid = T2.uuid WHERE T2.language = 'German' AND T1.subtypes IS NOT NULL AND T1.supertypes IS NOT NULL

## KB-015
- 상황: "질문: Please list the Italian text ruling of all the cards in the set Coldsnap." 이 시도에서 rulings 테이블을 사용했으나 foreign_data 테이블을 사용해야 했다.
- 태그: foreign_data, cards, sets, JOIN_LOGIC
- 교정 내용: 오답: SELECT r.text FROM rulings r JOIN cards c ON r.uuid = c.uuid JOIN sets s ON c.setCode = s.code WHERE s.name = 'Coldsnap' AND r.language = 'Italian' / 정답: SELECT DISTINCT T1.text FROM foreign_data AS T1 INNER JOIN cards AS T2 ON T2.uuid = T1.uuid INNER JOIN sets AS T3 ON T3.code = T2.setCode WHERE T3.name = 'Coldsnap' AND T1.language = 'Italian'

## KB-016
- 상황: "질문: Find all cards illustrated by Stephen Daniel and describe the text of the ruling of these cards. State if these cards have missing or degraded properties and values." 이 시도에서 CASE 문을 사용했으나 hasContentWarning 값을 직접 반환해야 했다.
- 태그: cards, rulings, hasContentWarning, AGGREGATION_LOGIC
- 교정 내용: 오답: SELECT c.id, r.text, CASE WHEN c.hasContentWarning = 1 THEN 'Missing or degraded properties and values' ELSE 'No missing or degraded properties and values' END AS property_status FROM cards c JOIN rulings r ON c.uuid = r.uuid WHERE c.artist = 'Stephen Daniele' / 정답: SELECT T1.id, T2.text, T1.hasContentWarning FROM cards AS T1 INNER JOIN rulings AS T2 ON T1.uuid = T2.uuid WHERE T1.artist = 'Stephen Daniele'

## KB-017
- 상황: "질문: Did the set of cards with "Angel of Mercy" appear on Magic: The Gathering Online?" 이 시도에서 mtgoCode 조건을 WHERE절에 넣었으나 SELECT에서 IIF로 판단해야 했다.
- 태그: cards, sets, mtgoCode, AGGREGATION_LOGIC
- 교정 내용: 오답: SELECT DISTINCT s.name FROM cards c JOIN sets s ON c.setCode = s.code WHERE c.name = 'Angel of Mercy' AND s.mtgoCode IS NOT NULL / 정답: SELECT IIF(T2.mtgoCode IS NOT NULL, 'YES', 'NO') FROM cards AS T1 INNER JOIN sets AS T2 ON T2.code = T1.setCode WHERE T1.name = 'Angel of Mercy'

## KB-018
- 상황: "질문: What percentage of cards with format commander and legal status do not have a content warning?" 이 시도에서 status 값을 소문자 'legal'로 사용했으나 대문자 'Legal'로 사용해야 했다.
- 태그: cards, legalities, hasContentWarning, AGGREGATION_LOGIC
- 교정 내용: 오답: SELECT CAST(COUNT(CASE WHEN l.status = 'legal' AND l.format = 'commander' AND c.hasContentWarning = 0 THEN 1 END) AS FLOAT) / COUNT(CASE WHEN l.status = 'legal' AND l.format = 'commander' THEN 1 END) * 100 AS percentage FROM cards c JOIN legalities l ON c.uuid = l.uuid / 정답: SELECT CAST(SUM(CASE WHEN T1.hasContentWarning = 0 THEN 1 ELSE 0 END) AS REAL) * 100 / COUNT(T1.id) FROM cards AS T1 INNER JOIN legalities AS T2 ON T1.uuid = T2.uuid WHERE T2.format = 'commander' AND T2.status = 'Legal'

## KB-019
- 상황: "질문: How many cards with original type of "Summon - Angel" have subtype other than "Angel"?" 이 시도에서 subtypes NOT LIKE '%Angel%'를 사용했으나 subtypes != 'Angel'로 정확히 비교해야 했다.
- 태그: cards, originalType, subtypes, AGGREGATION_LOGIC
- 교정 내용: 오답: SELECT COUNT(*) FROM cards WHERE originalType = 'Summon - Angel' AND subtypes NOT LIKE '%Angel%' / 정답: SELECT COUNT(id) FROM cards WHERE originalType = 'Summon - Angel' AND subtypes != 'Angel'
