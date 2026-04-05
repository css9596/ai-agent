#!/usr/bin/env python3
"""
AI 개발 분석서 생성 - Windows exe 실행 스크립트

이 스크립트는 exe로 변환되어 Windows에서 다음을 수행합니다:
1. Docker 설치 확인
2. docker-compose up -d 실행
3. 서버 시작 대기 (10-20초)
4. 웹 브라우저 자동 오픈
5. 실시간 로그 표시
"""

import os
import sys
import subprocess
import time
import webbrowser
from pathlib import Path

# Windows UTF-8 콘솔 활성화
if sys.platform == "win32":
    os.system("chcp 65001 > nul")

# 색상 정의 (Windows 10+ ANSI 지원)
class Colors:
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BOLD = '\033[1m'
    END = '\033[0m'

def print_header():
    """헤더 출력"""
    print(f"\n{Colors.BOLD}{Colors.BLUE}")
    print("╔" + "═" * 70 + "╗")
    print("║" + " " * 70 + "║")
    print("║" + "  AI 개발 분석서 생성 - 오프라인 환경".center(70) + "║")
    print("║" + " " * 70 + "║")
    print("╚" + "═" * 70 + "╝")
    print(f"{Colors.END}\n")

def print_step(step, total, msg):
    """진행 단계 출력"""
    print(f"{Colors.BLUE}[{step}/{total}] {msg}{Colors.END}")

def print_success(msg):
    """성공 메시지"""
    print(f"{Colors.GREEN}[OK] {msg}{Colors.END}")

def print_error(msg):
    """오류 메시지"""
    print(f"{Colors.RED}[ERROR] {msg}{Colors.END}")

def print_warning(msg):
    """경고 메시지"""
    print(f"{Colors.YELLOW}[WARN] {msg}{Colors.END}")

def check_docker():
    """Docker 설치 확인"""
    try:
        result = subprocess.run(
            ["docker", "--version"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            version = result.stdout.strip()
            print_success(f"Docker 설치 확인: {version}")
            return True
    except FileNotFoundError:
        # Docker가 설치되지 않음
        print_error("Docker Desktop이 설치되지 않았습니다.")
        print(f"\n{Colors.YELLOW}설치 방법:{Colors.END}")
        print("\n1) Docker Desktop 다운로드 (무료):")
        print("   https://www.docker.com/products/docker-desktop")
        print("\n2) 설치 파일 실행:")
        print("   - 다운로드 완료 후 설치 파일 더블클릭")
        print("   - 설치 마법사 따라가기 (기본 설정으로 OK)")
        print("   - 설치 완료 후 컴퓨터 재시작 (권장)")
        print("\n3) Docker Desktop 시작:")
        print("   - 설치 후 시작 메뉴에서 'Docker Desktop' 검색")
        print("   - Docker Desktop 아이콘이 초록색으로 변할 때까지 대기 (약 30초)")
        print("   - 시스템 트레이(화면 우측 아래)에 Docker 아이콘 표시 확인")
        print("\n4) 이 프로그램 다시 실행")
        return False
    except subprocess.TimeoutExpired:
        # Docker가 설치되어 있지만 응답 없음 (실행 중이 아닐 가능성)
        print_error("Docker Desktop이 응답하지 않습니다 (실행 중이 아닐 수 있음).")
        print(f"\n{Colors.YELLOW}해결 방법:{Colors.END}")
        print("\n1) Docker Desktop 시작:")
        print("   - 시스템 트레이(화면 우측 아래)에서 Docker 아이콘 찾기")
        print("   - 없으면 시작 메뉴에서 'Docker Desktop' 검색해 실행")
        print("   - Docker 아이콘이 초록색으로 변할 때까지 대기 (약 30초)")
        print("\n2) 이 프로그램 다시 실행")
        print("\n[팁] Docker Desktop을 항상 실행해두면 다음부터 더 빠릅니다.")
        return False

    print_error("Docker Desktop과 통신할 수 없습니다.")
    print(f"\n{Colors.YELLOW}해결 방법:{Colors.END}")
    print("1. Docker Desktop이 시작되었는지 확인")
    print("2. Windows: 시스템 트레이에서 Docker 아이콘 확인 (초록색)")
    print("3. 이 프로그램 다시 실행")
    return False

def check_docker_compose():
    """Docker Compose 설치 확인"""
    try:
        result = subprocess.run(
            ["docker-compose", "--version"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            version = result.stdout.strip()
            print_success(f"Docker Compose 확인: {version}")
            return True
    except FileNotFoundError:
        pass

    print_warning("docker-compose 명령어를 찾을 수 없습니다.")
    print("Docker Desktop 4.0 이상을 설치하면 자동으로 포함됩니다.")
    return False

def get_app_directory():
    """앱 실행 디렉토리 결정"""
    # exe로 변환되면 임시 폴더에 압축이 해제되므로
    # 현재 스크립트의 부모 디렉토리가 multi-agent 폴더가 됨
    if getattr(sys, 'frozen', False):
        # exe 버전
        app_dir = Path(sys.executable).parent
    else:
        # 일반 Python 실행 시
        app_dir = Path(__file__).parent.parent

    return app_dir

def check_docker_compose_file():
    """docker-compose.yml 파일 확인"""
    app_dir = get_app_directory()
    compose_file = app_dir / "docker-compose.yml"

    if not compose_file.exists():
        print_error(f"docker-compose.yml을 찾을 수 없습니다: {compose_file}")
        return False

    print_success(f"docker-compose.yml 확인: {compose_file}")
    return True

def stop_existing_containers():
    """기존 실행 중인 컨테이너 종료"""
    try:
        subprocess.run(
            ["docker-compose", "down"],
            cwd=get_app_directory(),
            capture_output=True,
            timeout=30
        )
        time.sleep(2)
    except Exception as e:
        print_warning(f"기존 컨테이너 종료 중 오류: {e}")

def start_docker_compose():
    """Docker Compose 시작 (이미지 빌드 포함)"""
    app_dir = get_app_directory()

    try:
        print("  Docker Compose 시작 중...")
        print(f"  (첫 실행: 이미지 빌드 + Ollama 다운로드로 10-30분 소요)")

        # --build 옵션으로 이미지 빌드 (첫 실행 시 필수)
        result = subprocess.run(
            ["docker-compose", "up", "-d", "--build"],
            cwd=app_dir,
            capture_output=True,
            text=True,
            timeout=1800  # 첫 실행: 이미지 빌드(5-10분) + Ollama 다운로드(10-20분) = 30분
        )

        if result.returncode == 0:
            print_success("Docker Compose 시작 완료")
            return True
        else:
            print_error(f"Docker Compose 시작 실패:\n{result.stderr}")
            return False
    except subprocess.TimeoutExpired:
        print_error("Docker Compose 시작 타임아웃 (30분 초과)")
        print_warning("백그라운드에서 계속 실행 중일 수 있습니다")
        print("확인: docker-compose logs -f")
        return False
    except Exception as e:
        print_error(f"Docker Compose 시작 오류: {e}")
        return False

def wait_for_server(max_attempts=600):
    """서버 시작 대기 (최대 10분)"""
    import socket

    print("  서버 시작 대기 중...", end="", flush=True)

    for attempt in range(max_attempts):
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            result = sock.connect_ex(('localhost', 8000))
            sock.close()

            if result == 0:
                # 추가 딜레이 (Ollama 헬스 체크 완료 대기)
                time.sleep(2)
                print(f" {Colors.GREEN}완료!{Colors.END}")
                return True
        except:
            pass

        print(".", end="", flush=True)
        time.sleep(1)

    print(f" {Colors.YELLOW}타임아웃{Colors.END}")
    return False

def open_browser():
    """웹 브라우저 오픈"""
    url = "http://localhost:8000"

    try:
        print("  웹 브라우저 오픈 중...")
        webbrowser.open(url)
        time.sleep(1)
        print_success(f"브라우저 오픈: {url}")
        return True
    except Exception as e:
        print_warning(f"브라우저 자동 오픈 실패: {e}")
        print(f"  수동으로 접속: {url}")
        return False

def show_logs():
    """로그 실시간 표시"""
    app_dir = get_app_directory()

    print(f"\n{Colors.BOLD}{Colors.BLUE}실시간 로그:{Colors.END}")
    print("-" * 70)

    try:
        subprocess.run(
            ["docker-compose", "logs", "-f", "app"],
            cwd=app_dir,
            timeout=None
        )
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}로그 보기 종료{Colors.END}")
    except Exception as e:
        print_error(f"로그 표시 오류: {e}")

def main():
    """메인 함수"""
    print_header()

    # 1단계: Docker 확인
    print_step(1, 5, "Docker 설치 확인...")
    if not check_docker():
        print("\n" + "=" * 70)
        input("엔터를 누르면 종료합니다...")
        sys.exit(1)

    # 2단계: docker-compose 확인
    print_step(2, 5, "Docker Compose 확인...")
    if not check_docker_compose():
        print_warning("계속 진행합니다...")

    # 3단계: docker-compose.yml 확인
    print_step(3, 5, "구성 파일 확인...")
    if not check_docker_compose_file():
        print_error("구성 파일이 없습니다. 올바른 위치에서 실행해주세요.")
        input("엔터를 누르면 종료합니다...")
        sys.exit(1)

    # 4단계: Docker Compose 시작
    print_step(4, 5, "서비스 시작...")

    try:
        stop_existing_containers()
        print("  기존 컨테이너 정리 완료")
    except Exception as e:
        print_warning(f"기존 컨테이너 정리 중 오류: {e}")

    if not start_docker_compose():
        print_error("서비스 시작 실패")
        input("엔터를 누르면 종료합니다...")
        sys.exit(1)

    # 서버 대기
    if not wait_for_server():
        print_warning("서버 응답 확인 실패. 브라우저를 수동으로 열어주세요.")

    # 브라우저 오픈
    open_browser()

    # 5단계: 로그 표시
    print_step(5, 5, "실시간 로그 모니터링...")
    print(f"\n{Colors.YELLOW}Ctrl+C를 눌러 로그 보기를 종료할 수 있습니다.{Colors.END}")
    print(f"{Colors.YELLOW}(서비스는 백그라운드에서 계속 실행됩니다){Colors.END}\n")

    show_logs()

    print(f"\n{Colors.GREEN}프로그램을 종료합니다.{Colors.END}")
    print("서비스는 백그라운드에서 실행 중입니다.")
    print("종료하려면 다시 이 프로그램을 실행하고 중지를 선택하세요.\n")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}사용자가 중단했습니다.{Colors.END}")
        sys.exit(0)
    except Exception as e:
        print_error(f"예상치 못한 오류: {e}")
        import traceback
        traceback.print_exc()
        input("엔터를 누르면 종료합니다...")
        sys.exit(1)
