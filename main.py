import os
import sys
import json
import typer
from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax
from rich.table import Table

load_dotenv()
console = Console()
app = typer.Typer(help="🏥 TrialMind: Autonomous Clinical Trial Matching Agent")


@app.command()
def extract(
    patient: str = typer.Option(..., "--patient", "-p", help="Path to patient medical record file (.txt or .pdf)"),
    model: str = typer.Option("gemini-1.5-flash", "--model", "-m", help="Gemini model to use"),
    output: str = typer.Option(None, "--output", "-o", help="Optional output path for extracted PatientRecord JSON"),
):
    """Extract structured PatientRecord JSON from unstructured medical text or PDF using Gemini."""
    console.print(Panel("[bold green]TrialMind EHR Multimodal Extractor[/bold green]", expand=False))
    
    if not os.path.exists(patient):
        console.print(f"[bold red]Error:[/bold red] File not found at '{patient}'")
        raise typer.Exit(code=1)

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key or api_key == "your_gemini_api_key_here":
        console.print("[bold red]Error:[/bold red] GEMINI_API_KEY is not set in environment or .env file.")
        raise typer.Exit(code=1)

    from src.services.gemini_client import GeminiExtractor

    console.print(f"Reading file: [cyan]{patient}[/cyan] ...")
    extractor = GeminiExtractor(api_key=api_key, model_name=model)
    
    try:
        if patient.endswith(".pdf"):
            patient_record = extractor.extract_patient_from_pdf(patient)
        else:
            with open(patient, "r", encoding="utf-8") as f:
                text_content = f.read()
            patient_record = extractor.extract_patient_from_text(text_content)

        formatted_json = json.dumps(patient_record.model_dump(), indent=2)
        
        console.print("\n[bold green]✅ Extraction Successful![/bold green]\n")
        console.print(Syntax(formatted_json, "json", theme="monokai", line_numbers=True))

        if output:
            with open(output, "w", encoding="utf-8") as f:
                f.write(formatted_json)
            console.print(f"\nSaved structured PatientRecord JSON to [cyan]{output}[/cyan]")

    except Exception as e:
        console.print(f"\n[bold red]Extraction Failed:[/bold red] {e}")
        raise typer.Exit(code=1)


@app.command()
def match(
    patient: str = typer.Option(..., "--patient", "-p", help="Path to patient medical record file (.txt or .pdf)"),
    trial: str = typer.Option(..., "--trial", "-t", help="Path to trial protocol JSON file or NCT ID (e.g. NCT05123456)"),
    model: str = typer.Option("gemini-1.5-flash", "--model", "-m", help="Gemini model to use"),
    output: str = typer.Option(None, "--output", "-o", help="Optional output path for MatchReport JSON"),
    pdf: str = typer.Option(None, "--pdf", help="Optional path to export executive PDF report (e.g. report.pdf)"),
):
    """Match patient medical record against a clinical trial protocol."""
    console.print(Panel("[bold cyan]TrialMind Clinical Trial Matching Engine[/bold cyan]", expand=False))

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key or api_key == "your_gemini_api_key_here":
        console.print("[bold red]Error:[/bold red] GEMINI_API_KEY is not set in environment or .env file.")
        raise typer.Exit(code=1)

    from src.services.gemini_client import GeminiExtractor
    from src.services.trial_fetcher import TrialFetcher
    from src.engine.matcher import ClinicalTrialMatcher
    from src.reports.pdf_generator import PDFReportExporter

    # 1. Extract Patient Record
    console.print(f"Extracting patient profile from: [cyan]{patient}[/cyan]...")
    extractor = GeminiExtractor(api_key=api_key, model_name=model)
    if patient.endswith(".pdf"):
        patient_record = extractor.extract_patient_from_pdf(patient)
    else:
        with open(patient, "r", encoding="utf-8") as f:
            patient_record = extractor.extract_patient_from_text(f.read())

    # 2. Fetch/Load Trial Protocol
    if trial.startswith("NCT"):
        console.print(f"Fetching protocol from ClinicalTrials.gov for: [cyan]{trial}[/cyan]...")
        trial_protocol = TrialFetcher.fetch_from_clinicaltrials_gov(trial)
    else:
        console.print(f"Loading trial protocol from: [cyan]{trial}[/cyan]...")
        trial_protocol = TrialFetcher.load_from_file(trial)

    # 3. Perform Match Evaluation
    console.print("Running AI match evaluation engine...")
    matcher = ClinicalTrialMatcher(api_key=api_key, model_name=model)
    report = matcher.evaluate_match(patient_record, trial_protocol)

    # 4. Display Results
    status_color = "green" if report.overall_status == "ELIGIBLE" else ("yellow" if report.overall_status == "POTENTIALLY_ELIGIBLE" else "red")
    console.print(f"\n[bold]MATCH RESULT:[/bold] [{status_color}]{report.overall_status.value}[/{status_color}] (Confidence: {report.confidence_score*100:.1f}%)")
    console.print(f"[bold]Summary:[/bold] {report.summary}\n")

    table = Table(title="Criteria Evaluation Matrix")
    table.add_column("ID", style="dim")
    table.add_column("Type")
    table.add_column("Criterion")
    table.add_column("Status")
    table.add_column("Reasoning & Evidence")

    for ev in report.evaluations:
        ev_color = "green" if ev.status == "MET" else ("red" if ev.status == "NOT_MET" else "yellow")
        table.add_row(
            ev.criterion_id,
            ev.rule_type,
            ev.criterion_text[:40] + "..." if len(ev.criterion_text) > 40 else ev.criterion_text,
            f"[{ev_color}]{ev.status}[/{ev_color}]",
            ev.reasoning
        )

    console.print(table)

    formatted_json = json.dumps(report.model_dump(), indent=2)
    if output:
        with open(output, "w", encoding="utf-8") as f:
            f.write(formatted_json)
        console.print(f"\nSaved MatchReport JSON to [cyan]{output}[/cyan]")

    if pdf:
        pdf_file = PDFReportExporter.generate_pdf(report, patient_record, trial_protocol, pdf)
        console.print(f"\n[bold green]📄 Generated PDF Report:[/bold green] [cyan]{pdf_file}[/cyan]")


@app.command()
def version():
    """Display TrialMind version info."""
    console.print("TrialMind Agent v0.1.0 (Phase 4: Audit & PDF Report Generator)")


if __name__ == "__main__":
    app()
