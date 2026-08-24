## KB-001
- 상황: 특정 카드의 원래 타입이 "Summon - Angel"인 카드 중에서 서브타입이 "Angel"이 아닌 카드의 수를 구하는 질문
- 태그: cards, originalType, subtypes, COUNT, AGGREGATION_LOGIC
- 교정 내용: 원래는 subtypes NOT LIKE '%Angel%'로 조건을 설정했으나, 정확한 일치 비교를 위해 subtypes != 'Angel'로 수정해야 했다.
- 예외: 없음

## KB-002
- 상황: 특정 카드의 이름이 "Angel of Mercy"인 카드가 Magic: The Gathering Online에 등장하는지 여부를 확인하는 질문
- 태그: cards, sets, mtgoCode, IIF, JOIN_LOGIC
- 교정 내용: 처음에는 mtgoCode가 NULL인지 여부를 WHERE절에서 판단하려 했으나, SELECT문에서 IIF로 'YES'/'NO'로 반환해야 한다는 힌트를 받아 수정했다.
- 예외: 없음

## KB-003
- 상황: 특정 카드의 포맷이 commander이고 법적 상태가 legal인 카드 중에서 콘텐츠 경고가 없는 카드의 비율을 구하는 질문
- 태그: cards, legalities, hasContentWarning, COUNT, AGGREGATION_LOGIC
- 교정 내용: 처음에는 status 값이 소문자 'legal'로 저장되어 있다고 잘못 판단했으나, 대문자 'Legal'로 저장되어 있다는 힌트를 받아 수정했다. 또한, WHERE절에서 format과 status를 먼저 필터링한 후 비율을 계산해야 한다.
- 예외: 없음

## KB-004
- 상황: 특정 카드의 이름이 "Ancestor's Chosen"인 카드의 이탈리아어 플레버 텍스트를 찾는 질문
- 태그: foreign_data, cards, flavorText, language, JOIN_LOGIC
- 교정 내용: 처음에는 foreign_data 테이블에서 language와 name을 조건으로 사용했으나, cards 테이블에서 해당 카드의 uuid를 찾은 후 foreign_data와 조인하여 language가 'Italian'인 행을 찾아야 한다는 힌트를 받아 수정했다.
- 예외: 없음

## KB-005
- 상황: 특정 카드의 이름이 "A Pedra Fellwar"인 카드의 사용된 외국어를 찾는 질문
- 태그: foreign_data, cards, language, name, JOIN_LOGIC
- 교정 내용: 처음에는 foreign_data 테이블에서 uuid를 사용하여 찾으려 했으나, foreign_data.name에서 직접 찾고 DISTINCT를 붙여야 한다는 힌트를 받아 수정했다.
- 예외: 없음

## KB-006
- 상황: 특정 카드의 포맷이 pre-modern이고, 특정 규칙 텍스트를 가진 카드 중에서 다중 면이 없는 카드의 수를 구하는 질문
- 태그: legalities, rulings, cards, format, text, side, COUNT, AGGREGATION_LOGIC
- 교정 내용: 처음에는 cards 테이블의 otherFaceIds를 사용했으나, side 컬럼으로 판단해야 한다는 힌트를 받아 수정했다. 또한, COUNT는 uuid가 아닌 id로 세야 한다는 점도 수정했다.
- 예외: 없음

## KB-007
- 상황: 특정 카드의 세트가 "Coldsnap"인 카드의 이탈리아어 텍스트 규칙을 나열하는 질문
- 태그: foreign_data, cards, sets, text, language, JOIN_LOGIC
- 교정 내용: 처음에는 rulings 테이블을 사용하려 했으나, foreign_data 테이블을 사용해야 한다는 힌트를 받아 수정했다. DISTINCT도 붙여야 한다는 점도 반영했다.
- 예외: 없음

## KB-008
- 상황: 특정 카드의 아티스트가 "Stephen Daniele"인 카드의 규칙 텍스트를 설명하고, 이 카드들이 결함이 있는지 여부를 확인하는 질문
- 태그: cards, rulings, artist, hasContentWarning, JOIN_LOGIC
- 교정 내용: 처음에는 CASE 문을 사용하여 텍스트 변환을 시도했으나, hasContentWarning 값을 그대로 반환해야 한다는 힌트를 받아 수정했다.
- 예외: 없음

## KB-009
- 상황: 특정 세트의 블록이 "Ice Age"인 카드 중에서 이탈리아어 번역이 있는 카드의 수를 구하는 질문
- 태그: sets, set_translations, language, block, COUNT, AGGREGATION_LOGIC
- 교정 내용: 처음에는 COUNT를 사용하지 않고 직접적으로 세트를 필터링하려 했으나, COUNT를 사용하여 이탈리아어 번역이 있는 카드의 수를 세야 한다는 힌트를 받아 수정했다.
- 예외: 없음

## KB-010
- 상황: 특정 카드의 이름이 "Angel of Mercy"인 카드가 Magic: The Gathering Online에 등장하는지 여부를 확인하는 질문
- 태그: cards, sets, mtgoCode, IIF, JOIN_LOGIC
- 교정 내용: 처음에는 mtgoCode가 NULL인지 여부를 WHERE절에서 판단하려 했으나, SELECT문에서 IIF로 'YES'/'NO'로 반환해야 한다는 힌트를 받아 수정했다.
- 예외: 없음

## KB-011
- 상황: 특정 카드의 타입이 "Creature"이고, 레이아웃이 "normal"이며, 아티스트가 "Matthew D. Wilson"인 카드의 프랑스어 이름을 찾는 질문
- 태그: foreign_data, cards, language, types, layout, artist, JOIN_LOGIC
- 교정 내용: 처음에는 type 컬럼을 사용했으나, types(복수형)으로 수정해야 했고, DISTINCT를 빼야 한다는 힌트를 받아 수정했다.
- 예외: 없음

## KB-012
- 상황: 금지된 카드 중에서 흰색 테두리인 카드의 수를 구하는 질문
- 태그: cards, legalities, borderColor, status, COUNT, AGGREGATION_LOGIC
- 교정 내용: 처음에는 uuid를 서브쿼리로 사용했으나, JOIN을 사용하여 legalities 테이블과 연결해야 한다는 힌트를 받아 수정했다.
- 예외: 없음

## KB-013
- 상황: EDHRec에서 1위인 카드의 이름과 금지된 플레이 포맷을 나열하는 질문
- 태그: cards, legalities, edhrecRank, status, GROUP BY, JOIN_LOGIC
- 교정 내용: 처음에는 GROUP BY를 사용하지 않았으나, 중복 제거를 위해 GROUP BY를 추가해야 한다는 힌트를 받아 수정했다.
- 예외: 없음

## KB-014
- 상황: 아티팩트 타입의 카드 중에서 다중 면이 없는 카드의 법적 상태를 빈티지 플레이 포맷에 대해 나열하는 질문
- 태그: cards, legalities, types, side, format, DISTINCT, JOIN_LOGIC
- 교정 내용: 처음에는 DISTINCT를 사용하지 않았으나, 중복 제거를 위해 DISTINCT를 추가해야 한다는 힌트를 받아 수정했다.
- 예외: 없음

## KB-015
- 상황: "Coldsnap" 세트에 속하는 카드 중에서 가장 높은 변환 마나 비용을 가진 카드의 이탈리아어 이름을 나열하는 질문
- 태그: foreign_data, cards, sets, language, convertedManaCost, MAX, JOIN_LOGIC
- 교정 내용: 처음에는 DISTINCT를 사용했으나, 카드 이름을 cards 테이블에서 가져와야 한다는 힌트를 받아 수정했다.
- 예외: 없음

## KB-016
- 상황: 아티스트가 "Allen Williams"인 카드의 프레임 스타일과 금지된 카드 여부를 확인하는 질문
- 태그: cards, legalities, artist, status, IIF, JOIN_LOGIC
- 교정 내용: 처음에는 WHERE절에서 status를 필터링하려 했으나, SELECT문에서 IIF로 'Banned' 여부를 반환해야 한다는 힌트를 받아 수정했다.
- 예외: 없음

## KB-017
- 상황: 카드 "Ancestor's Chosen"의 테두리 색상을 찾는 질문
- 태그: cards, name, borderColor, DISTINCT
- 교정 내용: 처음에는 DISTINCT를 사용하지 않았으나, 중복 제거를 위해 DISTINCT를 추가해야 한다는 힌트를 받아 수정했다.
- 예외: 없음

## KB-018
- 상황: "Adarkar Valkyrie" 카드가 미국 외에서만 사용 가능한지 여부를 확인하는 질문
- 태그: cards, sets, name, isForeignOnly, IIF, JOIN_LOGIC
- 교정 내용: 처음에는 WHERE절에서 isForeignOnly 조건을 사용했으나, SELECT문에서 IIF로 'YES'/'NO'로 반환해야 한다는 힌트를 받아 수정했다.
- 예외: 없음
