# -*- coding: utf-8 -*-
"""
ECOS(한국은행 경제통계시스템) 클라이언트 — 업종별 재무비율 벤치마크 조회

한국은행 「기업경영분석」 통계(ECOS 표 502Y002 손익지표, 502Y003 자산자본지표)에서
업종·규모별 재무비율을 조회한다. 하드코딩된 임의 값이 아니라 공식 통계를 실시간
조회하므로, 회사의 재무비율을 동종업계 실제 평균과 비교할 수 있다.

DART 표준산업분류 코드(induty_code) → ECOS 업종 코드 매핑을 제공한다.
"""
import os
import json
import time
import requests
from typing import Dict, Optional, Tuple

# ECOS 통계표 코드
TABLE_PROFIT = "502Y002"   # 5.2.2 손익 지표 (매출액영업이익률 등)
TABLE_ASSET = "502Y003"    # 5.2.3 자산/자본 지표 (부채비율 등)

# 규모 코드: A=종합, L=대기업, M=중소기업
SIZE_ALL, SIZE_LARGE, SIZE_SME = "A", "L", "M"

# 우리가 계산하는 비율 → (ECOS 표, 지표 코드)
METRIC_MAP = {
    "부채비율": (TABLE_ASSET, "2000"),
    "영업이익률": (TABLE_PROFIT, "3000"),  # 매출액영업이익률
}

# KSIC(한국표준산업분류) 앞 2자리 → ECOS 업종 코드
# ECOS 기업경영분석은 금융보험업(K, 64~66)을 포함하지 않으므로 해당 업종은 None
_KSIC_TO_ECOS = {
    # 제조업 세부 (C)
    **{f"{d:02d}": "2010" for d in (10, 11, 12)},   # 식음료담배
    **{f"{d:02d}": "2020" for d in (13, 14, 15)},   # 섬유의복가죽
    **{f"{d:02d}": "2030" for d in (16, 17, 18)},   # 목재종이인쇄
    **{f"{d:02d}": "2040" for d in (19, 20, 21, 22)},  # 석유화학
    "23": "2050",                                    # 비금속광물
    **{f"{d:02d}": "2060" for d in (24, 25)},        # 금속제품
    **{f"{d:02d}": "2070" for d in (26, 27, 28, 29)},  # 기계전기전자 (삼성전자 등)
    **{f"{d:02d}": "2080" for d in (30, 31)},        # 운송장비 (현대차 등)
    **{f"{d:02d}": "2090" for d in (32, 33, 34)},    # 가구및기타
    # 비제조 대분류
    "35": "4000",                                    # 전기가스
    **{f"{d:02d}": "5000" for d in (41, 42)},        # 건설
    **{f"{d:02d}": "7000" for d in (45, 46, 47)},    # 도소매
    **{f"{d:02d}": "8000" for d in (49, 50, 51, 52)},  # 운수
    **{f"{d:02d}": "9000" for d in (55, 56)},        # 숙박음식
    **{f"{d:02d}": "10000" for d in (58, 59, 60, 61, 62, 63)},  # 정보통신
    **{f"{d:02d}": "11000" for d in (70, 71, 72, 73, 74, 75)},  # 전문과학/사업지원
    **{f"{d:02d}": "12000" for d in (90, 91)},       # 예술스포츠
}

_ECOS_LABEL = {
    "2010": "식음료·담배", "2020": "섬유·의복·가죽", "2030": "목재·종이·인쇄",
    "2040": "석유·화학", "2050": "비금속광물", "2060": "금속제품",
    "2070": "기계·전기·전자", "2080": "운송장비", "2090": "가구·기타",
    "4000": "전기가스업", "5000": "건설업", "7000": "도소매업", "8000": "운수업",
    "9000": "숙박·음식점업", "10000": "정보통신업", "11000": "전문·과학·사업지원",
    "12000": "예술·스포츠·여가", "1000": "전산업",
}


def ksic_to_ecos_industry(induty_code: Optional[str]) -> Tuple[Optional[str], str]:
    """DART induty_code → (ECOS 업종코드, 업종명)

    매핑 실패 시 (None, 사유). 금융보험업 등 기업경영분석 미포함 업종은 None.
    """
    if not induty_code:
        return None, "업종코드 없음"
    prefix = str(induty_code).zfill(2)[:2]
    ecos = _KSIC_TO_ECOS.get(prefix)
    if ecos:
        return ecos, _ECOS_LABEL[ecos]
    # 금융보험업(64~66)은 기업경영분석 대상이 아님
    if prefix in ("64", "65", "66"):
        return None, "금융보험업 (기업경영분석 통계 대상 아님)"
    return None, f"매핑되지 않은 업종(KSIC {prefix})"


class ECOSClient:
    """ECOS 업종별 재무비율 벤치마크 조회 (파일 캐시로 반복 호출 최소화)"""

    BASE = "https://ecos.bok.or.kr/api/StatisticSearch"

    def __init__(self, api_key: str, cache_path: str = "analysis_results/ecos_cache.json"):
        self.api_key = api_key
        self.cache_path = cache_path
        self._cache = self._load_cache()

    def _load_cache(self) -> Dict:
        try:
            with open(self.cache_path, encoding="utf-8") as f:
                return json.load(f)
        except (OSError, json.JSONDecodeError):
            return {}

    def _save_cache(self):
        try:
            os.makedirs(os.path.dirname(self.cache_path), exist_ok=True)
            with open(self.cache_path, "w", encoding="utf-8") as f:
                json.dump(self._cache, f, ensure_ascii=False)
        except OSError:
            pass

    def get_benchmark(self, ecos_industry: str, metric: str, size: str = SIZE_ALL) -> Optional[Dict]:
        """업종·지표의 벤치마크 값 조회 (최근 4개 분기 평균)

        분기별 통계는 변동이 크고 최신 분기는 잠정치라 이상치가 섞일 수 있어,
        최근 4개 분기 평균(연간 근사, TTM)을 사용해 안정적인 벤치마크를 만든다.
        회사의 연간 재무제표와 비교하기에도 분기 스냅샷보다 적절하다.

        반환: {"value": float, "period": "2025Q2~2026Q1", "source": ...} 또는 None
        캐시 유효기간 7일 (분기 통계라 자주 바뀌지 않음).
        """
        if metric not in METRIC_MAP:
            return None
        table, metric_code = METRIC_MAP[metric]
        cache_key = f"{table}:{ecos_industry}:{size}:{metric_code}"

        cached = self._cache.get(cache_key)
        if cached and (time.time() - cached.get("_ts", 0) < 7 * 86400):
            return cached["data"]

        url = (f"{self.BASE}/{self.api_key}/json/kr/1/60/{table}/Q/"
               f"2023Q1/2026Q4/{ecos_industry}/{size}/{metric_code}/")
        try:
            resp = requests.get(url, timeout=15)
            rows = resp.json().get("StatisticSearch", {}).get("row", [])
        except (requests.RequestException, ValueError):
            return None

        valid = [r for r in rows if r.get("DATA_VALUE") not in (None, "")]
        if not valid:
            return None

        recent = valid[-4:]  # 최근 4개 분기
        avg = sum(float(r["DATA_VALUE"]) for r in recent) / len(recent)
        period = f"{recent[0].get('TIME','')}~{recent[-1].get('TIME','')}" if len(recent) > 1 else recent[-1].get("TIME", "")
        result = {
            "value": avg,
            "period": period,
            "source": "한국은행 기업경영분석 (ECOS), 최근 4개 분기 평균",
        }
        self._cache[cache_key] = {"_ts": time.time(), "data": result}
        self._save_cache()
        return result

    def compare(self, company_ratios: Dict, induty_code: Optional[str],
                size: str = SIZE_ALL) -> Optional[Dict]:
        """회사 비율을 동종업계 벤치마크와 비교

        세부 업종은 규모별 분리가 없어 '종합'(업종 전체 평균)을 기본으로 사용한다.

        반환: {"industry": 업종명, "period": ..., "items": [{지표, 회사값, 업종값, 판정}]}
        업종 매핑 불가 시 available=False.
        """
        ecos_industry, label = ksic_to_ecos_industry(induty_code)
        if not ecos_industry:
            return {"available": False, "reason": label}

        items = []
        period = ""
        for metric in METRIC_MAP:
            company_val = company_ratios.get(metric)
            if company_val is None:
                continue
            bench = self.get_benchmark(ecos_industry, metric, size)
            if not bench:
                continue
            period = bench["period"]
            # 부채비율은 낮을수록 우량, 나머지는 높을수록 우량
            lower_is_better = metric == "부채비율"
            better = (company_val < bench["value"]) if lower_is_better else (company_val > bench["value"])
            items.append({
                "metric": metric,
                "company": round(company_val, 1),
                "industry": round(bench["value"], 1),
                "verdict": "우량" if better else "열위",
            })

        if not items:
            return {"available": False, "reason": "비교 가능한 지표 없음"}

        return {
            "available": True,
            "industry": label,
            "size": {"L": "대기업", "M": "중소기업", "A": "업종 전체"}.get(size, size),
            "period": period,
            "source": "한국은행 기업경영분석 (ECOS)",
            "items": items,
        }
