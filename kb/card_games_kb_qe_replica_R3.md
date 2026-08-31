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

## KB-011
- 상황: "질문: Indicates the number of cards with pre-modern format, ruling text "This is a triggered mana ability." that do not have multiple faces." 이 시도에서 otherFaceIds 컬럼을 사용한 것이 잘못되었다.
- 태그: legalities, rulings, cards, side, JOIN, WRONG_COLUMN
- 교정 내용: 오답: SELECT COUNT(DISTINCT uuid) FROM legalities JOIN rulings ON legalities.uuid = rulings.uuid JOIN cards ON rulings.uuid = cards.uuid WHERE legalities.format = 'premodern' AND rulings.text = 'This is a triggered mana ability.' AND cards.otherFaceIds IS NULL / 정답: SELECT COUNT(T1.id) FROM cards AS T1 INNER JOIN legalities AS T2 ON T1.uuid = T2.uuid INNER JOIN rulings AS T3 ON T1.uuid = T3.uuid WHERE T2.format = 'premodern' AND T3.text = 'This is a triggered mana ability.' AND T1.Side IS NULL

## KB-012
- 상황: "질문: Which foreign language used by "A Pedra Fellwar"?" 이 시도에서 foreign_data 테이블을 잘못 사용한 것이 잘못되었다.
- 태그: foreign_data, name, JOIN, WRONG_TABLE
- 교정 내용: 오답: SELECT language FROM foreign_data WHERE uuid = (SELECT uuid FROM cards WHERE name = 'A Pedra Fellwar') / 정답: SELECT DISTINCT language FROM foreign_data WHERE name = 'A Pedra Fellwar'

## KB-013
- 상황: "질문: What is the Italian flavor text of the card "Ancestor's Chosen"?" 이 시도에서 foreign_data 테이블을 잘못 사용한 것이 잘못되었다.
- 태그: foreign_data, flavorText, JOIN, WRONG_TABLE
- 교정 내용: 오답: SELECT flavorText FROM foreign_data WHERE language = 'Italian' AND name = 'Ancestor''s Chosen' / 정답: SELECT T2.flavorText FROM cards AS T1 INNER JOIN foreign_data AS T2 ON T2.uuid = T1.uuid WHERE T1.name = 'Ancestor''s Chosen' AND T2.language = 'Italian'

## KB-014
- 상황: "질문: Lists all types of cards in German." 이 시도에서 DISTINCT를 사용한 것이 잘못되었다.
- 태그: cards, subtypes, supertypes, JOIN, COLUMN_ORDER
- 교정 내용: 오답: SELECT DISTINCT subtypes, supertypes FROM cards JOIN foreign_data ON cards.uuid = foreign_data.uuid WHERE foreign_data.language = 'German' AND (subtypes IS NOT NULL OR supertypes IS NOT NULL) / 정답: SELECT T1.subtypes, T1.supertypes FROM cards AS T1 INNER JOIN foreign_data AS T2 ON T1.uuid = T2.uuid WHERE T2.language = 'German' AND T1.subtypes IS NOT NULL AND T1.supertypes IS NOT NULL

## KB-015
- 상황: "질문: Please list the Italian text ruling of all the cards in the set Coldsnap." 이 시도에서 rulings 테이블을 잘못 사용한 것이 잘못되었다.
- 태그: rulings, foreign_data, JOIN, WRONG_TABLE
- 교정 내용: 오답: SELECT r.text FROM rulings r JOIN cards c ON r.uuid = c.uuid JOIN sets s ON c.setCode = s.code WHERE s.name = 'Coldsnap' AND r.language = 'Italian' / 정답: SELECT DISTINCT T1.text FROM foreign_data AS T1 INNER JOIN cards AS T2 ON T2.uuid = T1.uuid INNER JOIN sets AS T3 ON T3.code = T2.setCode WHERE T3.name = 'Coldsnap' AND T1.language = 'Italian'

## KB-016
- 상황: "질문: Find all cards illustrated by Stephen Daniel and describe the text of the ruling of these cards. State if these cards have missing or degraded properties and values." 이 시도에서 CASE 문을 사용한 것이 잘못되었다.
- 태그: cards, rulings, hasContentWarning, JOIN, COLUMN_ORDER
- 교정 내용: 오답: SELECT c.id, r.text, CASE WHEN c.hasContentWarning = 1 THEN 'Missing or degraded properties and values' ELSE 'No missing or degraded properties and values' END AS property_status FROM cards c JOIN rulings r ON c.uuid = r.uuid WHERE c.artist = 'Stephen Daniele' / 정답: SELECT T1.id, T2.text, T1.hasContentWarning FROM cards AS T1 INNER JOIN rulings AS T2 ON T1.uuid = T2.uuid WHERE T1.artist = 'Stephen Daniele'

## KB-017
- 상황: "질문: Did the set of cards with "Angel of Mercy" appear on Magic: The Gathering Online?" 이 시도에서 mtgoCode 조건을 잘못 사용한 것이 잘못되었다.
- 태그: cards, sets, mtgoCode, JOIN, AGGREGATION_LOGIC
- 교정 내용: 오답: SELECT DISTINCT s.name FROM cards c JOIN sets s ON c.setCode = s.code WHERE c.name = 'Angel of Mercy' AND s.mtgoCode IS NOT NULL / 정답: SELECT IIF(T2.mtgoCode IS NOT NULL, 'YES', 'NO') FROM cards AS T1 INNER JOIN sets AS T2 ON T2.code = T1.setCode WHERE T1.name = 'Angel of Mercy'

## KB-018
- 상황: "질문: What percentage of cards with format commander and legal status do not have a content warning?" 이 시도에서 status 값을 잘못 사용한 것이 잘못되었다.
- 태그: cards, legalities, hasContentWarning, JOIN, AGGREGATION_LOGIC
- 교정 내용: 오답: SELECT CAST(COUNT(CASE WHEN l.status = 'legal' AND l.format = 'commander' AND c.hasContentWarning = 0 THEN 1 END) AS FLOAT) / COUNT(CASE WHEN l.status = 'legal' AND l.format = 'commander' THEN 1 END) * 100 AS percentage FROM cards c JOIN legalities l ON c.uuid = l.uuid / 정답: SELECT CAST(SUM(CASE WHEN T1.hasContentWarning = 0 THEN 1 ELSE 0 END) AS REAL) * 100 / COUNT(T1.id) FROM cards AS T1 INNER JOIN legalities AS T2 ON T1.uuid = T2.uuid WHERE T2.format = 'commander' AND T2.status = 'Legal'

## KB-019
- 상황: "질문: How many cards with original type of "Summon - Angel" have subtype other than "Angel"?" 이 시도에서 subtypes 조건을 잘못 사용한 것이 잘못되었다.
- 태그: cards, originalType, subtypes, COLUMN_ORDER
- 교정 내용: 오답: SELECT COUNT(*) FROM cards WHERE originalType = 'Summon - Angel' AND subtypes NOT LIKE '%Angel%' / 정답: SELECT COUNT(id) FROM cards WHERE originalType = 'Summon - Angel' AND subtypes != 'Angel'

## KB-020
- 상황: "질문: What is the foreign name of the card in French of type Creature, normal layout and black border color, by artist Matthew D. Wilson?" 이 시도에서 type 컬럼을 잘못 사용한 것이 잘못되었다.
- 태그: cards, types, foreign_data, JOIN, WRONG_COLUMN
- 교정 내용: 오답: SELECT DISTINCT fd.name FROM foreign_data fd JOIN cards c ON fd.uuid = c.uuid WHERE fd.language = 'French' AND c.type = 'Creature' AND c.layout = 'normal' AND c.borderColor = 'black' AND c.artist = 'Matthew D. Wilson' / 정답: SELECT name FROM foreign_data WHERE uuid IN ( SELECT uuid FROM cards WHERE types = 'Creature' AND layout = 'normal' AND borderColor = 'black' AND artist = 'Matthew D. Wilson' ) AND language = 'French'

## KB-021
- 상황: "질문: How many of the banned cards are white border?" 이 시도에서 JOIN 조건이 잘못되었다.
- 태그: cards, legalities, borderColor, JOIN, WRONG_TABLE
- 교정 내용: 오답: SELECT COUNT(id) FROM cards WHERE borderColor = 'white' AND uuid IN (SELECT uuid FROM legalities WHERE status = 'Banned') / 정답: SELECT COUNT(T1.id) FROM cards AS T1 INNER JOIN legalities AS T2 ON T1.uuid = T2.uuid WHERE T2.status = 'Banned' AND T1.borderColor = 'white'

## KB-022
- 상황: "질문: Which cards are ranked 1st on EDHRec? List all of the cards name and its banned play format." 이 시도에서 GROUP BY 조건이 잘못되었다.
- 태그: cards, legalities, edhrecRank, GROUP BY, AGGREGATION_LOGIC
- 교정 내용: 오답: SELECT c.name, l.format FROM cards c JOIN legalities l ON c.uuid = l.uuid WHERE c.edhrecRank = 1 AND l.status = 'Banned' / 정답: SELECT T1.name, T2.format FROM cards AS T1 INNER JOIN legalities AS T2 ON T2.uuid = T1.uuid WHERE T1.edhrecRank = 1 AND T2.status = 'Banned' GROUP BY T1.name, T2.format

## KB-023
- 상황: "질문: For artifact type of cards that do not have multiple faces on the same card, state its legalities status for vintage play format." 이 시도에서 type 컬럼을 잘못 사용한 것이 잘못되었다.
- 태그: cards, legalities, side, JOIN, WRONG_COLUMN
- 교정 내용: 오답: SELECT l.status FROM cards c JOIN legalities l ON c.uuid = l.uuid WHERE c.type = 'Artifact' AND c.side IS NULL AND l.format = 'vintage' / 정답: SELECT DISTINCT T2.status FROM cards AS T1 INNER JOIN legalities AS T2 ON T1.uuid = T2.uuid WHERE T1.type = 'Artifact' AND T2.format = 'vintage' AND T1.side IS NULL

## KB-024
- 상황: "질문: Please list the Italian names of the cards in the set Coldsnap with the highest converted mana cost." 이 시도에서 DISTINCT를 잘못 사용한 것이 잘못되었다.
- 태그: foreign_data, cards, sets, COLUMN_ORDER
- 교정 내용: 오답: SELECT DISTINCT fd.name FROM foreign_data fd JOIN cards c ON fd.uuid = c.uuid JOIN sets s ON c.setCode = s.code WHERE s.name = 'Coldsnap' AND fd.language = 'Italian' AND c.convertedManaCost = ( SELECT MAX(convertedManaCost) FROM cards WHERE setCode = s.code ) / 정답: SELECT T2.name FROM foreign_data AS T1 INNER JOIN cards AS T2 ON T2.uuid = T1.uuid INNER JOIN sets AS T3 ON T3.code = T2.setCode WHERE T3.name = 'Coldsnap' AND T1.language = 'Italian' ORDER BY T2.convertedManaCost DESC

## KB-025
- 상황: "질문: List all the frame styles and cards Allen Williams worked on and find any banned cards if there are any." 이 시도에서 DISTINCT를 잘못 사용한 것이 잘못되었다.
- 태그: cards, legalities, artist, COLUMN_ORDER
- 교정 내용: 오답: SELECT DISTINCT c.frameVersion, c.name FROM cards c JOIN legalities l ON c.uuid = l.uuid WHERE c.artist = 'Allen Williams' AND l.status = 'Banned' / 정답: SELECT DISTINCT T1.frameVersion, T1.name , IIF(T2.status = 'Banned', T1.name, 'NO') FROM cards AS T1 INNER JOIN legalities AS T2 ON T1.uuid = T2.uuid WHERE T1.artist = 'Allen Williams'

## KB-026
- 상황: "질문: What is the border color of card "Ancestor's Chosen"?" 이 시도에서 DISTINCT를 잘못 사용한 것이 잘못되었다.
- 태그: cards, borderColor, COLUMN_ORDER
- 교정 내용: 오답: SELECT borderColor FROM cards WHERE name = 'Ancestor''s Chosen' / 정답: SELECT DISTINCT borderColor FROM cards WHERE name = 'Ancestor''s Chosen'

## KB-027
- 상황: "질문: Is the set of cards with Adarkar Valkyrie only available outside the United States?" 이 시도에서 SELECT 조건이 잘못 사용된 것이 잘못되었다.
- 태그: cards, sets, isForeignOnly, JOIN, WRONG_COLUMN
- 교정 내용: 오답: SELECT sets.isForeignOnly FROM cards JOIN sets ON cards.setCode = sets.code WHERE cards.name = 'Adarkar Valkyrie' AND sets.isForeignOnly = 1 / 정답: SELECT IIF(isForeignOnly = 1, 'YES', 'NO') FROM cards AS T1 INNER JOIN sets AS T2 ON T2.code = T1.setCode WHERE T1.name = 'Adarkar Valkyrie'


## KB-028
- 상황: "질문: Among the sets that contain a card named "Sol Ring", is there a Japanese translation available for the set name?" 이 시도에서 set_translations 테이블을 사용하지 않은 것이 잘못되었다.
- 태그: sets, name, set_translations, JOIN, WRONG_TABLE
- 교정 내용: 오답: SELECT IIF(SUM(CASE WHEN T2.language = 'Japanese' AND T2.translation IS NOT NULL THEN 1 ELSE 0 END) > 0, 'YES', 'NO') FROM sets AS T1 INNER JOIN cards AS T2 ON T1.code = T2.setCode WHERE T2.name = 'Sol Ring' / 정답: SELECT IIF(SUM(CASE WHEN T2.language = 'Japanese' AND T2.translation IS NOT NULL THEN 1 ELSE 0 END) > 0, 'YES', 'NO') FROM cards AS T1 INNER JOIN set_translations AS T2 ON T2.setCode = T1.setCode WHERE T1.name = 'Sol Ring'

## KB-029
- 상황: "질문: Which black-bordered cards have no Magic Online foil identifier or no TCGplayer product listing?" 이 시도에서 SELECT에 카드 이름을 포함시킨 것이 잘못되었다.
- 태그: cards, borderColor, mtgoFoilId, tcgplayerProductId, COLUMN_ORDER
- 교정 내용: 오답: SELECT name FROM cards WHERE borderColor = 'black' AND (mtgoFoilId IS NULL OR tcgplayerProductId IS NULL) / 정답: SELECT id FROM cards WHERE borderColor = 'black' AND (mtgoFoilId IS NULL OR tcgplayerProductId IS NULL)

## KB-030
- 상황: "질문: Identify a card and its artist that has ruling records, where the artist has the largest number of distinct cards that are not online-only. Also indicate whether the card is online-only." 이 시도에서 GROUP BY 조건이 잘못되었다.
- 태그: cards, rulings, isOnlineOnly, GROUP BY, AGGREGATION_LOGIC
- 교정 내용: 오답: SELECT c.name, c.artist, c.isOnlineOnly FROM cards c JOIN rulings r ON c.uuid = r.uuid WHERE c.isOnlineOnly = 0 GROUP BY c.artist HAVING COUNT(DISTINCT c.uuid) = (SELECT MAX(card_count) FROM (SELECT COUNT(DISTINCT uuid) AS card_count FROM cards WHERE isOnlineOnly = 0 GROUP BY artist)) LIMIT 1 / 정답: SELECT T1.name, T1.artist, T1.isOnlineOnly FROM cards AS T1 INNER JOIN rulings AS T2 ON T1.uuid = T2.uuid WHERE T1.isOnlineOnly = 0 AND T1.artist = (SELECT artist FROM cards WHERE isOnlineOnly = 0 GROUP BY artist HAVING COUNT(DISTINCT uuid) = (SELECT MAX(count_uuid) FROM ( SELECT COUNT(DISTINCT uuid) AS count_uuid FROM cards WHERE isOnlineOnly = 0 GROUP BY artist ))) LIMIT 1

## KB-031
- 상황: "질문: Among cards with no toughness value, what percentage have a German entry?" 이 시도에서 COUNT 조건이 잘못되었다.
- 태그: cards, toughness, foreign_data, AGGREGATION_LOGIC
- 교정 내용: 오답: SELECT CAST(SUM(CASE WHEN T1.toughness IS NULL OR T1.toughness = '*' THEN 1 ELSE 0 END) AS REAL) * 100 / COUNT(T1.toughness) FROM cards AS T1 INNER JOIN foreign_data AS T2 ON T1.uuid = T2.uuid WHERE T2.language = 'German' AND (T1.toughness IS NULL OR T1.toughness = '*') / 정답: SELECT CAST(SUM(CASE WHEN T2.language = 'German' THEN 1 ELSE 0 END) AS REAL) * 100 / COUNT(T1.id) FROM cards AS T1 INNER JOIN foreign_data AS T2 ON T1.uuid = T2.uuid WHERE T1.toughness IS NULL OR T1.toughness = '*'

## KB-032
- 상황: "질문: How many card records are available in foil, have a dated ruling, and are legal in at least one format?" 이 시도에서 COUNT에 DISTINCT를 사용한 것이 잘못되었다.
- 태그: cards, rulings, legalities, AGGREGATION_LOGIC
- 교정 내용: 오답: SELECT COUNT(DISTINCT T1.id) FROM cards AS T1 INNER JOIN rulings AS T2 ON T1.uuid = T2.uuid INNER JOIN legalities AS T3 ON T1.uuid = T3.uuid WHERE T1.hasFoil = 1 AND T2.date IS NOT NULL AND T3.status = 'Legal' / 정답: SELECT COUNT(T1.id) FROM cards AS T1 INNER JOIN legalities AS T2 ON T1.uuid = T2.uuid INNER JOIN rulings AS T3 ON T1.uuid = T3.uuid WHERE T1.hasFoil = 1 AND T2.status = 'Legal' AND T3.date IS NOT NULL

## KB-033
- 상황: "질문: Show the names and card types of cards available in French." 이 시도에서 SELECT에 잘못된 테이블 컬럼을 사용한 것이 잘못되었다.
- 태그: cards, foreign_data, language, COLUMN_ORDER
- 교정 내용: 오답: SELECT DISTINCT fd.name, c.type FROM foreign_data fd JOIN cards c ON fd.uuid = c.uuid WHERE fd.language = 'French' AND c.name IS NOT NULL AND c.type IS NOT NULL / 정답: SELECT c.name, c.type FROM foreign_data fd JOIN cards c ON fd.uuid = c.uuid WHERE fd.language = 'French' AND c.name IS NOT NULL AND c.type IS NOT NULL

## KB-034
- 상황: "질문: Among promotional cards, what percentage have German-language entries?" 이 시도에서 JOIN 조건이 잘못되었다.
- 태그: cards, foreign_data, isPromo, JOIN, WRONG_TABLE
- 교정 내용: 오답: SELECT CAST(SUM(CASE WHEN fd.language = 'German' THEN 1 ELSE 0 END) AS REAL) * 100 / COUNT(T1.id) FROM cards AS T1 LEFT JOIN foreign_data AS fd ON T1.uuid = fd.uuid WHERE T1.isPromo = 1 / 정답: SELECT CAST(SUM(CASE WHEN fd.language = 'German' THEN 1 ELSE 0 END) AS REAL) * 100 / COUNT(T1.id) FROM cards AS T1 INNER JOIN foreign_data AS fd ON T1.uuid = fd.uuid WHERE T1.isPromo = 1

## KB-035
- 상황: "질문: Show the names of cards with an EDHRec rank of 2, along with every format in which they are legal." 이 시도에서 GROUP BY 조건이 잘못되었다.
- 태그: cards, legalities, edhrecRank, GROUP BY, AGGREGATION_LOGIC
- 교정 내용: 오답: SELECT c.name, l.format FROM cards c INNER JOIN legalities l ON c.uuid = l.uuid WHERE c.edhrecRank = 2 AND l.status = 'Legal' GROUP BY c.name, l.format / 정답: SELECT T1.name, T2.format FROM cards AS T1 INNER JOIN legalities AS T2 ON T2.uuid = T1.uuid WHERE T1.edhrecRank = 2 AND T2.status = 'Legal' GROUP BY T1.name, T2.format

## KB-036
- 상황: "질문: Which language is listed for the 145-card set in the Zendikar block?" 이 시도에서 SELECT에 DISTINCT를 사용한 것이 잘못되었다.
- 태그: sets, block, baseSetSize, set_translations, COLUMN_ORDER
- 교정 내용: 오답: SELECT DISTINCT st.language FROM sets s JOIN set_translations st ON s.code = st.setCode WHERE s.baseSetSize = 145 / 정답: SELECT st.language FROM sets s JOIN set_translations st ON s.code = st.setCode WHERE s.baseSetSize = 145 AND s.block = 'Zendikar'

## KB-037
- 상황: "질문: For cards illustrated by Chris Rahn, show each frame version and card name, indicating the card name when its legality status is Banned and NO otherwise." 이 시도에서 SELECT에 DISTINCT를 사용한 것이 잘못되었다.
- 태그: cards, legalities, artist, COLUMN_ORDER
- 교정 내용: 오답: SELECT c.frameVersion, c.name, IIF(l.status = 'Banned', c.name, 'NO') AS legality_status FROM cards c JOIN legalities l ON c.uuid = l.uuid WHERE c.artist = 'Chris Rahn' / 정답: SELECT DISTINCT c.frameVersion, c.name, IIF(l.status = 'Banned', c.name, 'NO') AS legality_status FROM cards c JOIN legalities l ON c.uuid = l.uuid WHERE c.artist = 'Chris Rahn'

## KB-038
- 상황: "질문: What is the rarity of the card "Black Lotus"?" 이 시도에서 SELECT에 DISTINCT를 사용한 것이 잘못되었다.
- 태그: cards, name, rarity, COLUMN_ORDER
- 교정 내용: 오답: SELECT rarity FROM cards WHERE name = 'Black Lotus' / 정답: SELECT DISTINCT rarity FROM cards WHERE name = 'Black Lotus'

## KB-039
- 상황: "질문: Is the set containing Amugaba available in the United States?" 이 시도에서 SELECT 조건이 잘못 사용된 것이 잘못되었다.
- 태그: sets, cards, isForeignOnly, JOIN, COLUMN_ORDER
- 교정 내용: 오답: SELECT s.name FROM sets s JOIN cards c ON s.code = c.setCode WHERE c.name = 'Amugaba' AND s.isForeignOnly = 0 / 정답: SELECT IIF(isForeignOnly = 0, 'YES', 'NO') FROM cards AS T1 INNER JOIN sets AS T2 ON T2.code = T1.setCode WHERE T1.name = 'Amugaba'

## KB-040
- 상황: "질문: Which red Instant cards have entries in the foreign-language data?" 이 시도에서 카드의 식별자(`id`) 대신 카드의 이름(`name`)이 출력되도록 컬럼을 수정해야 했다.
- 태그: cards, originalType, colors, foreign_data, JOIN, COLUMN_ORDER
- 교정 내용: 오답: SELECT DISTINCT c.id FROM cards c INNER JOIN foreign_data fd ON c.uuid = fd.uuid WHERE c.originalType = 'Instant' AND c.colors = 'R' / 정답: SELECT DISTINCT T1.name FROM cards AS T1 INNER JOIN foreign_data AS T2 ON T1.uuid = T2.uuid WHERE T1.originalType = 'Instant' AND T1.colors = 'R'

## KB-041
- 상황: "질문: What percentage of cards with no toughness have a German translation?" 이 시도에서 `WHERE` 절에서 `T2.language = 'German'` 필터를 제거해야 했다.
- 태그: cards, toughness, foreign_data, AGGREGATION_LOGIC
- 교정 내용: 오답: SELECT CAST(SUM(CASE WHEN T1.toughness IS NULL OR T1.toughness = '*' THEN 1 ELSE 0 END) AS REAL) * 100 / COUNT(T1.id) FROM cards AS T1 INNER JOIN foreign_data AS T2 ON T1.uuid = T2.uuid WHERE T2.language = 'German' AND (T1.toughness IS NULL OR T1.toughness = '*') / 정답: SELECT CAST(SUM(CASE WHEN T2.language = 'German' THEN 1 ELSE 0 END) AS REAL) * 100 / COUNT(T1.id) FROM cards AS T1 INNER JOIN foreign_data AS T2 ON T1.uuid = T2.uuid WHERE T1.toughness IS NULL OR T1.toughness = '*'

## KB-042
- 상황: "질문: Which artists illustrated common white cards with a normal layout that are available in foil?" 이 시도에서 `SELECT` 절에서 `DISTINCT` 키워드를 제거해야 했다.
- 태그: cards, colors, layout, hasFoil, rarity, COLUMN_ORDER
- 교정 내용: 오답: SELECT DISTINCT artist FROM cards WHERE colors = 'W' AND layout = 'normal' AND hasFoil = 1 AND rarity = 'common' / 정답: SELECT artist FROM cards WHERE colors = 'W' AND rarity = 'common' AND hasFoil = 1 AND layout = 'normal'

## KB-043
- 상황: "질문: Retrieve the French card text entries for every card from the Mirrodin set." 이 시도에서 `SELECT` 절에 `DISTINCT` 키워드를 추가해야 했다.
- 태그: foreign_data, cards, sets, COLUMN_ORDER
- 교정 내용: 오답: SELECT fd.text FROM foreign_data fd JOIN cards c ON fd.uuid = c.uuid JOIN sets s ON c.setCode = s.code WHERE s.name = 'Mirrodin' AND fd.language = 'French' / 정답: SELECT DISTINCT T1.text FROM foreign_data AS T1 INNER JOIN cards AS T2 ON T2.uuid = T1.uuid INNER JOIN sets AS T3 ON T3.code = T2.setCode WHERE T3.name = 'Mirrodin' AND T1.language = 'French'

## KB-044
- 상황: "질문: How many cards are Instants and have a border color other than black?" 이 시도에서 `COUNT(*)` 대신 `COUNT(id)`를 사용해야 했다.
- 태그: cards, type, borderColor, AGGREGATION_LOGIC
- 교정 내용: 오답: SELECT COUNT(*) FROM cards WHERE types LIKE '%Instant%' AND borderColor != 'black' / 정답: SELECT COUNT(id) FROM cards WHERE type = 'Instant' AND borderColor != 'black'

## KB-045
- 상황: "질문: Which languages are listed as translations for the 145-card set in the Zendikar block?" 이 시도에서 서브쿼리 대신 `sets` 테이블과 `set_translations` 테이블을 조인해야 했다.
- 태그: sets, block, baseSetSize, set_translations, COLUMN_ORDER
- 교정 내용: 오답: SELECT DISTINCT language FROM set_translations WHERE setCode IN (SELECT code FROM sets WHERE baseSetSize = 145) / 정답: SELECT DISTINCT T2.language FROM sets AS T1 INNER JOIN set_translations AS T2 ON T1.code = T2.setCode WHERE T1.block = 'Zendikar' AND T1.baseSetSize = 145

## KB-046
- 상황: "질문: List the French names of cards from the Time Spiral set, ordered from the greatest converted mana cost downward." 이 시도에서 서브쿼리 대신 `sets` 테이블을 `INNER JOIN`으로 직접 조인해야 했다.
- 태그: foreign_data, cards, sets, COLUMN_ORDER
- 교정 내용: 오답: SELECT fd.name FROM foreign_data fd JOIN cards c ON fd.uuid = c.uuid WHERE c.setCode = (SELECT code FROM sets WHERE name = 'Time Spiral') AND fd.language = 'French' ORDER BY c.convertedManaCost DESC / 정답: SELECT T2.name FROM foreign_data AS T1 INNER JOIN cards AS T2 ON T2.uuid = T1.uuid INNER JOIN sets AS T3 ON T3.code = T2.setCode WHERE T3.name = 'Time Spiral' AND T1.language = 'French' ORDER BY T2.convertedManaCost DESC

## KB-047
- 상황: "질문: How many cards have common rarity?" 이 시도에서 `WHERE` 절의 희귀도(`rarity`) 조건값을 대문자 `'Common'` 대신 소문자 `'common'`으로 변경해야 했다.
- 태그: cards, rarity, AGGREGATION_LOGIC
- 교정 내용: 오답: SELECT COUNT(*) FROM cards WHERE rarity = 'Common' / 정답: SELECT COUNT(*) FROM cards WHERE rarity = 'common'

## KB-048
- 상황: "질문: Show each frame version and card illustrated by John Avon, indicating whether the card is banned." 이 시도에서 `LEFT JOIN` 대신 `INNER JOIN`을 사용해야 했다.
- 태그: cards, legalities, artist, COLUMN_ORDER
- 교정 내용: 오답: SELECT DISTINCT frameVersion, cards.name, legalities.status FROM cards LEFT JOIN legalities ON cards.uuid = legalities.uuid WHERE cards.artist = 'John Avon' / 정답: SELECT DISTINCT T1.frameVersion, T1.name, IIF(T2.status = 'Banned', T1.name, 'NO') FROM cards AS T1 INNER JOIN legalities AS T2 ON T1.uuid = T2.uuid WHERE T1.artist = 'John Avon'
