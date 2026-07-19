#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI 기반 회계 분석 시스템 - 간단 버전 (파일 이동 없이)
"""

import sys
import os
import logging
from datetime import datetime

# 한글 Windows 콘솔(cp949)은 이모지를 출력할 수 없어 print에서 크래시가 발생함
# → 표준 출력을 UTF-8로 강제 (표현 불가 문자는 ?로 대체해 크래시 방지)
for stream in (sys.stdout, sys.stderr):
    if stream and hasattr(stream, "reconfigure"):
        stream.reconfigure(encoding="utf-8", errors="replace")

# 현재 디렉토리를 Python 경로에 추가
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

def print_banner():
    """시스템 배너 출력"""
    banner = """
╔══════════════════════════════════════════════════════════════════════════════╗
║                        🏛️ AI 기반 회계 분석 시스템                              ║
║                     Professional Accounting AI Platform                     ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  🤖 A2A 다중 모델 협업: llama3.1:8b + qwen2.5:7b + mistral:7b                ║
║  📊 DART API 연동: 실시간 기업 재무 데이터 수집                                 ║
║  🎯 개발 목적: 삼일회계법인 AI 활용 전형 포트폴리오                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""
    print(banner)

def check_dependencies():
    """필수 패키지 확인"""
    required = ['requests', 'pandas', 'matplotlib', 'numpy']
    missing = []
    
    for package in required:
        try:
            __import__(package)
            print(f"✅ {package}")
        except ImportError:
            missing.append(package)
            print(f"❌ {package}")
    
    if missing:
        print(f"\n설치 필요: pip install {' '.join(missing)}")
        return False
    return True

def test_basic_functions():
    """기본 기능 테스트"""
    try:
        print("🧪 모듈 로딩 테스트...")
        
        # 파일명 그대로 import (경로 수정 없이)
        from core_agent_engine import AdvancedAuditAgent
        print("✅ AdvancedAuditAgent 로드 성공")
        
        from conversation_handler import SmartConversationHandler
        print("✅ SmartConversationHandler 로드 성공")
        
        print("✅ 모든 모듈 로드 성공!")
        return True
        
    except ImportError as e:
        print(f"❌ 모듈 로드 실패: {str(e)}")
        return False



def run_gui():
    """GUI 실행"""
    try:
        print("🖥️ GUI 모드 시작...")
        
        # 실제 파일명으로 import
        from main_gui_interface import ModernAccountingGUI
        
        app = ModernAccountingGUI()
        app.root.mainloop()
        
    except ImportError as e:
        print(f"❌ GUI 모듈 오류: {str(e)}")
        print("현재 디렉토리의 파일을 확인하세요:")
        
        # 현재 디렉토리 파일 목록 표시
        import os
        files = [f for f in os.listdir('.') if f.endswith('.py')]
        print("Python 파일들:", files)
        
    except Exception as e:
        print(f"❌ GUI 실행 오류: {str(e)}")

def main():
    """메인 함수"""
    print_banner()
    
    print("🔍 시스템 체크...")
    if not check_dependencies():
        return
    
    if not test_basic_functions():
        return
    
    run_gui() # GUI 모드 직접 실행

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 프로그램을 종료합니다.")
    except Exception as e:
        print(f"\n❌ 실행 오류: {str(e)}")