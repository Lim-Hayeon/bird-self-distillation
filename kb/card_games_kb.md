
## Round: R1
- 'setCode'로 조인할 때는 'sets' 테이블의 'name'을 사용해야 하며, 'cards' 테이블의 'setCode'는 코드값임을 기억해야 한다.
- SELECT 문에서 전체 컬럼(*) 대신 필요한 컬럼만 선택해야 하며, DISTINCT를 사용해야 할 경우도 있다.
- COUNT는 DISTINCT 기준으로 세야 할 때가 있으며, 조인 없이 원본 테이블에서 직접 세는 경우도 있다.
- 조건을 먼저 필터링한 후 GROUP BY를 사용해야 하며, GROUP BY 기준이 되는 컬럼에 따라 결과가 달라질 수 있다.
- 퍼센트 계산 시 COUNT 대신 SUM을 사용해야 하며, CAST를 통해 데이터 타입을 명시적으로 지정해야 한다.

## Round: R2
- 'otherFaceIds' 대신 'side' 컬럼을 사용해야 하며, COUNT는 'uuid'가 아닌 'id'로 세야 한다.
- foreign_data 테이블의 'name' 컬럼을 직접 사용해야 하며, DISTINCT를 붙여야 한다.
- foreign_data.name은 번역된 이름이므로, cards 테이블에서 원래 이름으로 uuid를 찾은 후 조인해야 한다.
- DISTINCT를 사용하지 말고, 조건은 AND로 설정해야 하며, 두 컬럼 모두 NOT NULL이어야 한다.
- rulings 대신 foreign_data 테이블을 사용해야 하며, DISTINCT를 붙여야 한다.
- CASE 문으로 텍스트 변환하지 말고, hasContentWarning 값을 그대로 반환해야 한다.
- mtgoCode의 NULL 여부를 'YES'/'NO'로 반환해야 하며, WHERE 절에서 mtgoCode 조건을 빼야 한다.
- status 값은 대문자 'Legal'로 저장되어 있으며, WHERE 절에서 먼저 format과 status를 필터링해야 한다.
- subtypes 비교 시 'NOT LIKE' 대신 '!='로 정확히 일치 비교해야 한다.

## Round: R3
- 컬럼명이 'type'이 아니라 'types'(복수형)임을 기억해야 하며, DISTINCT는 사용하지 말아야 한다.
- GROUP BY를 사용하여 중복을 제거해야 할 때는 필요한 컬럼을 명시적으로 지정해야 한다.
- DISTINCT를 사용하지 말고, WHERE 절에서 조건을 필터링할 때는 IIF 문을 사용하여 특정 값을 반환해야 한다.
