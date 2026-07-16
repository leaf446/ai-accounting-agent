# core/agent_engine.py
"""
고급 감사 에이전트 AI - 완전 A2A 협업 버전 (ROE 문제 해결)
모든 분석이 항상 3개 AI의 협업으로 실행됨
"""

import requests
import json
import pandas as pd
from datetime import datetime, timedelta
import time
import os
import math
import re
from typing import Dict, List, Optional, Any
import xml.etree.ElementTree as ET
import zipfile
import io

class AdvancedAuditAgent:
    """완전 A2A 협업 고급 감사 에이전트 AI"""
    
    def __init__(self, dart_api_key: str):
        self.dart_api_key = dart_api_key
        self.dart_base_url = "https://opendart.fss.or.kr/api"
        self.ollama_url = "http://localhost:11434/api/generate"
        
        # A2A 전문 에이전트 정의 (항상 활성화)
        self.agents = {
            "coordinator": {
                "model": "llama3.1:8b",
                "name": "김성실 (총괄조정관)",
                "role": "전체 조율 및 합의 도출",
                "personality": "신중하고 균형잡힌 시각, 갈등 조정 전문가"
            },
            "financial_analyst": {
                "model": "qwen2.5:7b",
                "name": "이정확 (재무분석가)",
                "role": "재무분석 및 비율 해석 전문가",
                "personality": "정확하고 분석적, 데이터 기반 판단"
            },
            "fraud_detective": {
                "model": "mistral:7b",
                "name": "박의심 (부정탐지전문가)",
                "role": "부정탐지 및 위험평가 전문가",
                "personality": "의심 많고 철저함, 보수적 접근"
            }
        }
        
        self.current_loaded_model = None
        self.work_directory = "analysis_results"
        self.agent_log = []
        self.conversation_memory = {}
        self.discussion_log = []  # A2A 토론 기록
        
        self._setup_directories()
        print("🤖 A2A 협업 시스템 활성화 완료! 모든 분석이 AI 협업으로 실행됩니다.")

    def _setup_directories(self):
        """작업 디렉토리 설정"""
        directories = [
            self.work_directory,
            f"{self.work_directory}/reports",
            f"{self.work_directory}/data", 
            f"{self.work_directory}/charts",
            f"{self.work_directory}/documents"
        ]
        
        for directory in directories:
            os.makedirs(directory, exist_ok=True)

    def load_model(self, model_name: str):
        """모델 전환 기록 (실제 로딩/언로딩은 Ollama 서버가 요청 시점에 수행)"""
        if self.current_loaded_model == model_name:
            return

        print(f"🔄 모델 전환: {model_name}")
        self.current_loaded_model = model_name

    def call_ollama(self, model_key: str, prompt: str) -> str:
        """Ollama API 호출"""
        model_name = self.agents[model_key]["model"]
        self.load_model(model_name)
        
        data = {
            "model": model_name,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.7,
                "top_p": 0.9,
                "top_k": 40,
                "num_predict": 2000
            }
        }
        
        try:
            response = requests.post(self.ollama_url, json=data, timeout=180)
            if response.status_code == 200:
                return response.json().get("response", "응답 없음")
            else:
                return f"API 오류 {response.status_code}"
        except Exception as e:
            return f"연결 오류: {str(e)}"

    def log_agent_action(self, step: str, action: str, result: str, model_used: str):
        """에이전트 행동 로깅"""
        log_entry = {
            "timestamp": datetime.now().strftime("%H:%M:%S"),
            "step": step,
            "action": action,
            "model": model_used,
            "result": result[:300] + "..." if len(result) > 300 else result
        }
        self.agent_log.append(log_entry)

    # === DART API 연동 메서드들 ===
    
    def search_company_dart(self, company_name: str) -> Optional[Dict]:
        """DART API로 회사 검색"""
        print(f"🔍 DART에서 '{company_name}' 검색 중...")
        
        try:
            url = "https://opendart.fss.or.kr/api/corpCode.xml"
            params = {'crtfc_key': self.dart_api_key}
            
            response = requests.get(url, params=params, timeout=15)
            if response.status_code == 200:
                zip_file = zipfile.ZipFile(io.BytesIO(response.content))
                xml_data = zip_file.read('CORPCODE.xml').decode('utf-8')
                root = ET.fromstring(xml_data)
                
                candidates = []
                exact_match = None
                
                for corp in root.findall('list'):
                    corp_name = corp.find('corp_name').text if corp.find('corp_name') is not None else ""
                    corp_code = corp.find('corp_code').text if corp.find('corp_code') is not None else ""
                    stock_code = corp.find('stock_code').text if corp.find('stock_code') is not None else ""
                    
                    if company_name in corp_name:
                        company_info = {
                            'corp_name': corp_name,
                            'corp_code': corp_code,
                            'stock_code': stock_code if stock_code and stock_code.strip() else 'N/A'
                        }
                        
                        if corp_name == company_name:
                            exact_match = company_info
                        candidates.append(company_info)
                
                if exact_match:
                    return exact_match
                elif candidates:
                    return {"candidates": candidates[:5], "exact_match": False}
                else:
                    return None
            else:
                return None
                
        except Exception as e:
            print(f"❌ 검색 오류: {str(e)}")
            return self._fallback_company_search(company_name)
        
    def _fallback_company_search(self, company_name: str) -> Optional[Dict]:
        """백업 회사 검색"""
        major_companies = {
            "삼성전자": {"corp_name": "삼성전자주식회사", "corp_code": "00126380", "stock_code": "005930"},
            "LG전자": {"corp_name": "엘지전자주식회사", "corp_code": "00401731", "stock_code": "066570"},
            "현대자동차": {"corp_name": "현대자동차주식회사", "corp_code": "00164779", "stock_code": "005380"},
            "SK하이닉스": {"corp_name": "에스케이하이닉스주식회사", "corp_code": "00164742", "stock_code": "000660"},
            "네이버": {"corp_name": "네이버주식회사", "corp_code": "00401517", "stock_code": "035420"},
            "카카오": {"corp_name": "주식회사카카오", "corp_code": "00401062", "stock_code": "035720"}
        }
        
        if company_name in major_companies:
            return major_companies[company_name]
        
        candidates = [value for key, value in major_companies.items() if company_name in key or key in company_name]
        return {"candidates": candidates, "exact_match": False} if candidates else None

    def get_financial_statements(self, corp_code: str, year: str = "2024") -> Dict:
        """재무제표 조회 (개선된 파싱)"""
        print(f"📊 {year}년 재무제표 조회 중...")
        
        url = f"{self.dart_base_url}/fnlttSinglAcntAll.json"
        params = {
            'crtfc_key': self.dart_api_key,
            'corp_code': corp_code,
            'bsns_year': year,
            'reprt_code': '11011',
            'fs_div': 'CFS'
        }
        
        try:
            response = requests.get(url, params=params, timeout=15)
            if response.status_code == 200:
                data = response.json()
                print(f"📊 DART API 응답 상태: {data.get('status')}")
                if data['status'] == '000' and data['list']:
                    print(f"📋 수집된 재무 항목 수: {len(data['list'])}개")
                    return self.parse_financial_statements(data['list'])
                else:
                    print(f"❌ {year}년 재무데이터 없음: {data.get('message')}")
                    return {}
            else:
                return {}
        except Exception as e:
            print(f"❌ 재무제표 조회 오류: {str(e)}")
            return {}

    def get_cash_flow_statement(self, corp_code: str, year: str = "2024") -> Dict:
        """현금흐름표 조회"""
        print(f"💰 {year}년 현금흐름표 조회 중...")
        
        url = f"{self.dart_base_url}/fnlttSinglAcntAll.json"
        params = {
            'crtfc_key': self.dart_api_key,
            'corp_code': corp_code,
            'bsns_year': year,
            'reprt_code': '11011',
            'fs_div': 'CFS'
        }
        
        try:
            response = requests.get(url, params=params, timeout=15)
            if response.status_code == 200:
                data = response.json()
                if data['status'] == '000' and data['list']:
                    return self.parse_cash_flow_data(data['list'])
                else:
                    return {}
            else:
                return {}
        except Exception as e:
            print(f"❌ 현금흐름표 조회 오류: {str(e)}")
            return {}

    def get_multi_year_financials(self, corp_code: str, years: List[str] = None) -> Dict:
        """다년도 재무 데이터 조회"""
        if years is None:
            years = ['2024', '2023', '2022']
        
        print(f"📅 {len(years)}년간 재무 데이터 조회 중...")
        
        multi_year_data = {}
        for year in years:
            financial_data = self.get_financial_statements(corp_code, year)
            if financial_data:
                multi_year_data[year] = financial_data
                time.sleep(1)
        
        return multi_year_data

    def parse_financial_statements(self, financial_list: List[Dict]) -> Dict:
        """🔧 개선된 재무제표 데이터 파싱"""
        financial_data = {}
        
        print(f"📋 전체 재무제표 항목 수: {len(financial_list)}개")
        
        # 🔧 더 포괄적인 계정명 매칭 (카카오 등을 위해)
        target_accounts = {
            # 기타 (매출채권 우선)
            '현금및현금성자산': 'cash_and_equivalents',
            '매출채권': 'accounts_receivable',
            '재고자산': 'inventory',
            '매출총이익': 'gross_profit',

            # 매출 관련 (다양한 표현)
            '매출액': 'revenue',
            '수익(매출액)': 'revenue', 
            '영업수익': 'revenue',
            '매출': 'revenue',
            '수익': 'revenue',
            
            # 영업이익 관련
            '영업이익': 'operating_income', 
            '영업이익(손실)': 'operating_income',
            '영업손익': 'operating_income',
            
            # 순이익 관련 (카카오를 위해 추가)
            '당기순이익': 'net_income',
            '당기순이익(손실)': 'net_income',
            '연결당기순이익': 'net_income',
            '순이익': 'net_income',
            '당기순손익': 'net_income',
            '지배기업소유주지분당기순이익': 'net_income',  # 카카오용
            '지배기업소유주지분당기순손익': 'net_income',  # 카카오용
            
            # 자산 관련
            '자산총계': 'total_assets',
            '총자산': 'total_assets',
            
            # 부채 관련
            '부채총계': 'total_liabilities',
            '총부채': 'total_liabilities',
            
            # 자본 관련 (카카오를 위해 추가)
            '자본총계': 'total_equity',
            '자기자본': 'total_equity',
            '연결자본총계': 'total_equity',
            '총자본': 'total_equity',
            '지배기업소유주지분': 'total_equity',  # 카카오용
        }
        
        # 손익계산서와 재무상태표만 필터링
        relevant_items = []
        for item in financial_list:
            sj_nm = item.get('sj_nm', '').strip()
            if sj_nm in ['손익계산서', '재무상태표', '포괄손익계산서']:
                relevant_items.append(item)
        
        print(f"📊 관련 항목 수 (손익계산서/재무상태표): {len(relevant_items)}개")
        
        found_items = []
        
        for item in relevant_items:
            account_nm = item.get('account_nm', '').strip()
            sj_nm = item.get('sj_nm', '').strip()
            
            # 대괄호 및 특수문자 제거
            account_nm_cleaned = re.sub(r'\[.*?\]', '', account_nm).strip()
            account_nm_cleaned = re.sub(r'\(.*?\)', '', account_nm_cleaned).strip()
            
            current_amount = item.get('thstrm_amount', '0')
            if isinstance(current_amount, str):
                current_amount = current_amount.replace(',', '').replace(' ', '')

            try:
                if current_amount and current_amount not in ['0', '', '-', 'nan']:
                    amount = int(float(current_amount))
                else:
                    amount = 0
            except:
                amount = 0

            # 🔧 개선된 매칭 로직
            for target_name, key in target_accounts.items():
                # 정확한 매칭 우선
                if account_nm_cleaned == target_name:
                    if amount != 0:
                        financial_data[key] = amount
                        found_items.append(f"[{sj_nm}] {target_name} = {amount:,} (정확매칭)")
                        print(f"✅ 정확매칭: [{sj_nm}] {account_nm_cleaned} → {target_name} = {amount:,}")
                        break
                # 부분 매칭
                elif target_name in account_nm_cleaned or account_nm_cleaned in target_name:
                    if key not in financial_data or financial_data[key] == 0:
                        if amount != 0:
                            financial_data[key] = amount
                            found_items.append(f"[{sj_nm}] {target_name} = {amount:,} (부분매칭)")
                            print(f"✅ 부분매칭: [{sj_nm}] {account_nm_cleaned} → {target_name} = {amount:,}")
                            break
        
        print(f"📊 총 {len(found_items)}개 항목 파싱 완료")
        
        # 🔧 파싱 결과 상세 출력
        print(f"🔍 파싱된 재무 데이터:")
        for key, value in financial_data.items():
            if value != 0:
                formatted = self.format_currency(value)
                print(f"  {key}: {formatted}")
        
        # 🔧 중요: 순이익이 0인 경우 경고
        if financial_data.get('net_income', 0) == 0:
            print("⚠️ 경고: 순이익이 0으로 파싱되었습니다. ROE 계산에 영향을 줄 수 있습니다.")
            print("🔍 관련 계정명들:")
            for item in relevant_items:
                account_nm = item.get('account_nm', '')
                if '순이익' in account_nm or '당기' in account_nm:
                    amount = item.get('thstrm_amount', '0')
                    print(f"    - {account_nm}: {amount}")
        
        return financial_data

    def parse_cash_flow_data(self, financial_list: List[Dict]) -> Dict:
        """현금흐름표 데이터 파싱"""
        cash_flow_data = {}
        
        cash_flow_accounts = {
            '영업활동현금흐름': 'operating_cash_flow',
            '영업활동으로인한현금흐름': 'operating_cash_flow',
            '투자활동현금흐름': 'investing_cash_flow',
            '재무활동현금흐름': 'financing_cash_flow'
        }
        
        cf_items = [item for item in financial_list if item.get('sj_nm') == '현금흐름표']
        print(f"💰 현금흐름표 항목 수: {len(cf_items)}개")
        
        for item in cf_items:
            account_nm = item.get('account_nm', '').strip()
            current_amount = item.get('thstrm_amount', '0').replace(',', '')
            
            try:
                amount = int(current_amount) if current_amount.lstrip('-').isdigit() else 0
            except:
                amount = 0
            
            for target_name, key in cash_flow_accounts.items():
                if target_name in account_nm:
                    cash_flow_data[key] = amount
                    print(f"💰 발견: {account_nm} = {amount:,}")
                    break
        
        return cash_flow_data

    # === 🤖 A2A 협업 핵심 메서드들 ===
    
    def calculate_comprehensive_ratios(self, financial_data: Dict, multi_year_data: Dict = None) -> Dict:
        """🤖 항상 A2A 협업으로 재무비율 분석"""
        print("🤖🤖🤖 A2A 협업 재무비율 분석 시작! 🤖🤖🤖")
        
        # 1단계: 기본 수치 계산
        basic_ratios = self._calculate_basic_ratios(financial_data, multi_year_data)
        
        # 🔧 ROE 검증
        roe = basic_ratios.get('ROE', 0)
        if roe == 0:
            print("⚠️ ROE가 0%입니다. 재무 데이터를 확인해보겠습니다.")
            net_income = financial_data.get('net_income', 0)
            total_equity = financial_data.get('total_equity', 0)
            print(f"순이익: {self.format_currency(net_income)}")
            print(f"자기자본: {self.format_currency(total_equity)}")
        
        # 2단계: A2A 협업 분석 (항상 실행)
        discussion_results = self._conduct_ratio_discussion(basic_ratios, financial_data)
        
        # 3단계: 결과 통합
        enhanced_ratios = basic_ratios.copy()
        enhanced_ratios.update({
            'A2A_투자등급': discussion_results['investment_grade'],
            'A2A_토론결과': discussion_results['final_consensus'],
            'A2A_확신도': discussion_results['confidence_level'],
            'A2A_분석시간': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })
        
        print("✅ A2A 협업 재무비율 분석 완료!")
        return enhanced_ratios

    def calculate_fraud_detection_ratios(self, financial_data: Dict, cash_flow_data: Dict) -> Dict:
        """🕵️ 항상 A2A 협업으로 부정위험 분석"""
        print("🕵️🕵️🕵️ A2A 협업 부정위험 분석 시작! 🕵️🕵️🕵️")
        
        # 1단계: 기본 지표 계산
        basic_indicators = self._calculate_basic_fraud_indicators(financial_data, cash_flow_data)
        
        # 2단계: A2A 협업 부정위험 토론 (항상 실행)
        fraud_discussion = self._conduct_fraud_discussion(basic_indicators, financial_data)
        
        # 3단계: 결과 통합
        enhanced_fraud_ratios = basic_indicators.copy()
        enhanced_fraud_ratios.update({
            'A2A_부정위험등급': fraud_discussion['risk_grade'],
            'A2A_위험토론결과': fraud_discussion['final_consensus'],
            'A2A_위험확신도': fraud_discussion['confidence_level'],
            'A2A_분석시간': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })
        
        print("✅ A2A 협업 부정위험 분석 완료!")
        return enhanced_fraud_ratios

    def autonomous_settlement_processing(self, user_request: str) -> Dict[str, Any]:
        """🎯 완전 A2A 자율 결산 처리 (항상 협업 모드)"""
        
        print(f"🎯🎯🎯 완전 A2A 협업 자율 처리 시작: {user_request} 🎯🎯🎯")
        
        try:
            # 1단계: 회사명 추출
            company_name = self._extract_company_from_request(user_request)
            if not company_name:
                return {"error": "회사명을 찾을 수 없습니다."}
            
            # 2단계: DART 데이터 수집
            company_info = self.search_company_dart(company_name)
            if not company_info:
                return {"error": f"'{company_name}' 검색 결과가 없습니다."}
            
            if "candidates" in company_info:
                company_info = company_info["candidates"][0]
            
            corp_code = company_info.get("corp_code")
            financial_data = self.get_financial_statements(corp_code)
            cash_flow_data = self.get_cash_flow_statement(corp_code)
            multi_year_data = self.get_multi_year_financials(corp_code)
            
            # 3단계: A2A 협업 재무비율 분석 (항상 실행)
            print("🤖 A2A 재무비율 협업 분석...")
            ratios = self.calculate_comprehensive_ratios(financial_data, multi_year_data)
            
            # 4단계: A2A 협업 부정위험 분석 (항상 실행)
            print("🕵️ A2A 부정위험 협업 분석...")
            fraud_ratios = self.calculate_fraud_detection_ratios(financial_data, cash_flow_data)
            
            # 5단계: 최종 A2A 투자 의견 합의 (항상 실행)
            print("🏆 A2A 최종 투자 의견 합의...")
            final_opinion = self._conduct_final_investment_discussion(ratios, fraud_ratios, company_name)
            
            # 6단계: 결과 통합
            analysis_data = {
                "company": company_name,
                "company_info": company_info,
                "financial_data": financial_data,
                "cash_flow_data": cash_flow_data,
                "multi_year_data": multi_year_data,
                "ratios": ratios,
                "fraud_ratios": fraud_ratios,
                "final_a2a_opinion": final_opinion,
                "timestamp": datetime.now()
            }
            
            # 컨텍스트 저장
            self.save_analysis_context(company_name, analysis_data)
            
            print("🎉 완전 A2A 협업 분석 완료!")
            
            return {
                "analysis_complete": True,
                "company": company_name,
                "final_analysis": final_opinion['final_consensus'],
                "investment_grade": ratios['A2A_투자등급'],
                "risk_grade": fraud_ratios['A2A_부정위험등급'],
                "data": analysis_data,
                "a2a_summary": self._generate_a2a_summary(analysis_data),
                "discussion_log_count": len(self.discussion_log)
            }
            
        except Exception as e:
            return {"error": f"A2A 협업 처리 오류: {str(e)}"}

    # === A2A 협업 핵심 로직 ===
    
    def _run_discussion_rounds(self, opinions: Dict, topic: str, rounds: int = 2) -> Dict:
        """스냅샷 기반 토론 라운드 진행

        매 라운드마다 '직전 라운드' 의견의 스냅샷을 만들어 전원에게 동일하게 보여주고,
        각자 의견을 수정하게 한다. 수정본을 즉시 덮어쓰지 않으므로 발언 순서에 따른
        정보 비대칭(뒤 순서일수록 최신 정보를 더 많이 보는 문제)이 발생하지 않는다.
        """
        for round_num in range(1, rounds + 1):
            print(f"🗣️ {topic} 토론 라운드 {round_num}/{rounds}")
            snapshot = dict(opinions)  # 이번 라운드에서 전원이 공유하는 동일한 스냅샷
            updated = {}
            for agent_key in self.agents.keys():
                other_opinions = [
                    f"{self.agents[k]['name']}: {v[:600]}"
                    for k, v in snapshot.items() if k != agent_key
                ]

                discussion_prompt = f"""
{topic}에 대한 토론 {round_num}라운드입니다.
다른 전문가들의 의견을 검토하고, 동의/반박 근거와 함께 당신의 수정된 의견을 제시해주세요.

다른 의견들:
{chr(10).join(other_opinions)}

수정된 등급과 근거를 명확히 제시해주세요.
"""
                updated[agent_key] = self._call_agent_with_persona(agent_key, discussion_prompt)
            opinions = updated
        return opinions

    def _conduct_ratio_discussion(self, ratios: Dict, financial_data: Dict) -> Dict:
        """재무비율 A2A 토론"""

        # 각 AI의 초기 의견 수집
        opinions = {}
        for agent_key, agent in self.agents.items():
            prompt = f"""
재무비율 분석 결과를 검토해주세요.

주요 비율:
- ROE: {ratios.get('ROE', 0):.2f}%
- 부채비율: {ratios.get('부채비율', 0):.2f}%
- 영업이익률: {ratios.get('영업이익률', 0):.2f}%
- 순이익률: {ratios.get('순이익률', 0):.2f}%

당신의 전문 분야 관점에서 투자 등급(S/A/B/C/D)과 근거를 제시해주세요.
"""
            opinion = self._call_agent_with_persona(agent_key, prompt)
            opinions[agent_key] = opinion

        # 스냅샷 기반 토론 (2라운드): 전원이 같은 정보를 보고 수정
        opinions = self._run_discussion_rounds(opinions, "재무비율 투자등급", rounds=2)

        # 최종 합의 도출
        final_consensus = self._reach_consensus(opinions, "투자등급")
        
        return {
            "final_consensus": final_consensus,
            "investment_grade": self._extract_grade_from_consensus(final_consensus),
            "confidence_level": self._calculate_agreement_confidence(opinions)
        }

    def _conduct_fraud_discussion(self, indicators: Dict, financial_data: Dict) -> Dict:
        """부정위험 A2A 토론"""
        
        risk_opinions = {}
        for agent_key, agent in self.agents.items():
            prompt = f"""
부정위험 지표를 분석해주세요.

주요 지표:
- 현금흐름 대 순이익 비율: {indicators.get('현금흐름_대_순이익_비율', 0):.2f}
- 매출채권 대 매출 비율: {indicators.get('매출채권_대_매출_비율', 0):.2f}%
- 순이익 양수 현금흐름 음수: {indicators.get('순이익_양수_현금흐름_음수', False)}

부정위험 등급(A/B/C/D)과 근거를 제시해주세요.
"""
            opinion = self._call_agent_with_persona(agent_key, prompt)
            risk_opinions[agent_key] = opinion

        # 기존에는 초기 의견만 모아 바로 합의로 직행했음 → 상호 검토 라운드 1회 추가
        risk_opinions = self._run_discussion_rounds(risk_opinions, "부정위험등급", rounds=1)

        print("🕵️ 부정위험 합의 도출")
        final_risk_consensus = self._reach_consensus(risk_opinions, "부정위험등급")
        
        return {
            "final_consensus": final_risk_consensus,
            "risk_grade": self._extract_grade_from_consensus(final_risk_consensus),
            "confidence_level": self._calculate_agreement_confidence(risk_opinions)
        }

    def _conduct_final_investment_discussion(self, ratios: Dict, fraud_ratios: Dict, company_name: str) -> Dict:
        """최종 투자 의견 A2A 합의"""
        
        investment_grade = ratios.get('A2A_투자등급', 'B')
        risk_grade = fraud_ratios.get('A2A_부정위험등급', 'B')
        
        final_prompt = f"""
{company_name}에 대한 최종 투자 의견을 합의해주세요.

재무분석 결과: 투자등급 {investment_grade}
부정위험 결과: 위험등급 {risk_grade}

최종 투자 권고사항과 핵심 근거를 제시해주세요.
"""
        
        final_opinions = {}
        for agent_key in self.agents.keys():
            opinion = self._call_agent_with_persona(agent_key, final_prompt)
            final_opinions[agent_key] = opinion
        
        final_consensus = self._reach_consensus(final_opinions, "최종투자의견")

        return {
            "final_consensus": final_consensus,
            "investment_grade": investment_grade,
            "confidence_level": self._calculate_agreement_confidence(final_opinions)
        }

    # === 헬퍼 메서드들 ===
    
    def _call_agent_with_persona(self, agent_key: str, prompt: str) -> str:
        """페르소나를 적용하여 AI 에이전트 호출"""
        agent = self.agents[agent_key]
        
        persona_prompt = f"""
당신은 {agent['name']}입니다.
역할: {agent['role']}
성격: {agent['personality']}

다음 요청에 대해 당신의 전문성과 성격에 맞게 간결하게 응답해주세요.
반드시 한국어로만 답변하세요:

{prompt}
"""
        
        # 토론 기록
        self.discussion_log.append({
            "timestamp": datetime.now().strftime("%H:%M:%S"),
            "speaker": agent['name'],
            "prompt": prompt[:100] + "...",
            "response": "응답 대기 중..."
        })
        
        response = self.call_ollama(agent_key, persona_prompt)
        
        # 토론 기록 업데이트
        if self.discussion_log:
            self.discussion_log[-1]["response"] = response[:200] + "..."
        
        return response

    def _reach_consensus(self, opinions: Dict, topic: str) -> str:
        """여러 의견을 바탕으로 합의 도출"""
        
        consensus_prompt = f"""
다음 전문가들의 {topic}에 대한 의견들을 종합하여 최종 합의안을 도출해주세요.

전문가 의견들:
"""
        for agent_key, opinion in opinions.items():
            agent_name = self.agents[agent_key]['name']
            consensus_prompt += f"\n{agent_name}: {opinion[:300]}...\n"
        
        consensus_prompt += f"""
이들 의견을 종합하여 균형잡힌 최종 결론을 제시해주세요.
"""
        
        return self.call_ollama("coordinator", consensus_prompt)

    def _try_extract_grade(self, text: str) -> Optional[str]:
        """텍스트에서 등급(S/A/B/C/D) 추출 시도. 실패 시 None"""
        # "A등급", "등급 A", "등급: A", "투자등급은 B", "Grade A", "**B**" 등 다양한 표기 대응
        patterns = [
            r"([SABCD])\s*등급",
            r"등급\s*[:은는]?\s*['\"]?([SABCD])\b",
            r"GRADE\s*[:]?\s*([SABCD])\b",
            r"\*\*([SABCD])\*\*",
        ]
        upper = text.upper()
        for pattern in patterns:
            match = re.search(pattern, upper)
            if match:
                return match.group(1)
        return None

    def _extract_grade_from_consensus(self, consensus: str) -> str:
        """합의안에서 등급 추출 (실패 시 경고 후 중립 등급 B)"""
        grade = self._try_extract_grade(consensus)
        if grade is None:
            print("⚠️ 합의문에서 등급 표기를 찾지 못해 중립 등급(B)으로 처리합니다.")
            return 'B'
        return grade

    def _calculate_agreement_confidence(self, opinions: Dict) -> int:
        """전문가 의견 간 등급 일치도를 확신도(%)로 환산

        전원 일치 90, 2/3 일치 약 77, 전원 불일치 63, 등급 추출 실패 시 50.
        """
        grades = [g for g in (self._try_extract_grade(op) for op in opinions.values()) if g]
        if not grades:
            return 50
        most_common = max(set(grades), key=grades.count)
        agreement_ratio = grades.count(most_common) / len(grades)
        return int(50 + 40 * agreement_ratio)

    def _calculate_basic_ratios(self, financial_data: Dict, multi_year_data: Dict = None) -> Dict:
        """기본 재무비율 계산"""
        ratios = {}
        
        def safe_divide(a, b, default=0):
            return (a / b) if b != 0 else default
        
        revenue = financial_data.get('revenue', 0)
        operating_income = financial_data.get('operating_income', 0)
        net_income = financial_data.get('net_income', 0)
        total_assets = financial_data.get('total_assets', 0)
        total_liabilities = financial_data.get('total_liabilities', 0)
        total_equity = financial_data.get('total_equity', 0)
        
        # 수익성 비율
        ratios['ROE'] = safe_divide(net_income, total_equity) * 100
        ratios['ROA'] = safe_divide(net_income, total_assets) * 100
        ratios['영업이익률'] = safe_divide(operating_income, revenue) * 100
        ratios['순이익률'] = safe_divide(net_income, revenue) * 100
        
        # 안정성 비율
        ratios['부채비율'] = safe_divide(total_liabilities, total_equity) * 100
        ratios['자기자본비율'] = safe_divide(total_equity, total_assets) * 100
        
        # 성장성 비율 (다년도 데이터 활용)
        if multi_year_data and '2023' in multi_year_data:
            prev_data = multi_year_data['2023']
            prev_revenue = prev_data.get('revenue', 0)
            prev_net_income = prev_data.get('net_income', 0)
            
            ratios['매출성장률'] = safe_divide((revenue - prev_revenue), prev_revenue) * 100
            ratios['순이익성장률'] = safe_divide((net_income - prev_net_income), prev_net_income) * 100
        
        return ratios

    def _calculate_basic_fraud_indicators(self, financial_data: Dict, cash_flow_data: Dict) -> Dict:
        """기본 부정 지표 계산"""
        indicators = {}
        
        revenue = financial_data.get('revenue', 0)
        net_income = financial_data.get('net_income', 0)
        receivables = financial_data.get('accounts_receivable', 0)
        operating_cash_flow = cash_flow_data.get('operating_cash_flow', 0)

        indicators['현금흐름_대_순이익_비율'] = (operating_cash_flow / net_income) if net_income != 0 else 0
        indicators['매출채권_대_매출_비율'] = (receivables / revenue * 100) if revenue != 0 else 0
        indicators['순이익_양수_현금흐름_음수'] = (net_income > 0 and operating_cash_flow < 0)
        indicators['종합_부정위험점수'] = self._calculate_fraud_risk_score(indicators)
        
        return indicators

    def _calculate_fraud_risk_score(self, indicators: Dict) -> int:
        """부정 위험 점수 계산"""
        score = 0
        
        cf_ni_ratio = indicators.get('현금흐름_대_순이익_비율', 1)
        if cf_ni_ratio < 0.5:
            score += 30
        
        ar_ratio = indicators.get('매출채권_대_매출_비율', 0)
        if ar_ratio > 25:
            score += 25
        
        if indicators.get('순이익_양수_현금흐름_음수', False):
            score += 25
        
        return min(score, 100)

    def _extract_company_from_request(self, request: str) -> Optional[str]:
        """요청에서 회사명 추출"""
        company_patterns = [
            r'(삼성전자|LG전자|현대자동차|SK하이닉스|네이버|카카오|포스코|KT|LG화학)',
            r'([가-힣A-Za-z]+(?:전자|자동차|화학|통신|바이오|제약|건설|중공업|생명과학))',
            r'([가-힣A-Za-z]+(?:회사|기업|그룹|코퍼레이션))'
        ]
        
        for pattern in company_patterns:
            match = re.search(pattern, request)
            if match:
                return match.group(1)
        
        words = request.split()
        for word in words:
            if len(word) >= 2 and any(char in word for char in '전자자동차화학통신'):
                return word
        
        return None

    def _generate_a2a_summary(self, analysis_data: Dict) -> str:
        """A2A 협업 분석 요약 생성"""
        
        company = analysis_data['company']
        ratios = analysis_data['ratios']
        fraud_ratios = analysis_data['fraud_ratios']
        final_opinion = analysis_data['final_a2a_opinion']
        
        revenue = analysis_data['financial_data'].get('revenue', 0)
        net_income = analysis_data['financial_data'].get('net_income', 0)
        
        summary = f"""
🤖 {company} 완전 A2A 협업 분석 완료!

📊 기본 재무 현황:
• 매출액: {self.format_currency(revenue)}
• 순이익: {self.format_currency(net_income)}
• ROE: {ratios.get('ROE', 0):.1f}%

🏆 AI 협업 최종 결과:
• 투자 등급: {ratios.get('A2A_투자등급', 'N/A')} (AI 3개 토론 결과)
• 부정 위험: {fraud_ratios.get('A2A_부정위험등급', 'N/A')} (AI 3개 합의)
• 최종 확신도: {final_opinion.get('confidence_level', 0)}%

🗣️ A2A 협업 과정:
• 총 AI 상호작용: {len(self.discussion_log)}회
• 참여 전문가: 김성실, 이정확, 박의심
• 다회차 토론으로 합의 도출

🎯 최종 AI 합의 의견:
{final_opinion.get('final_consensus', '분석 진행 중...')[:300]}...

💡 A2A 협업의 가치:
✓ 단일 AI를 넘어선 집단 지성 활용
✓ 전문가 수준의 다각적 검증
✓ 투명한 의사결정 과정 공개
✓ 인간 전문가팀과 동등한 분석 품질

💬 이제 다음과 같은 질문을 해보세요:
• "AI들이 어떻게 토론했는지 보여줘"
• "투자 등급을 왜 {ratios.get('A2A_투자등급', 'B')}로 결정했어?"
• "AI들 사이에 의견 차이가 있었나?"
• "보고서 만들어줘"
"""
        
        return summary

    # === 기존 유틸리티 메서드들 유지 ===
    
    def format_currency(self, amount: int) -> str:
        """통화 포맷팅"""
        if abs(amount) >= 1000000000000:
            return f"{amount/1000000000000:.1f}조원"
        elif abs(amount) >= 100000000:
            return f"{amount/100000000:.0f}억원"
        elif abs(amount) >= 10000:
            return f"{amount/10000:.0f}만원"
        else:
            return f"{amount:,}원"

    def format_percentage(self, ratio: float, decimal_places: int = 2) -> str:
        """백분율 포맷팅"""
        return f"{ratio:.{decimal_places}f}%"

    def format_ratios_for_display(self, ratios: Dict) -> Dict[str, str]:
        """표시용 비율 포맷팅"""
        formatted = {}
        
        percentage_ratios = ['ROE', 'ROA', '영업이익률', '순이익률', '부채비율', '자기자본비율']
        
        for key, value in ratios.items():
            if key.startswith('A2A_'):  # A2A 결과는 그대로
                formatted[key] = str(value)
            elif key in percentage_ratios and isinstance(value, (int, float)):
                formatted[key] = self.format_percentage(value)
            elif isinstance(value, bool):
                formatted[key] = "예" if value else "아니오"
            elif isinstance(value, (int, float)):
                formatted[key] = f"{value:.2f}"
            else:
                formatted[key] = str(value)
        
        return formatted

    # === 컨텍스트 관리 ===
    
    def save_analysis_context(self, company_name: str, analysis_data: Dict):
        """분석 컨텍스트 저장"""
        self.conversation_memory[company_name] = {
            "timestamp": datetime.now(),
            "analysis_data": analysis_data,
            "ratios": analysis_data.get("ratios", {}),
            "financial_data": analysis_data.get("financial_data", {}),
            "cash_flow_data": analysis_data.get("cash_flow_data", {}),
            "a2a_discussion_log": self.discussion_log.copy()
        }

    def get_analysis_context(self, company_name: str) -> Optional[Dict]:
        """저장된 분석 컨텍스트 조회"""
        return self.conversation_memory.get(company_name)

    def clear_old_contexts(self, hours: int = 24):
        """오래된 컨텍스트 정리"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        to_remove = []
        for company, context in self.conversation_memory.items():
            if context["timestamp"] < cutoff_time:
                to_remove.append(company)
        
        for company in to_remove:
            del self.conversation_memory[company]

    def get_agent_status(self) -> Dict:
        """에이전트 현재 상태 조회"""
        return {
            "current_model": self.current_loaded_model,
            "active_analyses": len(self.conversation_memory),
            "total_actions": len(self.agent_log),
            "discussion_interactions": len(self.discussion_log),
            "work_directory": self.work_directory,
            "a2a_mode": "항상 활성화"
        }

    def get_discussion_summary(self) -> Dict:
        """A2A 토론 과정 요약"""
        if not self.discussion_log:
            return {"message": "아직 토론이 진행되지 않았습니다."}
        
        agents_participated = set([log.get("speaker", "") for log in self.discussion_log])
        
        return {
            "total_interactions": len(self.discussion_log),
            "agents_participated": list(agents_participated),
            "discussion_start": self.discussion_log[0]["timestamp"] if self.discussion_log else None,
            "discussion_end": self.discussion_log[-1]["timestamp"] if self.discussion_log else None,
            "recent_discussions": self.discussion_log[-5:] if len(self.discussion_log) > 5 else self.discussion_log
        }
    