## KB-001
- 상황: 특정 카드의 세트에 대한 특정 언어의 번역이 있는지 확인하는 질문
- 태그: set_translations, cards.name, sets.name, JOIN_LOGIC
- 교정 내용: 처음에는 foreign_data 테이블을 사용하여 번역을 찾으려 했으나, set_translations 테이블을 사용해야 하며, 조건에 맞는 번역이 있는지 여부를 'YES'/'NO'로 반환해야 한다.
- 예외: 특정 카드가 여러 세트에 포함되어 있을 때, 모든 세트에 대한 번역을 확인해야 하는 경우.

## KB-002
- 상황: 두 카드 중 더 높은 비용을 가진 카드를 찾는 질문
- 태그: cards.name, cards.convertedManaCost, COLUMN_ORDER
- 교정 내용: 처음에는 convertedManaCost를 SELECT했으나, name만 SELECT해야 한다.
- 예외: 두 카드의 비용이 동일한 경우, 추가적인 정보를 제공해야 할 필요가 있는 경우.

## KB-003
- 상황: 특정 세트에 포함된 카드의 아티스트를 찾는 질문
- 태그: cards.setCode, sets.name, JOIN_LOGIC
- 교정 내용: 처음에는 cards.setCode를 직접 사용했으나, sets 테이블과 조인하여 sets.name을 사용해야 한다.
- 예외: 세트 이름이 아닌 코드로만 필터링해야 하는 경우.

## KB-004
- 상황: 특정 능력을 가진 카드의 수를 세는 질문
- 태그: cards.power, rulings.text, JOIN_LOGIC, AGGREGATION_LOGIC
- 교정 내용: 처음에는 rulings.text를 cards 테이블에서 찾으려 했으나, rulings 테이블과 조인하여 COUNT는 DISTINCT cards.id로 세야 한다.
- 예외: 특정 능력을 가진 카드가 없을 때, 0을 반환해야 하는 경우.

## KB-005
- 상황: 특정 조건을 만족하는 카드의 ID를 찾는 질문
- 태그: cards.borderColor, cards.cardKingdomId, AGGREGATION_LOGIC
- 교정 내용: 처음에는 모든 컬럼을 SELECT했으나, id 컬럼만 반환해야 하며, cardKingdomId가 NULL인 조건만 사용해야 한다.
- 예외: 카드의 모든 정보를 반환해야 하는 경우.

## KB-006
- 상황: 특정 카드 타입과 색상을 가진 카드의 외국어 번역을 찾는 질문
- 태그: cards.originalType, cards.colors, foreign_data.uuid, JOIN_LOGIC
- 교정 내용: 처음에는 전체 컬럼을 SELECT했으나, name 컬럼만 DISTINCT로 SELECT해야 한다.
- 예외: 특정 카드의 모든 정보를 반환해야 하는 경우.

## KB-007
- 상황: 가장 많은 룰링 정보를 가진 카드와 아티스트를 찾는 질문
- 태그: cards.isPromo, rulings.uuid, AGGREGATION_LOGIC, JOIN_LOGIC
- 교정 내용: 처음에는 카드 단위로 그룹핑했으나, 아티스트 단위로 그룹핑하고, isPromo = 1 조건으로 필터링해야 한다.
- 예외: 특정 아티스트의 모든 카드 정보를 반환해야 하는 경우.

## KB-008
- 상황: 특정 카드의 세트에 대한 특정 언어의 번역을 찾는 질문
- 태그: set_translations, cards.name, JOIN_LOGIC
- 교정 내용: 처음에는 set_translations에서 직접 번역을 찾으려 했으나, cards 테이블에서 세트를 찾는 서브쿼리를 사용해야 한다.
- 예외: 특정 카드가 여러 세트에 포함되어 있을 때, 모든 세트에 대한 번역을 확인해야 하는 경우.

## KB-009
- 상황: 특정 조건을 만족하는 카드의 비율을 계산하는 질문
- 태그: cards.isStorySpotlight, cards.isTextless, AGGREGATION_LOGIC
- 교정 내용: 처음에는 GROUP_CONCAT으로 ID 리스트를 반환하려 했으나, 퍼센트 값 하나만 SELECT해야 하며, CAST를 REAL로 해야 한다.
- 예외: ID 리스트가 필요한 경우.

## KB-010
- 상황: 특정 조건을 만족하는 카드의 비율을 계산하는 질문
- 태그: cards.power, foreign_data.language, JOIN_LOGIC, AGGREGATION_LOGIC
- 교정 내용: 처음에는 LEFT JOIN을 사용했으나, INNER JOIN을 사용해야 하며, COUNT(CASE...) 대신 SUM(CASE...)로 변경해야 한다.
- 예외: 특정 언어의 카드만 필터링해야 하는 경우.

## KB-011
- 상황: 특정 포맷과 법적 상태를 가진 카드의 비율을 계산하는 질문
- 태그: legalities.format, legalities.status, cards.hasContentWarning, AGGREGATION_LOGIC
- 교정 내용: 처음에는 status 값을 소문자 'legal'로 사용했으나, 대문자 'Legal'로 수정해야 하며, WHERE절에서 format과 status를 먼저 필터링한 후, SUM과 COUNT를 사용해야 한다.
- 예외: 특정 포맷의 카드만 필터링해야 하는 경우.

## KB-012
- 상황: 특정 원형 타입을 가진 카드의 서브타입을 확인하는 질문
- 태그: cards.originalType, cards.subtypes, AGGREGATION_LOGIC
- 교정 내용: 처음에는 서브타입을 LIKE로 비교했으나, 정확한 일치를 위해 '!=' 연산자를 사용해야 한다.
- 예외: 서브타입이 여러 개일 경우, 특정 서브타입을 포함하지 않는 카드를 찾고자 할 때.
