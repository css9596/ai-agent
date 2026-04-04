"""분석 작업 큐 관리"""

from dataclasses import dataclass
from typing import Dict, List, Optional
from datetime import datetime
from enum import Enum
from config import settings


class JobStatus(str, Enum):
    """작업 상태"""
    PENDING = "pending"  # 대기 중
    RUNNING = "running"  # 실행 중
    COMPLETED = "completed"  # 완료
    FAILED = "failed"  # 실패
    CANCELLED = "cancelled"  # 취소


@dataclass
class AnalysisJob:
    """분석 작업"""
    job_id: str
    document: str
    file_name: Optional[str] = None
    file_size: Optional[int] = None
    status: JobStatus = JobStatus.PENDING
    created_at: datetime = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error: Optional[str] = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()

    @property
    def duration_seconds(self) -> Optional[float]:
        """작업 소요 시간"""
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return None


class AnalysisQueueManager:
    """분석 작업 큐 관리"""

    def __init__(self, max_concurrent: int = settings.MAX_CONCURRENT_ANALYSES):
        self.max_concurrent = max_concurrent
        self.running_jobs: Dict[str, AnalysisJob] = {}  # 실행 중인 작업
        self.pending_queue: List[str] = []  # 대기 중인 작업 ID 목록
        self.completed_jobs: Dict[str, AnalysisJob] = {}  # 완료된 작업
        self.job_details: Dict[str, AnalysisJob] = {}  # 모든 작업 정보

    def add_job(
        self,
        job_id: str,
        document: str,
        file_name: Optional[str] = None,
        file_size: Optional[int] = None
    ) -> JobStatus:
        """작업 추가"""
        job = AnalysisJob(
            job_id=job_id,
            document=document,
            file_name=file_name,
            file_size=file_size
        )
        self.job_details[job_id] = job

        # 동시 실행 중인 작업이 최대치 이하면 바로 실행
        if len(self.running_jobs) < self.max_concurrent:
            self.start_job(job_id)
            return JobStatus.RUNNING
        else:
            # 아니면 큐에 추가
            self.pending_queue.append(job_id)
            return JobStatus.PENDING

    def start_job(self, job_id: str):
        """작업 시작"""
        if job_id in self.pending_queue:
            self.pending_queue.remove(job_id)

        job = self.job_details[job_id]
        job.status = JobStatus.RUNNING
        job.started_at = datetime.now()
        self.running_jobs[job_id] = job

    def complete_job(self, job_id: str):
        """작업 완료"""
        if job_id in self.running_jobs:
            job = self.running_jobs.pop(job_id)
            job.status = JobStatus.COMPLETED
            job.completed_at = datetime.now()
            self.completed_jobs[job_id] = job
            self.job_details[job_id] = job

            # 대기 중인 작업이 있으면 시작
            if self.pending_queue:
                next_job_id = self.pending_queue[0]
                self.start_job(next_job_id)

    def fail_job(self, job_id: str, error: str):
        """작업 실패"""
        if job_id in self.running_jobs:
            job = self.running_jobs.pop(job_id)
            job.status = JobStatus.FAILED
            job.error = error
            job.completed_at = datetime.now()
            self.job_details[job_id] = job

            # 대기 중인 작업이 있으면 시작
            if self.pending_queue:
                next_job_id = self.pending_queue[0]
                self.start_job(next_job_id)

    def cancel_job(self, job_id: str) -> bool:
        """작업 취소"""
        if job_id in self.pending_queue:
            self.pending_queue.remove(job_id)
            job = self.job_details[job_id]
            job.status = JobStatus.CANCELLED
            return True

        # 실행 중인 작업은 취소 불가 (진행 중이므로)
        if job_id in self.running_jobs:
            return False

        return False

    def get_job_status(self, job_id: str) -> Optional[JobStatus]:
        """작업 상태 조회"""
        if job_id in self.job_details:
            return self.job_details[job_id].status
        return None

    def get_job_details(self, job_id: str) -> Optional[AnalysisJob]:
        """작업 상세 정보 조회"""
        return self.job_details.get(job_id)

    def get_queue_status(self) -> Dict[str, any]:
        """큐 상태 조회"""
        return {
            "running": len(self.running_jobs),
            "pending": len(self.pending_queue),
            "max_concurrent": self.max_concurrent,
            "can_start_new": len(self.running_jobs) < self.max_concurrent,
            "pending_jobs": [
                {
                    "job_id": job_id,
                    "file_name": self.job_details[job_id].file_name,
                    "position": self.pending_queue.index(job_id) + 1
                }
                for job_id in self.pending_queue
            ]
        }

    def get_statistics(self) -> Dict[str, any]:
        """통계 조회"""
        total_jobs = len(self.job_details)
        completed = len(self.completed_jobs)
        failed = sum(1 for job in self.job_details.values() if job.status == JobStatus.FAILED)
        running = len(self.running_jobs)
        pending = len(self.pending_queue)

        return {
            "total": total_jobs,
            "completed": completed,
            "failed": failed,
            "running": running,
            "pending": pending,
            "success_rate": round((completed / total_jobs * 100) if total_jobs > 0 else 0, 2),
            "queue": self.get_queue_status()
        }


# 전역 큐 매니저 인스턴스
queue_manager = AnalysisQueueManager()
