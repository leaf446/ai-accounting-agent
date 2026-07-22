# -*- coding: utf-8 -*-
"""
core_agent_engine의 순수 로직 단위 테스트 (LLM/네트워크 불필요)

- 재무비율·부정지표 계산: 결정론적 산식 검증
- 등급 추출: 다양한 표기 대응과 실패 시 안전한 기본값
- 등급 분포·확신도: 판정 쏠림 계산 검증
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest

from core_agent_engine import AdvancedAuditAgent


@pytest.fixture
def agent():
    # DART 키는 초기화에만 저장되고 네트워크 호출은 없음
    return AdvancedAuditAgent(dart_api_key="test-key-not-used")


class TestRatioCalculation:
    """재무비율 계산 — LLM이 아닌 결정론적 파이썬 산식임을 보장"""

    def test_roe_and_debt_ratio(self, agent):
        financial_data = {
            "revenue": 1000,
            "operating_income": 100,
            "net_income": 80,
            "total_assets": 2000,
            "total_liabilities": 500,
            "total_equity": 1500,
        }
        ratios = agent._calculate_basic_ratios(financial_data)

        assert ratios["ROE"] == pytest.approx(80 / 1500 * 100)
        assert ratios["ROA"] == pytest.approx(80 / 2000 * 100)
        assert ratios["부채비율"] == pytest.approx(500 / 1500 * 100)
        assert ratios["영업이익률"] == pytest.approx(10.0)

    def test_zero_division_is_safe(self, agent):
        """자본이 0이어도 크래시 없이 기본값 0 반환"""
        ratios = agent._calculate_basic_ratios({"net_income": 100, "total_equity": 0})
        assert ratios["ROE"] == 0

    def test_growth_requires_prior_year(self, agent):
        financial_data = {"revenue": 1100, "net_income": 90}
        multi_year = {"2023": {"revenue": 1000, "net_income": 100}}
        ratios = agent._calculate_basic_ratios(financial_data, multi_year)

        assert ratios["매출성장률"] == pytest.approx(10.0)
        assert ratios["순이익성장률"] == pytest.approx(-10.0)


class TestFraudIndicators:
    def test_cash_flow_to_net_income(self, agent):
        indicators = agent._calculate_basic_fraud_indicators(
            {"revenue": 1000, "net_income": 100, "accounts_receivable": 200},
            {"operating_cash_flow": 95},
        )
        assert indicators["현금흐름_대_순이익_비율"] == pytest.approx(0.95)
        assert indicators["매출채권_대_매출_비율"] == pytest.approx(20.0)
        assert indicators["순이익_양수_현금흐름_음수"] is False

    def test_positive_income_negative_cashflow_flag(self, agent):
        """순이익은 흑자인데 현금흐름이 적자 — 대표적 부정 신호 플래그"""
        indicators = agent._calculate_basic_fraud_indicators(
            {"net_income": 100}, {"operating_cash_flow": -50}
        )
        assert indicators["순이익_양수_현금흐름_음수"] is True


class TestGradeExtraction:
    """LLM 자유 텍스트에서 등급을 안전하게 추출하는지"""

    @pytest.mark.parametrize("text,expected", [
        ("최종 투자등급은 A등급입니다.", "A"),
        ("등급: B (안정적)", "B"),
        ("**C** 등급으로 판단", "C"),
        ("Grade D로 평가함", "D"),
        ("등급 S를 부여합니다", "S"),
    ])
    def test_various_formats(self, agent, text, expected):
        assert agent._try_extract_grade(text) == expected

    def test_no_grade_returns_none(self, agent):
        assert agent._try_extract_grade("등급을 판단하기 어렵습니다.") is None

    def test_consensus_fallback_is_neutral_b(self, agent):
        """합의문에서 추출 실패 시 조용히 죽지 않고 중립 등급 B"""
        assert agent._extract_grade_from_consensus("판단 불가") == "B"


class TestGradeDistribution:
    """판정 분포와 확신도 — '확정이 아닌 판단 보조' 기능의 핵심 로직"""

    def test_distribution_counts_grades(self, agent):
        samples = ["A등급입니다", "등급: A", "B등급으로 판단", "등급 없음 텍스트"]
        dist = agent._build_grade_distribution(samples)
        assert dist == {"A": 2, "B": 1}

    def test_confidence_unanimous_is_90(self, agent):
        assert agent._distribution_confidence({"B": 9}) == 90

    def test_confidence_split_is_lower(self, agent):
        # 6/9 일치 → 50 + 40 * (6/9) ≈ 76
        assert agent._distribution_confidence({"B": 6, "C": 3}) == 76

    def test_confidence_empty_is_neutral_50(self, agent):
        assert agent._distribution_confidence({}) == 50

    def test_format_distribution_sorted_by_votes(self, agent):
        text = agent._format_distribution({"C": 1, "B": 6, "A": 2})
        assert text == "B 6표 · A 2표 · C 1표"
