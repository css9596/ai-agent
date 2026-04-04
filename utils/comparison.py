"""분석 결과 비교 기능"""

from typing import Dict, Any, List, Tuple
import difflib


def compare_analyses(analysis1: Dict[str, Any], analysis2: Dict[str, Any]) -> Dict[str, Any]:
    """두 분석 결과 비교"""
    comparison = {
        "analysis1_file": analysis1.get("output_file", "unknown"),
        "analysis2_file": analysis2.get("output_file", "unknown"),
        "timestamp": analysis2.get("created_at", ""),
        "differences": []
    }

    # 마크다운 콘텐츠 비교 (간단한 줄 단위 diff)
    md1 = analysis1.get("markdown", "")
    md2 = analysis2.get("markdown", "")

    if md1 or md2:
        diff = compute_diff(md1, md2)
        comparison["diff"] = diff

    # 주요 변경 사항 요약
    summary = summarize_changes(analysis1, analysis2)
    comparison["summary"] = summary

    return comparison


def compute_diff(text1: str, text2: str) -> Dict[str, List[Dict[str, Any]]]:
    """두 텍스트의 diff 계산"""
    lines1 = text1.splitlines(keepends=True)
    lines2 = text2.splitlines(keepends=True)

    diff_lines = list(difflib.unified_diff(lines1, lines2, lineterm=''))

    # diff 결과를 구조화된 형식으로 변환
    result = {
        "added": [],
        "removed": [],
        "modified": []
    }

    for line in diff_lines:
        if line.startswith('+') and not line.startswith('+++'):
            result["added"].append({
                "content": line[1:].strip(),
                "line": line
            })
        elif line.startswith('-') and not line.startswith('---'):
            result["removed"].append({
                "content": line[1:].strip(),
                "line": line
            })

    return result


def summarize_changes(analysis1: Dict[str, Any], analysis2: Dict[str, Any]) -> Dict[str, Any]:
    """두 분석 사이의 주요 변경 사항 요약"""
    summary = {
        "total_changes": 0,
        "categories": {}
    }

    # 각 에이전트별 결과 비교
    agents = ["planner", "developer", "reviewer"]

    for agent in agents:
        agent_data1 = analysis1.get(agent, {})
        agent_data2 = analysis2.get(agent, {})

        if not agent_data1 and not agent_data2:
            continue

        agent_changes = compare_agent_results(agent, agent_data1, agent_data2)
        if agent_changes:
            summary["categories"][agent] = agent_changes
            summary["total_changes"] += 1

    return summary


def compare_agent_results(agent: str, data1: Dict[str, Any], data2: Dict[str, Any]) -> Dict[str, Any]:
    """에이전트 결과 비교"""
    changes = {
        "added": [],
        "removed": [],
        "modified": []
    }

    if agent == "planner":
        changes["requirements"] = compare_lists(
            data1.get("core_requirements", []),
            data2.get("core_requirements", [])
        )

    elif agent == "developer":
        changes["modules"] = compare_lists(
            data1.get("impacted_modules", []),
            data2.get("impacted_modules", [])
        )

    elif agent == "reviewer":
        changes["security_risks"] = compare_lists(
            data1.get("security_risks", []),
            data2.get("security_risks", [])
        )
        changes["performance_risks"] = compare_lists(
            data1.get("performance_risks", []),
            data2.get("performance_risks", [])
        )

    return changes if any(v for v in changes.values()) else {}


def compare_lists(list1: List[str], list2: List[str]) -> Dict[str, List[str]]:
    """두 리스트 비교"""
    set1 = set(list1) if list1 else set()
    set2 = set(list2) if list2 else set()

    return {
        "added": sorted(set2 - set1),
        "removed": sorted(set1 - set2),
        "common": sorted(set1 & set2)
    }


def generate_comparison_report(comparison: Dict[str, Any]) -> str:
    """비교 결과 마크다운 리포트 생성"""
    report = f"""# 분석 결과 비교

## 비교 대상
- **분석 1**: {comparison.get('analysis1_file', 'Unknown')}
- **분석 2**: {comparison.get('analysis2_file', 'Unknown')}
- **비교 시간**: {comparison.get('timestamp', 'Unknown')}

## 변경 요약

"""

    summary = comparison.get("summary", {})
    if summary:
        report += f"**총 변경 사항 수**: {summary.get('total_changes', 0)}\n\n"

        categories = summary.get("categories", {})
        if categories:
            report += "### 카테고리별 변경 사항\n\n"
            for agent, changes in categories.items():
                agent_names = {
                    "planner": "기획자",
                    "developer": "개발자",
                    "reviewer": "검토자"
                }
                report += f"#### {agent_names.get(agent, agent)}\n"

                for category, items in changes.items():
                    if isinstance(items, dict):
                        if items.get("added"):
                            report += f"\n**추가됨**:\n"
                            for item in items["added"]:
                                report += f"  - {item}\n"

                        if items.get("removed"):
                            report += f"\n**제거됨**:\n"
                            for item in items["removed"]:
                                report += f"  - {item}\n"

                report += "\n"

    # Diff 정보 추가
    diff = comparison.get("diff", {})
    if diff:
        added = diff.get("added", [])
        removed = diff.get("removed", [])

        if added or removed:
            report += "## 상세 변경 사항\n\n"

            if removed:
                report += "### 삭제된 항목\n\n"
                for item in removed[:10]:  # 처음 10개만 표시
                    content = item.get("content", "")
                    report += f"- `{content[:80]}`\n"
                if len(removed) > 10:
                    report += f"\n... 외 {len(removed) - 10}개 삭제됨\n"

            if added:
                report += "\n### 추가된 항목\n\n"
                for item in added[:10]:  # 처음 10개만 표시
                    content = item.get("content", "")
                    report += f"- `{content[:80]}`\n"
                if len(added) > 10:
                    report += f"\n... 외 {len(added) - 10}개 추가됨\n"

    return report
