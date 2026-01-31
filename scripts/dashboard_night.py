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
from rich import box

# Config
INDEX_LOG = "/home/rinne/indexer.log"
INDEX_OUTPUT = "law_index_easyocr.jsonl"
TYPHOON_LOG = "/home/rinne/typhoon_runner.log"
TYPHOON_OUTPUT = "typhoon_extraction_results.jsonl"
PROGRESS_FILE = "/home/rinne/processed_zips_v1.txt"
TOTAL_ZIPS = 1673

console = Console()

def get_stats():
    # 1. Indexing Stats
    idx_count = 0
    high_value_count = 0
    if os.path.exists(INDEX_OUTPUT):
        try:
            with open(INDEX_OUTPUT, 'r') as f:
                for line in f:
                    idx_count += 1
                    try: 
                        if json.loads(line).get('is_high_value'): high_value_count += 1 
                    except: pass
        except: pass

    # 2. Typhoon Stats
    typhoon_count = 0
    if os.path.exists(TYPHOON_OUTPUT):
        try:
            with open(TYPHOON_OUTPUT, 'r') as f:
                typhoon_count = sum(1 for line in f)
        except: pass

    # 3. System Stats
    cpu_usage = psutil.cpu_percent()
    mem = psutil.virtual_memory()
    
    # 4. Logs
    idx_logs = []
    if os.path.exists(INDEX_LOG):
        with os.popen(f"tail -n 5 {INDEX_LOG}") as f:
            idx_logs = [line.strip() for line in f.readlines() if line.strip()]
            
    typhoon_logs = []
    if os.path.exists(TYPHOON_LOG):
        with os.popen(f"tail -n 5 {TYPHOON_LOG}") as f:
            typhoon_logs = [line.strip() for line in f.readlines() if line.strip()]

    return {
        "idx_total": idx_count,
        "idx_high_value": high_value_count,
        "typhoon_processed": typhoon_count,
        "cpu": cpu_usage,
        "mem": mem.percent,
        "idx_logs": idx_logs,
        "typhoon_logs": typhoon_logs
    }

def make_dashboard():
    stats = get_stats()
    
    layout = Layout()
    layout.split_column(
        Layout(name="header", size=3),
        Layout(name="main"),
        Layout(name="footer", size=12)
    )
    layout["main"].split_row(
        Layout(name="indexing"),
        Layout(name="typhoon")
    )
    
    # Header
    header = Panel(
        f"[bold cyan]🌃 Night Shift Command Center[/bold cyan] | [green]CPU: {stats['cpu']}%[/green] | [yellow]MEM: {stats['mem']}%[/yellow]",
        box=box.DOUBLE_EDGE
    )
    
    # Indexing Panel
    idx_table = Table(box=box.SIMPLE)
    idx_table.add_column("Metric", style="cyan")
    idx_table.add_column("Value", style="white")
    idx_table.add_row("Total Indexed", f"{stats['idx_total']:,}")
    idx_table.add_row("High Value Found", f"[bold yellow]{stats['idx_high_value']:,}[/bold yellow]")
    
    p_idx = Panel(
        idx_table, 
        title="🧠 EasyOCR Indexer (80 Cores)",
        border_style="cyan"
    )
    
    # Typhoon Panel
    typ_table = Table(box=box.SIMPLE)
    typ_table.add_column("Metric", style="red")
    typ_table.add_column("Value", style="white")
    typ_table.add_row("Files Processed", f"{stats['typhoon_processed']:,}")
    typ_table.add_row("Status", "Waiting" if stats['typhoon_processed'] == 0 else "Active")
    
    p_typ = Panel(
        typ_table,
        title="🌪️ Typhoon-OCR 7B (Overlord)",
        border_style="red"
    )
    
    # Logs
    log_text = "[bold cyan]--- Indexer Logs ---[/bold cyan]\n" + "\n".join(stats['idx_logs']) + "\n\n"
    log_text += "[bold red]--- Typhoon Logs ---[/bold red]\n" + "\n".join(stats['typhoon_logs'])
    
    p_log = Panel(log_text, title="📜 Live Operation Logs", border_style="dim")

    layout["header"].update(header)
    layout["indexing"].update(p_idx)
    layout["typhoon"].update(p_typ)
    layout["footer"].update(p_log)
    
    return layout

if __name__ == "__main__":
    with Live(make_dashboard(), refresh_per_second=1, screen=True) as live:
        while True:
            time.sleep(2)
            live.update(make_dashboard())
