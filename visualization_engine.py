# core/visualization.py
"""
고급 재무 데이터 시각화 엔진
실시간 차트 생성 및 인터랙티브 대시보드
"""

import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import seaborn as sns
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple, Any
import os
from datetime import datetime
import io
import base64

import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import seaborn as sns
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple, Any
import os
from datetime import datetime
import io
import base64

plt.rcParams['axes.unicode_minus'] = False

class FinancialVisualizationEngine:
    """재무 데이터 시각화 전문 엔진"""
    
    def __init__(self, save_directory: str = "analysis_results/charts"):
        self.save_directory = save_directory
        self.colors = self._initialize_color_schemes()
        self.chart_templates = self._initialize_chart_templates()
        
        # 디렉토리 생성
        os.makedirs(save_directory, exist_ok=True)
        
        # 스타일 설정
        plt.style.use('seaborn-v0_8')
        sns.set_palette("husl")

        # 폰트 재설정 (seaborn 스타일 적용 후)
        try:
            font_path = fm.findfont('Malgun Gothic')
            if font_path:
                fm.fontManager.addfont(font_path)
                plt.rcParams['font.family'] = 'Malgun Gothic'
                print(f"✅ Malgun Gothic 폰트 (재)로드 성공: {font_path}")
            else:
                print("⚠️ Malgun Gothic 폰트를 찾을 수 없습니다. 나눔고딕 등 다른 한글 폰트를 설치해주세요.")
                plt.rcParams['font.family'] = ['DejaVu Sans'] # Fallback to default
        except Exception as e:
            print(f"❌ 폰트 (재)설정 중 오류 발생: {e}")
            plt.rcParams['font.family'] = ['DejaVu Sans'] # Fallback to default
        
        self._diagnose_fonts() # Added: Call font diagnosis

    def _diagnose_fonts(self):
        """matplotlib이 인식하는 폰트 상태 진단"""
        print("\n--- Matplotlib 폰트 진단 시작 ---")
        print(f"현재 plt.rcParams['font.family']: {plt.rcParams['font.family']}")
        
        korean_font_found = False
        for font_path in fm.findSystemFonts(fontpaths=None, fontext='ttf'):
            try:
                prop = fm.FontProperties(fname=font_path)
                font_name = prop.get_name()
                if any(keyword in font_name.lower() for keyword in ['malgun', 'nanum', 'gothic', 'dotum', 'batang', 'myeongjo']):
                    print(f"  인식된 한글 폰트: {font_name} ({font_path})")
                    korean_font_found = True
            except Exception:
                pass
        
        if not korean_font_found:
            print("  ⚠️ Matplotlib이 인식하는 한글 폰트가 없습니다.")
            print("     시스템에 한글 폰트가 설치되어 있는지 확인하거나, matplotlib 캐시를 재빌드해보세요.")
            print("     (캐시 재빌드: Python에서 'import matplotlib.font_manager as fm; fm._rebuild()' 실행 후 재시도)")
        print("--- Matplotlib 폰트 진단 종료 ---\n")

    def _initialize_color_schemes(self) -> Dict[str, List[str]]:
        """색상 스키마 초기화"""
        return {
            "professional": ["#2E86AB", "#A23B72", "#F18F01", "#C73E1D", "#592941"],
            "financial": ["#1f4e79", "#2e75b6", "#70ad47", "#ffc000", "#c55a11"],
            "risk_levels": {
                "HIGH": "#d32f2f",
                "MEDIUM": "#f57c00", 
                "LOW": "#388e3c",
                "MINIMAL": "#1976d2"
            },
            "comparison": ["#4caf50", "#2196f3", "#ff9800", "#9c27b0", "#f44336"]
        }

    def _initialize_chart_templates(self) -> Dict[str, Dict]:
        """차트 템플릿 초기화"""
        return {
            "bar_chart": {
                "figsize": (12, 8),
                "title_size": 16,
                "label_size": 12,
                "tick_size": 10
            },
            "line_chart": {
                "figsize": (14, 8),
                "title_size": 16,
                "label_size": 12,
                "tick_size": 10
            },
            "pie_chart": {
                "figsize": (10, 10),
                "title_size": 16,
                "label_size": 11
            },
            "radar_chart": {
                "figsize": (10, 10),
                "title_size": 16,
                "label_size": 12
            },
            "dashboard": {
                "figsize": (20, 12),
                "title_size": 18,
                "subtitle_size": 14,
                "label_size": 12
            }
        }

    def create_ratio_comparison_chart(self, ratios: Dict, company_name: str, 
                                    industry_averages: Dict = None) -> str:
        """재무비율 비교 막대차트"""
        
        # 데이터 준비
        ratio_names = []
        company_values = []
        industry_values = []
        
        # 기본 업계 평균값 (실제로는 DB나 API에서)
        default_industry = {
            "ROE": 12.5, "ROA": 8.3, "영업이익률": 8.7, "순이익률": 6.4,
            "부채비율": 85.2, "유동비율": 150.0, "자기자본비율": 45.8
        }
        
        if industry_averages is None:
            industry_averages = default_industry
        
        for ratio_name, company_value in ratios.items():
            if isinstance(company_value, (int, float)) and ratio_name in industry_averages:
                ratio_names.append(ratio_name)
                company_values.append(company_value)
                industry_values.append(industry_averages[ratio_name])
        
        if not ratio_names:
            return self._create_no_data_chart("비교할 재무비율 데이터가 없습니다.")
        
        # 차트 생성
        fig, ax = plt.subplots(figsize=self.chart_templates["bar_chart"]["figsize"])
        
        x = np.arange(len(ratio_names))
        width = 0.35
        
        bars1 = ax.bar(x - width/2, company_values, width, 
                      label=company_name, color=self.colors["professional"][0], alpha=0.8)
        bars2 = ax.bar(x + width/2, industry_values, width,
                      label='업계 평균', color=self.colors["professional"][1], alpha=0.8)
        
        # 차트 스타일링
        ax.set_xlabel('재무비율', fontsize=self.chart_templates["bar_chart"]["label_size"])
        ax.set_ylabel('비율 (%)', fontsize=self.chart_templates["bar_chart"]["label_size"])
        ax.set_title(f'{company_name} 재무비율 vs 업계 평균 비교', 
                    fontsize=self.chart_templates["bar_chart"]["title_size"], fontweight='bold')
        ax.set_xticks(x)
        ax.set_xticklabels(ratio_names, rotation=45, ha='right')
        ax.legend()
        ax.grid(True, alpha=0.3)
        
        # 값 표시
        for bar in bars1:
            height = bar.get_height()
            ax.annotate(f'{height:.1f}%',
                       xy=(bar.get_x() + bar.get_width() / 2, height),
                       xytext=(0, 3), textcoords="offset points",
                       ha='center', va='bottom', fontsize=9)
        
        for bar in bars2:
            height = bar.get_height()
            ax.annotate(f'{height:.1f}%',
                       xy=(bar.get_x() + bar.get_width() / 2, height),
                       xytext=(0, 3), textcoords="offset points",
                       ha='center', va='bottom', fontsize=9)
        
        plt.tight_layout()
        
        # 파일 저장
        filename = f"{company_name}_ratio_comparison_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        filepath = os.path.join(self.save_directory, filename)
        plt.savefig(filepath, dpi=300, bbox_inches='tight')
        plt.close()
        
        return filepath

    def create_trend_analysis_chart(self, multi_year_data: Dict, company_name: str) -> str:
        """다년도 추세 분석 라인차트"""
        
        if not multi_year_data:
            return self._create_no_data_chart("다년도 데이터가 없습니다.")
        
        # 데이터 준비
        years = sorted(multi_year_data.keys())
        revenue_data = []
        profit_data = []
        
        for year in years:
            data = multi_year_data[year]
            revenue_data.append(data.get('revenue', 0) / 1000000000000)  # 조원 단위
            profit_data.append(data.get('net_income', 0) / 1000000000000)  # 조원 단위
        
        # 차트 생성
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=self.chart_templates["line_chart"]["figsize"])
        
        # 매출 추세
        ax1.plot(years, revenue_data, marker='o', linewidth=3, markersize=8,
                color=self.colors["financial"][0], label='매출액')
        ax1.set_title(f'{company_name} 매출 추세 분석', 
                     fontsize=self.chart_templates["line_chart"]["title_size"], fontweight='bold')
        ax1.set_ylabel('매출액 (조원)', fontsize=self.chart_templates["line_chart"]["label_size"])
        ax1.grid(True, alpha=0.3)
        ax1.legend()
        
        # 값 표시
        for i, (year, value) in enumerate(zip(years, revenue_data)):
            ax1.annotate(f'{value:.1f}조', (year, value), 
                        textcoords="offset points", xytext=(0,10), ha='center')
        
        # 순이익 추세
        ax2.plot(years, profit_data, marker='s', linewidth=3, markersize=8,
                color=self.colors["financial"][2], label='순이익')
        ax2.set_title(f'{company_name} 순이익 추세 분석', 
                     fontsize=self.chart_templates["line_chart"]["title_size"], fontweight='bold')
        ax2.set_xlabel('연도', fontsize=self.chart_templates["line_chart"]["label_size"])
        ax2.set_ylabel('순이익 (조원)', fontsize=self.chart_templates["line_chart"]["label_size"])
        ax2.grid(True, alpha=0.3)
        ax2.legend()
        
        # 값 표시
        for i, (year, value) in enumerate(zip(years, profit_data)):
            ax2.annotate(f'{value:.1f}조', (year, value), 
                        textcoords="offset points", xytext=(0,10), ha='center')
        
        plt.tight_layout()
        
        # 파일 저장
        filename = f"{company_name}_trend_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        filepath = os.path.join(self.save_directory, filename)
        plt.savefig(filepath, dpi=300, bbox_inches='tight')
        plt.close()
        
        return filepath

    def create_fraud_risk_radar_chart(self, fraud_ratios: Dict, company_name: str) -> str:
        """부정 위험 레이더 차트"""
        
        # 레이더 차트용 데이터 준비
        categories = ['현금흐름 비율', '매출채권 비율', '재고 비율', '이익 품질', '전반적 위험']
        values = []
        
        # 정규화된 위험 점수 (0-100)
        cf_ratio = fraud_ratios.get('현금흐름_대_순이익_비율', 1)
        ar_ratio = fraud_ratios.get('매출채권_대_매출_비율', 0)
        inv_ratio = fraud_ratios.get('재고_대_매출_비율', 0)
        
        # 위험 점수 계산 (높을수록 위험)
        values.append(min(100, max(0, (1 - cf_ratio) * 100)))  # 현금흐름 위험
        values.append(min(100, ar_ratio * 2))  # 매출채권 위험
        values.append(min(100, inv_ratio * 2))  # 재고 위험
        values.append(50 if fraud_ratios.get('순이익_양수_현금흐름_음수', False) else 10)  # 이익 품질
        values.append(fraud_ratios.get('종합_부정위험점수', 0))  # 전반적 위험
        
        # 레이더 차트 생성
        angles = np.linspace(0, 2 * np.pi, len(categories), endpoint=False).tolist()
        values += values[:1]  # 닫힌 도형을 위해 첫 값 추가
        angles += angles[:1]
        
        fig, ax = plt.subplots(figsize=self.chart_templates["radar_chart"]["figsize"], 
                              subplot_kw=dict(projection='polar'))
        
        # 위험 수준에 따른 색상
        risk_score = fraud_ratios.get('종합_부정위험점수', 0)
        if risk_score >= 70:
            color = self.colors["risk_levels"]["HIGH"]
        elif risk_score >= 40:
            color = self.colors["risk_levels"]["MEDIUM"]
        elif risk_score >= 20:
            color = self.colors["risk_levels"]["LOW"]
        else:
            color = self.colors["risk_levels"]["MINIMAL"]
        
        ax.plot(angles, values, 'o-', linewidth=2, color=color, alpha=0.8)
        ax.fill(angles, values, alpha=0.25, color=color)
        
        # 카테고리 라벨 설정
        ax.set_xticks(angles[:-1])
        ax.set_xticklabels(categories, fontsize=self.chart_templates["radar_chart"]["label_size"])
        
        # y축 설정
        ax.set_ylim(0, 100)
        ax.set_yticks([20, 40, 60, 80, 100])
        ax.set_yticklabels(['20', '40', '60', '80', '100'], fontsize=10)
        ax.grid(True)
        
        # 제목
        risk_level = "높음" if risk_score >= 70 else "보통" if risk_score >= 40 else "낮음"
        ax.set_title(f'{company_name} 부정 위험 분석\n(종합 위험도: {risk_score:.0f}점 - {risk_level})', 
                    fontsize=self.chart_templates["radar_chart"]["title_size"], 
                    fontweight='bold', pad=20)
        
        plt.tight_layout()
        
        # 파일 저장
        filename = f"{company_name}_fraud_risk_radar_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        filepath = os.path.join(self.save_directory, filename)
        plt.savefig(filepath, dpi=300, bbox_inches='tight')
        plt.close()
        
        return filepath

    def create_financial_structure_pie_chart(self, financial_data: Dict, company_name: str) -> str:
        """재무구조 파이차트"""
        
        total_assets = financial_data.get('total_assets', 0)
        if total_assets == 0:
            return self._create_no_data_chart("재무구조 데이터가 없습니다.")
        
        # 자산 구성 데이터
        cash = financial_data.get('cash_and_equivalents', 0)
        receivables = financial_data.get('accounts_receivable', 0)
        inventory = financial_data.get('inventory', 0)
        ppe = financial_data.get('property_plant_equipment', 0)
        other_assets = max(0, total_assets - cash - receivables - inventory - ppe)
        
        # 파이차트 데이터
        sizes = [cash, receivables, inventory, ppe, other_assets]
        labels = ['현금성자산', '매출채권', '재고자산', '유형자산', '기타자산']
        colors = self.colors["professional"]
        
        # 0인 항목 제거
        non_zero_data = [(size, label, color) for size, label, color in zip(sizes, labels, colors) if size > 0]
        if not non_zero_data:
            return self._create_no_data_chart("표시할 자산 구성 데이터가 없습니다.")
        
        sizes, labels, colors = zip(*non_zero_data)
        
        # 파이차트 생성
        fig, ax = plt.subplots(figsize=self.chart_templates["pie_chart"]["figsize"])
        
        wedges, texts, autotexts = ax.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%',
                                         startangle=90, textprops={'fontsize': 11})
        
        # 스타일 개선
        for autotext in autotexts:
            autotext.set_color('white')
            autotext.set_fontweight('bold')
        
        ax.set_title(f'{company_name} 자산 구성', 
                    fontsize=self.chart_templates["pie_chart"]["title_size"], 
                    fontweight='bold', pad=20)
        
        # 범례 추가 (금액 포함)
        legend_labels = []
        for label, size in zip(labels, sizes):
            amount_str = f"{size/1000000000000:.1f}조원" if size >= 1000000000000 else f"{size/100000000:.0f}억원"
            legend_labels.append(f"{label}: {amount_str}")
        
        ax.legend(wedges, legend_labels, title="자산 구성", loc="center left", bbox_to_anchor=(1, 0, 0.5, 1))
        
        plt.tight_layout()
        
        # 파일 저장
        filename = f"{company_name}_financial_structure_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        filepath = os.path.join(self.save_directory, filename)
        plt.savefig(filepath, dpi=300, bbox_inches='tight')
        plt.close()
        
        return filepath

    def create_comprehensive_dashboard(self, analysis_data: Dict, company_name: str) -> str:
        """종합 대시보드"""
        
        # 데이터 추출
        ratios = analysis_data.get('ratios', {})
        financial_data = analysis_data.get('financial_data', {})
        fraud_ratios = analysis_data.get('fraud_ratios', {})
        multi_year_data = analysis_data.get('multi_year_data', {})
        
        # 대시보드 생성 (2x2 서브플롯)
        fig = plt.figure(figsize=(20, 16))
        
        # 1. 재무비율 비교 (좌상단)
        ax1 = plt.subplot(2, 2, 1)
        self._create_dashboard_ratio_chart(ax1, ratios, company_name)
        
        # 2. 수익성 추세 (우상단)  
        ax2 = plt.subplot(2, 2, 2)
        self._create_dashboard_trend_chart(ax2, multi_year_data, company_name)
        
        # 3. 부정 위험 히트맵 (좌하단)
        ax3 = plt.subplot(2, 2, 3)
        self._create_dashboard_risk_heatmap(ax3, fraud_ratios, company_name)
        
        # 4. 재무 건전성 종합 점수 (우하단)
        ax4 = plt.subplot(2, 2, 4)
        self._create_dashboard_health_score(ax4, ratios, fraud_ratios, company_name)
        
        # 전체 제목
        fig.suptitle(f'{company_name} 종합 재무 분석 대시보드', 
                    fontsize=self.chart_templates["dashboard"]["title_size"], 
                    fontweight='bold', y=0.95)
        
        plt.tight_layout()
        
        # 파일 저장
        filename = f"{company_name}_comprehensive_dashboard_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        filepath = os.path.join(self.save_directory, filename)
        plt.savefig(filepath, dpi=300, bbox_inches='tight')
        plt.close()
        
        return filepath

    def _create_dashboard_ratio_chart(self, ax, ratios: Dict, company_name: str):
        """대시보드용 재무비율 차트"""
        key_ratios = ['ROE', 'ROA', '영업이익률', '순이익률', '부채비율']
        values = [ratios.get(ratio, 0) for ratio in key_ratios]
        
        bars = ax.bar(key_ratios, values, color=self.colors["financial"][:len(key_ratios)], alpha=0.8)
        ax.set_title('주요 재무비율', fontweight='bold')
        ax.set_ylabel('비율 (%)')
        ax.tick_params(axis='x', rotation=45)
        
        # 값 표시
        for bar, value in zip(bars, values):
            if value != 0:
                ax.annotate(f'{value:.1f}%', (bar.get_x() + bar.get_width()/2, bar.get_height()),
                           ha='center', va='bottom', fontsize=10)

    def _create_dashboard_trend_chart(self, ax, multi_year_data: Dict, company_name: str):
        """대시보드용 추세 차트"""
        if not multi_year_data:
            ax.text(0.5, 0.5, '다년도 데이터 없음', ha='center', va='center', transform=ax.transAxes)
            ax.set_title('수익성 추세')
            return
        
        years = sorted(multi_year_data.keys())
        revenues = [multi_year_data[year].get('revenue', 0) / 1000000000000 for year in years]
        
        ax.plot(years, revenues, marker='o', linewidth=2, color=self.colors["financial"][0])
        ax.set_title('매출 추세', fontweight='bold')
        ax.set_ylabel('매출액 (조원)')
        ax.grid(True, alpha=0.3)

    def _create_dashboard_risk_heatmap(self, ax, fraud_ratios: Dict, company_name: str):
        """대시보드용 위험 히트맵"""
        risk_categories = ['현금흐름', '매출채권', '재고', '이익품질']
        
        # 위험 점수 계산
        cf_risk = min(100, max(0, (1 - fraud_ratios.get('현금흐름_대_순이익_비율', 1)) * 100))
        ar_risk = min(100, fraud_ratios.get('매출채권_대_매출_비율', 0) * 2)
        inv_risk = min(100, fraud_ratios.get('재고_대_매출_비율', 0) * 2)
        quality_risk = 80 if fraud_ratios.get('순이익_양수_현금흐름_음수', False) else 20
        
        risk_scores = np.array([[cf_risk, ar_risk, inv_risk, quality_risk]])
        
        im = ax.imshow(risk_scores, cmap='RdYlGn_r', aspect='auto', vmin=0, vmax=100)
        ax.set_xticks(range(len(risk_categories)))
        ax.set_xticklabels(risk_categories, rotation=45)
        ax.set_yticks([])
        ax.set_title('부정 위험 히트맵', fontweight='bold')
        
        # 값 표시
        for i, score in enumerate([cf_risk, ar_risk, inv_risk, quality_risk]):
            ax.text(i, 0, f'{score:.0f}', ha='center', va='center', fontweight='bold')

    def _create_dashboard_health_score(self, ax, ratios: Dict, fraud_ratios: Dict, company_name: str):
        """대시보드용 재무 건전성 종합 점수"""
        
        # 종합 점수 계산 (0-100)
        profitability_score = min(100, max(0, ratios.get('ROE', 0) * 4))  # ROE 기준
        stability_score = min(100, max(0, 100 - ratios.get('부채비율', 100)))  # 부채비율 기준 (역산)
        fraud_penalty = fraud_ratios.get('종합_부정위험점수', 0)
        
        total_score = (profitability_score * 0.4 + stability_score * 0.4 - fraud_penalty * 0.2)
        total_score = max(0, min(100, total_score))
        
        # 게이지 차트 스타일
        colors = ['#d32f2f', '#f57c00', '#388e3c']  # 빨강, 주황, 초록
        
        if total_score >= 70:
            color = colors[2]
            grade = 'A'
        elif total_score >= 50:
            color = colors[1]
            grade = 'B'
        else:
            color = colors[0]
            grade = 'C'
        
        # 도넛 차트로 점수 표시
        ax.pie([total_score, 100-total_score], colors=[color, '#e0e0e0'], 
               startangle=90, counterclock=False,
               wedgeprops=dict(width=0.3))
        
        ax.text(0, 0, f'{total_score:.0f}점\n등급: {grade}', ha='center', va='center', 
               fontsize=16, fontweight='bold')
        ax.set_title('재무 건전성 종합 점수', fontweight='bold')

    def create_interactive_plotly_dashboard(self, analysis_data: Dict, company_name: str) -> str:
        """인터랙티브 Plotly 대시보드"""
        
        ratios = analysis_data.get('ratios', {})
        financial_data = analysis_data.get('financial_data', {})
        multi_year_data = analysis_data.get('multi_year_data', {})
        
        # 서브플롯 생성
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=('재무비율 비교', '다년도 매출 추세', '자산 구성', '수익성 지표'),
            specs=[[{"type": "bar"}, {"type": "scatter"}],
                   [{"type": "pie"}, {"type": "bar"}]]
        )
        
        # 1. 재무비율 비교
        ratio_names = list(ratios.keys())[:6]  # 상위 6개
        ratio_values = [ratios[name] for name in ratio_names if isinstance(ratios[name], (int, float))]
        
        fig.add_trace(
            go.Bar(x=ratio_names[:len(ratio_values)], y=ratio_values, 
                   name='재무비율', marker_color='rgb(55, 83, 109)'),
            row=1, col=1
        )
        
        # 2. 다년도 매출 추세
        if multi_year_data:
            years = sorted(multi_year_data.keys())
            revenues = [multi_year_data[year].get('revenue', 0) / 1000000000000 for year in years]
            
            fig.add_trace(
                go.Scatter(x=years, y=revenues, mode='lines+markers', 
                          name='매출액', line=dict(color='rgb(26, 118, 255)', width=3)),
                row=1, col=2
            )
        
        # 3. 자산 구성
        total_assets = financial_data.get('total_assets', 0)
        if total_assets > 0:
            asset_labels = ['현금성자산', '매출채권', '재고자산', '기타자산']
            asset_values = [
                financial_data.get('cash_and_equivalents', 0),
                financial_data.get('accounts_receivable', 0), 
                financial_data.get('inventory', 0),
                max(0, total_assets - sum([
                    financial_data.get('cash_and_equivalents', 0),
                    financial_data.get('accounts_receivable', 0),
                    financial_data.get('inventory', 0)
                ]))
            ]
            
            fig.add_trace(
                go.Pie(labels=asset_labels, values=asset_values, name="자산구성"),
                row=2, col=1
            )
        
        # 4. 수익성 지표
        profitability_ratios = ['ROE', 'ROA', '영업이익률', '순이익률']
        profitability_values = [ratios.get(ratio, 0) for ratio in profitability_ratios]
        
        fig.add_trace(
            go.Bar(x=profitability_ratios, y=profitability_values,
                   name='수익성', marker_color='rgb(255, 144, 14)'),
            row=2, col=2
        )
        
        # 레이아웃 업데이트
        fig.update_layout(
            title_text=f"{company_name} 인터랙티브 재무 분석 대시보드",
            title_x=0.5,
            height=800,
            showlegend=False
        )
        
        # HTML 파일로 저장
        filename = f"{company_name}_interactive_dashboard_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
        filepath = os.path.join(self.save_directory, filename)
        fig.write_html(filepath)
        
        return filepath

    def _create_no_data_chart(self, message: str) -> str:
        """데이터 없음 차트"""
        fig, ax = plt.subplots(figsize=(10, 6))
        ax.text(0.5, 0.5, message, ha='center', va='center', transform=ax.transAxes,
               fontsize=16, bbox=dict(boxstyle="round,pad=0.3", facecolor="lightgray"))
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.axis('off')
        
        filename = f"no_data_chart_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        filepath = os.path.join(self.save_directory, filename)
        plt.savefig(filepath, dpi=300, bbox_inches='tight')
        plt.close()
        
        return filepath

    def create_chart_for_gui(self, chart_type: str, analysis_data: Dict, 
                           company_name: str) -> Tuple[str, Any]:
        """GUI용 차트 생성 (Matplotlib Figure 객체 반환)"""
        
        if chart_type == "ratio_comparison":
            filepath = self.create_ratio_comparison_chart(
                analysis_data.get('ratios', {}), company_name
            )
        elif chart_type == "trend_analysis":
            filepath = self.create_trend_analysis_chart(
                analysis_data.get('multi_year_data', {}), company_name
            )
        elif chart_type == "fraud_risk":
            filepath = self.create_fraud_risk_radar_chart(
                analysis_data.get('fraud_ratios', {}), company_name
            )
        elif chart_type == "financial_structure":
            filepath = self.create_financial_structure_pie_chart(
                analysis_data.get('financial_data', {}), company_name
            )
        elif chart_type == "comprehensive":
            filepath = self.create_comprehensive_dashboard(analysis_data, company_name)
        else:
            filepath = self._create_no_data_chart(f"지원하지 않는 차트 유형: {chart_type}")
        
        return filepath, self._load_image_for_gui(filepath)

    def _load_image_for_gui(self, filepath: str) -> Any:
        """GUI 표시용 이미지 로드"""
        try:
            from PIL import Image
            return Image.open(filepath)
        except ImportError:
            # PIL이 없는 경우 파일 경로만 반환
            return filepath

    def create_comparison_table(self, ratios: Dict, industry_averages: Dict, 
                              company_name: str) -> pd.DataFrame:
        """비교 분석 테이블 생성"""
        
        comparison_data = []
        
        for ratio_name, company_value in ratios.items():
            if isinstance(company_value, (int, float)) and ratio_name in industry_averages:
                industry_value = industry_averages[ratio_name]
                difference = company_value - industry_value
                status = "우수" if difference > 0 else "열세"
                
                comparison_data.append({
                    "재무비율": ratio_name,
                    f"{company_name}": f"{company_value:.2f}%",
                    "업계평균": f"{industry_value:.2f}%", 
                    "차이": f"{difference:+.2f}%",
                    "평가": status
                })
        
        return pd.DataFrame(comparison_data)

    def export_charts_to_pdf(self, chart_filepaths: List[str], 
                           output_filepath: str, company_name: str) -> str:
        """차트들을 PDF로 통합 내보내기"""
        try:
            from reportlab.lib.pagesizes import A4, letter
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image as RLImage
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib.units import inch
            from reportlab.pdfbase import pdfmetrics
            from reportlab.pdfbase.ttfonts import TTFont
            
            # 한글 폰트 등록 시도
            try:
                pdfmetrics.registerFont(TTFont('Malgun', 'malgun.ttf'))
                font_name = 'Malgun'
            except:
                font_name = 'Helvetica'
            
            # PDF 문서 생성
            doc = SimpleDocTemplate(output_filepath, pagesize=A4)
            story = []
            
            # 스타일 설정
            styles = getSampleStyleSheet()
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontName=font_name,
                fontSize=18,
                spaceAfter=30,
                alignment=1  # 중앙 정렬
            )
            
            # 제목 추가
            title = Paragraph(f"{company_name} 재무 분석 차트 모음", title_style)
            story.append(title)
            story.append(Spacer(1, 20))
            
            # 차트들 추가
            for i, chart_path in enumerate(chart_filepaths):
                if os.path.exists(chart_path):
                    # 차트 이미지 추가
                    img = RLImage(chart_path, width=7*inch, height=5*inch)
                    story.append(img)
                    story.append(Spacer(1, 20))
                    
                    # 페이지 구분 (마지막 차트가 아닌 경우)
                    if i < len(chart_filepaths) - 1:
                        story.append(Spacer(1, 50))
            
            # PDF 생성
            doc.build(story)
            return output_filepath
            
        except ImportError:
            # reportlab이 없는 경우 차트 파일 경로들만 반환
            return f"PDF 생성을 위해 reportlab 설치가 필요합니다. 차트 파일들: {chart_filepaths}"

    def create_real_time_monitoring_chart(self, historical_data: Dict, 
                                        company_name: str) -> str:
        """실시간 모니터링 차트 (시계열 데이터)"""
        
        if not historical_data:
            return self._create_no_data_chart("실시간 모니터링 데이터가 없습니다.")
        
        # 시계열 데이터 준비
        dates = []
        key_ratios = []
        
        for date_str, data in sorted(historical_data.items()):
            dates.append(datetime.strptime(date_str, "%Y%m%d"))
            key_ratios.append(data.get('ROE', 0))
        
        # 차트 생성
        fig, ax = plt.subplots(figsize=(14, 8))
        
        ax.plot(dates, key_ratios, marker='o', linewidth=2, markersize=6,
               color=self.colors["financial"][0], alpha=0.8)
        
        # 경고선 추가 (ROE 8% 기준)
        ax.axhline(y=8, color='red', linestyle='--', alpha=0.7, label='최소 기준선 (8%)')
        ax.axhline(y=15, color='green', linestyle='--', alpha=0.7, label='우수 기준선 (15%)')
        
        ax.set_title(f'{company_name} ROE 실시간 모니터링', 
                    fontsize=16, fontweight='bold')
        ax.set_xlabel('날짜')
        ax.set_ylabel('ROE (%)')
        ax.grid(True, alpha=0.3)
        ax.legend()
        
        # 날짜 포맷 설정
        fig.autofmt_xdate()
        
        plt.tight_layout()
        
        # 파일 저장
        filename = f"{company_name}_monitoring_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        filepath = os.path.join(self.save_directory, filename)
        plt.savefig(filepath, dpi=300, bbox_inches='tight')
        plt.close()
        
        return filepath

    def get_chart_summary(self, chart_filepath: str) -> Dict[str, Any]:
        """차트 요약 정보 반환"""
        
        if not os.path.exists(chart_filepath):
            return {"error": "차트 파일을 찾을 수 없습니다."}
        
        filename = os.path.basename(chart_filepath)
        file_size = os.path.getsize(chart_filepath)
        creation_time = datetime.fromtimestamp(os.path.getctime(chart_filepath))
        
        # 파일명에서 차트 유형 추출
        chart_type = "unknown"
        if "ratio_comparison" in filename:
            chart_type = "재무비율 비교"
        elif "trend_analysis" in filename:
            chart_type = "추세 분석"
        elif "fraud_risk" in filename:
            chart_type = "부정 위험 분석"
        elif "financial_structure" in filename:
            chart_type = "재무구조 분석"
        elif "dashboard" in filename:
            chart_type = "종합 대시보드"
        
        return {
            "filename": filename,
            "chart_type": chart_type,
            "file_size_mb": round(file_size / (1024*1024), 2),
            "creation_time": creation_time.strftime("%Y-%m-%d %H:%M:%S"),
            "filepath": chart_filepath
        }

    def batch_create_all_charts(self, analysis_data: Dict, company_name: str) -> List[str]:
        """모든 차트 일괄 생성"""
        
        chart_filepaths = []
        
        try:
            # 1. 재무비율 비교 차트
            if analysis_data.get('ratios'):
                filepath = self.create_ratio_comparison_chart(
                    analysis_data['ratios'], company_name
                )
                chart_filepaths.append(filepath)
            
            # 2. 추세 분석 차트
            if analysis_data.get('multi_year_data'):
                filepath = self.create_trend_analysis_chart(
                    analysis_data['multi_year_data'], company_name
                )
                chart_filepaths.append(filepath)
            
            # 3. 부정 위험 레이더 차트
            if analysis_data.get('fraud_ratios'):
                filepath = self.create_fraud_risk_radar_chart(
                    analysis_data['fraud_ratios'], company_name
                )
                chart_filepaths.append(filepath)
            
            # 4. 재무구조 파이차트
            if analysis_data.get('financial_data'):
                filepath = self.create_financial_structure_pie_chart(
                    analysis_data['financial_data'], company_name
                )
                chart_filepaths.append(filepath)
            
            # 5. 종합 대시보드
            filepath = self.create_comprehensive_dashboard(analysis_data, company_name)
            chart_filepaths.append(filepath)
            
            # 6. 인터랙티브 대시보드
            filepath = self.create_interactive_plotly_dashboard(analysis_data, company_name)
            chart_filepaths.append(filepath)
            
        except Exception as e:
            print(f"차트 생성 중 오류: {str(e)}")
        
        return chart_filepaths

    def cleanup_old_charts(self, days_old: int = 7):
        """오래된 차트 파일 정리"""
        
        current_time = datetime.now()
        deleted_files = []
        
        for filename in os.listdir(self.save_directory):
            filepath = os.path.join(self.save_directory, filename)
            
            if os.path.isfile(filepath):
                file_time = datetime.fromtimestamp(os.path.getctime(filepath))
                age_days = (current_time - file_time).days
                
                if age_days > days_old:
                    try:
                        os.remove(filepath)
                        deleted_files.append(filename)
                    except Exception as e:
                        print(f"파일 삭제 실패 {filename}: {str(e)}")
        
        return deleted_files

    def get_visualization_stats(self) -> Dict[str, Any]:
        """시각화 엔진 통계"""
        
        chart_files = [f for f in os.listdir(self.save_directory) 
                      if f.endswith(('.png', '.html', '.pdf'))]
        
        chart_types = {}
        total_size = 0
        
        for filename in chart_files:
            filepath = os.path.join(self.save_directory, filename)
            total_size += os.path.getsize(filepath)
            
            # 차트 유형별 분류
            if "ratio" in filename:
                chart_types["ratio_comparison"] = chart_types.get("ratio_comparison", 0) + 1
            elif "trend" in filename:
                chart_types["trend_analysis"] = chart_types.get("trend_analysis", 0) + 1
            elif "fraud" in filename:
                chart_types["fraud_risk"] = chart_types.get("fraud_risk", 0) + 1
            elif "dashboard" in filename:
                chart_types["dashboard"] = chart_types.get("dashboard", 0) + 1
            else:
                chart_types["other"] = chart_types.get("other", 0) + 1
        
        return {
            "total_charts": len(chart_files),
            "chart_types": chart_types,
            "total_size_mb": round(total_size / (1024*1024), 2),
            "save_directory": self.save_directory,
            "available_colors": len(self.colors["professional"]),
            "template_count": len(self.chart_templates)
        }