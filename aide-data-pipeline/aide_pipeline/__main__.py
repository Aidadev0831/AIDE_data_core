"""AIDE Pipeline CLI Entry Point

Usage:
    python -m aide_pipeline run [job_name]
    python -m aide_pipeline schedule
    python -m aide_pipeline status
"""

import sys
import logging
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table
from rich import print as rprint

from aide_pipeline.orchestrator import PipelineOrchestrator
from aide_pipeline.config import load_config
from aide_data_core.models.base import get_session
from aide_data_core.models import IngestJobRun

app = typer.Typer(help="AIDE Platform Data Pipeline Orchestrator")
console = Console()

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@app.command()
def run(
    job: str = typer.Argument(..., help="Job name (naver_news, kdi_policy, credit_rating, all)"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Dry run mode (no DB writes)"),
    config_file: Path = typer.Option("config/schedule.yaml", "--config", "-c", help="Config file path"),
):
    """Run a single job or all jobs"""
    console.print(f"\n[bold blue]🚀 AIDE Pipeline - Running job: {job}[/bold blue]\n")

    try:
        # Load configuration
        config = load_config(config_file)

        if dry_run:
            console.print("[yellow]⚠️  DRY RUN MODE - No database writes will be performed[/yellow]\n")

        # Create orchestrator
        orchestrator = PipelineOrchestrator(config, dry_run=dry_run)

        # Run job(s)
        if job == "all":
            # Run all enabled jobs
            jobs_to_run = [
                job_name
                for job_name, job_config in config.get("jobs", {}).items()
                if job_config.get("enabled", True)
            ]

            console.print(f"[cyan]Running {len(jobs_to_run)} jobs: {', '.join(jobs_to_run)}[/cyan]\n")

            for job_name in jobs_to_run:
                console.print(f"\n[yellow]▶ Running {job_name}...[/yellow]")
                job_run = orchestrator.run_job(job_name)
                _print_job_result(job_run)

        else:
            # Run single job
            job_run = orchestrator.run_job(job)
            _print_job_result(job_run)

        console.print("\n[bold green]✅ Pipeline execution completed[/bold green]\n")

    except Exception as e:
        console.print(f"\n[bold red]❌ Error: {e}[/bold red]\n")
        logger.error(f"Pipeline execution failed: {e}", exc_info=True)
        raise typer.Exit(code=1)


@app.command()
def schedule():
    """Start scheduler (runs jobs based on schedule.yaml)"""
    console.print("[bold green]⏰ AIDE Pipeline Scheduler - Starting...[/bold green]\n")

    try:
        import schedule
        import time

        # Load configuration
        config = load_config()
        orchestrator = PipelineOrchestrator(config)

        # Schedule jobs
        for job_name, job_config in config.get("jobs", {}).items():
            if not job_config.get("enabled", True):
                continue

            schedule_time = job_config.get("schedule")
            if schedule_time:
                console.print(f"[cyan]📅 Scheduled {job_name} at {schedule_time}[/cyan]")

                # Parse cron-like schedule (simplified)
                # "30 8 * * *" -> every day at 08:30
                parts = schedule_time.split()
                if len(parts) >= 2:
                    minute, hour = parts[0], parts[1]
                    schedule_str = f"{hour}:{minute}"

                    schedule.every().day.at(schedule_str).do(
                        lambda jn=job_name: orchestrator.run_job(jn)
                    )

        console.print("\n[bold green]✅ Scheduler started. Press Ctrl+C to stop.[/bold green]\n")

        # Run scheduler loop
        while True:
            schedule.run_pending()
            time.sleep(60)  # Check every minute

    except KeyboardInterrupt:
        console.print("\n[bold red]🛑 Scheduler stopped[/bold red]\n")
    except Exception as e:
        console.print(f"\n[bold red]❌ Scheduler error: {e}[/bold red]\n")
        logger.error(f"Scheduler failed: {e}", exc_info=True)
        raise typer.Exit(code=1)


@app.command()
def status(
    limit: int = typer.Option(10, "--limit", "-n", help="Number of recent runs to show"),
    job_name: Optional[str] = typer.Option(None, "--job", "-j", help="Filter by job name"),
):
    """Show recent job runs status"""
    console.print("\n[bold]📊 Recent Job Runs[/bold]\n")

    try:
        with get_session() as db:
            query = db.query(IngestJobRun).order_by(IngestJobRun.started_at.desc())

            if job_name:
                query = query.filter_by(job_name=job_name)

            runs = query.limit(limit).all()

            if not runs:
                console.print("[yellow]No job runs found[/yellow]\n")
                return

            # Create table
            table = Table(show_header=True, header_style="bold magenta")
            table.add_column("Job Name", style="cyan")
            table.add_column("Started At")
            table.add_column("Status", justify="center")
            table.add_column("Items", justify="right")
            table.add_column("Duration", justify="right")
            table.add_column("Error")

            for run in runs:
                # Calculate duration
                duration = ""
                if run.completed_at:
                    delta = run.completed_at - run.started_at
                    duration = str(delta).split(".")[0]  # Remove microseconds

                # Status color
                status_color = {
                    "completed": "green",
                    "failed": "red",
                    "running": "yellow",
                }.get(run.status, "white")

                # Format status
                status_icon = {
                    "completed": "✅",
                    "failed": "❌",
                    "running": "⏳",
                }.get(run.status, "")
                status_display = f"[{status_color}]{status_icon} {run.status}[/{status_color}]"

                # Items collected
                items = str(run.items_collected or 0)
                if run.items_processed:
                    items += f" / {run.items_processed}"

                # Error message (truncated)
                error = ""
                if run.error_message:
                    error = run.error_message[:50] + "..." if len(run.error_message) > 50 else run.error_message

                table.add_row(
                    run.job_name,
                    str(run.started_at)[:19],  # Remove microseconds
                    status_display,
                    items,
                    duration,
                    error,
                )

            console.print(table)
            console.print()

    except Exception as e:
        console.print(f"\n[bold red]❌ Error: {e}[/bold red]\n")
        logger.error(f"Status command failed: {e}", exc_info=True)
        raise typer.Exit(code=1)


def _print_job_result(job_run):
    """Print job result summary

    Args:
        job_run: IngestJobRun instance
    """
    if job_run is None:
        return

    if job_run.status == "completed":
        console.print(
            f"  [green]✅ {job_run.job_name}[/green]: "
            f"{job_run.items_collected or 0} collected, "
            f"{job_run.items_processed or 0} processed"
        )
    else:
        console.print(
            f"  [red]❌ {job_run.job_name}[/red]: {job_run.error_message or 'Unknown error'}"
        )


if __name__ == "__main__":
    app()
