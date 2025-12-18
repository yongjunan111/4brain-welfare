# 기여 가이드 (Contributing Guide)

## 브랜치 전략

```
main        ← 배포용 (직접 푸시 금지)
develop     ← 통합 브랜치 (PR로만 머지)
  │
  ├── backend/기능명     ← 백엔드 작업
  ├── frontend/기능명    ← 프론트엔드 작업
  └── llm/기능명         ← LLM 작업
```

### 브랜치 만들기 (Git Graph)
1. `develop` 브랜치로 이동 (체크아웃)
2. `develop` 우클릭 → Create Branch
3. 이름 규칙: `담당/기능명`
   - 예: `backend/api-setup`, `frontend/chat-ui`, `llm/prompt-tuning`

---

## 커밋 메시지 규칙

### 형식
```
타입: 제목 (50자 이내)

본문 (선택사항, 뭘 왜 했는지)
```

### 타입 종류

| 타입 | 언제 쓰나 | 예시 |
|------|----------|------|
| `feat` | 새 기능 추가 | `feat: 청년정책 API 호출 함수 추가` |
| `fix` | 버그 수정 | `fix: 나이 필터링 오류 수정` |
| `docs` | 문서 수정 | `docs: README에 설치 방법 추가` |
| `style` | 코드 포맷팅 (동작 변화 없음) | `style: 들여쓰기 정리` |
| `refactor` | 리팩토링 (기능 변화 없음) | `refactor: API 호출 로직 분리` |
| `test` | 테스트 추가/수정 | `test: 프로필 추출 테스트 추가` |
| `chore` | 빌드, 설정 파일 수정 | `chore: requirements.txt 업데이트` |
| `init` | 초기 생성 | `init: 프로젝트 초기 세팅` |
| `rename` | 파일/폴더 이름 변경 | `rename: utils.py → helpers.py` |
| `remove` | 파일 삭제 | `remove: 사용 안 하는 테스트 파일 삭제` |

### 좋은 예시
```
feat: 청년정책 API 연동

- youthcenter API 호출 함수 구현
- 서울 지역 필터링 추가
- 페이지네이션 처리
```

### 나쁜 예시
```
수정함
ㅇㅇ
asdf
feat: 여러가지 수정  ← 너무 모호함
```

---

## PR (Pull Request) 규칙

### PR 올리는 방법
1. 작업 브랜치에서 커밋 & 푸시
2. GitHub 웹에서 `Pull requests` → `New pull request`
3. `base: develop` ← `compare: 내 브랜치` 확인
4. 템플릿 채우고 Create

### PR 전 체크리스트
- [ ] 내 브랜치에서 `develop` 최신 코드 pull 받았는지
- [ ] 로컬에서 테스트 해봤는지
- [ ] 커밋 메시지 규칙 지켰는지

### 코드 리뷰
- PR 올리면 팀원 1명 이상 리뷰 후 머지
- 급하면 슬랙/디코에 리뷰 요청

---

## 개발 환경 세팅

### 1. 클론
```bash
git clone https://github.com/팀/4brain.git
cd 4brain
```

### 2. uv 설치 (없으면)
```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

### 3. 의존성 설치
```bash
uv sync
```

### 4. 커밋 템플릿 적용 (선택)
```bash
git config --local commit.template .gitmessage
```
이후 터미널에서 `git commit` 하면 가이드가 뜸.

---

## 질문 있으면
- 팀 슬랙/디스코드에 물어보기
- Claude/GPT한테 물어보기 ㅋㅋ
