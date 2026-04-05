"""
개발 분석서 자동 생성 시스템 - FastAPI 애플리케이션

Phase 1 개선 사항:
- 에러 핸들링 강화
- 분석 결과 자동 정리
- 동시 분석 제한 & 큐 시스템
- 입력 검증 강화
"""

import asyncio
import json
import os
import uuid
import psutil
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional

from dotenv import load_dotenv
from fastapi import FastAPI, File, Form, UploadFile, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse, StreamingResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import sse_starlette.sse

from config import settings
from database import db
from utils.logger import logger
from utils.queue_manager import queue_manager, JobStatus
from utils.file_processor import extract_text_from_file, is_supported_file, get_supported_formats
from utils.export_formats import export_to_html, export_to_pdf, export_to_docx, export_to_json
from utils.comparison import compare_analyses, generate_comparison_report
from orchestrator import Orchestrator
from utils.claude_client import ClaudeClient
from utils.llm_client import LLMClient
from utils.project_extractor import ProjectExtractor
from agents.source_comparator import SourceComparatorAgent

# 환경 변수 로드
load_dotenv()

app = FastAPI(title="개발 분석서 자동 생성기", version="0.2.0")

# ============================================================================
# LLM 클라이언트 초기화 (LLM_MODE에 따라 다른 클라이언트 사용)
# ============================================================================
# LLM_MODE 설정값 (3가지):
#   "mock"   - API 없이 테스트용 하드코딩 응답 반환
#               개발/테스트용. API 키 불필요.
#   "local"  - Ollama 로컬 LLM 사용
#               무료. 인터넷 불필요. Ollama 설치 필수.
#   "claude" - Anthropic Claude API 사용
#               유료. 가장 정확한 분석.
#
# .env 파일에서 변경:
#   LLM_MODE=mock
#   LLM_MODE=local
#   LLM_MODE=claude

if settings.LLM_MODE == "mock":
    # Mock 모드: LLM 없이 하드코딩된 응답 반환
    client = ClaudeClient(api_key="", mock=True)
    print("🔧 Mock 모드 활성화 (API 없이 테스트)")

elif settings.LLM_MODE == "local":
    # Local 모드: Ollama LLM 사용
    # 사전 준비: ollama pull llama3.3:70b (또는 설정한 모델명)
    client = LLMClient(
        base_url=settings.LLM_BASE_URL,
        model=settings.LLM_MODEL,
        api_key=settings.LLM_API_KEY
    )
    print(f"🏠 로컬 LLM 모드 활성화 ({settings.LLM_MODEL} @ {settings.LLM_BASE_URL})")

else:  # "claude" (기본값)
    # Claude 모드: Anthropic Claude API 사용
    client = ClaudeClient(
        api_key=settings.ANTHROPIC_API_KEY,
        model="claude-sonnet-4-5"
    )
    print("🚀 Claude API 모드 활성화")

# SSE 이벤트 큐 관리
event_queues: Dict[str, asyncio.Queue] = {}

# job_id별 분석 컨텍스트 저장 (채팅 정제용)
job_contexts: Dict[str, Dict] = {}

# job_id → analysis_id 매핑 (DB 저장용)
job_to_analysis: Dict[str, str] = {}

# Static 파일 서빙
static_path = Path(__file__).parent / "static"
if static_path.exists():
    app.mount("/static", StaticFiles(directory=str(static_path)), name="static")


# ============================================================================
# 스케줄러 (분석 결과 자동 정리)
# ============================================================================

scheduler = AsyncIOScheduler()


async def cleanup_old_analyses():
    """30일 이상 된 분석 결과 자동 삭제"""
    try:
        deleted_count = db.delete_old_analyses(settings.RETENTION_DAYS)
        logger.info(f"분석 결과 정리", deleted_files=deleted_count)
    except Exception as e:
        logger.error(f"정리 중 오류", error=str(e))


@app.on_event("startup")
async def startup_event():
    """애플리케이션 시작"""
    logger.info("시스템 시작", mock_mode=settings.MOCK_MODE)

    # 스케줄러 설정 (매일 새벽 2시)
    scheduler.add_job(cleanup_old_analyses, "cron", hour=2, minute=0)
    scheduler.start()


@app.on_event("shutdown")
async def shutdown_event():
    """애플리케이션 종료"""
    scheduler.shutdown()
    logger.info("시스템 종료")


# ============================================================================
# 유틸리티 함수
# ============================================================================

def create_event_callback(job_id: str, loop: asyncio.AbstractEventLoop):
    """이벤트 큐에 데이터를 넣는 콜백 함수"""
    def on_event(event_type: str, data: dict):
        if job_id in event_queues:
            event_data = {"type": event_type, **data}
            asyncio.run_coroutine_threadsafe(
                event_queues[job_id].put(event_data),
                loop
            )

    return on_event


async def stream_events(job_id: str):
    """SSE 형식으로 이벤트를 스트림"""
    try:
        while True:
            try:
                event_data = await asyncio.wait_for(
                    event_queues[job_id].get(),
                    timeout=60.0
                )
                yield f"data: {json.dumps(event_data, ensure_ascii=False)}\n\n"

                if event_data.get("type") in ["complete", "error"]:
                    break
            except asyncio.TimeoutError:
                pass
    finally:
        if job_id in event_queues:
            del event_queues[job_id]


def validate_file(file_name: str, file_size: int) -> Optional[str]:
    """파일 검증"""
    # 파일 형식 확인
    if not is_supported_file(file_name):
        return f"지원하지 않는 파일 형식입니다. 지원 형식: {', '.join(get_supported_formats())}"

    # 파일 크기 확인
    max_size_bytes = settings.MAX_FILE_SIZE_MB * 1024 * 1024
    if file_size > max_size_bytes:
        return f"파일 크기가 {settings.MAX_FILE_SIZE_MB}MB를 초과합니다. (현재: {file_size / 1024 / 1024:.1f}MB)"

    return None


def validate_document(document: str) -> Optional[str]:
    """문서 검증"""
    # 길이 확인 (간단한 추정: 1 토큰 ≈ 4 글자)
    estimated_tokens = len(document) // 4
    if estimated_tokens > settings.MAX_DOCUMENT_TOKENS:
        return f"문서가 너무 깁니다. 최대 {settings.MAX_DOCUMENT_TOKENS}개 토큰까지 지원합니다. (현재: ~{estimated_tokens})"

    # 비어있는지 확인
    if not document.strip():
        return "입력이 비어 있습니다."

    return None


# ============================================================================
# API 엔드포인트
# ============================================================================

@app.get("/")
async def root():
    """메인 페이지"""
    index_path = static_path / "index.html"
    if index_path.exists():
        return FileResponse(index_path)
    return {"message": "개발 분석서 자동 생성 시스템"}


@app.get("/api/health")
async def health_check():
    """헬스 체크"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "0.2.0",
        "queue": queue_manager.get_queue_status(),
        "statistics": db.get_statistics()
    }


@app.post("/api/analyze")
async def analyze(
    file: Optional[UploadFile] = File(None),
    text: Optional[str] = Form(None),
    background_tasks: BackgroundTasks = BackgroundTasks()
):
    """분석 요청"""
    # 입력 검증
    if not file and not text:
        logger.warning("분석 요청 실패", reason="입력 없음")
        raise HTTPException(status_code=400, detail={
            "error_code": "NO_INPUT",
            "message": "파일 또는 텍스트를 제공해야 합니다",
            "actions": ["파일을 업로드하거나", "텍스트를 입력하세요"]
        })

    job_id = str(uuid.uuid4())
    analysis_id = f"analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{job_id[:8]}"

    try:
        # 파일 처리
        if file:
            # 파일 검증
            file_size = len(await file.read())
            await file.seek(0)

            error = validate_file(file.filename, file_size)
            if error:
                logger.warning("파일 검증 실패", file_name=file.filename, file_size=file_size, error=error)
                raise HTTPException(status_code=400, detail={
                    "error_code": "FILE_VALIDATION_FAILED",
                    "message": error,
                    "file": file.filename,
                    "size_mb": round(file_size / 1024 / 1024, 2),
                    "max_size_mb": settings.MAX_FILE_SIZE_MB,
                    "actions": ["파일 크기를 줄이세요", "지원 형식을 확인하세요"]
                })

            # 임시 파일로 저장
            temp_dir = Path(settings.TEMP_UPLOAD_DIR)
            temp_dir.mkdir(exist_ok=True)
            temp_file = temp_dir / file.filename

            content = await file.read()
            with open(temp_file, "wb") as f:
                f.write(content)

            # 파일에서 텍스트 추출
            extraction_result = extract_text_from_file(str(temp_file), file.filename)

            if not extraction_result.success:
                logger.error("파일 추출 실패", file_name=file.filename, error=extraction_result.error)
                raise HTTPException(status_code=400, detail={
                    "error_code": "FILE_EXTRACTION_FAILED",
                    "message": f"파일 처리 실패: {extraction_result.error}",
                    "file": file.filename,
                    "actions": ["파일이 손상되지 않았는지 확인하세요", "다른 파일로 시도하세요"]
                })

            document = extraction_result.text

            # 임시 파일 정리
            try:
                temp_file.unlink()
            except Exception:
                pass

            logger.file_upload(file.filename, file_size)

        else:
            document = text.strip()
            file_size = len(document.encode('utf-8'))

        # 문서 검증
        error = validate_document(document)
        if error:
            logger.warning("문서 검증 실패", error=error)
            raise HTTPException(status_code=400, detail={
                "error_code": "DOCUMENT_VALIDATION_FAILED",
                "message": error,
                "actions": ["텍스트를 줄여보세요", "여러 파일로 나누세요"]
            })

        # DB에 분석 기록
        db.create_analysis(
            analysis_id,
            job_id,
            file_name=file.filename if file else None,
            file_size=file_size,
            input_text=document
        )

        # 큐에 작업 추가
        job_status = queue_manager.add_job(
            job_id,
            document,
            file_name=file.filename if file else None,
            file_size=file_size
        )

        logger.analysis_start(analysis_id, file.filename if file else "text_input")

        # 백그라운드에서 분석 실행
        if job_status == JobStatus.RUNNING:
            background_tasks.add_task(run_analysis, job_id, analysis_id, document)

        return {
            "job_id": job_id,
            "analysis_id": analysis_id,
            "status": job_status.value,
            "queue": queue_manager.get_queue_status()
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error("분석 요청 처리 실패", error=str(e), job_id=job_id)
        raise HTTPException(status_code=500, detail={
            "error_code": "INTERNAL_ERROR",
            "message": "내부 오류가 발생했습니다",
            "actions": ["잠시 후 다시 시도하세요", "관리자에게 문의하세요"]
        })


async def run_analysis(job_id: str, analysis_id: str, document: str):
    """백그라운드에서 분석 실행"""
    try:
        loop = asyncio.get_running_loop()
        event_queues[job_id] = asyncio.Queue()

        orchestrator = Orchestrator(
            client=client,
            output_dir=settings.OUTPUT_DIR,
            on_event=create_event_callback(job_id, loop)
        )

        # 분석 실행 후 context 저장
        context = await asyncio.to_thread(orchestrator.run, document)
        job_contexts[job_id] = context  # 채팅 정제용 컨텍스트 저장
        job_to_analysis[job_id] = analysis_id  # DB 저장용 매핑

        # 출력 파일 찾기
        output_dir = Path(settings.OUTPUT_DIR)
        files = sorted(output_dir.glob("analysis_*.md"), key=lambda p: p.stat().st_mtime, reverse=True)
        if files:
            output_file = files[0].name
            db.update_analysis_success(analysis_id, str(files[0]))
            logger.analysis_complete(analysis_id, 0)
        else:
            raise Exception("출력 파일을 찾을 수 없습니다")

        queue_manager.complete_job(job_id)

    except Exception as e:
        error_msg = f"분석 실패: {str(e)}"
        logger.analysis_error(analysis_id, error_msg)
        db.update_analysis_error(analysis_id, error_msg)
        queue_manager.fail_job(job_id, error_msg)

        # 사용자에게 에러 전송
        if job_id in event_queues:
            await event_queues[job_id].put({
                "type": "error",
                "message": error_msg,
                "actions": ["파일 형식을 확인하세요", "텍스트를 단축하세요", "다시 시도하세요"]
            })


@app.get("/api/stream/{job_id}")
async def stream(job_id: str):
    """SSE 스트림 엔드포인트"""
    if job_id not in event_queues:
        event_queues[job_id] = asyncio.Queue()

    return StreamingResponse(
        stream_events(job_id),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )


@app.get("/api/download/{filename}")
async def download(filename: str):
    """분석 결과 파일 다운로드"""
    file_path = Path(settings.OUTPUT_DIR) / filename

    if not file_path.exists() or ".." in filename:
        raise HTTPException(status_code=404, detail={
            "error_code": "FILE_NOT_FOUND",
            "message": "파일을 찾을 수 없습니다"
        })

    return FileResponse(
        file_path,
        filename=filename,
        media_type="text/markdown; charset=utf-8"
    )


# ============================================================================
# Phase 3: 내보내기 API (HTML, PDF, DOCX, JSON)
# ============================================================================

@app.get("/api/download/{filename}/html")
async def download_html(filename: str):
    """분석 결과를 HTML로 다운로드"""
    md_file_path = Path(settings.OUTPUT_DIR) / filename

    if not md_file_path.exists() or ".." in filename:
        raise HTTPException(status_code=404, detail={
            "error_code": "FILE_NOT_FOUND",
            "message": "파일을 찾을 수 없습니다"
        })

    try:
        # 마크다운 파일 읽기
        with open(md_file_path, "r", encoding="utf-8") as f:
            markdown_content = f.read()

        # HTML로 변환
        html_content = export_to_html(markdown_content)

        # 파일명 생성
        base_name = md_file_path.stem
        html_filename = f"{base_name}.html"

        # 파일 저장
        html_path = md_file_path.parent / html_filename
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(html_content)

        logger.info("HTML 내보내기", filename=html_filename)

        return FileResponse(
            html_path,
            filename=html_filename,
            media_type="text/html; charset=utf-8"
        )

    except Exception as e:
        logger.error("HTML 내보내기 실패", error=str(e))
        raise HTTPException(status_code=500, detail={
            "error_code": "EXPORT_FAILED",
            "message": f"HTML 변환 실패: {str(e)}"
        })


@app.get("/api/download/{filename}/pdf")
async def download_pdf(filename: str):
    """분석 결과를 PDF로 다운로드"""
    md_file_path = Path(settings.OUTPUT_DIR) / filename

    if not md_file_path.exists() or ".." in filename:
        raise HTTPException(status_code=404, detail={
            "error_code": "FILE_NOT_FOUND",
            "message": "파일을 찾을 수 없습니다"
        })

    try:
        # 마크다운 파일 읽기
        with open(md_file_path, "r", encoding="utf-8") as f:
            markdown_content = f.read()

        # 파일명 생성
        base_name = md_file_path.stem
        pdf_filename = f"{base_name}.pdf"
        pdf_path = md_file_path.parent / pdf_filename

        # WeasyPrint 사용 가능하면 PDF 생성, 없으면 프린트용 HTML 반환
        from utils.export_formats import HAS_WEASYPRINT
        if HAS_WEASYPRINT:
            success = export_to_pdf(markdown_content, str(pdf_path))
            if not success:
                raise Exception("PDF 변환에 실패했습니다")
            logger.info("PDF 내보내기", filename=pdf_filename)
            return FileResponse(pdf_path, filename=pdf_filename, media_type="application/pdf")
        else:
            # 브라우저 프린트로 PDF 저장 안내
            html_content = export_to_html(markdown_content)
            print_html = html_content.replace(
                "</head>",
                """<style>
                    @media print { .no-print { display: none !important; } }
                    body { margin: 0; }
                </style>
                <script>
                    window.addEventListener('load', function() {
                        var banner = document.createElement('div');
                        banner.className = 'no-print';
                        banner.style.cssText = 'background:#2563eb;color:white;padding:12px 20px;font-family:sans-serif;font-size:14px;display:flex;align-items:center;justify-content:space-between;';
                        banner.innerHTML = '<span>📄 브라우저 인쇄 기능으로 PDF를 저장하세요 (Ctrl+P / Cmd+P → PDF로 저장)</span><button onclick="window.print()" style="background:white;color:#2563eb;border:none;padding:6px 14px;border-radius:6px;cursor:pointer;font-weight:bold;">🖨 인쇄 / PDF 저장</button>';
                        document.body.insertBefore(banner, document.body.firstChild);
                    });
                </script>
                </head>"""
            )
            logger.info("PDF 폴백: 프린트용 HTML 반환", filename=base_name)
            from fastapi.responses import HTMLResponse
            return HTMLResponse(content=print_html)

    except Exception as e:
        logger.error("PDF 내보내기 실패", error=str(e))
        raise HTTPException(status_code=500, detail={
            "error_code": "EXPORT_FAILED",
            "message": f"PDF 변환 실패: {str(e)}"
        })


@app.get("/api/download/{filename}/docx")
async def download_docx(filename: str):
    """분석 결과를 Word로 다운로드"""
    md_file_path = Path(settings.OUTPUT_DIR) / filename

    if not md_file_path.exists() or ".." in filename:
        raise HTTPException(status_code=404, detail={
            "error_code": "FILE_NOT_FOUND",
            "message": "파일을 찾을 수 없습니다"
        })

    try:
        # 마크다운 파일 읽기
        with open(md_file_path, "r", encoding="utf-8") as f:
            markdown_content = f.read()

        # 파일명 생성
        base_name = md_file_path.stem
        docx_filename = f"{base_name}.docx"
        docx_path = md_file_path.parent / docx_filename

        # Word로 변환
        success = export_to_docx(markdown_content, str(docx_path))

        if not success:
            raise Exception("Word 변환에 실패했습니다")

        logger.info("Word 내보내기", filename=docx_filename)

        return FileResponse(
            docx_path,
            filename=docx_filename,
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )

    except Exception as e:
        logger.error("Word 내보내기 실패", error=str(e))
        raise HTTPException(status_code=500, detail={
            "error_code": "EXPORT_FAILED",
            "message": f"Word 변환 실패: {str(e)}"
        })


@app.get("/api/download/{filename}/json")
async def download_json(filename: str):
    """분석 결과를 JSON으로 다운로드"""
    md_file_path = Path(settings.OUTPUT_DIR) / filename

    if not md_file_path.exists() or ".." in filename:
        raise HTTPException(status_code=404, detail={
            "error_code": "FILE_NOT_FOUND",
            "message": "파일을 찾을 수 없습니다"
        })

    try:
        # 마크다운 파일 읽기
        with open(md_file_path, "r", encoding="utf-8") as f:
            markdown_content = f.read()

        # JSON 데이터 구성
        json_data = {
            "metadata": {
                "filename": filename,
                "generated_at": datetime.now().isoformat(),
                "format": "analysis"
            },
            "content": markdown_content
        }

        # 파일명 생성
        base_name = md_file_path.stem
        json_filename = f"{base_name}.json"
        json_path = md_file_path.parent / json_filename

        # JSON으로 저장
        success = export_to_json(json_data, str(json_path))

        if not success:
            raise Exception("JSON 변환에 실패했습니다")

        logger.info("JSON 내보내기", filename=json_filename)

        return FileResponse(
            json_path,
            filename=json_filename,
            media_type="application/json; charset=utf-8"
        )

    except Exception as e:
        logger.error("JSON 내보내기 실패", error=str(e))
        raise HTTPException(status_code=500, detail={
            "error_code": "EXPORT_FAILED",
            "message": f"JSON 변환 실패: {str(e)}"
        })


@app.get("/api/history")
async def history(limit: int = 50, offset: int = 0):
    """분석 이력 조회"""
    analyses = db.get_analyses(limit=limit, offset=offset)
    return {
        "analyses": analyses,
        "total": len(analyses),
        "statistics": db.get_statistics()
    }


@app.get("/api/queue/status")
async def queue_status():
    """큐 상태 조회"""
    return {
        "status": queue_manager.get_queue_status(),
        "statistics": queue_manager.get_statistics()
    }


@app.post("/api/job/{job_id}/cancel")
async def cancel_job(job_id: str):
    """작업 취소"""
    if queue_manager.cancel_job(job_id):
        logger.info("작업 취소", job_id=job_id)
        return {"status": "cancelled", "job_id": job_id}
    else:
        raise HTTPException(status_code=400, detail={
            "error_code": "CANNOT_CANCEL",
            "message": "이미 실행 중인 작업은 취소할 수 없습니다"
        })


# ============================================================================
# 채팅형 요구사항 정제 API
# ============================================================================

@app.post("/api/chat/{job_id}")
async def chat_refinement(job_id: str, message: str, history: Optional[list] = None):
    """
    분석 결과에 대한 후속 질문 처리.
    기존 분석 컨텍스트를 기반으로 답변 또는 재분석을 제공합니다.
    """
    if job_id not in job_contexts:
        raise HTTPException(status_code=404, detail={
            "error_code": "CONTEXT_NOT_FOUND",
            "message": "분석 결과를 찾을 수 없습니다. 분석을 먼저 완료하세요."
        })

    try:
        from agents.chat_agent import ChatAgent
        chat_agent = ChatAgent(client)
        context = job_contexts[job_id]
        chat_history = history or []

        # ChatAgent 실행
        result = chat_agent.run(context, message, chat_history)

        # 대화 히스토리 누적
        updated_history = chat_history + [
            {"role": "user", "content": message},
            {"role": "assistant", "content": result.get("answer", "")}
        ]

        # DB에 저장 (analysis_id가 있는 경우)
        if job_id in job_to_analysis:
            analysis_id = job_to_analysis[job_id]
            db.save_chat_history(analysis_id, updated_history)

        logger.info("채팅 정제", job_id=job_id, message=message[:100])
        return {
            "type": result.get("type", "answer"),
            "answer": result.get("answer", ""),
            "requires_reanalysis": result.get("requires_reanalysis", False),
            "reanalyzed_impact": result.get("reanalyzed_impact"),  # 재분석된 영향도
            "follow_up_suggestions": result.get("follow_up_suggestions", [])
        }

    except Exception as e:
        logger.error("채팅 정제 실패", job_id=job_id, error=str(e))
        raise HTTPException(status_code=500, detail={
            "error_code": "CHAT_FAILED",
            "message": f"채팅 처리 실패: {str(e)}"
        })


# ============================================================================
# Phase 2: 관리자 대시보드 API
# ============================================================================

@app.get("/admin")
async def admin_dashboard():
    """관리자 대시보드"""
    admin_path = static_path / "admin.html"
    if admin_path.exists():
        return FileResponse(admin_path)
    raise HTTPException(status_code=404, detail="관리자 대시보드를 찾을 수 없습니다")


@app.get("/api/admin/dashboard")
async def admin_dashboard_data():
    """대시보드 데이터"""
    stats = db.get_statistics()
    queue_status = queue_manager.get_queue_status()
    queue_stats = queue_manager.get_statistics()

    # 최근 분석 10개
    recent_analyses = db.get_analyses(limit=10, offset=0)

    return {
        "timestamp": datetime.now().isoformat(),
        "statistics": stats,
        "queue": queue_status,
        "queue_statistics": queue_stats,
        "recent_analyses": recent_analyses,
        "settings": {
            "max_file_size_mb": settings.MAX_FILE_SIZE_MB,
            "max_document_tokens": settings.MAX_DOCUMENT_TOKENS,
            "max_concurrent_analyses": settings.MAX_CONCURRENT_ANALYSES,
            "retention_days": settings.RETENTION_DAYS,
            "llm_model": settings.LLM_MODEL,
        }
    }


@app.get("/api/admin/settings")
async def get_settings():
    """현재 설정 조회"""
    return {
        "llm": {
            "base_url": settings.LLM_BASE_URL,
            "model": settings.LLM_MODEL,
            "mock_mode": settings.MOCK_MODE,
        },
        "analysis": {
            "max_file_size_mb": settings.MAX_FILE_SIZE_MB,
            "max_document_tokens": settings.MAX_DOCUMENT_TOKENS,
            "max_concurrent_analyses": settings.MAX_CONCURRENT_ANALYSES,
            "timeout_minutes": settings.ANALYSIS_TIMEOUT_MINUTES,
        },
        "storage": {
            "retention_days": settings.RETENTION_DAYS,
            "output_dir": settings.OUTPUT_DIR,
        },
        "logging": {
            "level": settings.LOG_LEVEL,
            "format": settings.LOG_FORMAT,
        }
    }


@app.get("/api/admin/logs")
async def get_logs(limit: int = 100, offset: int = 0, level: str = None):
    """로그 조회"""
    log_file = Path(settings.LOG_FILE)

    if not log_file.exists():
        return {"logs": [], "total": 0}

    try:
        with open(log_file, "r") as f:
            lines = f.readlines()

        # 역순으로 정렬 (최근 로그부터)
        lines = list(reversed(lines))

        # 로그 파싱
        logs = []
        for line in lines:
            try:
                if line.strip():
                    log_data = json.loads(line)

                    # 레벨 필터링
                    if level and log_data.get("level") != level.upper():
                        continue

                    logs.append(log_data)
            except json.JSONDecodeError:
                pass

        # 페이지네이션
        total = len(logs)
        logs = logs[offset:offset + limit]

        return {"logs": logs, "total": total, "limit": limit, "offset": offset}

    except Exception as e:
        logger.error("로그 조회 실패", error=str(e))
        return {"logs": [], "total": 0, "error": str(e)}


@app.get("/api/health/detailed")
async def health_detailed():
    """상세 헬스 체크"""
    try:
        # 프로세스 정보
        process = psutil.Process()
        memory_info = process.memory_info()

        # 디스크 정보
        disk_info = psutil.disk_usage("/")

        # LLM 연결 테스트
        llm_status = "healthy"
        try:
            # 간단한 헬스 체크 (실제로는 LLM에 ping 요청)
            if not settings.MOCK_MODE:
                # LLM 서버 연결 테스트는 실제 구현 필요
                pass
        except Exception:
            llm_status = "unhealthy"

        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "services": {
                "database": {
                    "status": "healthy",
                    "path": settings.DATABASE_PATH,
                },
                "llm": {
                    "status": llm_status,
                    "model": settings.LLM_MODEL,
                    "mode": "mock" if settings.MOCK_MODE else "real",
                },
                "storage": {
                    "status": "healthy",
                    "output_dir": settings.OUTPUT_DIR,
                }
            },
            "system": {
                "memory": {
                    "rss_mb": round(memory_info.rss / 1024 / 1024, 2),
                    "vms_mb": round(memory_info.vms / 1024 / 1024, 2),
                },
                "disk": {
                    "total_gb": round(disk_info.total / 1024 / 1024 / 1024, 2),
                    "used_gb": round(disk_info.used / 1024 / 1024 / 1024, 2),
                    "free_gb": round(disk_info.free / 1024 / 1024 / 1024, 2),
                    "percent": disk_info.percent,
                }
            },
            "queue": queue_manager.get_queue_status(),
            "statistics": db.get_statistics(),
        }

    except Exception as e:
        logger.error("헬스 체크 실패", error=str(e))
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now().isoformat(),
        }


# ============================================================================
# Phase 3: 분석 결과 비교
# ============================================================================

@app.get("/api/analyses/{analysis_id1}/compare/{analysis_id2}")
async def compare_analyses_endpoint(analysis_id1: str, analysis_id2: str):
    """두 분석 결과 비교"""
    try:
        # 분석 정보 조회
        analysis1 = db.get_analysis(analysis_id1)
        analysis2 = db.get_analysis(analysis_id2)

        if not analysis1:
            raise HTTPException(status_code=404, detail={
                "error_code": "ANALYSIS_NOT_FOUND",
                "message": f"분석을 찾을 수 없습니다: {analysis_id1}"
            })

        if not analysis2:
            raise HTTPException(status_code=404, detail={
                "error_code": "ANALYSIS_NOT_FOUND",
                "message": f"분석을 찾을 수 없습니다: {analysis_id2}"
            })

        # 마크다운 파일 읽기
        output_file1 = analysis1.get("output_file")
        output_file2 = analysis2.get("output_file")

        markdown1 = ""
        markdown2 = ""

        if output_file1 and Path(output_file1).exists():
            with open(output_file1, "r", encoding="utf-8") as f:
                markdown1 = f.read()

        if output_file2 and Path(output_file2).exists():
            with open(output_file2, "r", encoding="utf-8") as f:
                markdown2 = f.read()

        # 비교 데이터 구성
        analysis1_data = {
            "analysis_id": analysis_id1,
            "output_file": output_file1,
            "created_at": analysis1.get("created_at"),
            "markdown": markdown1
        }

        analysis2_data = {
            "analysis_id": analysis_id2,
            "output_file": output_file2,
            "created_at": analysis2.get("created_at"),
            "markdown": markdown2
        }

        # 비교 수행
        comparison_result = compare_analyses(analysis1_data, analysis2_data)

        logger.info("분석 비교", analysis_id1=analysis_id1, analysis_id2=analysis_id2)

        return comparison_result

    except HTTPException:
        raise
    except Exception as e:
        logger.error("분석 비교 실패", error=str(e))
        raise HTTPException(status_code=500, detail={
            "error_code": "COMPARISON_FAILED",
            "message": f"비교 실패: {str(e)}"
        })


@app.get("/api/analyses/{analysis_id1}/compare/{analysis_id2}/report")
async def generate_comparison_report_endpoint(analysis_id1: str, analysis_id2: str):
    """비교 결과 마크다운 리포트 생성"""
    try:
        # 분석 정보 조회
        analysis1 = db.get_analysis(analysis_id1)
        analysis2 = db.get_analysis(analysis_id2)

        if not analysis1 or not analysis2:
            raise HTTPException(status_code=404, detail={
                "error_code": "ANALYSIS_NOT_FOUND",
                "message": "분석을 찾을 수 없습니다"
            })

        # 마크다운 파일 읽기
        markdown1 = ""
        markdown2 = ""

        output_file1 = analysis1.get("output_file")
        output_file2 = analysis2.get("output_file")

        if output_file1 and Path(output_file1).exists():
            with open(output_file1, "r", encoding="utf-8") as f:
                markdown1 = f.read()

        if output_file2 and Path(output_file2).exists():
            with open(output_file2, "r", encoding="utf-8") as f:
                markdown2 = f.read()

        # 비교 데이터 구성
        analysis1_data = {
            "analysis_id": analysis_id1,
            "output_file": output_file1,
            "markdown": markdown1
        }

        analysis2_data = {
            "analysis_id": analysis_id2,
            "output_file": output_file2,
            "markdown": markdown2
        }

        # 비교 수행
        comparison_result = compare_analyses(analysis1_data, analysis2_data)

        # 리포트 생성
        report = generate_comparison_report(comparison_result)

        logger.info("비교 리포트 생성", analysis_id1=analysis_id1, analysis_id2=analysis_id2)

        return {
            "report": report,
            "comparison": comparison_result
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error("비교 리포트 생성 실패", error=str(e))
        raise HTTPException(status_code=500, detail={
            "error_code": "REPORT_GENERATION_FAILED",
            "message": f"리포트 생성 실패: {str(e)}"
        })


# ============================================================================
# Phase 6: 프로젝트 관리 & 소스 비교 엔드포인트
# ============================================================================

@app.post("/api/projects/upload")
async def upload_project(
    file: UploadFile = File(...),
    name: str = Form(default=""),
    description: str = Form(default=""),
    background_tasks: BackgroundTasks = BackgroundTasks()
):
    """프로젝트 ZIP 업로드"""
    try:
        # 파일 검증
        file_size = len(await file.read())
        await file.seek(0)

        if file_size > settings.MAX_PROJECT_SIZE_MB * 1024 * 1024:
            raise HTTPException(status_code=400, detail={
                "error_code": "PROJECT_TOO_LARGE",
                "message": f"프로젝트가 너무 큽니다. 최대 {settings.MAX_PROJECT_SIZE_MB}MB까지 가능합니다.",
                "size_mb": round(file_size / 1024 / 1024, 2),
                "max_size_mb": settings.MAX_PROJECT_SIZE_MB
            })

        if not file.filename.endswith('.zip'):
            raise HTTPException(status_code=400, detail={
                "error_code": "INVALID_FILE_FORMAT",
                "message": "ZIP 파일만 업로드 가능합니다.",
                "file": file.filename
            })

        # 프로젝트 저장
        project_id = str(uuid.uuid4())
        project_name = name or Path(file.filename).stem
        project_dir = Path(settings.PROJECT_DIR)
        project_dir.mkdir(exist_ok=True)

        # ZIP 저장
        zip_path = project_dir / f"{project_id}.zip"
        content = await file.read()
        with open(zip_path, "wb") as f:
            f.write(content)

        # 소스 파싱 (백그라운드)
        snapshot_path = project_dir / f"{project_id}_snapshot.json"
        background_tasks.add_task(
            parse_project_in_background,
            str(zip_path),
            str(snapshot_path),
            project_id,
            project_name
        )

        # DB 저장
        db.create_project(
            project_id=project_id,
            name=project_name,
            zip_file_path=str(zip_path),
            snapshot_path=str(snapshot_path),
            total_files=0,  # 나중에 업데이트됨
            total_size=file_size,
            description=description
        )

        logger.info("프로젝트 업로드", project_id=project_id, project_name=project_name)

        return {
            "project_id": project_id,
            "name": project_name,
            "status": "parsing",
            "message": "프로젝트 파싱 중입니다..."
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error("프로젝트 업로드 실패", error=str(e))
        raise HTTPException(status_code=500, detail={
            "error_code": "PROJECT_UPLOAD_FAILED",
            "message": f"프로젝트 업로드 실패: {str(e)}"
        })


@app.get("/api/projects")
async def get_projects(limit: int = 50, offset: int = 0):
    """등록된 프로젝트 목록 조회"""
    try:
        projects = db.get_projects(limit=limit, offset=offset)
        return {
            "projects": projects,
            "total": len(projects),
            "limit": limit,
            "offset": offset
        }
    except Exception as e:
        logger.error("프로젝트 목록 조회 실패", error=str(e))
        raise HTTPException(status_code=500, detail={
            "error_code": "GET_PROJECTS_FAILED",
            "message": str(e)
        })


@app.get("/api/projects/{project_id}")
async def get_project(project_id: str):
    """프로젝트 상세 조회"""
    try:
        project = db.get_project(project_id)
        if not project:
            raise HTTPException(status_code=404, detail={
                "error_code": "PROJECT_NOT_FOUND",
                "message": f"프로젝트를 찾을 수 없습니다: {project_id}"
            })

        # 스냅샷 로드
        snapshot_data = {}
        if project.get("snapshot_path"):
            try:
                with open(project["snapshot_path"]) as f:
                    snapshot_data = json.load(f)
            except Exception:
                pass

        return {
            "project": project,
            "snapshot": snapshot_data
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error("프로젝트 조회 실패", project_id=project_id, error=str(e))
        raise HTTPException(status_code=500, detail={
            "error_code": "GET_PROJECT_FAILED",
            "message": str(e)
        })


@app.post("/api/compare")
async def start_comparison(
    project_id: str = Form(...),
    analysis_id: str = Form(...),
    background_tasks: BackgroundTasks = BackgroundTasks()
):
    """소스 코드와 분석 결과 비교 시작"""
    try:
        # 프로젝트 확인
        project = db.get_project(project_id)
        if not project:
            raise HTTPException(status_code=404, detail={
                "error_code": "PROJECT_NOT_FOUND",
                "message": f"프로젝트를 찾을 수 없습니다"
            })

        # 분석 확인
        analysis = db.get_analysis(analysis_id)
        if not analysis:
            raise HTTPException(status_code=404, detail={
                "error_code": "ANALYSIS_NOT_FOUND",
                "message": f"분석을 찾을 수 없습니다"
            })

        # 비교 ID 생성
        comparison_id = f"comparison_{uuid.uuid4().hex[:12]}"

        # DB 저장
        db.create_comparison(comparison_id, project_id, analysis_id)

        # 백그라운드에서 비교 실행
        background_tasks.add_task(
            run_comparison_in_background,
            comparison_id,
            project_id,
            analysis_id,
            project["snapshot_path"],
            analysis_id
        )

        logger.info("소스 비교 시작", comparison_id=comparison_id, project_id=project_id, analysis_id=analysis_id)

        return {
            "comparison_id": comparison_id,
            "status": "running",
            "message": "비교 분석 중입니다..."
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error("비교 시작 실패", error=str(e))
        raise HTTPException(status_code=500, detail={
            "error_code": "COMPARISON_FAILED",
            "message": str(e)
        })


@app.get("/api/compare/{comparison_id}")
async def get_comparison(comparison_id: str):
    """비교 결과 조회"""
    try:
        comparison = db.get_comparison(comparison_id)
        if not comparison:
            raise HTTPException(status_code=404, detail={
                "error_code": "COMPARISON_NOT_FOUND",
                "message": "비교 결과를 찾을 수 없습니다"
            })

        result = {
            "comparison_id": comparison_id,
            "status": comparison["status"],
            "created_at": comparison["created_at"]
        }

        # 결과 로드
        if comparison["status"] == "completed" and comparison.get("result_path"):
            try:
                with open(comparison["result_path"]) as f:
                    result["guide"] = json.load(f)
            except Exception:
                pass

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error("비교 결과 조회 실패", comparison_id=comparison_id, error=str(e))
        raise HTTPException(status_code=500, detail={
            "error_code": "GET_COMPARISON_FAILED",
            "message": str(e)
        })


# ============================================================================
# 백그라운드 작업 함수
# ============================================================================

def parse_project_in_background(zip_path: str, snapshot_path: str, project_id: str, project_name: str) -> None:
    """프로젝트 파싱 (백그라운드)"""
    try:
        snapshot = ProjectExtractor.extract_from_zip(zip_path, project_id, project_name)
        if snapshot:
            # JSON 저장
            with open(snapshot_path, "w", encoding="utf-8") as f:
                f.write(ProjectExtractor.snapshot_to_json(snapshot))

            # DB 업데이트
            with __import__("sqlite3").connect(settings.DATABASE_PATH) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE projects
                    SET total_files = ?, snapshot_path = ?
                    WHERE id = ?
                """, (snapshot.total_files, snapshot_path, project_id))
                conn.commit()

            logger.info("프로젝트 파싱 완료", project_id=project_id, total_files=snapshot.total_files)
        else:
            logger.error("프로젝트 파싱 실패", project_id=project_id)

    except Exception as e:
        logger.error("프로젝트 파싱 오류", project_id=project_id, error=str(e))


def run_comparison_in_background(
    comparison_id: str,
    project_id: str,
    analysis_id: str,
    snapshot_path: str,
    analysis_id_: str
) -> None:
    """소스 비교 실행 (백그라운드)"""
    try:
        import sqlite3

        # 컨텍스트 로드
        if analysis_id_ not in job_contexts:
            logger.warning("컨텍스트 없음", analysis_id=analysis_id_)
            return

        context = job_contexts[analysis_id_]

        # 스냅샷 로드
        with open(snapshot_path) as f:
            snapshot_data = json.load(f)

        # 간단한 스냅샷 객체 생성
        from utils.project_extractor import ProjectSnapshot, SourceFile
        files = [
            SourceFile(
                path=f["path"],
                relative_path=f["relative_path"],
                size=f["size"],
                language=f["language"],
                methods=f.get("methods", [])
            )
            for f in snapshot_data.get("files", [])
        ]
        snapshot = ProjectSnapshot(
            project_id=snapshot_data["project_id"],
            name=snapshot_data["name"],
            files=files,
            file_tree=snapshot_data.get("file_tree", {}),
            total_files=snapshot_data["total_files"],
            total_size=snapshot_data["total_size"],
            supported_files=snapshot_data["supported_files"]
        )

        # 비교 실행
        comparator = SourceComparatorAgent(client)
        result_context = comparator.run(context, snapshot)
        comparison_result = result_context.get("source_comparator", {})

        # 결과 저장
        result_path = Path(settings.OUTPUT_DIR) / f"comparison_{comparison_id}.json"
        result_path.parent.mkdir(exist_ok=True)
        with open(result_path, "w", encoding="utf-8") as f:
            json.dump(comparison_result, f, ensure_ascii=False, indent=2)

        # DB 업데이트
        db.update_comparison_result(comparison_id, "completed", str(result_path))

        logger.info("소스 비교 완료", comparison_id=comparison_id)

    except Exception as e:
        logger.error("소스 비교 오류", comparison_id=comparison_id, error=str(e))
        db.update_comparison_result(comparison_id, "failed")


# ============================================================================
# 애플리케이션 시작
# ============================================================================

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        app,
        host=settings.HOST,
        port=settings.PORT,
        log_level=settings.LOG_LEVEL.lower()
    )
