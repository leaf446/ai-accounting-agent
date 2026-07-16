# main_gui_interface.py
"""
보고서 생성 기능이 완전히 통합된 GUI 인터페이스
모든 기능을 포함한 완성된 버전
"""
import time
import customtkinter as ctk
import tkinter as tk
from tkinter import ttk, messagebox, filedialog, scrolledtext
import threading
import queue
import os
import sys
from datetime import datetime
from typing import Dict, List, Optional, Any
import webbrowser

# 현재 디렉토리를 Python 경로에 추가
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

# 백엔드 모듈들 import (안전하게)
try:
    from core_agent_engine import AdvancedAuditAgent
    print("✅ AdvancedAuditAgent import 성공")
except ImportError as e:
    print(f"❌ AdvancedAuditAgent import 실패: {e}")
    AdvancedAuditAgent = None

try:
    from conversation_handler import SmartConversationHandler
    print("✅ SmartConversationHandler import 성공")
except ImportError as e:
    print(f"❌ SmartConversationHandler import 실패: {e}")
    SmartConversationHandler = None

try:
    from document_generator import ProfessionalReportGenerator
    print("✅ ProfessionalReportGenerator import 성공")
except ImportError as e:
    print(f"❌ ProfessionalReportGenerator import 실패: {e}")
    ProfessionalReportGenerator = None

# CustomTkinter 설정
try:
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")
except:
    print("⚠️ CustomTkinter 테마 설정 실패")

class ModernAccountingGUI:
    """현대적 회계 AI GUI - 보고서 생성 기능 완전 통합"""
    
    def __init__(self):
        self.root = ctk.CTk()
        self.setup_window()
        
        # 백엔드 시스템 초기화
        self.agent = None
        self.conversation_handler = None
        self.report_generator = None
        
        # GUI 상태 관리
        self.current_company = None
        self.analysis_results = {}
        self.is_analyzing = False
        self.is_connected = False
        
        # 컴포넌트 초기화
        self.setup_components()
        self.setup_layout()
        self.setup_bindings()
        
        # 시작 메시지
        self.add_chat_message("system", "🤖 AI 회계 분석 시스템이 준비되었습니다.")
        self.add_chat_message("system", "💡 사용법:\n1. DART API 키 입력 후 연결\n2. 회사명 검색\n3. AI 분석 시작\n4. 보고서 생성 및 질문하기")

    @staticmethod
    def _load_key_from_env_file() -> str:
        """프로젝트 폴더의 .env 파일에서 DART_API_KEY를 읽어온다 (없으면 빈 문자열)"""
        env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
        try:
            with open(env_path, encoding="utf-8-sig") as f:
                for line in f:
                    line = line.strip()
                    if line.startswith("DART_API_KEY="):
                        return line.split("=", 1)[1].strip()
        except OSError:
            pass
        return ""

    def setup_window(self):
        """메인 윈도우 설정"""
        self.root.title("🏛️ AI 기반 회계 분석 시스템 - 보고서 생성 통합")
        self.root.geometry("1700x1000")
        self.root.minsize(1500, 900)
        
        # 윈도우 중앙 배치
        self.center_window()
        
        # 종료 이벤트 바인딩
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def center_window(self):
        """윈도우를 화면 중앙에 배치"""
        self.root.update_idletasks()
        width = 1700
        height = 1000
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f"{width}x{height}+{x}+{y}")

    def setup_components(self):
        """GUI 컴포넌트 초기화"""
        
        # 메인 컨테이너
        self.main_frame = ctk.CTkFrame(self.root)
        
        # 상단 헤더
        self.header_frame = ctk.CTkFrame(self.main_frame)
        
        # 로고 및 제목
        self.logo_label = ctk.CTkLabel(
            self.header_frame,
            text="🏛️ AI 기반 회계 분석 시스템",
            font=ctk.CTkFont(size=28, weight="bold")
        )
        
        self.subtitle_label = ctk.CTkLabel(
            self.header_frame,
            text="Professional Accounting AI Platform - A2A Multi-Agent System + Report Generation",
            font=ctk.CTkFont(size=14, slant="italic")
        )
        
        # API 키 입력 프레임
        self.api_frame = ctk.CTkFrame(self.header_frame)
        
        self.api_label = ctk.CTkLabel(
            self.api_frame,
            text="DART API 키:",
            font=ctk.CTkFont(size=12, weight="bold")
        )
        
        self.api_entry = ctk.CTkEntry(
            self.api_frame,
            placeholder_text="DART API 키를 입력하세요",
            width=350,
            show="*"
        )

        # .env 파일에 DART_API_KEY가 있으면 자동으로 채워넣기
        saved_key = self._load_key_from_env_file()
        if saved_key:
            self.api_entry.insert(0, saved_key)
        
        self.connect_button = ctk.CTkButton(
            self.api_frame,
            text="🔗 연결",
            command=self.connect_to_dart,
            width=100,
            height=32
        )
        
        self.connection_status = ctk.CTkLabel(
            self.api_frame,
            text="● 연결 안됨",
            text_color="red",
            font=ctk.CTkFont(size=12, weight="bold")
        )
        
        # 좌측 패널 - 회사 검색 및 분석
        self.left_panel = ctk.CTkFrame(self.main_frame)
        
        # 회사 검색 섹션
        self.search_frame = ctk.CTkFrame(self.left_panel)
        self.search_label = ctk.CTkLabel(
            self.search_frame,
            text="🏢 회사 분석",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        
        self.company_entry = ctk.CTkEntry(
            self.search_frame,
            placeholder_text="회사명 입력 (예: 삼성전자)",
            width=280,
            height=35
        )
        
        self.search_button = ctk.CTkButton(
            self.search_frame,
            text="🔍 검색",
            command=self.search_company,
            width=130,
            height=35
        )
        
        self.analyze_button = ctk.CTkButton(
            self.search_frame,
            text="🤖 AI 분석 시작",
            command=self.start_analysis,
            width=280,
            height=50,
            state="disabled",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        
        # 분석 옵션
        self.options_frame = ctk.CTkFrame(self.search_frame)
        self.options_label = ctk.CTkLabel(
            self.options_frame,
            text="📊 분석 옵션:",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        
        self.fraud_check = ctk.CTkCheckBox(
            self.options_frame,
            text="부정 위험 분석",
            font=ctk.CTkFont(size=12)
        )
        
        self.trend_check = ctk.CTkCheckBox(
            self.options_frame, 
            text="다년도 추세 분석",
            font=ctk.CTkFont(size=12)
        )
        
        self.comparison_check = ctk.CTkCheckBox(
            self.options_frame,
            text="업계 평균 비교",
            font=ctk.CTkFont(size=12)
        )
        
        # 기본 옵션 선택
        self.fraud_check.select()
        self.trend_check.select()
        self.comparison_check.select()
        
        # 진행 상황 표시
        self.progress_frame = ctk.CTkFrame(self.left_panel)
        self.progress_label = ctk.CTkLabel(
            self.progress_frame,
            text="📈 분석 진행 상황",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        
        self.progress_bar = ctk.CTkProgressBar(
            self.progress_frame,
            width=280,
            height=20
        )
        self.progress_bar.set(0)
        
        self.progress_text = ctk.CTkLabel(
            self.progress_frame,
            text="대기 중...",
            font=ctk.CTkFont(size=12)
        )
        
        # 🎯 보고서 생성 섹션 (새로 추가)
        self.report_frame = ctk.CTkFrame(self.left_panel)
        self.report_label = ctk.CTkLabel(
            self.report_frame,
            text="📋 보고서 생성",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        
        self.docx_button = ctk.CTkButton(
            self.report_frame,
            text="📄 DOCX 보고서",
            command=self.generate_docx_report,
            width=280,
            height=40,
            state="disabled"
        )
        
        self.excel_button = ctk.CTkButton(
            self.report_frame,
            text="📊 Excel 보고서", 
            command=self.generate_excel_report,
            width=280,
            height=40,
            state="disabled"
        )
        
        self.all_reports_button = ctk.CTkButton(
            self.report_frame,
            text="📑 전체 보고서 생성",
            command=self.generate_all_reports,
            width=280,
            height=50,
            state="disabled",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        
        self.open_folder_button = ctk.CTkButton(
            self.report_frame,
            text="📁 보고서 폴더 열기",
            command=self.open_reports_folder,
            width=280,
            height=35,
            state="disabled"
        )
        
        # 중앙 패널 - 대화형 채팅 (크게 확장)
        self.center_panel = ctk.CTkFrame(self.main_frame)
        
        self.chat_label = ctk.CTkLabel(
            self.center_panel,
            text="💬 AI 대화창",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        
        # 사용자 입력 (상단으로 이동)
        self.input_frame = ctk.CTkFrame(self.center_panel, height=60)
        
        self.user_entry = ctk.CTkEntry(
            self.input_frame,
            placeholder_text="💬 여기에 질문을 입력하세요! (예: ROE가 어떻게 돼? 보고서 만들어줘)",
            width=480,
            height=45,
            font=ctk.CTkFont(size=14)
        )
        
        self.send_button = ctk.CTkButton(
            self.input_frame,
            text="📤 전송",
            command=self.send_message,
            width=100,
            height=45,
            font=ctk.CTkFont(size=14, weight="bold")
        )
        
        # 채팅 히스토리
        self.chat_frame = ctk.CTkFrame(self.center_panel)
        
        self.chat_display = ctk.CTkTextbox(
            self.chat_frame,
            width=600,
            height=450,
            font=ctk.CTkFont(size=12),
            wrap="word"
        )
        
        # 빠른 질문 버튼들 (보고서 관련 추가)
        self.quick_questions_frame = ctk.CTkFrame(self.center_panel)
        self.quick_label = ctk.CTkLabel(
            self.quick_questions_frame,
            text="⚡ 빠른 질문:",
            font=ctk.CTkFont(size=12, weight="bold")
        )
        
        quick_questions = [
            ("재무비율 보여줘", "📊"),
            ("부정 위험 어떄?", "⚠️"), 
            ("업계 평균과 비교", "📈"),
            ("그래프로 보여줘", "📊"),
            ("보고서 만들어줘", "📋"),  # 새로 추가
            ("DOCX 보고서", "📄"),      # 새로 추가
            ("Excel 보고서", "📊"),     # 새로 추가
            ("현금흐름 분석", "💸")
        ]
        
        self.quick_buttons = []
        for i, (question, emoji) in enumerate(quick_questions):
            btn = ctk.CTkButton(
                self.quick_questions_frame,
                text=f"{emoji} {question}",
                command=lambda q=question: self.quick_question(q),
                width=140,
                height=30,
                font=ctk.CTkFont(size=10)
            )
            self.quick_buttons.append(btn)
        
        # 우측 패널 - 결과 및 시각화
        self.right_panel = ctk.CTkFrame(self.main_frame)
        
        self.results_label = ctk.CTkLabel(
            self.right_panel,
            text="📊 분석 결과",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        
        # 탭뷰 생성
        self.tabview = ctk.CTkTabview(self.right_panel, width=400, height=600)
        
        # 요약 탭
        self.tabview.add("📋 요약")
        self.summary_text = ctk.CTkTextbox(
            self.tabview.tab("📋 요약"),
            font=ctk.CTkFont(size=11),
            wrap="word"
        )
        
        # 재무비율 탭
        self.tabview.add("📊 재무비율")
        self.ratios_frame = ctk.CTkScrollableFrame(self.tabview.tab("📊 재무비율"))
        
        # 보고서 상태 탭 (새로 추가)
        self.tabview.add("📋 보고서")
        self.reports_text = ctk.CTkTextbox(
            self.tabview.tab("📋 보고서"),
            font=ctk.CTkFont(size=11),
            wrap="word"
        )
        
        # 하단 상태바
        self.status_frame = ctk.CTkFrame(self.main_frame)
        self.status_label = ctk.CTkLabel(
            self.status_frame,
            text="시스템 준비됨",
            font=ctk.CTkFont(size=11)
        )
        
        self.model_status = ctk.CTkLabel(
            self.status_frame,
            text="AI 모델: 미연결",
            font=ctk.CTkFont(size=11)
        )
        
        self.time_label = ctk.CTkLabel(
            self.status_frame,
            text="",
            font=ctk.CTkFont(size=11)
        )
        
        # 시간 업데이트
        self.update_time()

    def setup_layout(self):
        """레이아웃 배치"""
        
        # 메인 프레임
        self.main_frame.pack(fill="both", expand=True, padx=15, pady=15)
        
        # 헤더
        self.header_frame.pack(fill="x", pady=(0, 15))
        
        # 로고 및 제목
        self.logo_label.pack(pady=8)
        self.subtitle_label.pack(pady=(0, 12))
        
        # API 키 프레임
        self.api_frame.pack(fill="x", pady=8)
        self.api_label.pack(side="left", padx=(15, 8))
        self.api_entry.pack(side="left", padx=8)
        self.connect_button.pack(side="left", padx=8)
        self.connection_status.pack(side="left", padx=(15, 0))
        
        # 메인 컨텐츠 영역 (3열 레이아웃)
        content_frame = ctk.CTkFrame(self.main_frame)
        content_frame.pack(fill="both", expand=True, pady=15)
        
        # 좌측 패널 (320px - 조금 더 넓게)
        self.left_panel.pack(side="left", fill="y", padx=(0, 8))
        
        # 회사 검색 섹션
        self.search_frame.pack(fill="x", padx=15, pady=15)
        self.search_label.pack(pady=(15, 8))
        self.company_entry.pack(pady=8)
        self.search_button.pack(pady=8)
        self.analyze_button.pack(pady=15)
        
        # 분석 옵션
        self.options_frame.pack(fill="x", pady=15)
        self.options_label.pack(pady=(15, 8))
        self.fraud_check.pack(anchor="w", padx=25, pady=3)
        self.trend_check.pack(anchor="w", padx=25, pady=3)
        self.comparison_check.pack(anchor="w", padx=25, pady=3)
        
        # 진행 상황
        self.progress_frame.pack(fill="x", padx=15, pady=15)
        self.progress_label.pack(pady=(15, 8))
        self.progress_bar.pack(pady=8)
        self.progress_text.pack(pady=8)
        
        # 🎯 보고서 생성 섹션 (새로 추가)
        self.report_frame.pack(fill="x", padx=15, pady=15)
        self.report_label.pack(pady=(15, 8))
        self.docx_button.pack(pady=5)
        self.excel_button.pack(pady=5)
        self.all_reports_button.pack(pady=15)
        self.open_folder_button.pack(pady=5)
        
        # 중앙 패널 (확장됨)
        self.center_panel.pack(side="left", fill="both", expand=True, padx=8)
        
        self.chat_label.pack(pady=(15, 8))
        
        # 입력 영역을 맨 위로
        self.input_frame.pack(fill="x", padx=15, pady=(0, 10))
        self.input_frame.pack_propagate(False)
        
        self.user_entry.pack(side="left", fill="x", expand=True, padx=(15, 8))
        self.send_button.pack(side="right", padx=(8, 15))
        
        # 채팅 영역
        self.chat_frame.pack(fill="both", expand=True, padx=15, pady=(10, 8))
        self.chat_display.pack(fill="both", expand=True, padx=15, pady=15)
        
        # 빠른 질문
        self.quick_questions_frame.pack(fill="x", padx=15, pady=(0, 8))
        self.quick_label.pack(pady=(8, 5))
        
        # 빠른 질문 버튼들을 위한 그리드 프레임
        self.quick_grid_frame = ctk.CTkFrame(self.quick_questions_frame)
        self.quick_grid_frame.pack(fill="x", padx=10, pady=5)
        
        # 빠른 질문 버튼들 배치 (4x2 그리드)
        for i, btn in enumerate(self.quick_buttons):
            row = i // 4
            col = i % 4
            btn.grid(row=row, column=col, padx=3, pady=3, sticky="ew", in_=self.quick_grid_frame)
        
        # 그리드 컬럼 설정
        for i in range(4):
            self.quick_grid_frame.grid_columnconfigure(i, weight=1)
        
        # 우측 패널 (400px)
        self.right_panel.pack(side="right", fill="y", padx=(8, 0))
        
        self.results_label.pack(pady=(15, 8))
        self.tabview.pack(fill="both", expand=True, padx=15, pady=15)
        
        # 탭 내용 배치
        self.summary_text.pack(fill="both", expand=True, padx=8, pady=8)
        self.ratios_frame.pack(fill="both", expand=True, padx=8, pady=8)
        self.reports_text.pack(fill="both", expand=True, padx=8, pady=8)
        
        # 하단 상태바
        self.status_frame.pack(fill="x", pady=(15, 0))
        self.status_label.pack(side="left", padx=15)
        self.model_status.pack(side="right", padx=15)
        self.time_label.pack(side="right", padx=(0, 150))

    def setup_bindings(self):
        """이벤트 바인딩 설정"""
        
        # 엔터키 바인딩
        self.company_entry.bind("<Return>", lambda e: self.search_company())
        self.user_entry.bind("<Return>", lambda e: self.send_message())
        self.api_entry.bind("<Return>", lambda e: self.connect_to_dart())

    def connect_to_dart(self):
        """DART API 연결"""
        
        api_key = self.api_entry.get().strip()
        if not api_key:
            messagebox.showerror("오류", "DART API 키를 입력해주세요.")
            return
        
        if not AdvancedAuditAgent or not SmartConversationHandler:
            messagebox.showerror("오류", "백엔드 모듈을 불러올 수 없습니다.\n필요한 파일들이 같은 폴더에 있는지 확인해주세요.")
            return
        
        self.add_chat_message("system", "🔗 DART API 연결 시도 중...")
        self.connection_status.configure(text="연결 중...", text_color="orange")
        
        def connect_thread():
            try:
                # 백엔드 시스템 초기화
                self.agent = AdvancedAuditAgent(api_key)
                self.conversation_handler = SmartConversationHandler(self.agent)
                
                # 보고서 생성기 초기화
                if ProfessionalReportGenerator:
                    self.report_generator = ProfessionalReportGenerator()
                
                # UI 업데이트
                self.root.after(0, self.connection_success)
                
            except Exception as e:
                self.root.after(0, lambda: self.connection_failed(str(e)))
        
        threading.Thread(target=connect_thread, daemon=True).start()

    def connection_success(self):
        """연결 성공 처리"""
        self.is_connected = True
        self.connection_status.configure(text="● 연결됨", text_color="green")
        self.model_status.configure(text="AI 모델: llama3.1 + qwen2.5 + mistral")
        
        # API 키 숨기기 및 비활성화
        self.api_entry.configure(show="*", state="disabled")
        self.connect_button.configure(state="disabled")
        
        # 분석 버튼 활성화 준비
        self.search_button.configure(state="normal")
        
        self.add_chat_message("system", "✅ DART API 연결 성공!")
        self.add_chat_message("ai", "🤖 AI 모델 3개 로딩 완료! A2A 협업 시스템이 준비되었습니다.\n💡 이제 회사명을 검색해보세요!")

    def connection_failed(self, error_message):
        """연결 실패 처리"""
        self.connection_status.configure(text="● 연결 실패", text_color="red")
        messagebox.showerror("연결 실패", f"DART API 연결에 실패했습니다:\n{error_message}")
        self.add_chat_message("error", f"❌ 연결 실패: {error_message}")

    def search_company(self):
        """회사 검색"""
        
        if not self.is_connected:
            messagebox.showwarning("알림", "먼저 DART API에 연결해주세요.")
            return
        
        company_name = self.company_entry.get().strip()
        if not company_name:
            messagebox.showwarning("알림", "회사명을 입력해주세요.")
            return
        
        self.add_chat_message("system", f"🔍 '{company_name}' 검색 중...")
        
        def search_thread():
            try:
                company_info = self.agent.search_company_dart(company_name)
                
                if company_info:
                    if "candidates" in company_info:
                        candidates = company_info["candidates"]
                        choice = candidates[0]
                        self.current_company = choice["corp_name"]
                    else:
                        self.current_company = company_info["corp_name"]
                    
                    self.root.after(0, self.search_success)
                else:
                    self.root.after(0, lambda: self.search_failed(company_name))
                    
            except Exception as e:
                self.root.after(0, lambda: self.search_error(str(e)))
        
        threading.Thread(target=search_thread, daemon=True).start()

    def search_success(self):
        """검색 성공 처리"""
        self.analyze_button.configure(state="normal")
        self.add_chat_message("system", f"✅ '{self.current_company}' 검색 성공!")
        self.add_chat_message("ai", f"🎯 {self.current_company} 정보를 찾았습니다!\n\n🚀 이제 'AI 분석 시작' 버튼을 클릭하여 종합 분석을 시작하세요.")

    def search_failed(self, company_name):
        """검색 실패 처리"""
        self.add_chat_message("error", f"❌ '{company_name}' 검색 결과 없음")
        messagebox.showinfo("검색 결과", f"'{company_name}' 검색 결과가 없습니다.\n\n추천 기업: 삼성전자, LG전자, 현대자동차, SK하이닉스")

    def search_error(self, error_message):
        """검색 오류 처리"""
        self.add_chat_message("error", f"❌ 검색 오류: {error_message}")
        messagebox.showerror("검색 오류", f"검색 중 오류가 발생했습니다:\n{error_message}")

    def start_analysis(self):
        """AI 분석 시작"""
        
        if not self.current_company:
            messagebox.showwarning("알림", "먼저 회사를 검색해주세요.")
            return
        
        if self.is_analyzing:
            messagebox.showinfo("알림", "이미 분석이 진행 중입니다.")
            return
        
        self.is_analyzing = True
        self.analyze_button.configure(state="disabled")
        self.progress_bar.set(0)
        
        self.add_chat_message("system", f"🚀 {self.current_company} 실제 DART 분석 시작...")
        self.add_chat_message("ai", "🔥 core_agent_engine.py를 직접 호출하여 실제 DART API 분석을 실행합니다!")
        
        def real_analysis_thread():
            try:
                print(f"🔥🔥🔥 직접 백엔드 엔진 호출: {self.current_company}")
                
                # 실제 분석 실행
                self.root.after(0, lambda: self.update_progress(10, "DART에서 회사 정보 검색 중..."))
                company_info = self.agent.search_company_dart(self.current_company)
                
                if not company_info:
                    raise Exception(f"{self.current_company} 검색 결과가 없습니다.")
                
                # 후보가 여러 개인 경우 첫 번째 선택
                if "candidates" in company_info:
                    company_info = company_info["candidates"][0]
                
                corp_code = company_info.get('corp_code')
                if not corp_code:
                    raise Exception(f"{self.current_company}의 기업코드를 찾을 수 없습니다.")
                
                # 재무제표 수집
                self.root.after(0, lambda: self.update_progress(30, "DART에서 재무제표 수집 중..."))
                financial_data = self.agent.get_financial_statements(corp_code)
                
                # 현금흐름표 수집  
                self.root.after(0, lambda: self.update_progress(50, "DART에서 현금흐름표 수집 중..."))
                cash_flow_data = self.agent.get_cash_flow_statement(corp_code)
                
                # 다년도 데이터 수집
                self.root.after(0, lambda: self.update_progress(70, "다년도 데이터 수집 중..."))
                multi_year_data = self.agent.get_multi_year_financials(corp_code, ['2024', '2023'])
                
                # 재무비율 계산
                self.root.after(0, lambda: self.update_progress(85, "재무비율 계산 중..."))
                ratios = self.agent.calculate_comprehensive_ratios(financial_data, multi_year_data)
                
                # 부정위험 분석
                self.root.after(0, lambda: self.update_progress(95, "부정 위험 분석 중..."))
                fraud_ratios = self.agent.calculate_fraud_detection_ratios(financial_data, cash_flow_data)
                
                # 결과 정리
                self.root.after(0, lambda: self.update_progress(100, "분석 완료!"))
                
                analysis_data = {
                    "company": self.current_company,
                    "company_info": company_info,
                    "financial_data": financial_data,
                    "cash_flow_data": cash_flow_data,
                    "multi_year_data": multi_year_data,
                    "ratios": ratios,
                    "fraud_ratios": fraud_ratios,
                    "timestamp": datetime.now()
                }
                
                # 컨텍스트 저장
                self.agent.save_analysis_context(self.current_company, analysis_data)
                
                # GUI 업데이트
                self.root.after(0, lambda: self.display_analysis_results(analysis_data))
                
            except Exception as e:
                print(f"❌ 분석 오류: {str(e)}")
                self.root.after(0, lambda: self.analysis_error(str(e)))
        
        threading.Thread(target=real_analysis_thread, daemon=True).start()

    def update_progress(self, percentage, status_text):
        """진행률 업데이트"""
        self.progress_bar.set(percentage / 100)
        self.progress_text.configure(text=status_text)
        
        if percentage % 20 == 0:
            self.add_chat_message("system", f"📊 {percentage}% - {status_text}")
        
        self.root.update_idletasks()

    def display_analysis_results(self, data):
        """분석 결과 표시"""
        
        self.is_analyzing = False
        self.analyze_button.configure(state="normal")
        
        # 분석 결과 저장
        self.analysis_results = {
            "type": "analysis_complete",
            "data": data,
            "company": self.current_company
        }
        
        # 보고서 버튼 활성화
        self.docx_button.configure(state="normal")
        self.excel_button.configure(state="normal")
        self.all_reports_button.configure(state="normal")
        self.open_folder_button.configure(state="normal")
        
        # 실제 데이터 추출
        ratios = data.get('ratios', {})
        financial_data = data.get('financial_data', {})
        fraud_ratios = data.get('fraud_ratios', {})
        
        revenue = financial_data.get('revenue', 0)
        net_income = financial_data.get('net_income', 0)
        roe = ratios.get('ROE', 0)
        debt_ratio = ratios.get('부채비율', 0)
        fraud_score = fraud_ratios.get('종합_부정위험점수', 0)
        
        # 포맷팅
        def format_currency(amount):
            if amount >= 1000000000000:
                return f"{amount/1000000000000:.1f}조원"
            elif amount >= 100000000:
                return f"{amount/100000000:.0f}억원"
            elif amount > 0:
                return f"{amount/10000:.0f}만원"
            else:
                return "데이터 없음"
        
        # 요약 텍스트 생성
        summary_text = f"""🏢 {self.current_company} 실제 DART 분석 완료

🔥 실제 DART API 데이터:
• 매출액: {format_currency(revenue)}
• 순이익: {format_currency(net_income)}
• ROE: {roe:.2f}%
• 부채비율: {debt_ratio:.2f}%

⚠️ 부정위험 분석:
• 위험점수: {fraud_score:.1f}점

✅ 데이터 검증:
• 재무항목: {len([k for k,v in financial_data.items() if v != 0])}개 수집
• 비율계산: {len([k for k,v in ratios.items() if isinstance(v,(int,float)) and v != 0])}개 완료

💬 이제 다음을 할 수 있습니다:
• 질문하기: "ROE가 좋아?", "부정위험은?"
• 보고서 생성: "보고서 만들어줘" 채팅에 입력
• 상세 분석: 우측 탭에서 확인
"""
        
        # 요약 탭 업데이트
        self.summary_text.delete("1.0", tk.END)
        self.summary_text.insert("1.0", summary_text)
        
        # 재무비율 탭 업데이트
        for widget in self.ratios_frame.winfo_children():
            widget.destroy()
            
        if ratios:
            row_idx = 0
            for ratio_name, ratio_value in ratios.items():
                if isinstance(ratio_value, (int, float)) and ratio_value != 0:
                    # 비율 이름
                    name_label = ctk.CTkLabel(
                        self.ratios_frame,
                        text=f"• {ratio_name}:",
                        font=ctk.CTkFont(size=12, weight="bold"),
                        anchor="w"
                    )
                    name_label.grid(row=row_idx, column=0, padx=5, pady=2, sticky="ew")
                    
                    # 비율 값
                    if ratio_name in ['ROE', 'ROA', '영업이익률', '순이익률', '부채비율']:
                        formatted_value = f"{ratio_value:.2f}%"
                    else:
                        formatted_value = f"{ratio_value:.2f}"
                    
                    value_label = ctk.CTkLabel(
                        self.ratios_frame,
                        text=formatted_value,
                        font=ctk.CTkFont(size=12),
                        anchor="e"
                    )
                    value_label.grid(row=row_idx, column=1, padx=5, pady=2, sticky="ew")
                    
                    row_idx += 1
            
            self.ratios_frame.grid_columnconfigure(0, weight=1)
            self.ratios_frame.grid_columnconfigure(1, weight=1)
        
        # 보고서 상태 탭 업데이트
        reports_status = f"""📋 보고서 생성 준비 완료

✅ 분석 데이터: {self.current_company}
📊 수집 항목: {len([k for k,v in financial_data.items() if v != 0])}개
🧮 계산 비율: {len([k for k,v in ratios.items() if isinstance(v,(int,float))])}개

📋 생성 가능한 보고서:
• DOCX: 전문 회계법인 수준 보고서
• Excel: 상세 데이터 분석표
• PDF: DOCX를 PDF로 변환 (선택사항)

💡 사용법:
1. 채팅에서 "보고서 만들어줘" 입력
2. 생성된 파일은 자동으로 열림

📁 저장 위치: analysis_results/documents/
"""
        
        self.reports_text.delete("1.0", tk.END)
        self.reports_text.insert("1.0", reports_status)
        
        # 채팅 메시지
        self.add_chat_message("ai", f"🎉 {self.current_company} 실제 DART 분석 완료!\n\n매출액: {format_currency(revenue)}\nROE: {roe:.2f}%\n\n📋 이제 보고서를 생성할 수 있습니다!")
        self.add_chat_message("system", "✅ 분석 완료!  '보고서 만들어줘'라고 말해보세요.")
        
        # 요약 탭으로 전환
        self.tabview.set("📋 요약")

    def analysis_error(self, error_message):
        """분석 오류 처리"""
        self.is_analyzing = False
        self.analyze_button.configure(state="normal")
        self.add_chat_message("error", f"❌ 분석 오류: {error_message}")
        messagebox.showerror("분석 오류", f"분석 중 오류가 발생했습니다:\n{error_message}")

    # 🎯 보고서 생성 메서드들 (새로 추가)
    def generate_docx_report(self):
        """DOCX 보고서 생성"""
        if not self.current_company or not self.analysis_results:
            messagebox.showwarning("알림", "먼저 분석을 완료해주세요.")
            return
        
        self.add_chat_message("system", "📄 DOCX 보고서 생성 중...")
        
        def generate_thread():
            try:
                response = self.conversation_handler.process_user_query(
                    "DOCX 보고서 생성해줘", self.current_company
                )
                
                self.root.after(0, lambda: self.handle_report_response(response, "DOCX"))
                
            except Exception as e:
                self.root.after(0, lambda: self.report_generation_error(str(e)))
        
        threading.Thread(target=generate_thread, daemon=True).start()

    def generate_excel_report(self):
        """Excel 보고서 생성"""
        if not self.current_company or not self.analysis_results:
            messagebox.showwarning("알림", "먼저 분석을 완료해주세요.")
            return
        
        self.add_chat_message("system", "📊 Excel 보고서 생성 중...")
        
        def generate_thread():
            try:
                response = self.conversation_handler.process_user_query(
                    "Excel 보고서 생성해줘", self.current_company
                )
                
                self.root.after(0, lambda: self.handle_report_response(response, "Excel"))
                
            except Exception as e:
                self.root.after(0, lambda: self.report_generation_error(str(e)))
        
        threading.Thread(target=generate_thread, daemon=True).start()

    def generate_all_reports(self):
        """전체 보고서 생성"""
        if not self.current_company or not self.analysis_results:
            messagebox.showwarning("알림", "먼저 분석을 완료해주세요.")
            return
        
        self.add_chat_message("system", "📑 전체 보고서 생성 중...")
        
        def generate_thread():
            try:
                if not self.report_generator:
                    raise Exception("보고서 생성기가 초기화되지 않았습니다.")
                
                analysis_data = self.analysis_results.get("data", {})
                reports = self.report_generator.generate_all_reports(analysis_data, self.current_company)
                
                self.root.after(0, lambda: self.handle_direct_report_response(reports))
                
            except Exception as e:
                self.root.after(0, lambda: self.report_generation_error(str(e)))
        
        threading.Thread(target=generate_thread, daemon=True).start()

    def open_reports_folder(self):
        """보고서 폴더 열기"""
        try:
            if self.report_generator:
                folder_path = self.report_generator.save_directory
            else:
                folder_path = "analysis_results/documents"
            
            if not os.path.exists(folder_path):
                os.makedirs(folder_path, exist_ok=True)
            
            import platform
            if platform.system() == 'Windows':
                os.startfile(folder_path)
            elif platform.system() == 'Darwin':  # macOS
                os.system(f'open "{folder_path}"')
            else:  # Linux
                os.system(f'xdg-open "{folder_path}"')
            
            self.add_chat_message("system", f"📁 보고서 폴더를 열었습니다: {folder_path}")
            
        except Exception as e:
            self.add_chat_message("error", f"❌ 폴더 열기 실패: {str(e)}")

    def handle_report_response(self, response: Dict, report_type: str):
        """보고서 생성 응답 처리"""
        
        if response.get("type") == "report_generated":
            message = response.get("message", "보고서 생성 완료")
            main_report = response.get("main_report", "")
            
            self.add_chat_message("ai", f"✅ {report_type} 보고서 생성 완료!\n\n{message}")
            
            # 보고서 탭 업데이트
            self.update_reports_tab(f"✅ {report_type} 보고서 생성 완료", main_report)
            
            if main_report and os.path.exists(main_report):
                try:
                    os.startfile(main_report)  # Windows
                    self.add_chat_message("system", "📄 보고서 파일이 열렸습니다.")
                except:
                    self.add_chat_message("system", f"📁 보고서 위치: {main_report}")
        else:
            error_message = response.get("message", "보고서 생성에 실패했습니다.")
            self.add_chat_message("error", f"❌ {error_message}")

    def handle_direct_report_response(self, reports: Dict):
        """직접 보고서 생성 응답 처리"""
        
        if reports:
            self.add_chat_message("ai", f"✅ 전체 보고서 생성 완료! {len(reports)}개 파일 생성")
            
            # 보고서 목록 표시
            report_list = "📋 생성된 보고서:\n"
            for report_type, filepath in reports.items():
                filename = os.path.basename(filepath)
                report_list += f"• {report_type.upper()}: {filename}\n"
            
            self.update_reports_tab("✅ 전체 보고서 생성 완료", report_list)
            
            # 첫 번째 보고서 열기
            if reports:
                first_report = list(reports.values())[0]
                try:
                    os.startfile(first_report)
                    self.add_chat_message("system", "📄 대표 보고서를 열었습니다.")
                except:
                    self.add_chat_message("system", f"📁 보고서들이 생성되었습니다.")
        else:
            self.add_chat_message("error", "❌ 보고서 생성에 실패했습니다.")

    def update_reports_tab(self, status: str, details: str = ""):
        """보고서 탭 업데이트"""
        
        current_content = self.reports_text.get("1.0", tk.END)
        new_content = f"{status}\n시간: {datetime.now().strftime('%H:%M:%S')}\n\n{details}\n\n{current_content}"
        
        self.reports_text.delete("1.0", tk.END)
        self.reports_text.insert("1.0", new_content)
        
        # 보고서 탭으로 전환
        self.tabview.set("📋 보고서")

    def report_generation_error(self, error_message: str):
        """보고서 생성 오류 처리"""
        self.add_chat_message("error", f"❌ 보고서 생성 오류: {error_message}")
        self.update_reports_tab("❌ 보고서 생성 실패", error_message)

    def send_message(self):
        """사용자 메시지 전송"""
        
        user_message = self.user_entry.get().strip()
        if not user_message:
            return
        
        if not self.is_connected:
            messagebox.showwarning("알림", "먼저 DART API에 연결해주세요.")
            return
        
        # 보고서 관련 키워드 감지
        report_keywords = ["보고서", "문서", "report", "docx", "excel", "word", "엑셀"]
        is_report_request = any(keyword in user_message.lower() for keyword in report_keywords)
        
        if is_report_request and not self.analysis_results:
            self.add_chat_message("user", user_message)
            self.add_chat_message("ai", "📋 보고서를 생성하려면 먼저 회사 분석을 완료해주세요!\n\n1. 회사 검색\n2. AI 분석 시작\n3. 보고서 생성")
            self.user_entry.delete(0, tk.END)
            return
        
        # 사용자 메시지 표시
        self.add_chat_message("user", user_message)
        self.user_entry.delete(0, tk.END)
        
        # AI 응답 처리
        def response_thread():
            try:
                self.add_chat_message("ai", "🤖 생각 중...")
                
                response = self.conversation_handler.process_user_query(
                    user_message, self.current_company
                )
                
                self.remove_last_thinking_message()
                self.handle_ai_response(response)
                
            except Exception as e:
                self.remove_last_thinking_message()
                self.add_chat_message("error", f"오류가 발생했습니다: {str(e)}")
        
        threading.Thread(target=response_thread, daemon=True).start()

    def handle_ai_response(self, response):
        """AI 응답 처리"""
        
        response_type = response.get("type", "general_response")
        message = response.get("message", "응답을 생성할 수 없습니다.")
        
        if response_type == "report_generated":
            # 보고서 생성 완료
            self.add_chat_message("ai", f"✅ 보고서 생성 완료!\n\n{message}")
            main_report = response.get("main_report", "")
            if main_report:
                self.update_reports_tab("✅ 채팅 요청 보고서 생성 완료", main_report)
                
        elif response_type == "analysis_complete":
            # 분석 완료
            self.add_chat_message("ai", f"✅ 분석 완료!\n\n{message}")
            
        elif response_type == "ratio_response":
            # 재무비율 응답
            self.add_chat_message("ai", f"📊 재무비율 분석:\n\n{message}")
            self.tabview.set("📊 재무비율")
            
        elif response_type == "fraud_analysis":
            # 부정 분석 응답
            self.add_chat_message("ai", f"⚠️ 부정위험 분석:\n\n{message}")
            
        elif response_type == "company_request":
            # 회사 지정 요청
            self.add_chat_message("ai", f"🏢 회사 선택:\n\n{message}")
            suggested = response.get("suggested_companies", [])
            if suggested:
                suggestion_text = "\n💡 추천 기업: " + ", ".join(suggested)
                self.add_chat_message("ai", suggestion_text)
        
        elif response_type == "analysis_needed":
            # 분석 필요
            self.add_chat_message("ai", f"📋 분석 필요:\n\n{message}")
            
        else:
            # 일반 응답
            self.add_chat_message("ai", message)
            
            # 후속 제안이 있는 경우
            suggestions = response.get("suggestions", [])
            if suggestions:
                suggestion_text = "\n💡 다음 질문도 해보세요:\n" + "\n".join(f"• {s}" for s in suggestions)
                self.add_chat_message("ai", suggestion_text)

    def quick_question(self, question):
        """빠른 질문 처리"""
        self.user_entry.delete(0, tk.END)
        self.user_entry.insert(0, question)
        self.send_message()

    def add_chat_message(self, msg_type, content):
        """채팅 메시지 추가"""
        
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        # 메시지 타입별 아이콘과 색상
        type_config = {
            "user": ("👤 사용자", "#4CAF50"),
            "ai": ("🤖 AI", "#2196F3"),
            "system": ("🖥️ 시스템", "#FF9800"),
            "error": ("❌ 오류", "#F44336")
        }
        
        sender, color = type_config.get(msg_type, ("💬 메시지", "#666666"))
        
        # 메시지 포맷팅
        formatted_message = f"[{timestamp}] {sender}\n{content}\n\n"
        
        # 채팅 디스플레이에 추가
        self.chat_display.configure(state="normal")
        self.chat_display.insert(tk.END, formatted_message)
        self.chat_display.configure(state="disabled")
        
        # 스크롤을 맨 아래로
        self.chat_display.see(tk.END)

    def remove_last_thinking_message(self):
        """마지막 '생각 중...' 메시지 제거"""
        try:
            current_text = self.chat_display.get("1.0", tk.END)
            lines = current_text.split('\n')
            
            # "생각 중..." 메시지가 포함된 라인들 제거
            filtered_lines = []
            skip_block = False
            
            for line in reversed(lines):
                if "🤖 생각 중..." in line:
                    skip_block = True
                    continue
                elif skip_block and line.strip().startswith("[") and "🤖 AI" in line:
                    skip_block = False
                    continue
                elif not skip_block:
                    filtered_lines.append(line)
            
            # 텍스트 업데이트
            filtered_lines.reverse()
            new_text = '\n'.join(filtered_lines)
            
            self.chat_display.configure(state="normal")
            self.chat_display.delete("1.0", tk.END)
            self.chat_display.insert("1.0", new_text)
            self.chat_display.configure(state="disabled")
            self.chat_display.see(tk.END)
            
        except Exception as e:
            print(f"메시지 제거 오류: {e}")

    def update_time(self):
        """시간 업데이트"""
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.time_label.configure(text=current_time)
        self.root.after(1000, self.update_time)

    def on_closing(self):
        """프로그램 종료 시 정리"""
        
        if self.is_analyzing:
            result = messagebox.askyesnocancel(
                "종료 확인",
                "분석이 진행 중입니다. 정말 종료하시겠습니까?"
            )
            if not result:
                return
        
        # 정리 작업
        try:
            if self.agent:
                print("🧹 시스템 정리 중...")
                
        except Exception as e:
            print(f"정리 작업 오류: {str(e)}")
        
        print("👋 프로그램을 종료합니다.")
        self.root.destroy()

def main():
    """GUI 애플리케이션 시작"""
    
    try:
        print("🚀 AI 회계 분석 시스템 GUI 시작...")
        print("📂 현재 작업 디렉토리:", os.getcwd())
        
        # 필요한 모듈 확인
        required_files = [
            "core_agent_engine.py",
            "conversation_handler.py",
            "document_generator.py"  # 추가
        ]
        
        missing_files = []
        for file in required_files:
            if not os.path.exists(file):
                missing_files.append(file)
        
        if missing_files:
            print(f"❌ 필수 파일 누락: {', '.join(missing_files)}")
            print("💡 모든 파일이 같은 폴더에 있는지 확인하세요.")
            return
        
        # GUI 시작
        app = ModernAccountingGUI()
        print("✅ GUI 초기화 완료")
        app.root.mainloop()
        
    except Exception as e:
        print(f"❌ 시작 오류: {str(e)}")
        try:
            import tkinter.messagebox as mb
            mb.showerror("시작 오류", f"애플리케이션 시작 중 오류가 발생했습니다:\n{str(e)}")
        except:
            pass

if __name__ == "__main__":
    main()