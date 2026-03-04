# LLM Agents Integration Test Gates

오케스트레이터 통합 테스트는 목적에 따라 2개 트랙으로 분리한다.

- `integration_orchestrator`: 실제 LLM + stub 도구 (계약 검증 중심)
- `integration_live`: 실제 LLM + 실제 도구 (연결/생존 스모크)

## 현재 운영 원칙

- PR 기본 게이트는 `integration_orchestrator` 결과를 우선 신뢰한다.
- `integration_live`는 외부 의존성(네트워크, 모델 API, 벡터 DB 상태)에 영향을 받으므로
  최소 스모크만 유지한다.
- live 케이스 확장은 아래 "확장 게이트"를 모두 만족한 뒤 진행한다.

## 실행 명령

```bash
# orchestrator 계약 검증
pytest llm/agents/tests/test_orchestrator_integration.py -v -m integration_orchestrator

# live 스모크
pytest llm/agents/tests/test_orchestrator_integration.py -v -m integration_live

# agents 전체 (integration 제외)
pytest llm/agents/tests/ -v -k "not integration"
```

## Live 확장 게이트 (4개 -> 8~12개)

아래 3가지를 모두 충족해야 `integration_live` 케이스를 늘린다.

1. 데이터 게이트 (벡터 DB 준비)
   - `policies` 컬렉션 문서 수가 0보다 커야 한다.
   - 권장 확인 스크립트:
     ```bash
     python -c "import chromadb; c=chromadb.PersistentClient(path='llm/vectorstore/chroma_db'); print(c.get_or_create_collection('policies').count())"
     ```
   - count가 0이면 live 확장 금지.

2. 안정성 게이트 (반복 실행)
   - `integration_live`를 최소 2~3회 연속 실행했을 때 `0 failed`를 만족해야 한다.
   - 네트워크/API 불가로 인한 skip은 원인 명시 후 해결 계획이 있어야 한다.

3. 시간/비용 게이트
   - `integration_live` 실행 시간이 팀 합의 상한(예: 2~4분) 이내여야 한다.
   - 비용이 급증하면 live는 유지/축소하고 계약 검증은 stub 트랙에서 확장한다.

## 실패 해석 가이드

- `integration_orchestrator` 실패:
  - 오케스트레이터 프롬프트/도구 선택/호출 계약 회귀를 먼저 의심한다.
- `integration_live` 실패:
  - 순서대로 점검: API 연결 -> 벡터 DB 상태 -> 도구/인프라 의존성.
  - 이 트랙만 실패하고 orchestrator 트랙이 통과하면, 우선순위는 인프라/데이터 문제다.

## 확장 승인 체크리스트

- [ ] `integration_orchestrator` 전체 통과
- [ ] `integration_live` 연속 실행에서 실패 0회
- [ ] `policies` 컬렉션 count > 0 확인
- [ ] 실행시간/비용 상한 충족

