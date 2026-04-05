"""프롬프트 컨텍스트 빌더 (프로필 + 히스토리 → 프롬프트 섹션)"""
from typing import Dict, List

KOREAN_INSTRUCTION = "\n\n[언어 규칙] 반드시 한국어로만 답변하세요. 절대 중국어나 영어로 답변하지 마세요."


def build_profile_section(profile: Dict[str, str]) -> str:
    """프로필 → 프롬프트 섹션 변환"""
    if not profile:
        return ""
    lines = ["[팀 프로필 - 반드시 이 팀 기준으로 분석하세요]"]
    label_map = {
        "company_name": "회사명",
        "team_name": "팀명",
        "tech_stack": "기술스택",
        "custom_terms": "팀 전용 용어",
        "analysis_style": "분석 스타일",
        "extra_notes": "추가 참고사항",
    }
    for key, label in label_map.items():
        value = profile.get(key, "").strip()
        if value:
            lines.append(f"- {label}: {value}")
    return "\n\n" + "\n".join(lines) if len(lines) > 1 else ""


def build_history_section(history: List[Dict]) -> str:
    """이전 분석 히스토리 → 프롬프트 섹션 변환"""
    if not history:
        return ""
    lines = ["[이전 분석 맥락 - 일관성 유지에 참고하세요]"]
    for i, item in enumerate(history[:3], 1):
        input_text = (item.get("input_text") or "")[:100]
        summary = (item.get("output_summary") or "")[:300]
        file_name = item.get("file_name", "")
        lines.append(f"\n이전 분석 {i} ({file_name}):")
        if input_text:
            lines.append(f"  요청: {input_text}...")
        if summary:
            lines.append(f"  결과(일부): {summary}...")
    return "\n\n" + "\n".join(lines)
