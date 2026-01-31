import time
import os
import sys
import psutil
import json
from datetime import datetime
from rich.live import Live
from rich.table import Table
from rich.panel import Panel
from rich.layout import Layout
from rich.console import Console
from rich.progress import Progress, BarColumn, TextColumn, TimeElapsedColumn
from rich import box

# Config
LOG_FILE = "/home/rinne/batch_extraction.log"
OUTPUT_FILE = "/home/rinne/royal_gazette_corpus_v1.jsonl"
PROGRESS_FILE = "/home/rinne/processed_zips_v1.txt"
TOTAL_ZIPS = 1673

console = Console()

def get_stats():
    # 1. Progress Stats
    processed_count = 0
    if os.path.exists(PROGRESS_FILE):
        with open(PROGRESS_FILE, 'r') as f:
            processed_count = len(f.readlines())
    
    doc_count = 0
    file_size = "0 KB"
    if os.path.exists(OUTPUT_FILE):
        file_size = f"{os.path.getsize(OUTPUT_FILE) / 1024 / 1024:.2f} MB"
        # Quick line count
        with open(OUTPUT_FILE, 'rb') as f:
            doc_count = sum(1 for line in f)

    # 2. System Stats
    cpu_usage = psutil.cpu_percent()
    mem = psutil.virtual_memory()
    disk = psutil.disk_usage('/home/rinne')
    
    # 3. Recent Logs
    recent_logs = []
    if os.path.exists(LOG_FILE):
        with os.popen(f"tail -n 10 {LOG_FILE}") as f:
            recent_logs = [line.strip() for line in f.readlines() if line.strip()]

    return {
        "processed": processed_count,
        "total": TOTAL_ZIPS,
        "docs": doc_count,
        "size": file_size,
        "cpu": cpu_usage,
        "mem": mem.percent,
        "disk": disk.percent,
        "logs": recent_logs
    }

def generate_layout() -> Layout:
    layout = Layout()
    layout.split_column(
        Layout(name="header", size=3),
        Layout(name="main"),
        Layout(name="footer", size=10)
    )
    layout["main"].split_row(
        Layout(name="stats"),
        Layout(name="sys_info")
    )
    return layout

def make_dashboard():
    stats = get_stats()
    
    # Header
    header = Panel(
        f"[bold cyan]🏎️ Ferrari OCR Ultimate Dashboard[/bold cyan] | [green]STATUS: RUNNING[/green] | [yellow]{datetime.now().strftime('%H:%M:%S')}[/yellow]",
        box=box.DOUBLE_EDGE
    )
    
    # Stats Table
    stats_table = Table(title="📦 Extraction Progress", box=box.ROUNDED, expand=True)
    stats_table.add_column("Category", style="cyan")
    stats_table.add_column("Value", style="magenta")
    
    stats_table.add_row("ZIP Files Processed", f"{stats['processed']} / {stats['total']}")
    stats_table.add_row("Documents Extracted", f"{stats['docs']:,}")
    stats_table.add_row("Output File Size", stats['size'])
    stats_table.add_row("Progress %", f"{(stats['processed']/stats['total'])*100:.2f}%")
    
    # Sys Info Table
    sys_table = Table(title="🧠 System Resources", box=box.ROUNDED, expand=True)
    sys_table.add_column("Resource", style="cyan")
    sys_table.add_column("Usage", style="magenta")
    
    sys_table.add_row("CPU Load (70-Core Priority)", f"{stats['cpu']}%")
    sys_table.add_row("Memory (RAM)", f"{stats['mem']}%")
    sys_table.add_row("Disk Space (Home)", f"{stats['disk']}%")

    # Logs Panel
    logs_content = "\n".join(stats['logs'][-8:])
    logs_panel = Panel(logs_content, title="💬 Recent Logs (Real-time)", border_style="dim")

    layout = generate_layout()
    layout["header"].update(header)
    layout["stats"].update(Panel(stats_table, border_style="cyan"))
    layout["sys_info"].update(Panel(sys_table, border_style="magenta"))
    layout["footer"].update(logs_panel)
    
    return layout

if __name__ == "__main__":
    with Live(make_dashboard(), refresh_per_second=1, screen=True) as live:
        while True:
            time.sleep(1)
            live.update(make_dashboard())
