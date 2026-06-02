from enum import Enum
from pathlib import Path

import typer

from daily_ai_insight.evaluate import evaluation_output_paths, run_evaluation, write_evaluation_outputs
from daily_ai_insight.errors import PipelineError
from daily_ai_insight.pipeline import run_pipeline
from daily_ai_insight.reviewer import run_review, write_review_outputs

app = typer.Typer(help="运行 Daily AI Insight Engine 的本地 pipeline。")


class ExtractorOption(str, Enum):
    rule = "rule"
    mock_llm = "mock-llm"
    openai_compatible = "openai-compatible"


@app.callback()
def main() -> None:
    """Daily AI Insight 命令组。"""


@app.command()
def run(
    input_path: Path = typer.Option(
        Path("data/raw/sample_ai_news.json"),
        "--input",
        "-i",
        help="原始 AI 新闻 JSON 路径。",
    ),
    extractor_name: ExtractorOption = typer.Option(
        ExtractorOption.rule,
        "--extractor",
        help="抽取模式：rule、mock-llm 或 openai-compatible。",
    ),
) -> None:
    try:
        report = run_pipeline(input_path, extractor_name=extractor_name.value)
    except PipelineError as exc:
        typer.echo(f"日报生成失败：{exc}", err=True)
        raise typer.Exit(code=1) from exc

    typer.echo("日报生成完成。")
    typer.echo(f"抽取模式：{extractor_name.value}")
    typer.echo(f"已校验事件数：{report.total_events}")
    typer.echo("已生成：data/processed/structured_events.json")
    typer.echo("已生成：outputs/daily_report.md")


@app.command()
def evaluate(
    input_path: Path = typer.Option(
        Path("data/raw/real_ai_news_sample.json"),
        "--input",
        "-i",
        help="原始 AI 新闻 JSON 路径。",
    ),
    expected_path: Path = typer.Option(
        Path("data/eval/expected_real_sample_categories.json"),
        "--expected",
        "-e",
        help="预期分类 fixture 路径。",
    ),
    extractor_name: ExtractorOption = typer.Option(
        ExtractorOption.rule,
        "--extractor",
        help="抽取模式：rule、mock-llm 或 openai-compatible。",
    ),
    output_prefix: str | None = typer.Option(
        None,
        "--output-prefix",
        help="可选输出前缀，例如 rule 或 llm。",
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
        typer.echo(f"评估失败：{exc}", err=True)
        raise typer.Exit(code=1) from exc

    typer.echo("评估完成。")
    typer.echo(f"抽取模式：{summary.extractor}")
    typer.echo(f"样本总数：{summary.total_items}")
    typer.echo(f"成功项：{summary.successful_items}")
    typer.echo(f"失败项：{summary.failed_items}")
    typer.echo(f"分类准确率：{summary.category_accuracy:.2f}")
    typer.echo(f"来源追溯通过率：{summary.grounding_pass_rate:.2f}")
    typer.echo(f"平均置信度：{summary.average_confidence:.2f}")
    typer.echo(f"已生成：{summary_path}")
    typer.echo(f"已生成：{report_path}")


@app.command()
def review(
    evaluation_path: Path = typer.Option(
        Path("outputs/evaluation_summary.json"),
        "--evaluation",
        "-e",
        help="评估 summary JSON 路径。",
    ),
    baseline_path: Path | None = typer.Option(
        None,
        "--baseline",
        "-b",
        help="可选 baseline 评估 summary JSON 路径。",
    ),
) -> None:
    try:
        summary = run_review(
            evaluation_path=evaluation_path,
            baseline_path=baseline_path,
        )
        summary_path, report_path = write_review_outputs(summary)
    except (OSError, ValueError, PipelineError) as exc:
        typer.echo(f"复审失败：{exc}", err=True)
        raise typer.Exit(code=1) from exc

    typer.echo("复审完成。")
    typer.echo(f"最终结论：{summary.final_verdict}")
    typer.echo(f"问题总数：{summary.total_issues}")
    typer.echo(f"错误数：{summary.error_count}")
    typer.echo(f"警告数：{summary.warning_count}")
    typer.echo(f"信息数：{summary.info_count}")
    typer.echo(f"已生成：{summary_path}")
    typer.echo(f"已生成：{report_path}")


if __name__ == "__main__":
    app()
