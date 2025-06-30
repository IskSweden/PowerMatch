from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
import uvicorn
import time

console = Console()

def main():
    console.print("[bold green]🚀 PowerMatch Launcher[/bold green]")
    console.print("Preparing to launch backend...")

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        transient=True,
    ) as progress:
        task = progress.add_task("Loading app factory", total=None)
        time.sleep(0.5)
        progress.update(task, description="Starting FastAPI server")
        time.sleep(0.5)

    console.print("[bold cyan]Running at [yellow]http://localhost:8000[/yellow][/bold cyan]")

    # This must match your app layout:
    uvicorn.run("powermatch.app:create_app", host="0.0.0.0", port=8000, reload=True, factory=True)
