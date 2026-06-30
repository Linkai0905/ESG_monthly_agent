from __future__ import annotations

import argparse
import os
import sys
from datetime import date
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from esg_monthly_agent.graph import run_graph


def previous_month_label(today: date | None = None) -> str:
    """Return the previous complete calendar month as YYYY-MM."""
    today = today or date.today()
    year = today.year
    month = today.month - 1
    if month == 0:
        year -= 1
        month = 12
    return f"{year:04d}-{month:02d}"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate an evidence-driven ESG monthly report.")
    parser.add_argument("--company", default="中国神华")
    parser.add_argument("--period", default=previous_month_label())
    parser.add_argument("--tickers", nargs="*", default=["601088.SH", "01088.HK"])
    parser.add_argument("--peers", nargs="*", default=["中煤能源", "陕西煤业", "兖矿能源", "华能国际", "华电国际"])
    parser.add_argument("--language", default="zh-CN")
    parser.add_argument("--output-format", default="markdown", choices=["markdown"])
    parser.add_argument(
        "--research-mode",
        default=None,
        choices=["local_vector", "hosted_web", "deep_research", "hybrid"],
        help="Research path. hosted_web/deep_research use hosted DeepSearch providers, not fetch_pages.",
    )
    parser.add_argument(
        "--research-provider",
        default=None,
        choices=[
            "openai_web_search",
            "openai_deep_research",
            "anthropic_web_search",
            "qwen_dashscope_search",
            "zhipu_web_search",
            "zhipu_glm_web_search",
            "tavily_official_search",
            "local_vector",
        ],
        help="Default DeepSearch provider.",
    )
    parser.add_argument("--max-research-rounds", type=int, default=None)
    parser.add_argument("--max-search-calls", type=int, default=None)
    parser.add_argument(
        "--call-all-available-providers",
        action="store_true",
        help="Run the first DeepSearch round against every configured hosted provider.",
    )
    parser.add_argument("--use-llm", action="store_true", help="Call an OpenAI-compatible LLM to review the generated report.")
    parser.add_argument("--llm-provider", default=None, help="Provider label, for example deepseek or qwen.")
    parser.add_argument("--llm-model", default=None, help="Model name, for example deepseek-v4-pro.")
    parser.add_argument("--llm-base-url", default=None, help="OpenAI-compatible base URL.")
    parser.add_argument("--use-qwen", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--qwen-model", default=None, help=argparse.SUPPRESS)
    parser.add_argument("--qwen-base-url", default=None, help=argparse.SUPPRESS)
    return parser


def main() -> None:
    args = build_parser().parse_args()
    input_state = {
        "company": {"name": args.company},
        "ticker": args.tickers,
        "period": args.period,
        "peers": args.peers,
        "language": args.language,
        "report_type": "monthly",
        "use_llm": args.use_llm or args.use_qwen,
        "use_qwen": args.use_qwen,
    }
    if args.research_mode:
        input_state["research_mode"] = args.research_mode
        input_state["source_mode"] = args.research_mode
    if args.research_provider:
        input_state["default_research_provider"] = args.research_provider
    if args.max_research_rounds:
        input_state["max_research_rounds"] = args.max_research_rounds
    if args.max_search_calls:
        input_state["max_search_calls_per_task"] = args.max_search_calls
    if args.call_all_available_providers:
        input_state["call_all_available_providers"] = True
    if args.llm_provider:
        input_state["llm_provider"] = args.llm_provider
    elif args.use_qwen:
        input_state["llm_provider"] = "qwen"
    if args.llm_model or args.qwen_model:
        input_state["llm_model"] = args.llm_model or args.qwen_model
    if args.llm_base_url or args.qwen_base_url:
        input_state["llm_base_url"] = args.llm_base_url or args.qwen_base_url

    preflight_error = validate_research_provider_config(input_state)
    if preflight_error:
        raise SystemExit(preflight_error)

    final_state = run_graph(input_state)
    report_path = final_state.get("export_paths", {}).get("report_markdown")
    llm_review = final_state.get("llm_review") or {}
    print(f"Run ID: {final_state.get('run_id')}")
    print(f"Report: {report_path}")
    print(f"Quality passed: {final_state.get('quality_checks', {}).get('passed')}")
    if llm_review:
        print(
            "LLM review: "
            f"{llm_review.get('status')} "
            f"({llm_review.get('provider') or 'provider not set'} / "
            f"{llm_review.get('model') or 'model not set'})"
        )


def validate_research_provider_config(input_state: dict) -> str | None:
    mode = input_state.get("research_mode")
    provider = input_state.get("default_research_provider")
    if mode not in {"hosted_web", "deep_research", "hybrid"}:
        return None
    if provider == "openai_web_search" and not os.getenv("OPENAI_API_KEY"):
        return (
            "Hosted DeepSearch requires OPENAI_API_KEY for provider=openai_web_search. "
            "Set OPENAI_API_KEY, switch to --research-provider anthropic_web_search with ANTHROPIC_API_KEY, "
            "or run --research-mode local_vector for the local/manual-source draft."
        )
    if provider == "openai_deep_research" and not os.getenv("OPENAI_API_KEY"):
        return "OpenAI deep research requires OPENAI_API_KEY."
    if provider == "anthropic_web_search" and not os.getenv("ANTHROPIC_API_KEY"):
        return "Anthropic hosted web search requires ANTHROPIC_API_KEY."
    if provider == "qwen_dashscope_search" and not (
        os.getenv("DASHSCOPE_API_KEY") or os.getenv("QWEN_DASHSCOPE_API_KEY")
    ):
        return "Qwen DashScope hosted search requires DASHSCOPE_API_KEY or QWEN_DASHSCOPE_API_KEY."
    if provider in {"zhipu_web_search", "zhipu_glm_web_search"} and not (
        os.getenv("ZHIPU_API_KEY") or os.getenv("BIGMODEL_API_KEY")
    ):
        return "Zhipu web search requires ZHIPU_API_KEY or BIGMODEL_API_KEY."
    if provider == "tavily_official_search" and not os.getenv("TAVILY_API_KEY"):
        return "Tavily official search requires TAVILY_API_KEY."
    if provider == "local_vector" and mode in {"hosted_web", "deep_research"}:
        return "local_vector is not a hosted realtime web provider. Use --research-mode local_vector instead."
    return None


if __name__ == "__main__":
    main()
