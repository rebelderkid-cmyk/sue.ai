import time
import os
import json
from rich.console import Console
from rich.layout import Layout
from rich.panel import Panel
from rich.table import Table
from rich.live import Live
from rich import box
import datetime

# --- CONFIG ---
LOG_FILE = "/home/rinne/gemini_pipeline.log"
OUTPUT_FILE = "/home/rinne/law_knowledge_graph.jsonl"
FAILED_LOG = "/home/rinne/failed_files.log"
PROGRESS_FILE = "/home/rinne/pipeline_progress.txt"

console = Console()

def get_stats():
    # 1. Count processed
    success_count = 0
    if os.path.exists(OUTPUT_FILE):
        try:
            # Efficiently count lines using a system call or file scan
            # For simplicity in python:
            with open(OUTPUT_FILE, 'r') as f:
                success_count = sum(1 for _ in f)
        except: pass

    # 2. Count failures
    fail_count = 0
    if os.path.exists(FAILED_LOG):
        try:
            with open(FAILED_LOG, 'r') as f:
                fail_count = sum(1 for _ in f)
        except: pass

    # 3. Read Progress (Zips Done)
    zips_done = 0
    if os.path.exists(PROGRESS_FILE):
        try:
            with open(PROGRESS_FILE, 'r') as f:
                zips_done = sum(1 for _ in f)
        except: pass

    # 4. Tail Logs
    logs = []
    if os.path.exists(LOG_FILE):
        with os.popen(f"tail -n 10 {LOG_FILE}") as f:
            logs = [line.strip() for line in f.readlines() if line.strip()]

    return success_count, fail_count, zips_done, logs

def make_layout():
    layout = Layout()
    layout.split_column(
        Layout(name="header", size=3),
        Layout(name="main"),
        Layout(name="footer", size=14)
    )
    layout["main"].split_row(
        Layout(name="stats"),
        Layout(name="details")
    )
    return layout

def update_ui(layout):
    success, failed, zips, logs = get_stats()
    
    # Header
    layout["header"].update(Panel(
        f"[bold white]🚀 Gemini 2.0 Flash Payload Dashboard[/bold white] | [cyan]Time: {datetime.datetime.now().strftime('%H:%M:%S')}[/cyan]",
        style="blue", box=box.DOUBLE
    ))
    
    # Stats Table
    table = Table(box=box.SIMPLE)
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="bold green")
    
    total_processed = success + failed
    success_rate = (success / total_processed * 100) if total_processed > 0 else 0
    
    table.add_row("Files Indexed", f"{success:,}")
    table.add_row("Files Failed", f"[red]{failed:,}[/red]")
    table.add_row("Zips Completed", f"{zips:,}")
    table.add_row("Success Rate", f"{success_rate:.1f}%")
    
    layout["stats"].update(Panel(table, title="📊 Live Statistics", border_style="green"))
    
    # Details/Cost Estimator
    cost_est = (success * 1000 / 1000000 * 0.10) + (success * 500 / 1000000 * 0.30) 
    # Approx 1000 in, 500 out per file. $0.10/M In (Audio/Image rate blended), $0.30/M Out. Very rough est.
    
    detail_text = f"""
    [bold yellow]💰 API Cost Estimate[/bold yellow]
    ~${cost_est:.2f} USD
    
    [bold magenta]Estimate Speed[/bold magenta]
    Checking...
    """
    layout["details"].update(Panel(detail_text, title="📈 Performance", border_style="yellow"))

    # Logs
    log_text = "\n".join(logs)
    layout["footer"].update(Panel(log_text, title="📜 Pipeline Logs (Tail)", border_style="white"))

def monitor():
    layout = make_layout()
    with Live(layout, refresh_per_second=2, screen=True):
        while True:
            update_ui(layout)
            time.sleep(0.5)

if __name__ == "__main__":
    monitor()
