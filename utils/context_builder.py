"""프롬프트 컨텍스트 빌더 (프로필 + 히스토리 → 프롬프트 섹션)"""
import re
from typing import Dict, List

KOREAN_INSTRUCTION = (
    "\n\n[필수 언어 규칙 - CRITICAL]\n"
    "반드시 한국어로만 답변하세요.\n"
    "절대 금지 언어: 중국어(中文), 영어(English), 아랍어(Arabic), 일본어(Japanese), 기타 모든 외국어.\n"
    "허용 언어: 한국어(Korean/한글)만 허용. 숫자·기술용어(Java, SQL 등)는 그대로 사용 가능.\n"
    "You MUST respond in Korean (한국어) ONLY.\n"
    "FORBIDDEN: Chinese, Arabic, Japanese, English sentences.\n"
    "请只用韩语(한국어)回答。禁止使用中文、阿拉伯语、日语。\n"
)

KOREAN_SUFFIX = (
    "\n\n[최종 언어 확인 - 절대 준수]\n"
    "모든 설명·이유·피드백은 반드시 한국어로만 작성하세요.\n"
    "중국어·아랍어·일본어·영어 문장 사용 시 오답으로 처리됩니다.\n"
    "Korean ONLY. No Chinese. No Arabic. No Japanese.\n"
)


# ── 비한국어 텍스트 필터 ──────────────────────────────────────────────────────

# 허용 문자: 한글, ASCII(숫자·영문·기호), 공백
_ALLOWED = re.compile(r"^[\uAC00-\uD7A3\u1100-\u11FF\u3130-\u318F\u0000-\u007F\s\.\,\!\?\:\;\-\|\(\)\[\]\{\}/]+$")
# 금지 유니코드 블록: 아랍어, 중국어CJK, 일본어
_FORBIDDEN_RANGES = re.compile(
    r"[\u0600-\u06FF"    # 아랍어
    r"\u0750-\u077F"     # 아랍어 보충
    r"\u4E00-\u9FFF"     # 중국어 CJK
    r"\u3040-\u30FF"     # 일본어 히라가나·가타카나
    r"\u31F0-\u31FF]"    # 일본어 가타카나 확장
)


def has_forbidden_chars(text: str) -> bool:
    """아랍어·중국어·일본어 등 금지 문자가 포함돼 있으면 True"""
    return bool(_FORBIDDEN_RANGES.search(text))


def strip_forbidden_text(text: str) -> str:
    """금지 문자가 전체 텍스트의 30% 이상이면 빈 문자열 반환, 아니면 금지 문자만 제거"""
    if not text:
        return text
    forbidden_count = len(_FORBIDDEN_RANGES.findall(text))
    if forbidden_count / max(len(text), 1) >= 0.3:
        return ""  # 30% 이상이면 해당 항목 전체 버림
    return _FORBIDDEN_RANGES.sub("", text).strip()


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
