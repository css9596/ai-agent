"""소스 코드와 분석 결과를 비교하여 수정 가이드를 생성하는 에이전트"""

import json
from typing import Any, Dict, List

from utils.claude_client import ClaudeClient
from utils.project_extractor import ProjectSnapshot
from utils.context_builder import KOREAN_INSTRUCTION


class SourceComparatorAgent:
    """분석 결과 vs 실제 소스코드 비교 에이전트"""

    name = "SourceComparatorAgent"

    def __init__(self, client: ClaudeClient) -> None:
        self.client = client

    def run(
        self,
        context: Dict[str, Any],
        project_snapshot: ProjectSnapshot,
        feedback: str = ""
    ) -> Dict[str, Any]:
        """
        분석 결과와 실제 소스코드를 비교합니다.

        입력:
            context: {
                "planner": {...요구사항...},
                "developer": {...기술설계...},
                "impact_analyzer": {...파일영향...},
                "reviewer": {...리스크...}
            }
            project_snapshot: {
                files: [파일 목록],
                file_tree: 디렉토리 구조
            }

        출력:
            context["source_comparator"] = {
                "summary": {...},
                "file_guides": [...],
                "db_guide": [...]
            }
        """
        print("[SourceComparatorAgent] 소스 코드 비교 중...")

        # 분석 결과 추출
        impact = context.get("impact_analyzer", {})
        developer = context.get("developer", {})
        impacted_modules = developer.get("impacted_modules", [])
        file_impacts = impact.get("file_impacts", {})
        db_changes = impact.get("db_changes", [])

        # 프로젝트 파일 목록 생성
        project_file_list = self._build_file_list(project_snapshot)

        # LLM 호출: 비교 분석
        prompt = self._build_comparison_prompt(
            impacted_modules,
            file_impacts,
            db_changes,
            project_file_list,
            context.get("planner", {})
        )

        comparison_result = self.client.request_json(
            system_prompt=(
                "You are a source code comparison assistant. "
                "Compare analysis requirements with actual source structure and provide modification guides. "
                "Always respond with valid JSON only. Always respond in Korean only."
            ),
            user_prompt=prompt
        )

        # 결과 정리
        result = self._parse_comparison_result(comparison_result, project_snapshot)
        context["source_comparator"] = result

        return context

    def _build_file_list(self, snapshot: ProjectSnapshot) -> str:
        """프로젝트 파일 목록 생성"""
        lines = []
        for f in snapshot.files[:50]:  # 처음 50개 파일만
            methods_str = ""
            if f.language == "java" and f.methods:
                methods_str = f" [{', '.join(m['name'] for m in f.methods[:5])}]"
            lines.append(f"- {f.path} ({f.language}){methods_str}")
        return "\n".join(lines)

    def _build_comparison_prompt(
        self,
        impacted_modules: List[str],
        file_impacts: Dict[str, Any],
        db_changes: List[Dict],
        project_file_list: str,
        planner: Dict[str, Any]
    ) -> str:
        """비교 분석 프롬프트 구성"""
        functional_reqs = planner.get("functional_requirements", [])

        prompt = (
            f"{KOREAN_INSTRUCTION}\n\n"
            "# 소스 코드 비교 분석\n\n"
            "## 분석 결과 (필요한 변경)\n\n"
            f"**영향받는 모듈**: {', '.join(impacted_modules)}\n\n"
            f"**기능 요구사항**: {json.dumps(functional_reqs[:5], ensure_ascii=False, indent=2)}\n\n"
        )

        # 파일 영향도
        if file_impacts:
            prompt += "## 파일 영향도\n"
            for layer, files in file_impacts.items():
                if isinstance(files, list):
                    for f in files[:3]:
                        file_path = f.get("file", "")
                        change_type = f.get("change_type", "")
                        reason = f.get("reason", "")
                        prompt += f"\n- [{layer}] {file_path} ({change_type})\n  이유: {reason}"

        # DB 변경
        if db_changes:
            prompt += "\n\n## 데이터베이스 변경\n"
            for db in db_changes[:3]:
                table = db.get("table", "")
                change = db.get("change_type", "")
                reason = db.get("reason", "")
                prompt += f"\n- {table} ({change}): {reason}"

        # 실제 프로젝트 파일 목록
        prompt += (
            f"\n\n## 실제 프로젝트 파일 목록\n"
            f"{project_file_list}\n\n"
            "## 수정 가이드 생성\n\n"
            "위 분석 결과와 실제 파일을 비교해서 JSON으로 수정 가이드를 생성하세요.\n\n"
            "응답 형식:\n"
            "{\n"
            '  "summary": {\n'
            '    "total_files_analyzed": 숫자,\n'
            '    "files_need_change": 숫자,\n'
            '    "new_files_needed": 숫자\n'
            "  },\n"
            '  "file_guides": [\n'
            "    {\n"
            '      "file": "파일경로",\n'
            '      "status": "NEW|MODIFY|NO_CHANGE",\n'
            '      "changes": [\n'
            "        {\n"
            '          "type": "ADD_METHOD|MODIFY_METHOD|ADD_FIELD|etc",\n'
            '          "location": "위치 설명",\n'
            '          "reason": "변경 사유",\n'
            '          "before": "기존 코드 (없으면 null)",\n'
            '          "after": "변경될 코드",\n'
            '          "priority": "HIGH|MEDIUM|LOW"\n'
            "        }\n"
            "      ]\n"
            "    }\n"
            "  ],\n"
            '  "db_guide": [\n'
            "    {\n"
            '      "table": "테이블명",\n'
            '      "status": "NEW|ADD_COLUMN|MODIFY",\n'
            '      "sql": "SQL 문장",\n'
            '      "reason": "변경 사유"\n'
            "    }\n"
            "  ]\n"
            "}\n"
        )

        return prompt

    def _parse_comparison_result(
        self,
        result: Dict[str, Any],
        snapshot: ProjectSnapshot
    ) -> Dict[str, Any]:
        """비교 결과 파싱 및 정리"""
        return {
            "summary": result.get("summary", {
                "total_files_analyzed": len(snapshot.files),
                "files_need_change": 0,
                "new_files_needed": 0
            }),
            "file_guides": result.get("file_guides", []),
            "db_guide": result.get("db_guide", []),
            "project_name": snapshot.name,
            "total_files": snapshot.total_files
        }

    @staticmethod
    def pretty(result: Dict[str, Any]) -> str:
        """결과를 보기 좋게 포맷팅"""
        return json.dumps(result, ensure_ascii=False, indent=2)
