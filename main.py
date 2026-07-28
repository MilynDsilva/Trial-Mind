import os
import sys
from dotenv import load_dotenv
from rich.console import Console

load_dotenv()
console = Console()


def main():
    console.print("[bold green]🏥 TrialMind AI Agent[/bold green] v0.1.0")
    console.print("Autonomous Multimodal Clinical Trial Matcher\n")
    
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key or api_key == "your_gemini_api_key_here":
        console.print("[bold yellow]Warning:[/bold yellow] GEMINI_API_KEY is missing or unconfigured in .env file.")
        console.print("Please set your API key in .env to run live extractions.\n")
    else:
        console.print("[bold cyan]Gemini API Key detected.[/bold cyan] Agent ready.\n")
    
    console.print("Usage:")
    console.print("  python main.py --patient <path-to-ehr-pdf> --trial <nct-id-or-json>")


if __name__ == "__main__":
    main()
