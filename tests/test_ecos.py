# -*- coding: utf-8 -*-
"""
ecos_client의 순수 로직 단위 테스트 (네트워크 불필요)

- KSIC 업종코드 → ECOS 업종 매핑
- 비교 판정 로직 (get_benchmark를 목으로 대체)
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest

from ecos_client import ksic_to_ecos_industry, ECOSClient


class TestKsicMapping:
    @pytest.mark.parametrize("ksic,expected_code,expected_label", [
        ("264", "2070", "기계·전기·전자"),    # 삼성전자 (앞 2자리 26)
        ("30121", "2080", "운송장비"),         # 현대차 (30)
        ("47", "7000", "도소매업"),            # 유통
        ("62", "10000", "정보통신업"),         # IT
        ("41", "5000", "건설업"),
    ])
    def test_maps_to_industry(self, ksic, expected_code, expected_label):
        code, label = ksic_to_ecos_industry(ksic)
        assert code == expected_code
        assert label == expected_label

    def test_financial_industry_excluded(self):
        """금융보험업은 기업경영분석 통계 대상이 아니므로 매핑 없음"""
        code, reason = ksic_to_ecos_industry("64992")
        assert code is None
        assert "금융" in reason

    def test_missing_code(self):
        code, reason = ksic_to_ecos_industry(None)
        assert code is None


class TestCompareVerdict:
    """비교 판정: 부채비율은 낮을수록, 영업이익률은 높을수록 우량"""

    def _client_with_fake_benchmark(self, industry_values):
        client = ECOSClient.__new__(ECOSClient)  # __init__ 우회 (네트워크/파일 없이)
        client._cache = {}
        client.get_benchmark = lambda ind, metric, size="A": (
            {"value": industry_values[metric], "period": "테스트"} if metric in industry_values else None
        )
        return client

    def test_low_debt_high_margin_is_superior(self):
        client = self._client_with_fake_benchmark({"부채비율": 60.0, "영업이익률": 10.0})
        result = client.compare({"부채비율": 30.0, "영업이익률": 15.0}, "264")
        verdicts = {i["metric"]: i["verdict"] for i in result["items"]}
        assert verdicts["부채비율"] == "우량"   # 30 < 60
        assert verdicts["영업이익률"] == "우량"  # 15 > 10

    def test_high_debt_low_margin_is_inferior(self):
        client = self._client_with_fake_benchmark({"부채비율": 60.0, "영업이익률": 10.0})
        result = client.compare({"부채비율": 90.0, "영업이익률": 5.0}, "264")
        verdicts = {i["metric"]: i["verdict"] for i in result["items"]}
        assert verdicts["부채비율"] == "열위"
        assert verdicts["영업이익률"] == "열위"

    def test_financial_company_unavailable(self):
        client = self._client_with_fake_benchmark({"부채비율": 60.0})
        result = client.compare({"부채비율": 500.0}, "64992")
        assert result["available"] is False
