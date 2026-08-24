## KB-001
- 상황: 특정 카드의 세트에 대한 특정 언어의 번역이 있는지 여부를 확인하는 질문
- 태그: set_translations, cards.name, sets.name, JOIN_LOGIC
- 교정 내용: 처음에는 foreign_data 테이블을 사용하여 번역을 찾으려 했으나, set_translations 테이블을 사용해야 하며, 조건에 맞는 번역이 있는지 여부를 'YES'/'NO'로 반환해야 한다.
- 예외: 특정 언어의 번역이 없는 경우, 'NO'를 반환하는 것이 아닌 다른 처리를 해야 할 수 있다.

## KB-002
- 상황: 두 카드 중에서 더 높은 비용을 가진 카드를 찾는 질문
- 태그: cards.name, cards.convertedManaCost, COLUMN_ORDER
- 교정 내용: 처음에는 name과 convertedManaCost를 모두 SELECT하려 했으나, name만 SELECT해야 한다.
- 예외: 두 카드의 비용이 동일한 경우, 어떤 카드를 반환할지에 대한 추가 조건이 필요할 수 있다.

## KB-003
- 상황: 특정 세트에 속한 카드의 아티스트를 찾는 질문
- 태그: cards.setCode, sets.name, JOIN_LOGIC
- 교정 내용: 처음에는 cards.setCode를 직접 사용하려 했으나, sets 테이블과 조인하여 sets.name을 사용해야 한다.
- 예외: 세트 이름이 아닌 코드로 필터링해야 하는 경우가 있을 수 있다.

## KB-004
- 상황: 특정 능력을 가진 카드의 수를 세는 질문
- 태그: cards.power, rulings.text, JOIN_LOGIC, AGGREGATION_LOGIC
- 교정 내용: 처음에는 rulings 테이블의 text 컬럼을 사용하려 했으나, cards 테이블의 id를 기준으로 COUNT해야 한다.
- 예외: 특정 능력이 없는 카드가 없을 경우, COUNT 결과가 0이 되는 상황을 처리해야 할 수 있다.

## KB-005
- 상황: 특정 조건을 만족하는 카드의 ID를 찾는 질문
- 태그: cards.borderColor, cards.cardKingdomId, AGGREGATION_LOGIC
- 교정 내용: 처음에는 모든 컬럼을 SELECT하려 했으나, id 컬럼만 반환해야 한다.
- 예외: 특정 조건을 만족하는 카드가 없을 경우, 반환할 결과가 없을 수 있다.

## KB-006
- 상황: 특정 카드의 아티스트와 관련된 룰링 정보를 찾는 질문
- 태그: cards.isPromo, rulings.uuid, AGGREGATION_LOGIC
- 교정 내용: 처음에는 카드 단위로 그룹핑하려 했으나, 아티스트 단위로 그룹핑해야 하며, COUNT(DISTINCT uuid)로 세야 한다.
- 예외: 특정 아티스트가 룰링 정보를 전혀 가지지 않는 경우, 결과가 없을 수 있다.

## KB-007
- 상황: 특정 카드의 세트에 대한 특정 언어의 번역을 찾는 질문
- 태그: set_translations, cards.name, JOIN_LOGIC
- 교정 내용: 처음에는 set_translations에서 직접 번역을 찾으려 했으나, cards 테이블에서 세트를 찾는 서브쿼리를 사용해야 한다.
- 예외: 특정 언어의 번역이 없는 경우, 'NO'를 반환하는 것이 아닌 다른 처리를 해야 할 수 있다.

## KB-008
- 상황: 특정 카드의 비율을 계산하는 질문
- 태그: cards.isStorySpotlight, cards.isTextless, AGGREGATION_LOGIC
- 교정 내용: 처음에는 GROUP_CONCAT으로 ID 리스트를 반환하려 했으나, 퍼센트 값 하나만 SELECT해야 한다.
- 예외: 특정 조건을 만족하는 카드가 없을 경우, 0%로 반환해야 할 수 있다.

## KB-009
- 상황: 특정 카드의 언어에 대한 비율을 계산하는 질문
- 태그: cards.power, foreign_data.language, JOIN_LOGIC, AGGREGATION_LOGIC
- 교정 내용: 처음에는 LEFT JOIN을 사용하려 했으나, INNER JOIN을 사용해야 하며, COUNT(CASE...) 대신 SUM(CASE...)로 변경해야 한다.
- 예외: 특정 언어의 카드가 없는 경우, 0%로 반환해야 할 수 있다.

## KB-010
- 상황: 특정 포맷과 법적 상태를 가진 카드 중에서 콘텐츠 경고가 없는 카드의 비율을 계산하는 질문
- 태그: cards.hasContentWarning, legalities.format, legalities.status, AGGREGATION_LOGIC
- 교정 내용: 처음에는 status 값을 'legal'로 소문자 사용했으나, 대문자 'Legal'로 저장되어 있어야 하며, WHERE절로 먼저 format='commander' AND status='Legal' 필터링한 다음, SUM(CASE...)/COUNT(id)로 계산해야 한다.
- 예외: 특정 포맷이나 법적 상태에 해당하는 카드가 없는 경우, 0%로 반환해야 할 수 있다.

## KB-011
- 상황: 특정 카드의 룰링 텍스트를 찾는 질문
- 태그: foreign_data.language, cards.name, JOIN_LOGIC
- 교정 내용: 처음에는 foreign_data 테이블에서 직접 룰링 텍스트를 찾으려 했으나, cards 테이블에서 해당 카드를 찾은 후 uuid로 foreign_data와 조인하여 룰링 텍스트를 찾아야 한다.
- 예외: 특정 카드에 대한 룰링 정보가 없는 경우, 결과가 없을 수 있다.

## KB-012
- 상황: 특정 카드의 아티스트와 관련된 룰링 정보를 찾는 질문
- 태그: cards.artist, rulings.uuid, AGGREGATION_LOGIC
- 교정 내용: 처음에는 카드 단위로 그룹핑하려 했으나, 아티스트 단위로 그룹핑해야 하며, COUNT(DISTINCT uuid)로 세야 한다.
- 예외: 특정 아티스트가 룰링 정보를 전혀 가지지 않는 경우, 결과가 없을 수 있다.
