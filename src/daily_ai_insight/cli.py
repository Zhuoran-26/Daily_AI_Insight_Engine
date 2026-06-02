"""Command-line interface for the harnessed MVP pipeline."""

from pathlib import Path
from enum import Enum

import typer

from daily_ai_insight.errors import PipelineError
from daily_ai_insight.pipeline import run_pipeline

app = typer.Typer(help="Run the Daily AI Insight deterministic MVP pipeline.")


class ExtractorOption(str, Enum):
    rule = "rule"
    mock_llm = "mock-llm"
    openai_compatible = "openai-compatible"


@app.callback()
def main() -> None:
    """Daily AI Insight command group."""


@app.command()
def run(
    input_path: Path = typer.Option(
        Path("data/raw/sample_ai_news.json"),
        "--input",
        "-i",
        help="Path to raw AI news JSON.",
    ),
    extractor_name: ExtractorOption = typer.Option(
        ExtractorOption.rule,
        "--extractor",
        help="Extractor mode: rule, mock-llm, or openai-compatible.",
    ),
) -> None:
    try:
        report = run_pipeline(input_path, extractor_name=extractor_name.value)
    except PipelineError as exc:
        typer.echo(f"Pipeline failed: {exc}", err=True)
        raise typer.Exit(code=1) from exc

    typer.echo("Pipeline completed.")
    typer.echo(f"Extractor: {extractor_name.value}")
    typer.echo(f"Validated events: {report.total_events}")
    typer.echo("Generated data/processed/structured_events.json")
    typer.echo("Generated outputs/daily_report.md")


if __name__ == "__main__":
    app()
