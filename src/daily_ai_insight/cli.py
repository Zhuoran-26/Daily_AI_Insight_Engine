from enum import Enum
from pathlib import Path

import typer

from daily_ai_insight.evaluate import evaluation_output_paths, run_evaluation, write_evaluation_outputs
from daily_ai_insight.errors import PipelineError
from daily_ai_insight.pipeline import run_pipeline
from daily_ai_insight.reviewer import run_review, write_review_outputs

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


@app.command()
def evaluate(
    input_path: Path = typer.Option(
        Path("data/raw/real_ai_news_sample.json"),
        "--input",
        "-i",
        help="Path to raw AI news JSON.",
    ),
    expected_path: Path = typer.Option(
        Path("data/eval/expected_real_sample_categories.json"),
        "--expected",
        "-e",
        help="Path to expected category fixture.",
    ),
    extractor_name: ExtractorOption = typer.Option(
        ExtractorOption.rule,
        "--extractor",
        help="Extractor mode: rule, mock-llm, or openai-compatible.",
    ),
    output_prefix: str | None = typer.Option(
        None,
        "--output-prefix",
        help="Optional output prefix, for example rule or llm.",
    ),
) -> None:
    try:
        summary = run_evaluation(
            input_path=input_path,
            expected_path=expected_path,
            extractor_name=extractor_name.value,
        )
        summary_output_path, report_output_path = evaluation_output_paths(output_prefix)
        summary_path, report_path = write_evaluation_outputs(
            summary,
            summary_path=summary_output_path,
            report_path=report_output_path,
        )
    except PipelineError as exc:
        typer.echo(f"Evaluation failed: {exc}", err=True)
        raise typer.Exit(code=1) from exc

    typer.echo("Evaluation completed.")
    typer.echo(f"Extractor: {summary.extractor}")
    typer.echo(f"Total items: {summary.total_items}")
    typer.echo(f"Successful items: {summary.successful_items}")
    typer.echo(f"Failed items: {summary.failed_items}")
    typer.echo(f"Category accuracy: {summary.category_accuracy:.2f}")
    typer.echo(f"Grounding pass rate: {summary.grounding_pass_rate:.2f}")
    typer.echo(f"Average confidence: {summary.average_confidence:.2f}")
    typer.echo(f"Generated {summary_path}")
    typer.echo(f"Generated {report_path}")


@app.command()
def review(
    evaluation_path: Path = typer.Option(
        Path("outputs/evaluation_summary.json"),
        "--evaluation",
        "-e",
        help="Path to an evaluation summary JSON file.",
    ),
    baseline_path: Path | None = typer.Option(
        None,
        "--baseline",
        "-b",
        help="Optional baseline evaluation summary JSON file.",
    ),
) -> None:
    try:
        summary = run_review(
            evaluation_path=evaluation_path,
            baseline_path=baseline_path,
        )
        summary_path, report_path = write_review_outputs(summary)
    except (OSError, ValueError, PipelineError) as exc:
        typer.echo(f"Review failed: {exc}", err=True)
        raise typer.Exit(code=1) from exc

    typer.echo("Review completed.")
    typer.echo(f"Final verdict: {summary.final_verdict}")
    typer.echo(f"Total issues: {summary.total_issues}")
    typer.echo(f"Errors: {summary.error_count}")
    typer.echo(f"Warnings: {summary.warning_count}")
    typer.echo(f"Info: {summary.info_count}")
    typer.echo(f"Generated {summary_path}")
    typer.echo(f"Generated {report_path}")


if __name__ == "__main__":
    app()
