"""
쿼리 리라이터 테스트

- Unit 테스트: Mock 기반, LLM 호출 없음 (CI용)
- Hard 케이스: 실제 LLM 호출, OPENAI_API_KEY 필요

실행:
    pytest llm/agents/tests/test_rewrite_query.py -v          # Unit만
    pytest llm/agents/tests/test_rewrite_query.py -v -s       # Unit + 출력 보기
    pytest llm/agents/tests/test_rewrite_query.py -v -s -k hard  # Hard 케이스만
"""

import json
import os
import pytest
from unittest.mock import patch


# ============================================================================
# Unit: JSON 파싱 (_parse_json_response)
# ============================================================================

class TestParseJsonResponse:

    def test_valid_json(self):
        from llm.agents.tools.rewrite_query import _parse_json_response

        raw = json.dumps({
            "bm25_query": "청년 월세 지원",
            "intent_keywords": ["월세", "지원"],
            "detected_pattern": "easy"
        })
        result = _parse_json_response(raw, "원본 쿼리")

        assert result["bm25_query"] == "청년 월세 지원"
        assert result["intent_keywords"] == ["월세", "지원"]
        assert result["detected_pattern"] == "easy"
        assert result["original_query"] == "원본 쿼리"

    def test_json_with_code_block(self):
        from llm.agents.tools.rewrite_query import _parse_json_response

        raw = '```json\n{"bm25_query": "청년 취업", "intent_keywords": ["취업"], "detected_pattern": "easy"}\n```'
        result = _parse_json_response(raw, "원본")
        assert result["bm25_query"] == "청년 취업"

    def test_missing_fields_fallback(self):
        from llm.agents.tools.rewrite_query import _parse_json_response

        raw = json.dumps({"bm25_query": "테스트"})
        result = _parse_json_response(raw, "원본")
        assert result["intent_keywords"] == []
        assert result["detected_pattern"] == "unknown"

    def test_invalid_json_fallback(self):
        from llm.agents.tools.rewrite_query import _parse_json_response

        raw = "이건 JSON이 아님 청년 월세 지원"
        result = _parse_json_response(raw, "원본 쿼리")
        assert result["detected_pattern"] == "parse_error"
        assert len(result["bm25_query"]) > 0

    def test_empty_bm25_query_uses_original(self):
        from llm.agents.tools.rewrite_query import _parse_json_response

        raw = json.dumps({"bm25_query": "", "intent_keywords": [], "detected_pattern": "easy"})
        result = _parse_json_response(raw, "원본 쿼리")
        assert result["bm25_query"] == "원본 쿼리"


# ============================================================================
# Unit: 텍스트 정리 (_clean_fallback)
# ============================================================================

class TestCleanFallback:

    def test_removes_json_chars(self):
        from llm.agents.tools.rewrite_query import _clean_fallback
        assert _clean_fallback('{"청년 월세"}') == "청년 월세"

    def test_removes_quotes(self):
        from llm.agents.tools.rewrite_query import _clean_fallback
        assert _clean_fallback('"청년 월세 지원"') == "청년 월세 지원"

    def test_collapses_spaces(self):
        from llm.agents.tools.rewrite_query import _clean_fallback
        assert _clean_fallback("청년   월세   지원") == "청년 월세 지원"

    def test_removes_newlines(self):
        from llm.agents.tools.rewrite_query import _clean_fallback
        assert _clean_fallback("청년\n월세\n지원") == "청년 월세 지원"


# ============================================================================
# Unit: @tool Mock 테스트
# ============================================================================

class TestRewriteQueryTool:

    @patch('llm.agents.tools.rewrite_query._rewrite_with_llm')
    def test_returns_bm25_query_from_json(self, mock_llm):
        from llm.agents.tools.rewrite_query import rewrite_query

        mock_llm.return_value = json.dumps({
            "bm25_query": "청년 월세 지원 주거 보조금",
            "intent_keywords": ["월세", "지원"],
            "detected_pattern": "easy"
        })
        result = rewrite_query.invoke("월세 도움 받을 수 있어?")
        assert result == "청년 월세 지원 주거 보조금"

    @patch('llm.agents.tools.rewrite_query._rewrite_with_llm')
    def test_returns_original_on_empty_bm25(self, mock_llm):
        from llm.agents.tools.rewrite_query import rewrite_query

        mock_llm.return_value = json.dumps({
            "bm25_query": "", "intent_keywords": [], "detected_pattern": "easy"
        })
        result = rewrite_query.invoke("테스트 쿼리")
        assert result == "테스트 쿼리"

    @patch('llm.agents.tools.rewrite_query._rewrite_with_llm')
    def test_returns_original_on_error(self, mock_llm):
        from llm.agents.tools.rewrite_query import rewrite_query

        mock_llm.side_effect = Exception("API Error")
        result = rewrite_query.invoke("테스트 쿼리")
        assert result == "테스트 쿼리"

    @patch('llm.agents.tools.rewrite_query._rewrite_with_llm')
    def test_handles_non_json_response(self, mock_llm):
        from llm.agents.tools.rewrite_query import rewrite_query

        mock_llm.return_value = "청년 월세 지원 주거"
        result = rewrite_query.invoke("월세 도움")
        assert isinstance(result, str)
        assert len(result) > 0

    def test_empty_input_returns_as_is(self):
        from llm.agents.tools.rewrite_query import rewrite_query
        assert rewrite_query.invoke("") == ""
        assert rewrite_query.invoke("a") == "a"

    @patch('llm.agents.tools.rewrite_query._rewrite_with_llm')
    def test_tool_returns_string_not_json(self, mock_llm):
        """@tool은 JSON이 아닌 plain string 반환"""
        from llm.agents.tools.rewrite_query import rewrite_query

        mock_llm.return_value = json.dumps({
            "bm25_query": "청년 지원", "intent_keywords": [], "detected_pattern": "easy"
        })
        result = rewrite_query.invoke("테스트")
        assert isinstance(result, str)
        assert "{" not in result


# ============================================================================
# Unit: rewrite_query_full Mock 테스트
# ============================================================================

class TestRewriteQueryFull:

    @patch('llm.agents.tools.rewrite_query._get_llm')
    @patch('llm.agents.tools.rewrite_query._rewrite_with_llm')
    def test_returns_full_dict(self, mock_llm, mock_get_llm):
        from llm.agents.tools.rewrite_query import rewrite_query_full

        mock_llm.return_value = json.dumps({
            "bm25_query": "청년 월세 지원",
            "intent_keywords": ["월세"],
            "detected_pattern": "easy"
        })
        result = rewrite_query_full("월세 도움")
        assert result["bm25_query"] == "청년 월세 지원"
        assert result["intent_keywords"] == ["월세"]
        assert result["detected_pattern"] == "easy"
        assert result["original_query"] == "월세 도움"

    def test_empty_input(self):
        from llm.agents.tools.rewrite_query import rewrite_query_full
        result = rewrite_query_full("")
        assert result["detected_pattern"] == "empty"


# ============================================================================
# Unit: 엣지 케이스
# ============================================================================

class TestEdgeCases:

    @patch('llm.agents.tools.rewrite_query._rewrite_with_llm')
    def test_very_long_query(self, mock_llm):
        from llm.agents.tools.rewrite_query import rewrite_query

        mock_llm.return_value = json.dumps({
            "bm25_query": "청년 지원", "intent_keywords": [], "detected_pattern": "abstract"
        })
        result = rewrite_query.invoke("안녕하세요 저는 27살이고 " * 20)
        assert result == "청년 지원"

    @patch('llm.agents.tools.rewrite_query._rewrite_with_llm')
    def test_special_characters(self, mock_llm):
        from llm.agents.tools.rewrite_query import rewrite_query

        mock_llm.return_value = json.dumps({
            "bm25_query": "청년 지원", "intent_keywords": [], "detected_pattern": "easy"
        })
        result = rewrite_query.invoke("월세!!! 도움??? 받을 수 있어???")
        assert result == "청년 지원"

    @patch('llm.agents.tools.rewrite_query._rewrite_with_llm')
    def test_emoji_in_query(self, mock_llm):
        from llm.agents.tools.rewrite_query import rewrite_query

        mock_llm.return_value = json.dumps({
            "bm25_query": "청년 지원", "intent_keywords": [], "detected_pattern": "easy"
        })
        result = rewrite_query.invoke("월세 도움 받고 싶어요 😭")
        assert result == "청년 지원"


# ============================================================================
# Hard: 실제 LLM 호출 (OPENAI_API_KEY 필요)
# ============================================================================

needs_api_key = pytest.mark.skipif(
    not os.getenv("OPENAI_API_KEY"),
    reason="OPENAI_API_KEY not set"
)


def _full(query: str):
    from llm.agents.tools.rewrite_query import rewrite_query_full
    return rewrite_query_full(query)


@needs_api_key
class TestHardLexicalGap:

    def test_cheap_transport(self):
        result = _full("대중교통 싸게 타는 방법 없어?")
        q = result["bm25_query"]
        print(f"입력: 대중교통 싸게 타는 방법 없어? → {q} | {result['detected_pattern']}")
        assert any(kw in q for kw in ["할인", "교통비", "기후동행"]), f"got: {q}"

    def test_borrow_clothes(self):
        result = _full("면접인데 입을 옷이 없어ㅠ 빌릴 수 있어?")
        q = result["bm25_query"]
        print(f"입력: 면접 옷 빌리기 → {q} | {result['detected_pattern']}")
        assert any(kw in q for kw in ["정장", "대여", "의류"]), f"got: {q}"

    def test_deposit_loan(self):
        result = _full("이사할 때 보증금 좀 빌려주는 데 없어?")
        q = result["bm25_query"]
        print(f"입력: 보증금 빌려줘 → {q} | {result['detected_pattern']}")
        assert any(kw in q for kw in ["보증금", "대출", "임차", "주거"]), f"got: {q}"

    def test_art_studio_rental(self):
        result = _full("그림 그리는데 작업실 빌릴 수 있어?")
        q = result["bm25_query"]
        print(f"입력: 그림 그리는데 작업실 → {q} | {result['detected_pattern']}")
        assert any(kw in q for kw in ["예술", "창작", "문화", "스튜디오"]), f"got: {q}"

    def test_local_business(self):
        result = _full("우리 동네에서 가게 열고 싶은데 지원받을 수 있어?")
        q = result["bm25_query"]
        print(f"입력: 우리 동네에서 가게 열고 → {q} | {result['detected_pattern']}")
        assert any(kw in q for kw in ["창업", "로컬", "소상공인"]), f"got: {q}"

    def test_creators_gathering(self):
        result = _full("창작하는 사람들 모이는 곳 어떻게 가?")
        q = result["bm25_query"]
        print(f"입력: 창작하는 사람들 모이는 곳 → {q} | {result['detected_pattern']}")
        assert any(kw in q for kw in ["청년예술청", "예술", "창작공간", "문화예술"]), f"got: {q}"

    def test_local_cafe_startup(self):
        result = _full("서른인데 동네 카페 창업 지원 가능해?")
        q = result["bm25_query"]
        print(f"입력: 동네 카페 창업 → {q} | {result['detected_pattern']}")
        assert any(kw in q for kw in ["로컬크리에이터", "창업", "지역기반", "소상공인"]), f"got: {q}"


@needs_api_key
class TestHardSlang:

    def test_hikikomori(self):
        result = _full("방에서 안 나오는 동생도 도움받을 수 있어?")
        q = result["bm25_query"]
        print(f"입력: 안 나오는 동생 → {q} | {result['detected_pattern']}")
        assert any(kw in q for kw in ["고립", "은둔"]), f"got: {q}"

    def test_emotional_plus_employment(self):
        result = _full("요즘 취업 안 돼서 힘든데 뭐 없어?")
        q = result["bm25_query"]
        print(f"입력: 취업 힘들어 → {q} | {result['detected_pattern']}")
        assert "취업" in q, f"got: {q}"

    def test_part_time_only(self):
        result = _full("알바만 하는데 뭐 해당되는 거 있어?")
        q = result["bm25_query"]
        print(f"입력: 알바만 → {q} | {result['detected_pattern']}")
        assert any(kw in q for kw in ["취업", "근로", "일자리", "고용", "사회보험"]), f"got: {q}"

    def test_friend_at_home(self):
        result = _full("집에만 있는 친구 도와주는 거 어디서 해?")
        q = result["bm25_query"]
        print(f"입력: 집에만 있는 친구 → {q} | {result['detected_pattern']}")
        assert any(kw in q for kw in ["고립", "은둔", "멘토링", "사회참여"]), f"got: {q}"

    def test_allowance_slang(self):
        result = _full("서울 살면 용돈 받을 수 있다던데 조건이 뭐야?")
        q = result["bm25_query"]
        print(f"입력: 용돈 받을 수 → {q} | {result['detected_pattern']}")
        assert any(kw in q for kw in ["청년수당", "지원금", "수당"]), f"got: {q}"

    def test_unemployed_money(self):
        result = _full("백수인데 돈 받을 수 있는 거 있어?")
        q = result["bm25_query"]
        print(f"입력: 백수인데 돈 받을 수 → {q} | {result['detected_pattern']}")
        assert any(kw in q for kw in ["청년수당", "구직", "생활지원", "지원금"]), f"got: {q}"

    def test_no_deposit_housing(self):
        result = _full("보증금 없어서 집 못 구하겠는데 나도 지원받을 수 있어?")
        q = result["bm25_query"]
        print(f"입력: 보증금 없어서 집 못 구함 → {q} | {result['detected_pattern']}")
        assert any(kw in q for kw in ["임차보증금", "주거", "지원", "전세자금"]), f"got: {q}"


@needs_api_key
class TestHardIndirect:

    def test_monthly_amount(self):
        result = _full("월 50만원 받는 거 어디서 신청해?")
        q = result["bm25_query"]
        print(f"입력: 월 50만원 → {q} | {result['detected_pattern']}")
        assert any(kw in q for kw in ["수당", "지원금"]), f"got: {q}"

    def test_matching_savings(self):
        result = _full("매달 10만원씩 모으면 정부가 보태주는 거?")
        q = result["bm25_query"]
        print(f"입력: 모으면 보태줌 → {q} | {result['detected_pattern']}")
        assert any(kw in q for kw in ["저축", "매칭", "내일"]), f"got: {q}"

    def test_job_seeking_living_cost(self):
        result = _full("취준 중인데 생활비 지원받을 수 있다던데?")
        q = result["bm25_query"]
        print(f"입력: 생활비 지원 → {q} | {result['detected_pattern']}")
        assert any(kw in q for kw in ["청년수당", "구직", "지원금", "생활"]), f"got: {q}"

    def test_zero_interest_deposit(self):
        result = _full("보증금 무이자로 빌릴 수 있어?")
        q = result["bm25_query"]
        print(f"입력: 보증금 무이자 → {q} | {result['detected_pattern']}")
        assert any(kw in q for kw in ["임차보증금", "무이자", "대출", "주거"]), f"got: {q}"

    def test_age_bus_discount(self):
        result = _full("30살인데 버스비 할인 되나?")
        q = result["bm25_query"]
        print(f"입력: 30살 버스비 할인 → {q} | {result['detected_pattern']}")
        assert any(kw in q for kw in ["기후동행카드", "청년", "대중교통", "할인", "교통비"]), f"got: {q}"

    def test_interview_clothes(self):
        result = _full("28살인데 면접 볼 때 뭐 입고 가지...")
        q = result["bm25_query"]
        print(f"입력: 면접 뭐 입고 가지 → {q} | {result['detected_pattern']}")
        assert any(kw in q for kw in ["면접정장", "대여", "취업", "의류"]), f"got: {q}"

    def test_dobong_job_training(self):
        result = _full("도봉구 사는데 퇴근 후에 들을 수 있는 직무교육 있어?")
        q = result["bm25_query"]
        print(f"입력: 도봉구 퇴근 후 직무교육 → {q} | {result['detected_pattern']}")
        assert any(kw in q for kw in ["직무교육", "온라인", "부트캠프", "교육"]), f"got: {q}"

    def test_deposit_loan_interest_free(self):
        result = _full("전세 보증금 무이자로 빌려주는 거 어디서 신청해?")
        q = result["bm25_query"]
        print(f"입력: 전세 보증금 무이자 신청 → {q} | {result['detected_pattern']}")
        assert any(kw in q for kw in ["임차보증금", "무이자대출", "청년", "주거"]), f"got: {q}"


@needs_api_key
class TestHardAbstract:

    def test_want_to_learn(self):
        result = _full("배우고 싶은데 학비 지원 어디서 받아?")
        q = result["bm25_query"]
        print(f"입력: 배우고 싶어 → {q} | {result['detected_pattern']}")
        assert any(kw in q for kw in ["교육", "학습", "학비", "훈련"]), f"got: {q}"

    def test_dont_know_what_to_do(self):
        result = _full("뭔가 하고 싶은데 뭘 해야 될지 모르겠어")
        q = result["bm25_query"]
        print(f"입력: 뭘 해야 될지 → {q} | {result['detected_pattern']}")
        assert any(kw in q for kw in ["진로", "상담", "컨설팅", "역량", "취업"]), f"got: {q}"

    def test_counseling_needed(self):
        result = _full("뭘 해야 할지 모르겠어서 상담받고 싶어")
        q = result["bm25_query"]
        print(f"입력: 상담받고 싶어 → {q} | {result['detected_pattern']}")
        assert any(kw in q for kw in ["진로", "상담", "컨설팅", "코칭"]), f"got: {q}"

    def test_practical_experience(self):
        result = _full("실무 경험 쌓고 싶은데 어디 지원하면 돼?")
        q = result["bm25_query"]
        print(f"입력: 실무 경험 → {q} | {result['detected_pattern']}")
        assert any(kw in q for kw in ["인턴", "실습", "직무", "경력"]), f"got: {q}"

    def test_no_career_practical(self):
        result = _full("경력 없이 졸업만 했는데 실무 경험 쌓을 데 있어?")
        q = result["bm25_query"]
        print(f"입력: 경력 없이 실무 경험 → {q} | {result['detected_pattern']}")
        assert any(kw in q for kw in ["청년인턴", "인턴십", "직무체험", "현장실습"]), f"got: {q}"

    def test_marketing_free_learning(self):
        result = _full("마케팅 실무 배우고 싶은데 무료로 할 수 있어?")
        q = result["bm25_query"]
        print(f"입력: 마케팅 실무 무료 학습 → {q} | {result['detected_pattern']}")
        assert any(kw in q for kw in ["마케팅", "직무교육", "부트캠프", "무료", "교육"]), f"got: {q}"


# ============================================================================
# Hard: 종합 통과율
# ============================================================================

@needs_api_key
class TestHardCaseSummary:

    HARD_CASES = [
        ("대중교통 싸게 타는 방법 없어?", ["할인", "교통비", "기후동행"], "lexical_gap"),
        ("면접인데 입을 옷이 없어ㅠ 빌릴 수 있어?", ["정장", "대여", "의류"], "lexical_gap"),
        ("그림 그리는데 작업실 빌릴 수 있어?", ["예술", "창작", "문화", "스튜디오"], "lexical_gap"),
        ("우리 동네에서 가게 열고 싶은데 지원받을 수 있어?", ["창업", "로컬", "소상공인"], "lexical_gap"),
        ("창작하는 사람들 모이는 곳 어떻게 가?", ["청년예술청", "예술", "창작공간", "문화예술"], "abstract"),
        ("서른인데 동네 카페 창업 지원 가능해?", ["로컬크리에이터", "창업", "지역기반", "소상공인"], "easy"),
        ("방에서 안 나오는 동생도 도움받을 수 있어?", ["고립", "은둔"], "slang"),
        ("집에만 있는 친구 도와주는 거 어디서 해?", ["고립", "은둔", "멘토링", "사회참여"], "slang"),
        ("서울 살면 용돈 받을 수 있다던데 조건이 뭐야?", ["청년수당", "지원금", "수당"], "slang"),
        ("백수인데 돈 받을 수 있는 거 있어?", ["청년수당", "구직", "생활지원", "지원금"], "slang"),
        ("보증금 없어서 집 못 구하겠는데 나도 지원받을 수 있어?", ["임차보증금", "주거", "지원", "전세자금"], "slang"),
        ("월 50만원 받는 거 어디서 신청해?", ["수당", "지원금"], "indirect"),
        ("취준 중인데 생활비 지원받을 수 있다던데?", ["청년수당", "구직", "지원금", "생활"], "indirect"),
        ("보증금 무이자로 빌릴 수 있어?", ["임차보증금", "무이자", "대출", "주거"], "indirect"),
        ("30살인데 버스비 할인 되나?", ["기후동행카드", "청년", "대중교통", "할인", "교통비"], "lexical_gap"),
        ("28살인데 면접 볼 때 뭐 입고 가지...", ["면접정장", "대여", "취업", "의류"], "lexical_gap"),
        ("도봉구 사는데 퇴근 후에 들을 수 있는 직무교육 있어?", ["직무교육", "온라인", "부트캠프", "교육"], "easy"),
        ("전세 보증금 무이자로 빌려주는 거 어디서 신청해?", ["임차보증금", "무이자대출", "청년", "주거"], "indirect"),
        ("배우고 싶은데 학비 지원 어디서 받아?", ["교육", "학습", "학비", "훈련"], "abstract"),
        ("뭔가 하고 싶은데 뭘 해야 될지 모르겠어", ["진로", "상담", "컨설팅", "역량", "취업"], "abstract"),
        ("뭘 해야 할지 모르겠어서 상담받고 싶어", ["진로", "상담", "컨설팅", "코칭"], "abstract"),
        ("실무 경험 쌓고 싶은데 어디 지원하면 돼?", ["인턴", "실습", "직무", "경력"], "abstract"),
        ("경력 없이 졸업만 했는데 실무 경험 쌓을 데 있어?", ["청년인턴", "인턴십", "직무체험", "현장실습"], "abstract"),
        ("마케팅 실무 배우고 싶은데 무료로 할 수 있어?", ["마케팅", "직무교육", "부트캠프", "무료", "교육"], "abstract"),
    ]

    def test_hard_overall_pass_rate(self):
        """hard 케이스 키워드 통과율 80%+ 목표"""
        passed = 0
        pattern_correct = 0
        total = len(self.HARD_CASES)

        print("\n" + "=" * 70)
        print("HARD CASE 종합 결과")
        print("=" * 70)

        for query, expected_any, expected_pattern in self.HARD_CASES:
            result = _full(query)
            q = result["bm25_query"]
            hit = any(kw in q for kw in expected_any)
            pat_hit = result["detected_pattern"] == expected_pattern

            if hit:
                passed += 1
            if pat_hit:
                pattern_correct += 1

            print(f"{'✅' if hit else '❌'} {query}")
            print(f"   → {q}")
            print(f"   → intent: {result['intent_keywords']} | pattern: {result['detected_pattern']} ({'✅' if pat_hit else '⚠️'} 기대: {expected_pattern})")

        kw_rate = passed / total * 100
        pat_rate = pattern_correct / total * 100

        print(f"\n키워드 통과율: {passed}/{total} ({kw_rate:.0f}%)")
        print(f"패턴 분류 정확도: {pattern_correct}/{total} ({pat_rate:.0f}%)")
        print("=" * 70)

        assert kw_rate >= 80, f"Hard case 통과율 {kw_rate:.0f}% < 80%"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])