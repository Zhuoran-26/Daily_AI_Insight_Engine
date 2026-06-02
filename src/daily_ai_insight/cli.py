"""Command-line interface for the deterministic MVP pipeline."""

from pathlib import Path

import typer

from daily_ai_insight.errors import PipelineError
from daily_ai_insight.pipeline import run_pipeline

app = typer.Typer(help="Run the Daily AI Insight deterministic MVP pipeline.")


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
) -> None:
    try:
        report = run_pipeline(input_path)
    except PipelineError as exc:
        typer.echo(f"Pipeline failed: {exc}", err=True)
        raise typer.Exit(code=1) from exc

    typer.echo("Pipeline completed.")
    typer.echo(f"Validated events: {report.total_events}")
    typer.echo("Generated data/processed/structured_events.json")
    typer.echo("Generated outputs/daily_report.md")


if __name__ == "__main__":
    app()
