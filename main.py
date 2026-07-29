import os
import sys
import json
import typer
from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax

load_dotenv()
console = Console()
app = typer.Typer(help="🏥 TrialMind: Autonomous Clinical Trial Matching Agent")


@app.command()
def extract(
    patient: str = typer.Option(..., "--patient", "-p", help="Path to patient medical record file (.txt or .pdf)"),
    model: str = typer.Option("gemini-1.5-flash", "--model", "-m", help="Gemini model to use (gemini-1.5-flash or gemini-1.5-pro)"),
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
def version():
    """Display TrialMind version info."""
    console.print("TrialMind Agent v0.1.0 (Phase 3: Gemini Multimodal Extractor)")


if __name__ == "__main__":
    app()
