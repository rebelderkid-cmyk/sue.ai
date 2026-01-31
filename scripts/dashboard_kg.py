import time
import os
import datetime
from rich.console import Console
from rich.layout import Layout
from rich.panel import Panel
from rich.table import Table
from rich.live import Live
from rich import box

# --- CONFIG ---
LOG_FILE = "/home/rinne/kg_pipeline.log"
OUTPUT_FILE = "/home/rinne/law_knowledge_graph_final.jsonl"
FAILED_LOG = "/home/rinne/kg_failed_log.txt"
PROGRESS_FILE = "/home/rinne/kg_progress_log.txt"

console = Console()

def get_stats():
    # Count output lines (Success extracted KG)
    success_count = 0
    if os.path.exists(OUTPUT_FILE):
        try:
            with os.popen(f"wc -l {OUTPUT_FILE}") as f:
                success_count = int(f.read().split()[0])
        except: pass

    # Count filtered/processed (Attempted that matched keyword filter)
    processed_count = 0
    if os.path.exists(PROGRESS_FILE):
        try:
            with os.popen(f"wc -l {PROGRESS_FILE}") as f:
                processed_count = int(f.read().split()[0])
        except: pass

    # Failures
    fail_count = 0
    if os.path.exists(FAILED_LOG):
        try:
             with os.popen(f"wc -l {FAILED_LOG}") as f:
                fail_count = int(f.read().split()[0])
        except: pass

    # Tail Logs
    logs = []
    if os.path.exists(LOG_FILE):
        with os.popen(f"tail -n 12 {LOG_FILE}") as f:
            logs = [line.strip() for line in f.readlines() if line.strip()]

    return success_count, processed_count, fail_count, logs

def make_dashboard(stats):
    success, processed, failed, logs = stats
    
    layout = Layout()
    layout.split_column(
        Layout(name="header", size=3),
        Layout(name="main"),
        Layout(name="footer", size=14)
    )
    
    # Header
    layout["header"].update(Panel(
        f"[bold white]🧠 Knowledge Graph Extraction (Text Mode)[/bold white] | [cyan]{datetime.datetime.now().strftime('%H:%M:%S')}[/cyan]",
        style="purple", box=box.HEAVY
    ))
    
    # Stats Table
    table = Table(box=box.SIMPLE, expand=True)
    table.add_column("Metric", justify="center", style="cyan")
    table.add_column("Value", justify="center", style="bold white")
    
    table.add_row("Total Processed via AI", f"[bold green]{success:,}[/bold green]")
    table.add_row("Failed", f"[red]{failed:,}[/red]")
    table.add_row("Success Rate", f"{(success/(processed+0.001)*100):.1f}%")
    
    cost_est = success * (0.0002) # approx $0.0002 per doc (input+output blended)
    table.add_row("Estimated Cost", f"[yellow]${cost_est:.4f}[/yellow]")

    panel_stats = Panel(table, title="KPIs", border_style="green")
    layout["main"].update(panel_stats)

    # Logs
    log_text = "\n".join(logs)
    layout["footer"].update(Panel(log_text, title="📜 Live Logs", border_style="white"))
    
    return layout

if __name__ == "__main__":
    with Live(refresh_per_second=2, screen=True) as live:
        while True:
            stats = get_stats()
            layout = make_dashboard(stats)
            live.update(layout)
            time.sleep(1)
