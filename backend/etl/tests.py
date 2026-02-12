from datetime import date

from django.test import SimpleTestCase

from etl.services.transformer import PolicyTransformer, ZIPCD_TO_DISTRICT


class PolicyTransformerDateFixTests(SimpleTestCase):
    def setUp(self):
        self.transformer = PolicyTransformer()

    def test_parse_date_with_year_fix_2024_to_2026(self):
        parsed = self.transformer._parse_date_with_year_fix("20240916")
        self.assertEqual(parsed, date(2026, 9, 16))

    def test_parse_date_with_year_fix_2025_to_2026(self):
        parsed = self.transformer._parse_date_with_year_fix("20250630")
        self.assertEqual(parsed, date(2026, 6, 30))

    def test_parse_date_with_year_fix_2026_unchanged(self):
        parsed = self.transformer._parse_date_with_year_fix("20260101")
        self.assertEqual(parsed, date(2026, 1, 1))

    def test_parse_date_range_with_year_fix(self):
        start, end = self.transformer._parse_date_range_with_year_fix("20240916 ~ 20251231")
        self.assertEqual(start, date(2026, 9, 16))
        self.assertEqual(end, date(2026, 12, 31))

    def test_normalize_text_years(self):
        self.assertEqual(
            self.transformer._normalize_text_years("2024 청년 2025 지원"),
            "2026 청년 2026 지원"
        )

    def test_transform_keeps_policy_id_and_normalizes_text_fields(self):
        raw = {
            "plcyNo": "P-001",
            "plcyNm": "2024 청년 일자리 정책",
            "plcyExplnCn": "2025년 신청 가능",
            "plcySprtCn": "2024~2025 지원금",
            "plcyAplyMthdCn": "2025 온라인 신청",
            "aplyYmd": "20240916 ~ 20251231",
        }

        transformed = self.transformer.transform(raw)

        self.assertEqual(transformed.policy_id, "P-001")
        self.assertIn("2026", transformed.title)
        self.assertIn("2026", transformed.description)
        self.assertIn("2026", transformed.support_content)
        self.assertIn("2026", transformed.apply_method)


class PolicyTransformerDistrictTests(SimpleTestCase):
    def setUp(self):
        self.transformer = PolicyTransformer()

    def test_zipcd_to_district(self):
        self.assertEqual(self.transformer._parse_district('11380', ''), '은평구')

    def test_zipcd_gangnam(self):
        self.assertEqual(self.transformer._parse_district('11680', ''), '강남구')

    def test_zipcd_11000_returns_none(self):
        """11000은 서울시 전체 → 구 제한 없음(None)"""
        self.assertIsNone(self.transformer._parse_district('11000', ''))

    def test_zipcd_comma_multiple_returns_none(self):
        """쉼표 다중 코드 → 구 제한 없음(None)"""
        self.assertIsNone(self.transformer._parse_district('11380,11680', ''))

    def test_fallback_to_rgtr_inst(self):
        """zipCd 없으면 rgtrInstCdNm에서 추출"""
        self.assertEqual(
            self.transformer._parse_district('', '서울특별시 마포구'),
            '마포구'
        )

    def test_fallback_seoul_city_returns_none(self):
        self.assertIsNone(self.transformer._parse_district('', '서울특별시'))

    def test_both_empty_returns_none(self):
        self.assertIsNone(self.transformer._parse_district('', ''))

    def test_all_25_districts_mapped(self):
        """25개 구 코드가 전부 매핑되어 있는지"""
        self.assertEqual(len(ZIPCD_TO_DISTRICT), 25)
