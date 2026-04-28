"""
模块作用：
- 定义 stock-agent 命令行入口，负责读取参数、拉取数据、执行分析并写出报告。
- 提供可选开关控制是否把 LangGraph 的 node_trace 写入 Markdown 和 JSON 结果。
联动关系：
- 串联 data.AkShareChinaStockProvider、llm 客户端、pipeline.AnalysisPipeline 和 reports.ReportWriter。
运行示例：
- stock-agent analyze --symbol 600519 --days 30 --mock-llm
- stock-agent analyze --symbol 600519 --days 30 --mock-llm --include-node-trace
"""

from __future__ import annotations

from datetime import date
from pathlib import Path

import typer
from dotenv import load_dotenv
from rich.console import Console

from stock_agent_lab.data import AkShareChinaStockProvider, DataProviderError
from stock_agent_lab.llm import MockLLMClient, OpenAICompatibleClient
from stock_agent_lab.pipeline import AnalysisPipeline
from stock_agent_lab.reports import ReportWriter

app = typer.Typer(help="Multi-agent A-share stock analysis lab.")
console = Console()


@app.callback()
def main() -> None:
    """Multi-agent A-share stock analysis lab."""


@app.command()
def analyze(
    symbol: str = typer.Option(..., "--symbol", "-s", help="6-digit A-share stock code, e.g. 600519."),
    days: int = typer.Option(90, "--days", "-d", min=1, help="Number of recent trading days to analyze."),
    output_dir: Path = typer.Option(None, "--output-dir", "-o", help="Directory for report.md and result.json."),
    mock_llm: bool = typer.Option(False, "--mock-llm", help="Use a deterministic local mock LLM."),
    include_node_trace: bool = typer.Option(
        False,
        "--include-node-trace",
        help="Include LangGraph node_trace in Markdown and JSON outputs.",
    ),
) -> None:
    load_dotenv()
    if not symbol.isdigit() or len(symbol) != 6:
        typer.echo("Error: symbol must be a 6-digit A-share code, for example 600519.")
        raise typer.Exit(code=1)

    console.print(f"[bold]Fetching A-share data for {symbol}...[/bold]")
    provider = AkShareChinaStockProvider()
    try:
        dataset = provider.fetch(symbol=symbol, days=days)
        llm = MockLLMClient() if mock_llm else OpenAICompatibleClient()
        report = AnalysisPipeline(llm, include_node_trace=include_node_trace).run(dataset)
    except (DataProviderError, ValueError) as exc:
        console.print(f"[red]Error:[/red] {exc}")
        raise typer.Exit(code=1) from exc

    target_dir = output_dir or Path("outputs") / f"{symbol}_{date.today().isoformat()}"
    markdown_path, json_path = ReportWriter().write(report, target_dir)
    console.print(f"[green]Done.[/green] Markdown: {markdown_path}")
    console.print(f"[green]Done.[/green] JSON: {json_path}")


if __name__ == "__main__":
    app()
