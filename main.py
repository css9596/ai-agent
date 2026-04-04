import argparse
from pathlib import Path

from dotenv import load_dotenv

from orchestrator import Orchestrator
from utils.claude_client import ClaudeClient


def read_input_document(user_input: str) -> str:
    possible_file = Path(user_input.strip())
    if possible_file.exists() and possible_file.is_file():
        return possible_file.read_text(encoding="utf-8")
    return user_input


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="멀티 에이전트 개발 분석 CLI")
    parser.add_argument("--input", type=str, default="", help="요청 문서 텍스트 또는 파일 경로")
    parser.add_argument("--mock", action="store_true", help="Claude API 대신 모의 응답 사용")
    return parser


def main() -> None:
    load_dotenv()
    parser = build_parser()
    args = parser.parse_args()

    if args.input:
        raw_input = args.input
    else:
        raw_input = input("요청 문서 텍스트 또는 파일 경로를 입력하세요: ").strip()
    if not raw_input:
        raise ValueError("입력이 비어 있습니다.")

    document = read_input_document(raw_input)

    import os

    api_key = os.getenv("ANTHROPIC_API_KEY")
    client = ClaudeClient(api_key=api_key, mock=args.mock)
    orchestrator = Orchestrator(client=client, output_dir="output")
    context = orchestrator.run(document)

    print("\n=== Orchestrator 선택 결과(JSON) ===")
    print(Orchestrator.pretty_selection(context))
    print("\n=== 최종 Markdown 출력 파일 ===")
    print(context["output_file"])
    print("\n=== 미리보기 ===")
    print(context.get("documenter", {}).get("markdown", "")[:1200])


if __name__ == "__main__":
    main()
