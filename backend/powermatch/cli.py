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
        task = progress.add_task("Installing dependencies", total=None)
        time.sleep(0.8)
        progress.update(task, description="Verifying MQTT broker connection")
        time.sleep(0.8)
        progress.update(task, description="Launching FastAPI server")
        time.sleep(0.8)

    console.print("[bold cyan]Starting backend on [yellow]http://localhost:8000[/yellow][/bold cyan]")
    uvicorn.run("powermatch.app:app", host="0.0.0.0", port=8000)
