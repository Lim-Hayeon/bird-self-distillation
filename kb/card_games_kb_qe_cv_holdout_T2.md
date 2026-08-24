## KB-001
- 상황: 특정 카드의 세트에 대한 특정 언어의 번역이 있는지 여부를 확인하는 질문
- 태그: set_translations, cards.name, sets.name, JOIN_LOGIC
- 교정 내용: 처음에는 foreign_data 테이블을 사용하여 번역을 찾으려 했으나, set_translations 테이블을 사용해야 하며, 번역 내용이 아닌 존재 여부를 'YES'/'NO'로 반환해야 한다.
- 예외: 특정 카드가 여러 세트에 포함되어 있을 때, 모든 세트에 대한 번역 여부를 확인해야 하는 경우.

## KB-002
- 상황: 두 카드 중 더 높은 비용을 가진 카드를 찾는 질문
- 태그: cards.name, cards.convertedManaCost, COLUMN_ORDER
- 교정 내용: 처음에는 convertedManaCost를 SELECT했으나, name만 SELECT해야 한다.
- 예외: 두 카드의 비용이 동일한 경우, 추가적인 기준이 필요할 수 있다.

## KB-003
- 상황: 특정 세트에 포함된 카드의 아티스트를 찾는 질문
- 태그: cards.setCode, sets.name, JOIN_LOGIC
- 교정 내용: 처음에는 cards.setCode를 직접 사용했으나, sets 테이블과 조인하여 sets.name을 사용해야 한다.
- 예외: 세트 이름이 아닌 코드로만 주어진 경우.

## KB-004
- 상황: 특정 능력을 가진 카드의 수를 세는 질문
- 태그: cards.power, rulings.text, JOIN_LOGIC, AGGREGATION_LOGIC
- 교정 내용: 처음에는 rulings.text를 cards 테이블에서 찾으려 했으나, rulings 테이블과 조인하여 COUNT는 DISTINCT cards.id로 세야 한다.
- 예외: 능력 정보가 없는 카드에 대한 추가적인 조건이 필요한 경우.

## KB-005
- 상황: 특정 조건을 만족하는 카드의 ID를 찾는 질문
- 태그: cards.borderColor, cards.cardKingdomId, AGGREGATION_LOGIC
- 교정 내용: 처음에는 모든 컬럼을 SELECT했으나, id만 SELECT해야 하며, cardKingdomId가 NULL인 조건만 사용해야 한다.
- 예외: 카드의 다른 속성에 따라 추가적인 필터링이 필요한 경우.

## KB-006
- 상황: 특정 카드의 외국어 번역이 있는지 확인하는 질문
- 태그: cards.originalType, cards.colors, foreign_data.uuid, JOIN_LOGIC
- 교정 내용: 처음에는 전체 컬럼을 SELECT했으나, name 컬럼만 DISTINCT로 SELECT해야 한다.
- 예외: 특정 카드가 여러 외국어 번역을 가지고 있을 때, 모든 번역을 확인해야 하는 경우.

## KB-007
- 상황: 특정 카드의 룰링 정보를 가장 많이 가진 아티스트를 찾는 질문
- 태그: cards.isPromo, rulings.uuid, AGGREGATION_LOGIC, JOIN_LOGIC
- 교정 내용: 처음에는 카드 단위로 그룹핑했으나, 아티스트 단위로 그룹핑하고, COUNT는 DISTINCT uuid로 세야 하며, LIMIT 1을 추가해야 한다.
- 예외: 룰링 정보가 없는 카드에 대한 추가적인 조건이 필요한 경우.

## KB-008
- 상황: 특정 카드의 세트에 대한 특정 언어의 번역이 있는지 여부를 확인하는 질문
- 태그: set_translations, cards.name, JOIN_LOGIC
- 교정 내용: 처음에는 set_translations 테이블을 사용하여 번역을 찾으려 했으나, 세트 코드로 서브쿼리를 사용해야 한다.
- 예외: 특정 카드가 여러 세트에 포함되어 있을 때, 모든 세트에 대한 번역 여부를 확인해야 하는 경우.

## KB-009
- 상황: 특정 카드의 비율을 계산하는 질문
- 태그: cards.isStorySpotlight, cards.isTextless, AGGREGATION_LOGIC
- 교정 내용: 처음에는 GROUP_CONCAT으로 ID 리스트를 반환하려 했으나, 퍼센트 값 하나만 SELECT해야 하며, CAST를 REAL로 해야 한다.
- 예외: 특정 카드의 ID 리스트가 필요한 경우.

## KB-010
- 상황: 특정 카드의 언어와 능력에 대한 비율을 계산하는 질문
- 태그: cards.power, foreign_data.language, JOIN_LOGIC, AGGREGATION_LOGIC
- 교정 내용: 처음에는 LEFT JOIN을 사용했으나, INNER JOIN을 사용해야 하며, COUNT(CASE...)가 아니라 SUM(CASE...)로, CAST도 REAL로 해야 한다.
- 예외: 특정 카드의 언어가 여러 개일 때, 모든 언어에 대한 비율을 확인해야 하는 경우.

## KB-011
- 상황: 특정 카드의 외국어 이름을 찾는 질문
- 태그: foreign_data, cards.types, JOIN_LOGIC, COLUMN_ORDER
- 교정 내용: 처음에는 cards.type을 사용했으나, cards.types(복수형)을 사용해야 하며, DISTINCT는 빼야 한다.
- 예외: 카드의 타입이 여러 개인 경우, 모든 타입에 대한 외국어 이름을 확인해야 하는 경우.

## KB-012
- 상황: 특정 카드의 법적 상태를 확인하는 질문
- 태그: cards.artist, legalities.status, JOIN_LOGIC
- 교정 내용: 처음에는 status = 'Banned' 조건을 WHERE에 사용했으나, IIF문을 사용하여 카드 이름을 반환해야 한다.
- 예외: 카드의 법적 상태가 여러 개인 경우, 모든 상태를 확인해야 하는 경우.

## KB-013
- 상황: 특정 카드의 세트에 대한 특정 언어의 번역이 있는지 여부를 확인하는 질문
- 태그: cards.name, sets.name, JOIN_LOGIC, AGGREGATION_LOGIC
- 교정 내용: 처음에는 sets.isForeignOnly 조건을 WHERE에 사용했으나, IIF문을 사용하여 'YES'/'NO'로 반환해야 한다.
- 예외: 특정 카드가 여러 세트에 포함되어 있을 때, 모든 세트에 대한 번역 여부를 확인해야 하는 경우.
