# 🏛️ AI 기반 회계 분석 시스템

> **AI 에이전트 포트폴리오 프로젝트**

회계법인 업무를 자동화할 수 있는 AI 에이전트 시스템입니다. 3개의 전문 AI가 협업하여 기업 재무 분석부터 전문 보고서 생성까지 전 과정을 자동화합니다.

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)
![Status](https://img.shields.io/badge/Status-완성-success.svg)

## ✨ 핵심 기능

### 🤖 A2A (AI-to-AI) 협업 시스템
- **김성실 (총괄조정관)** - llama3.1:8b
- **이정확 (재무분석가)** - qwen2.5:7b  
- **박의심 (부정탐지전문가)** - mistral:7b

3개 AI가 실제로 토론하며 합의를 도출하는 혁신적 시스템

### 📊 실시간 DART API 연동
- 금융감독원 공식 전자공시시스템 연동
- 실시간 기업 재무제표 수집
- 다년도 추세 분석
- 부정 위험 자동 탐지

### 💬 지능형 대화 시스템
- 자연어 질의 자동 분류 (7가지 유형)
- 컨텍스트 기반 대화 관리
- 보고서 생성 요청 자동 감지

### 📋 전문 보고서 자동 생성
- **DOCX**: 회계법인 수준 종합 보고서
- **Excel**: 상세 재무 데이터 분석표  
- **PDF**: 프레젠테이션용 요약 보고서

### 📈 고급 시각화
- 재무비율 비교 차트
- 다년도 추세 분석
- 부정위험 레이더 차트
- 종합 대시보드 (인터랙티브)

## 🛠️ 기술 스택

| 분야 | 기술 |
|------|------|
| **Backend** | Python 3.8+, Ollama |
| **AI Models** | llama3.1:8b, qwen2.5:7b, mistral:7b |
| **API** | DART 전자공시시스템 |
| **Frontend** | CustomTkinter |
| **Document** | python-docx, openpyxl |
| **Visualization** | Matplotlib, Plotly, Seaborn |

## 🚀 설치 및 실행

### 1단계: 저장소 클론
```bash
git clone https://github.com/YOUR_USERNAME/ai-accounting-agent.git
cd ai-accounting-agent
