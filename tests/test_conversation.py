# -*- coding: utf-8 -*-
"""
conversation_handler 질의 분류 단위 테스트

실사용 중 발견된 버그의 회귀 방지: 입력을 소문자화한 뒤 대문자 키워드("ROE")와
비교해 재무비율 질문이 일반 질의로 오분류되던 문제 (2026-07 수정).
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest

from conversation_handler import SmartConversationHandler


@pytest.fixture
def handler():
    # 분류 로직은 agent 엔진을 사용하지 않으므로 None으로 충분
    return SmartConversationHandler(None)


class TestQueryClassification:
    @pytest.mark.parametrize("query,expected", [
        # 대소문자 회귀 테스트 — 수정 전에는 전부 general_query로 오분류됐음
        ("ROE는 어때?", "ratio_query"),
        ("roe 좋아?", "ratio_query"),
        ("ROA랑 부채비율 알려줘", "ratio_query"),
        # 나머지 유형들
        ("부정 위험은 어느정도야?", "fraud_query"),
        ("보고서 만들어줘", "report_query"),
        ("업계 평균이랑 비교해줘", "comparison_query"),
        ("차트로 보여줘", "visualization_query"),
        ("삼성전자 분석해줘", "full_analysis"),
    ])
    def test_classification(self, handler, query, expected):
        assert handler._classify_query_type(query) == expected

    def test_unrelated_question_is_general(self, handler):
        assert handler._classify_query_type("오늘 저녁 뭐 먹지") == "general_query"


class TestRatioExtraction:
    def test_extracts_requested_ratios(self, handler):
        requested = handler._extract_requested_ratios("ROE랑 부채비율이 궁금해")
        assert "ROE" in requested
        assert "부채비율" in requested

    def test_no_ratio_mentioned(self, handler):
        assert handler._extract_requested_ratios("안녕하세요") == []
