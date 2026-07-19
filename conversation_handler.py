# core/conversation_handler.py
"""
스마트 대화형 질의응답 핸들러 - 보고서 생성 기능 포함
유연한 자연어 처리 및 컨텍스트 기반 응답
"""

import os
import re
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
import json

class SmartConversationHandler:
    """지능형 대화 처리 시스템 - 보고서 생성 통합"""
    
    def __init__(self, agent_engine):
        self.agent = agent_engine
        self.conversation_history = []
        self.current_company = None
        self.query_patterns = self._initialize_query_patterns()
        self.context_keywords = self._initialize_context_keywords()
        
    def _initialize_query_patterns(self) -> Dict[str, List[str]]:
        """질의 패턴 초기화"""
        return {
            # 기본 분석 요청
            "full_analysis": [
                "결산", "감사", "분석해줘", "검토해줘", "분석하자", "결산처리",
                "전체분석", "종합분석", "완전분석"
            ],
            
            # 재무비율 관련
            "ratio_query": [
                "비율", "ratio", "ROE", "ROA", "부채비율", "유동비율", "영업이익률",
                "순이익률", "자기자본비율", "매출성장률", "회전율"
            ],
            
            # 부정 탐지 관련
            "fraud_query": [
                "부정", "이상", "특이", "위험", "fraud", "의심", "문제",
                "조작", "부정회계", "회계조작"
            ],
            
            # 비교 분석
            "comparison_query": [
                "비교", "대비", "vs", "차이", "compared", "업계평균", "경쟁사",
                "작년", "전년", "동종업계"
            ],
            
            # 시각화 요청
            "visualization_query": [
                "그래프", "차트", "시각화", "graph", "chart", "plot", "보여줘",
                "그림", "도표", "막대그래프", "선그래프"
            ],
            
            # 상세 설명 요청
            "explanation_query": [
                "설명", "이유", "왜", "어떻게", "explain", "why", "how",
                "자세히", "구체적으로", "detail"
            ],
            
            # 데이터 출처 문의
            "data_source_query": [
                "언제", "몇년", "년도", "데이터", "자료", "출처", "source",
                "기준", "시점", "when"
            ],
            
            # 보고서 요청 (새로 추가)
            "report_query": [
                "보고서", "문서", "정리", "요약", "report", "document",
                "파일", "저장", "다운로드", "출력", "내보내기", "export",
                "워드", "엑셀", "pdf", "docx", "xlsx", "word", "excel"
            ]
        }
    
    def _initialize_context_keywords(self) -> Dict[str, List[str]]:
        """컨텍스트 키워드 초기화"""
        return {
            "financial_items": {
                "매출": ["revenue", "sales", "매출액"],
                "영업이익": ["operating_income", "영업이익"],
                "순이익": ["net_income", "당기순이익", "순이익"],
                "자산": ["assets", "총자산", "자산총계"],
                "부채": ["liabilities", "총부채", "부채총계"],
                "자본": ["equity", "자본총계", "자기자본"],
                "현금": ["cash", "현금", "현금성자산"],
                "매출채권": ["receivables", "매출채권", "채권"],
                "재고": ["inventory", "재고자산", "재고"]
            },
            
            "ratio_items": {
                "ROE": ["roe", "자기자본수익률", "자본수익률"],
                "ROA": ["roa", "총자산수익률", "자산수익률"],
                "부채비율": ["debt_ratio", "부채비율"],
                "유동비율": ["current_ratio", "유동비율"],
                "영업이익률": ["operating_margin", "영업이익률"],
                "순이익률": ["net_margin", "순이익률"]
            },
            
            "time_periods": {
                "올해": "2024",
                "작년": "2023", 
                "재작년": "2022",
                "2024년": "2024",
                "2023년": "2023",
                "2022년": "2022"
            }
        }

    def process_user_query(self, user_input: str, company_name: str = None) -> Dict[str, Any]:
        print(f"🚨🚨🚨 process_user_query 실행됨: '{user_input}' 🚨🚨🚨")
        """사용자 질의 처리 메인 함수"""
        # 대화 기록 저장
        self.conversation_history.append({
            "timestamp": datetime.now(),
            "user_input": user_input,
            "company": company_name or self.current_company
        })
        
        # 회사명 추출 또는 설정
        if company_name:
            self.current_company = company_name
        else:
            extracted_company = self._extract_company_name(user_input)
            if extracted_company:
                self.current_company = extracted_company
        
        # 질의 유형 분류
        query_type = self._classify_query_type(user_input)
        print(f"🔍 DEBUG: '{user_input}' → 분류결과: {query_type}")

        # 질의 처리
        if query_type == "full_analysis":
            return self._handle_full_analysis_request(user_input)
        elif query_type == "ratio_query":
            return self._handle_ratio_query(user_input)
        elif query_type == "fraud_query":
            return self._handle_fraud_query(user_input)
        elif query_type == "comparison_query":
            return self._handle_comparison_query(user_input)
        elif query_type == "visualization_query":
            return self._handle_visualization_query(user_input)
        elif query_type == "explanation_query":
            return self._handle_explanation_query(user_input)
        elif query_type == "data_source_query":
            return self._handle_data_source_query(user_input)
        elif query_type == "report_query":  # 새로 추가
            return self._handle_report_query(user_input)
        else:
            print(f"📊 DEBUG: 일반 쿼리로 분류됨: {query_type}")
            return self._handle_general_query(user_input)

    def _extract_company_name(self, user_input: str) -> Optional[str]:
        """사용자 입력에서 회사명 추출"""
        company_patterns = [
            r'(삼성전자|LG전자|현대자동차|SK하이닉스|네이버|카카오|포스코|KT|LG화학)',
            r'([A-Za-z가-힣]+(?:전자|자동차|화학|통신|바이오|제약|건설|중공업|생명과학))',
            r'([A-Za-z가-힣]+(?:회사|기업|그룹|코퍼레이션))'
        ]
        
        for pattern in company_patterns:
            match = re.search(pattern, user_input)
            if match:
                return match.group(1)
        
        return None

    def _classify_query_type(self, user_input: str) -> str:
        """질의 유형 분류"""
        user_input_lower = user_input.lower()
        
        # 각 패턴별 매칭 점수 계산
        # 입력을 소문자화했으므로 키워드도 소문자로 비교해야 함
        # (기존에는 "ROE" 같은 대문자 키워드가 영원히 매칭되지 않는 버그가 있었음)
        scores = {}
        for query_type, keywords in self.query_patterns.items():
            score = sum(1 for keyword in keywords if keyword.lower() in user_input_lower)
            if score > 0:
                scores[query_type] = score
        
        # 최고 점수 반환
        if scores:
            return max(scores.keys(), key=lambda x: scores[x])
        else:
            return "general_query"

    # conversation_handler.py 수정 사항
    """
    A2A 통합 및 보고서 메시지 수정
    """

    def _handle_full_analysis_request(self, user_input: str) -> Dict[str, Any]:
        """A2A 통합 전체 분석 (항상 협업 모드)"""
        print("🤖🤖🤖 A2A 협업 분석 시작! 🤖🤖🤖")
        
        if not self.current_company:
            return {
                "type": "company_request",
                "message": "분석할 회사명을 알려주세요.",
                "suggested_companies": ["삼성전자", "LG전자", "현대자동차", "SK하이닉스"]
            }
        
        try:
            # A2A 자율 처리 호출 (항상 협업 모드)
            result = self.agent.autonomous_settlement_processing(f"{self.current_company} 분석해줘")
            
            if "error" in result:
                return {"type": "analysis_error", "message": f"분석 오류: {result['error']}"}
            
            # A2A 결과 반환
            return {
                "type": "a2a_analysis_complete",
                "company": self.current_company,
                "message": result['a2a_summary'],
                "data": result['data'],
                "investment_grade": result['investment_grade'],
                "risk_grade": result['risk_grade'],
                "discussion_count": result['discussion_log_count']
            }
            
        except Exception as e:
            return {"type": "analysis_error", "message": f"A2A 분석 오류: {str(e)}"}

    # 기존 _generate_analysis_summary 메서드도 수정 (보고서 버튼 언급 제거)
    def _generate_analysis_summary(self, analysis_data: Dict) -> str:
        """분석 결과 요약 생성 (수정됨)"""
        
        ratios = analysis_data.get('ratios', {})
        fraud_ratios = analysis_data.get('fraud_ratios', {})
        financial_data = analysis_data.get('financial_data', {})
        
        # 주요 지표 추출
        roe = ratios.get('ROE', 0)
        debt_ratio = ratios.get('부채비율', 0)
        fraud_score = fraud_ratios.get('종합_부정위험점수', 0)
        revenue = financial_data.get('revenue', 0)
        net_income = financial_data.get('net_income', 0)
        
        # 등급 결정
        if roe > 15 and debt_ratio < 100 and fraud_score < 30:
            grade = "A (우수)"
        elif roe > 10 and debt_ratio < 150 and fraud_score < 50:
            grade = "B (양호)" 
        else:
            grade = "C (개선필요)"
        
        summary = f"""
    📊 {analysis_data['company']} 분석 완료!

    🏆 종합 등급: {grade}

    📈 주요 재무지표:
    • 매출액: {self.agent.format_currency(revenue)}
    • 순이익: {self.agent.format_currency(net_income)}
    • ROE: {roe:.1f}%
    • 부채비율: {debt_ratio:.1f}%

    ⚠️ 부정위험 분석:
    • 위험점수: {fraud_score:.0f}점 (100점 만점)
    • 위험수준: {"높음" if fraud_score >= 60 else "보통" if fraud_score >= 30 else "낮음"}

    💬 이제 다음과 같은 질문을 해보세요:
    • "재무비율 자세히 보여줘"
    • "부정위험 분석 결과는?"
    • "업계 평균과 비교해줘" 
    • "그래프로 시각화해줘"
    • "보고서 만들어줘"
    """
        
        return summary

    def _handle_ratio_query(self, user_input: str) -> Dict[str, Any]:
        """재무비율 질의 처리"""
        if not self.current_company:
            return {
                "type": "error",
                "message": "먼저 분석할 회사를 지정해주세요."
            }
        
        # 컨텍스트에서 기존 분석 결과 확인
        context = self.agent.get_analysis_context(self.current_company)
        if not context:
            return {
                "type": "analysis_needed",
                "message": f"{self.current_company}의 분석을 먼저 진행해주세요.",
                "action": "request_analysis"
            }
        
        # 특정 비율 추출
        requested_ratios = self._extract_requested_ratios(user_input)
        ratios = context.get("ratios", {})
        
        if requested_ratios:
            filtered_ratios = {k: v for k, v in ratios.items() if k in requested_ratios}
        else:
            filtered_ratios = ratios
        
        return {
            "type": "ratio_response",
            "company": self.current_company,
            "ratios": filtered_ratios,
            "formatted_ratios": self.agent.format_ratios_for_display(filtered_ratios),
            "message": self._generate_ratio_explanation(filtered_ratios)
        }

    def _handle_fraud_query(self, user_input: str) -> Dict[str, Any]:
        """부정 탐지 질의 처리"""
        if not self.current_company:
            return {
                "type": "error",
                "message": "먼저 분석할 회사를 지정해주세요."
            }
        
        context = self.agent.get_analysis_context(self.current_company)
        if not context:
            return {
                "type": "analysis_needed",
                "message": f"{self.current_company}의 분석을 먼저 진행해주세요."
            }
        
        # 부정 탐지 분석 실행
        financial_data = context.get("financial_data", {})
        cash_flow_data = context.get("cash_flow_data", {})
        
        fraud_ratios = self.agent.calculate_fraud_detection_ratios(financial_data, cash_flow_data)
        
        return {
            "type": "fraud_analysis",
            "company": self.current_company,
            "fraud_ratios": fraud_ratios,
            "risk_level": self._determine_fraud_risk_level(fraud_ratios),
            "message": self._generate_fraud_explanation(fraud_ratios),
            "action": "show_fraud_details"
        }

    def _handle_comparison_query(self, user_input: str) -> Dict[str, Any]:
        """비교 분석 질의 처리"""
        if not self.current_company:
            return {
                "type": "error", 
                "message": "먼저 분석할 회사를 지정해주세요."
            }
        
        context = self.agent.get_analysis_context(self.current_company)
        if not context:
            return {
                "type": "analysis_needed",
                "message": f"{self.current_company}의 분석을 먼저 진행해주세요."
            }
        
        # 비교 대상 추출
        comparison_target = self._extract_comparison_target(user_input)
        
        if comparison_target == "industry":
            return self._generate_industry_comparison(context)
        elif comparison_target == "previous_year":
            return self._generate_year_comparison(context)
        else:
            return {
                "type": "comparison_options",
                "message": "어떤 기준으로 비교하시겠습니까?",
                "options": ["업계 평균", "전년 대비", "경쟁사"]
            }

    def _handle_visualization_query(self, user_input: str) -> Dict[str, Any]:
        """시각화 요청 처리 (실제 차트 생성)"""
        print("🔥🔥🔥 시각화 메서드 실행됨! 🔥🔥🔥")
    
        if not self.current_company:
            return {
                "type": "error",
                "message": "먼저 분석할 회사를 지정해주세요."
            }
    
        context = self.agent.get_analysis_context(self.current_company)
        if not context:
            return {
                "type": "analysis_needed", 
                "message": f"{self.current_company}의 분석을 먼저 진행해주세요."
            }
        
        try:
            print("🎨 차트 생성 시작...")
            
            # 시각화 엔진 import
            from visualization_engine import FinancialVisualizationEngine
            viz_engine = FinancialVisualizationEngine()
            
            # 분석 데이터 준비
            analysis_data = {
                "ratios": context.get("ratios", {}),
                "financial_data": context.get("financial_data", {}),
                "fraud_ratios": context.get("fraud_ratios", {}),
                "multi_year_data": context.get("multi_year_data", {})
            }
            
            # 종합 대시보드 생성
            print("📊 종합 대시보드 생성 중...")
            chart_filepath = viz_engine.create_comprehensive_dashboard(
                analysis_data, self.current_company
            )
            
            if chart_filepath:
                print(f"✅ 차트 생성 완료: {chart_filepath}")
                
                # 파일 열기
                import os
                if os.path.exists(chart_filepath):
                    try:
                        os.startfile(chart_filepath)  # Windows
                        return {
                            "type": "visualization_complete",
                            "message": f"✅ {self.current_company} 차트 생성 완료!\n📂 차트가 열렸습니다."
                        }
                    except:
                        return {
                            "type": "visualization_complete",
                            "message": f"✅ {self.current_company} 차트 생성 완료!\n📁 위치: {chart_filepath}"
                        }
                else:
                    return {"type": "error", "message": "차트 파일을 찾을 수 없습니다."}
            else:
                return {"type": "error", "message": "차트 생성에 실패했습니다."}
                
        except Exception as e:
            print(f"❌ 오류: {str(e)}")
            return {"type": "error", "message": f"오류: {str(e)}"}
        
    def _handle_explanation_query(self, user_input: str) -> Dict[str, Any]:
        """설명 요청 처리"""
        if not self.current_company:
            return {
                "type": "error",
                "message": "먼저 분석할 회사를 지정해주세요."
            }
        
        context = self.agent.get_analysis_context(self.current_company)
        if not context:
            return {
                "type": "analysis_needed",
                "message": f"{self.current_company}의 분석을 먼저 진행해주세요."
            }
        
        # AI에게 상세 설명 요청
        explanation_prompt = f"""
    사용자가 다음과 같이 질문했습니다: "{user_input}"

    {self.current_company}의 분석 결과를 바탕으로 상세히 설명해주세요.

    분석 데이터:
    {self._format_context_for_ai(context)}

    사용자가 이해하기 쉽게 구체적으로 설명해주세요.
    """
        
        explanation = self.agent.call_ollama("analyzer", explanation_prompt)
        
        return {
            "type": "detailed_explanation",
            "company": self.current_company,
            "explanation": explanation,
            "message": explanation
        }

    def _handle_data_source_query(self, user_input: str) -> Dict[str, Any]:
        """데이터 출처 문의 처리"""
        if not self.current_company:
            return {
                "type": "general_info",
                "message": "분석 데이터는 DART(전자공시시스템) 공식 API에서 수집합니다."
            }
        
        context = self.agent.get_analysis_context(self.current_company)
        if not context:
            return {
                "type": "general_info",
                "message": "아직 분석하지 않은 회사입니다. DART API에서 2024년 기준 데이터를 수집할 예정입니다."
            }
        
        return {
            "type": "data_source_info",
            "company": self.current_company,
            "message": f"""
    📊 {self.current_company} 데이터 출처 정보:

    🏛️ **데이터 출처**: DART(전자공시시스템) 공식 API
    📅 **기준 연도**: 2024년 (최근 공시 기준)  
    📋 **수집 항목**: 
       - 재무제표 (손익계산서, 재무상태표)
       - 현금흐름표
       - 최근 30일 공시사항

    ⏰ **마지막 수집**: {context['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}
    🔍 **신뢰도**: 금융감독원 공식 데이터로 최고 신뢰도
    """,
            "source": "DART",
            "year": "2024",
            "timestamp": context['timestamp']
        }

    def _handle_report_query(self, user_input: str) -> Dict[str, Any]:
        """보고서 요청 처리 - 실제 보고서 생성"""
        if not self.current_company:
            return {
                "type": "error",
                "message": "먼저 분석할 회사를 지정해주세요."
            }
        
        context = self.agent.get_analysis_context(self.current_company)
        if not context:
            return {
                "type": "analysis_needed",
                "message": f"{self.current_company}의 분석을 먼저 진행해주세요."
            }
        
        try:
            print(f"📋 {self.current_company} 보고서 생성 시작...")
            
            # 보고서 생성기 import
            from document_generator import ProfessionalReportGenerator
            
            # 보고서 생성기 초기화
            report_generator = ProfessionalReportGenerator()
            
            # 분석 데이터 준비
            analysis_data = context.get("analysis_data", {})
            
            # 보고서 유형 결정
            report_type = self._determine_report_type(user_input)
            
            if report_type == "comprehensive":
                # 종합 보고서 생성
                reports = report_generator.generate_all_reports(analysis_data, self.current_company)
                
                if reports:
                    # 첫 번째 보고서 자동 열기
                    first_report = list(reports.values())[0]
                    report_generator.open_report(first_report)
                    
                    # 결과 요약
                    summary = report_generator.get_report_summary(reports)
                    
                    return {
                        "type": "report_generated",
                        "company": self.current_company,
                        "reports": reports,
                        "message": f"✅ {self.current_company} 보고서 생성 완료!\n\n{summary}",
                        "main_report": first_report
                    }
                else:
                    return {
                        "type": "error",
                        "message": "보고서 생성에 실패했습니다."
                    }
                    
            elif report_type == "docx":
                # DOCX 보고서만 생성
                docx_path = report_generator.generate_comprehensive_report(analysis_data, self.current_company)
                if docx_path:
                    report_generator.open_report(docx_path)
                    return {
                        "type": "report_generated",
                        "company": self.current_company,
                        "message": f"✅ DOCX 보고서 생성 완료!\n📄 파일: {docx_path}",
                        "main_report": docx_path
                    }
                    
            elif report_type == "excel":
                # Excel 보고서만 생성
                excel_path = report_generator.create_excel_report(analysis_data, self.current_company)
                if excel_path:
                    report_generator.open_report(excel_path)
                    return {
                        "type": "report_generated", 
                        "company": self.current_company,
                        "message": f"✅ Excel 보고서 생성 완료!\n📊 파일: {excel_path}",
                        "main_report": excel_path
                    }
                    
            return {
                "type": "error",
                "message": "지원하지 않는 보고서 유형입니다."
            }
            
        except Exception as e:
            print(f"❌ 보고서 생성 오류: {str(e)}")
            return {
                "type": "error",
                "message": f"보고서 생성 중 오류가 발생했습니다: {str(e)}"
            }

    def _determine_report_type(self, user_input: str) -> Dict[str, Any]:
        """사용자 입력에서 보고서 유형 결정"""
        user_input_lower = user_input.lower()
        
        if any(keyword in user_input_lower for keyword in ["excel", "엑셀", "xlsx"]):
            return "excel"
        elif any(keyword in user_input_lower for keyword in ["word", "워드", "docx"]):
            return "docx"
        elif any(keyword in user_input_lower for keyword in ["pdf"]):
            return "pdf"
        else:
            return "comprehensive"  # 기본값: 모든 형태

    def _handle_general_query(self, user_input: str) -> Dict[str, Any]:
        """일반 질의 처리

        분석 결과가 있으면 반드시 컨텍스트로 주입한다. 주입하지 않으면 모델이
        분석과 무관한 일반론을 지어내는 환각이 발생한다 (예: 실제 분석 결과 대신
        "이 회사는 재무정보를 공개하지 않지만..." 같은 잘못된 답변).
        """
        context_block = ""
        if self.current_company:
            context = self.agent.get_analysis_context(self.current_company)
            if context:
                ratios = context.get("ratios", {})
                fraud = context.get("fraud_ratios", {})
                key_figures = {
                    k: v for k, v in ratios.items()
                    if k in ("ROE", "ROA", "부채비율", "영업이익률", "순이익률",
                             "A2A_투자등급", "A2A_확신도")
                }
                context_block = f"""
[분석 결과 데이터 — 반드시 이 수치에 근거해 답변할 것]
회사: {self.current_company}
주요 지표: {key_figures}
부정위험 등급: {fraud.get('A2A_부정위험등급', 'N/A')} (확신도 {fraud.get('A2A_위험확신도', 'N/A')}%)
"""

        general_prompt = f"""
사용자가 다음과 같이 질문했습니다: "{user_input}"
{context_block}
위 분석 결과 데이터가 있다면 그 수치에 근거해서 회계/재무 전문가 관점으로 답변해주세요.
분석 데이터가 없다면 일반론을 지어내지 말고, 먼저 회사 분석을 실행하도록 안내해주세요.
"""

        response = self.agent.call_ollama("coordinator", general_prompt)

        return {
            "type": "general_response",
            "message": response,
            "suggestions": self._generate_followup_suggestions()
        }

    # === 헬퍼 메서드들 ===
    
    def _extract_requested_ratios(self, user_input: str) -> List[str]:
        """요청된 특정 비율 추출"""
        requested = []
        
        for ratio_name, keywords in self.context_keywords["ratio_items"].items():
            if any(keyword in user_input.lower() for keyword in keywords):
                requested.append(ratio_name)
        
        return requested

    def _extract_comparison_target(self, user_input: str) -> str:
        """비교 대상 추출"""
        user_input_lower = user_input.lower()
        
        if any(keyword in user_input_lower for keyword in ["업계", "평균", "industry"]):
            return "industry"
        elif any(keyword in user_input_lower for keyword in ["작년", "전년", "2023", "previous"]):
            return "previous_year"
        elif any(keyword in user_input_lower for keyword in ["경쟁사", "competitor"]):
            return "competitors"
        else:
            return "unknown"

    def _determine_chart_type(self, user_input: str) -> str:
        """시각화 유형 결정"""
        user_input_lower = user_input.lower()
        
        if any(keyword in user_input_lower for keyword in ["막대", "bar", "비교"]):
            return "bar_chart"
        elif any(keyword in user_input_lower for keyword in ["선", "line", "추세", "trend"]):
            return "line_chart"
        elif any(keyword in user_input_lower for keyword in ["파이", "pie", "비중", "구성"]):
            return "pie_chart"
        elif any(keyword in user_input_lower for keyword in ["레이더", "radar", "종합"]):
            return "radar_chart"
        else:
            return "comprehensive_dashboard"

    def _determine_fraud_risk_level(self, fraud_ratios: Dict) -> str:
        """부정 위험 수준 결정"""
        risk_score = fraud_ratios.get("종합_부정위험점수", 0)
        
        if risk_score >= 70:
            return "HIGH"
        elif risk_score >= 40:
            return "MEDIUM" 
        elif risk_score >= 20:
            return "LOW"
        else:
            return "MINIMAL"

    def _generate_ratio_explanation(self, ratios: Dict) -> str:
        """비율 설명 생성"""
        if not ratios:
            return "요청하신 비율 정보를 찾을 수 없습니다."
        
        explanations = []
        
        for ratio_name, value in ratios.items():
            if ratio_name == "ROE" and isinstance(value, (int, float)):
                if value > 15:
                    explanations.append(f"ROE {value:.1f}%는 우수한 수준입니다.")
                elif value > 8:
                    explanations.append(f"ROE {value:.1f}%는 양호한 수준입니다.")
                else:
                    explanations.append(f"ROE {value:.1f}%는 개선이 필요합니다.")
            
            elif ratio_name == "부채비율" and isinstance(value, (int, float)):
                if value > 200:
                    explanations.append(f"부채비율 {value:.1f}%는 높은 편입니다.")
                elif value > 100:
                    explanations.append(f"부채비율 {value:.1f}%는 보통 수준입니다.")
                else:
                    explanations.append(f"부채비율 {value:.1f}%는 안정적입니다.")
        
        return " ".join(explanations) if explanations else "분석된 비율을 확인해주세요."

    def _generate_fraud_explanation(self, fraud_ratios: Dict) -> str:
        """부정 위험 설명 생성"""
        risk_score = fraud_ratios.get("종합_부정위험점수", 0)
        risk_level = self._determine_fraud_risk_level(fraud_ratios)
        
        base_message = f"종합 부정 위험 점수: {risk_score}점 ({risk_level} 위험)"
        
        concerns = []
        if fraud_ratios.get("순이익_양수_현금흐름_음수", False):
            concerns.append("순이익은 양수이지만 영업현금흐름이 음수입니다.")
        
        if fraud_ratios.get("매출채권_급증여부", False):
            concerns.append("매출채권 비율이 비정상적으로 높습니다.")
        
        cf_ni_ratio = fraud_ratios.get("현금흐름_대_순이익_비율", 1)
        if cf_ni_ratio < 0.5:
            concerns.append("현금흐름 대 순이익 비율이 낮습니다.")
        
        if concerns:
            return f"{base_message}\n\n주요 우려사항:\n" + "\n".join(f"• {concern}" for concern in concerns)
        else:
            return f"{base_message}\n\n특별한 부정 위험 징후는 발견되지 않았습니다."

    def _generate_industry_comparison(self, context: Dict) -> Dict[str, Any]:
        """업계 비교 분석 생성"""
        ratios = context.get("ratios", {})
        
        # 업계 평균 (임시 데이터 - 실제로는 DB나 API에서 가져와야 함)
        industry_averages = {
            "ROE": 12.5,
            "ROA": 8.3,
            "부채비율": 85.2,
            "영업이익률": 8.7,
            "순이익률": 6.4
        }
        
        comparison_results = {}
        for ratio_name, company_value in ratios.items():
            if ratio_name in industry_averages and isinstance(company_value, (int, float)):
                industry_value = industry_averages[ratio_name]
                difference = company_value - industry_value
                comparison_results[ratio_name] = {
                    "company": company_value,
                    "industry": industry_value,
                    "difference": difference,
                    "status": "우수" if difference > 0 else "열세"
                }
        
        return {
            "type": "industry_comparison",
            "company": self.current_company,
            "comparison_results": comparison_results,
            "message": self._format_comparison_message(comparison_results)
        }

    def _generate_year_comparison(self, context: Dict) -> Dict[str, Any]:
        """전년 대비 분석 생성"""
        # 다년도 데이터가 있는 경우 실제 비교, 없으면 성장률 기반 추정
        ratios = context.get("ratios", {})
        
        year_comparison = {}
        if "매출성장률" in ratios:
            year_comparison["매출성장률"] = ratios["매출성장률"]
        if "순이익성장률" in ratios:
            year_comparison["순이익성장률"] = ratios["순이익성장률"]
        
        return {
            "type": "year_comparison",
            "company": self.current_company,
            "comparison_results": year_comparison,
            "message": f"{self.current_company}의 전년 대비 성장 분석 결과입니다."
        }

    def _format_comparison_message(self, comparison_results: Dict) -> str:
        """비교 결과 메시지 포맷팅"""
        messages = []
        
        for ratio_name, data in comparison_results.items():
            company_val = data["company"]
            industry_val = data["industry"]
            status = data["status"]
            
            messages.append(f"{ratio_name}: {company_val:.1f}% (업계 {industry_val:.1f}%, {status})")
        
        return "\n".join(messages)

    def _format_context_for_ai(self, context: Dict) -> str:
        """AI용 컨텍스트 포맷팅"""
        formatted = []
        
        if "ratios" in context:
            formatted.append("주요 재무비율:")
            for key, value in context["ratios"].items():
                if isinstance(value, (int, float)):
                    formatted.append(f"- {key}: {value:.2f}")
        
        if "financial_data" in context:
            formatted.append("\n재무 데이터:")
            for key, value in context["financial_data"].items():
                if isinstance(value, (int, float)) and value != 0:
                    formatted.append(f"- {key}: {self.agent.format_currency(value)}")
        
        return "\n".join(formatted)

    def _generate_followup_suggestions(self) -> List[str]:
        """후속 질문 제안 생성"""
        if self.current_company:
            return [
                f"{self.current_company}의 재무비율을 보여주세요",
                f"{self.current_company}의 부정 위험을 분석해주세요",
                "업계 평균과 비교해주세요",
                "그래프로 시각화해주세요",
                "보고서를 생성해주세요"
            ]
        else:
            return [
                "회사 이름을 알려주시면 분석해드릴게요",
                "삼성전자 분석해주세요",
                "어떤 재무비율을 확인하고 싶으신가요?"
            ]

    # === 대화 히스토리 관리 ===
    
    def get_conversation_history(self, limit: int = 10) -> List[Dict]:
        """대화 히스토리 조회"""
        return self.conversation_history[-limit:] if limit else self.conversation_history

    def clear_conversation_history(self):
        """대화 히스토리 초기화"""
        self.conversation_history.clear()
        self.current_company = None

    def export_conversation_history(self, filepath: str = None) -> str:
        """대화 히스토리 내보내기"""
        if filepath is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filepath = f"conversation_history_{timestamp}.json"
        
        history_data = {
            "export_time": datetime.now().isoformat(),
            "current_company": self.current_company,
            "conversation_count": len(self.conversation_history),
            "conversations": [
                {
                    "timestamp": conv["timestamp"].isoformat(),
                    "user_input": conv["user_input"],
                    "company": conv["company"]
                }
                for conv in self.conversation_history
            ]
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(history_data, f, ensure_ascii=False, indent=2)
        
        return filepath

    def get_conversation_summary(self) -> Dict[str, Any]:
        """대화 요약 정보"""
        if not self.conversation_history:
            return {
                "total_conversations": 0,
                "current_company": None,
                "most_recent": None
            }
        
        companies_discussed = set()
        query_types = {}
        
        for conv in self.conversation_history:
            if conv["company"]:
                companies_discussed.add(conv["company"])
            
            # 질의 유형 통계
            query_type = self._classify_query_type(conv["user_input"])
            query_types[query_type] = query_types.get(query_type, 0) + 1
        
        return {
            "total_conversations": len(self.conversation_history),
            "current_company": self.current_company,
            "companies_discussed": list(companies_discussed),
            "query_type_stats": query_types,
            "most_recent": self.conversation_history[-1]["timestamp"].isoformat(),
            "session_duration": (
                self.conversation_history[-1]["timestamp"] - 
                self.conversation_history[0]["timestamp"]
            ).total_seconds() / 60  # minutes
        }