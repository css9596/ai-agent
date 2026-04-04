"""파일 처리 유틸리티 단위 테스트"""

import tempfile
from pathlib import Path
import pytest
from utils.file_processor import (
    extract_text_from_file,
    read_text_file,
    is_supported_file,
    get_supported_formats,
    ExtractionResult,
)


class TestIsSupportedFile:
    """지원 파일 형식 확인 테스트"""

    def test_is_supported_txt(self):
        """txt 파일"""
        assert is_supported_file("document.txt") is True

    def test_is_supported_md(self):
        """마크다운 파일"""
        assert is_supported_file("readme.md") is True

    def test_is_supported_pdf(self):
        """PDF 파일"""
        assert is_supported_file("report.pdf") is True

    def test_is_supported_xlsx(self):
        """Excel 파일"""
        assert is_supported_file("data.xlsx") is True

    def test_is_supported_pptx(self):
        """PowerPoint 파일"""
        assert is_supported_file("presentation.pptx") is True

    def test_unsupported_docx(self):
        """.docx는 지원하지 않음 (추출기 없음)"""
        assert is_supported_file("document.docx") is False

    def test_unsupported_csv(self):
        """.csv는 지원하지 않음"""
        assert is_supported_file("data.csv") is False

    def test_unsupported_jpg(self):
        """이미지 파일은 지원하지 않음"""
        assert is_supported_file("image.jpg") is False

    def test_is_supported_case_insensitive(self):
        """대소문자 무관"""
        assert is_supported_file("DOCUMENT.TXT") is True
        assert is_supported_file("README.MD") is True
        assert is_supported_file("REPORT.PDF") is True


class TestGetSupportedFormats:
    """지원 형식 목록 테스트"""

    def test_get_supported_formats_contains_common(self):
        """일반적인 형식 포함"""
        formats = get_supported_formats()
        assert ".txt" in formats
        assert ".md" in formats
        assert ".pdf" in formats

    def test_get_supported_formats_no_docx(self):
        """.docx 제외"""
        formats = get_supported_formats()
        assert ".docx" not in formats

    def test_get_supported_formats_is_list(self):
        """리스트 반환"""
        formats = get_supported_formats()
        assert isinstance(formats, list)


class TestReadTextFile:
    """텍스트 파일 읽기 테스트"""

    def test_read_text_file_utf8(self):
        """UTF-8 파일"""
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", suffix=".txt", delete=False
        ) as f:
            f.write("Hello World\n한글 테스트")
            f.flush()
            temp_path = f.name

        try:
            result = read_text_file(temp_path)
            assert result.success is True
            assert "Hello World" in result.text
            assert "한글 테스트" in result.text
        finally:
            Path(temp_path).unlink()

    def test_read_text_file_euc_kr_fallback(self):
        """EUC-KR 폴백"""
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="euc-kr", suffix=".txt", delete=False
        ) as f:
            f.write("한글 파일\n테스트")
            f.flush()
            temp_path = f.name

        try:
            result = read_text_file(temp_path)
            assert result.success is True
            assert "한글 파일" in result.text or "테스트" in result.text
        finally:
            Path(temp_path).unlink()

    def test_read_text_file_not_found(self):
        """파일 없음"""
        result = read_text_file("/nonexistent/path/file.txt")
        assert result.success is False
        assert result.error is not None

    def test_read_text_file_returns_extraction_result(self):
        """ExtractionResult 반환"""
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", suffix=".txt", delete=False
        ) as f:
            f.write("test")
            temp_path = f.name

        try:
            result = read_text_file(temp_path)
            assert isinstance(result, ExtractionResult)
            assert result.page_count == 1
        finally:
            Path(temp_path).unlink()


class TestExtractTextFromFile:
    """파일 형식 자동 감지 및 추출 테스트"""

    def test_extract_txt_file(self):
        """텍스트 파일"""
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", suffix=".txt", delete=False
        ) as f:
            f.write("Test content")
            temp_path = f.name

        try:
            result = extract_text_from_file(temp_path, "test.txt")
            assert result.success is True
            assert "Test content" in result.text
        finally:
            Path(temp_path).unlink()

    def test_extract_md_file(self):
        """마크다운 파일"""
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", suffix=".md", delete=False
        ) as f:
            f.write("# Heading\n\nContent")
            temp_path = f.name

        try:
            result = extract_text_from_file(temp_path, "readme.md")
            assert result.success is True
            assert "# Heading" in result.text
        finally:
            Path(temp_path).unlink()

    def test_extract_unknown_extension_fallback(self):
        """미지원 확장자는 텍스트로 폴백"""
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", suffix=".unknown", delete=False
        ) as f:
            f.write("fallback test")
            temp_path = f.name

        try:
            result = extract_text_from_file(temp_path, "file.unknown")
            # 텍스트 파일로 취급되므로 성공
            assert result.success is True
            assert "fallback test" in result.text
        finally:
            Path(temp_path).unlink()

    def test_extract_nonexistent_file(self):
        """존재하지 않는 파일"""
        result = extract_text_from_file("/nonexistent/file.txt", "file.txt")
        assert result.success is False
        assert result.error is not None

    def test_extract_stores_file_size(self):
        """파일 크기 저장"""
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", suffix=".txt", delete=False
        ) as f:
            f.write("Content")  # 7 bytes
            temp_path = f.name

        try:
            result = extract_text_from_file(temp_path, "test.txt")
            assert result.file_size > 0
        finally:
            Path(temp_path).unlink()


class TestExtractionResult:
    """ExtractionResult 데이터클래스 테스트"""

    def test_extraction_result_success(self):
        """성공 결과"""
        result = ExtractionResult(success=True, text="Extracted text")
        assert result.success is True
        assert result.text == "Extracted text"
        assert result.error is None

    def test_extraction_result_failure(self):
        """실패 결과"""
        result = ExtractionResult(
            success=False, error="File not found"
        )
        assert result.success is False
        assert result.error == "File not found"

    def test_extraction_result_default_values(self):
        """기본값"""
        result = ExtractionResult(success=True)
        assert result.text == ""
        assert result.error is None
        assert result.file_size == 0
        assert result.page_count == 0

    def test_extraction_result_with_metadata(self):
        """메타데이터"""
        result = ExtractionResult(
            success=True,
            text="PDF content",
            file_size=102400,
            page_count=10
        )
        assert result.file_size == 102400
        assert result.page_count == 10


class TestFileProcessorIntegration:
    """파일 처리 통합 테스트"""

    def test_process_multiple_files(self):
        """여러 파일 처리"""
        files = []
        try:
            # 텍스트 파일
            with tempfile.NamedTemporaryFile(
                mode="w", encoding="utf-8", suffix=".txt", delete=False
            ) as f:
                f.write("Text content")
                files.append((f.name, "test.txt"))

            # 마크다운 파일
            with tempfile.NamedTemporaryFile(
                mode="w", encoding="utf-8", suffix=".md", delete=False
            ) as f:
                f.write("# Markdown")
                files.append((f.name, "readme.md"))

            # 모두 처리 가능
            for path, name in files:
                result = extract_text_from_file(path, name)
                assert result.success is True
        finally:
            for path, _ in files:
                Path(path).unlink()

    def test_supported_formats_consistency(self):
        """is_supported_file과 get_supported_formats 일관성"""
        formats = get_supported_formats()

        # supported_formats의 모든 확장자는 is_supported_file도 지원
        for ext in formats:
            filename = f"test{ext}"
            assert is_supported_file(filename) is True

        # is_supported_file이 지원하지 않는 것
        assert is_supported_file("test.docx") is False
        assert is_supported_file("test.csv") is False
