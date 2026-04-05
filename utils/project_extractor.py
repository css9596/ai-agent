"""ZIP 프로젝트 파일을 파싱해서 소스 구조를 추출하는 유틸리티"""

import json
import re
import zipfile
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict


@dataclass
class SourceFile:
    """소스 파일 정보"""
    path: str              # 상대 경로 (예: src/main/java/BoardController.java)
    relative_path: str     # 읽기 쉬운 경로
    size: int
    language: str          # "java", "jsp", "xml", "sql", "js", "html", "properties"
    content: Optional[str] = None  # 파일 내용
    methods: List[Dict] = None     # Java: [{name, line_start, line_end}]

    def __post_init__(self):
        if self.methods is None:
            self.methods = []


@dataclass
class ProjectSnapshot:
    """프로젝트 스냅샷 (파싱된 소스 구조)"""
    project_id: str
    name: str
    files: List[SourceFile]
    file_tree: Dict  # 디렉토리 구조
    total_files: int
    total_size: int
    supported_files: int  # 지원되는 파일 수


class ProjectExtractor:
    """ZIP 프로젝트 추출 및 파싱"""

    # 지원 파일 확장자
    SUPPORTED_EXTENSIONS = {
        ".java", ".jsp", ".xml", ".sql", ".js", ".html", ".properties"
    }

    # 제외할 패턴
    EXCLUDED_PATTERNS = {
        "/target/", "/.git/", "/node_modules/", "/.mvn/",
        ".class", ".jar", ".war", ".zip", ".tar", ".gz"
    }

    @staticmethod
    def extract_from_zip(zip_path: str, project_id: str, project_name: str) -> Optional[ProjectSnapshot]:
        """
        ZIP 파일에서 소스 구조를 추출합니다.

        Args:
            zip_path: ZIP 파일 경로
            project_id: 프로젝트 ID
            project_name: 프로젝트 이름

        Returns:
            ProjectSnapshot 또는 None (실패 시)
        """
        try:
            files = []
            file_tree = {}
            total_size = 0
            supported_count = 0

            with zipfile.ZipFile(zip_path, 'r') as zf:
                for zip_info in zf.infolist():
                    file_path = zip_info.filename

                    # 제외 패턴 확인
                    if ProjectExtractor._should_exclude(file_path):
                        continue

                    # 디렉토리 제외
                    if zip_info.is_dir():
                        continue

                    # 파일 크기
                    file_size = zip_info.file_size
                    total_size += file_size

                    # 확장자 확인
                    ext = Path(file_path).suffix.lower()
                    if ext not in ProjectExtractor.SUPPORTED_EXTENSIONS:
                        continue

                    supported_count += 1

                    # 언어 결정
                    language = ProjectExtractor._get_language(ext)

                    # 파일 내용 읽기 (작은 파일만 - 메모리 절약)
                    content = None
                    try:
                        if file_size < 1024 * 100:  # 100KB 이하만 읽기
                            with zf.open(file_path) as f:
                                content = f.read().decode('utf-8', errors='ignore')
                    except Exception:
                        pass

                    # 메서드 추출 (Java 파일)
                    methods = []
                    if language == "java" and content:
                        methods = ProjectExtractor._extract_java_methods(content)

                    # SourceFile 생성
                    source_file = SourceFile(
                        path=file_path,
                        relative_path=file_path.replace("\\", "/"),
                        size=file_size,
                        language=language,
                        content=content[:5000] if content else None,  # 처음 5000자만
                        methods=methods
                    )
                    files.append(source_file)

                    # 파일 트리 업데이트
                    ProjectExtractor._update_file_tree(file_tree, file_path, language)

            # ProjectSnapshot 생성
            snapshot = ProjectSnapshot(
                project_id=project_id,
                name=project_name,
                files=files,
                file_tree=file_tree,
                total_files=len(files),
                total_size=total_size,
                supported_files=supported_count
            )

            return snapshot

        except Exception as e:
            print(f"❌ 프로젝트 추출 실패: {str(e)}")
            return None

    @staticmethod
    def _should_exclude(file_path: str) -> bool:
        """파일이 제외 대상인지 확인"""
        for pattern in ProjectExtractor.EXCLUDED_PATTERNS:
            if pattern in file_path:
                return True
        return False

    @staticmethod
    def _get_language(extension: str) -> str:
        """확장자에서 언어 결정"""
        ext_map = {
            ".java": "java",
            ".jsp": "jsp",
            ".xml": "xml",
            ".sql": "sql",
            ".js": "javascript",
            ".html": "html",
            ".properties": "properties"
        }
        return ext_map.get(extension, "unknown")

    @staticmethod
    def _extract_java_methods(content: str) -> List[Dict]:
        """Java 파일에서 메서드 추출 (정규식)"""
        methods = []

        # 메서드 패턴: public/private/protected void/String/List methodName(...)
        pattern = r'(public|private|protected)?\s+(static)?\s+(\w+[\[\]]*)\s+(\w+)\s*\('

        for match in re.finditer(pattern, content, re.MULTILINE):
            method_name = match.group(4)
            line_start = content[:match.start()].count('\n') + 1
            methods.append({
                "name": method_name,
                "line": line_start,
                "signature": match.group(0)
            })

        return methods[:20]  # 최대 20개만

    @staticmethod
    def _update_file_tree(file_tree: Dict, file_path: str, language: str) -> None:
        """파일 트리 업데이트"""
        parts = file_path.split('/')
        current = file_tree

        for part in parts[:-1]:
            if part not in current:
                current[part] = {}
            current = current[part]

        # 마지막 파일
        file_name = parts[-1]
        current[file_name] = {"type": "file", "lang": language}

    @staticmethod
    def snapshot_to_json(snapshot: ProjectSnapshot) -> str:
        """ProjectSnapshot을 JSON으로 직렬화"""
        data = {
            "project_id": snapshot.project_id,
            "name": snapshot.name,
            "files": [
                {
                    "path": f.path,
                    "relative_path": f.relative_path,
                    "size": f.size,
                    "language": f.language,
                    "methods": f.methods
                }
                for f in snapshot.files
            ],
            "file_tree": snapshot.file_tree,
            "total_files": snapshot.total_files,
            "total_size": snapshot.total_size,
            "supported_files": snapshot.supported_files
        }
        return json.dumps(data, ensure_ascii=False, indent=2)

    @staticmethod
    def json_to_snapshot(json_str: str) -> Optional[ProjectSnapshot]:
        """JSON에서 ProjectSnapshot 복원"""
        try:
            data = json.loads(json_str)
            files = [
                SourceFile(
                    path=f["path"],
                    relative_path=f["relative_path"],
                    size=f["size"],
                    language=f["language"],
                    methods=f.get("methods", [])
                )
                for f in data["files"]
            ]
            return ProjectSnapshot(
                project_id=data["project_id"],
                name=data["name"],
                files=files,
                file_tree=data["file_tree"],
                total_files=data["total_files"],
                total_size=data["total_size"],
                supported_files=data["supported_files"]
            )
        except Exception as e:
            print(f"❌ JSON 파싱 실패: {str(e)}")
            return None
