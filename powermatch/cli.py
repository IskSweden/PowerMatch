# powermatch/cli.py
import uvicorn
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from time import sleep

console = Console()

def main():
    console.print("[bold cyan]Launching PowerMatch Game Server...[/bold cyan]")

    with Progress(
        SpinnerColumn(style="green"),
        TextColumn("[progress.description]{task.description}"),
        transient=True,
    ) as progress:
        progress.add_task(description="Preparing FastAPI app...", total=None)
        sleep(0.5)  # simulate some loading
        progress.add_task(description="Initializing WebSocket manager...", total=None)
        sleep(0.5)
        progress.add_task(description="Starting Uvicorn...", total=None)
        sleep(0.5)

    console.print("[bold green]✅ Server ready! Listening on [cyan]http://0.0.0.0:8000[/cyan][/bold green]")

    uvicorn.run("powermatch.app:create_app", host="0.0.0.0", port=8000, factory=True)
