#!/usr/bin/env bash
# NEURO terminal welcome — biopunk AI dashboard
[[ -z "$PS1" ]] && return
[[ -n "$PLS_WELCOMED" ]] && return
export PLS_WELCOMED=1

# Resolve paths relative to this script so the project works anywhere
_NEURO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_PYTHON="${_NEURO_DIR}/.venv/bin/python"
INTERACTIVE="${_NEURO_DIR}/pls_interactive.py"

python3 - <<'PYEOF'
import os, random, shutil, subprocess, time
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich.rule import Rule
from rich.align import Align
from rich import box
from datetime import datetime

try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False

console = Console(width=82)
now = datetime.now()
h   = now.hour

if   h < 5:  greet = "Still up, night owl?";               mood = "dim green"
elif h < 12: greet = "Good morning. Systems online.";      mood = "bright_green"
elif h < 17: greet = "Afternoon. Neural uplink active.";   mood = "bright_green"
elif h < 21: greet = "Evening. Running final processes.";  mood = "green"
else:        greet = "Late night. The best sessions happen now."; mood = "dim green"

date_str = now.strftime("%a, %d %b %Y").upper()
time_str = now.strftime("%I:%M %p")

quotes = [
    '"Any sufficiently advanced technology is indistinguishable from magic."',
    '"First, solve the problem. Then, write the code."',
    '"Make it work, make it right, make it fast."',
    '"The best error message is the one that never shows up."',
    '"Talk is cheap. Show me the code."',
    '"Simplicity is the soul of efficiency."',
]

def bar(pct, w=16):
    filled = int(w * pct / 100)
    col = "red" if pct >= 80 else ("yellow" if pct >= 60 else "bright_green")
    return Text.from_markup(
        f"[{col}]{'█'*filled}[/{col}][dim green]{'░'*(w-filled)}[/dim green]"
        f" [{col}]{pct:>3}%[/{col}]"
    )

def tc(s):
    try:
        v = float(s.replace("°C",""))
        c = "red" if v>=80 else ("yellow" if v>=65 else "bright_green")
        return f"[{c}]{s}[/{c}]"
    except:
        return s

cpu_pct = cpu_temp = freq_str = "N/A"
ram_pct = ram_used = ram_tot = swap_str = "N/A"
disk_pct = disk_used = disk_tot = "N/A"
uptime = net_rx = net_tx = "N/A"
gpu = None
top_procs = []

if HAS_PSUTIL:
    cpu_pct = psutil.cpu_percent(interval=0.5)
    freq = psutil.cpu_freq()
    freq_str = f"{freq.current/1000:.2f} GHz" if freq else "N/A"
    try:
        ts = psutil.sensors_temperatures()
        for k in ["coretemp","k10temp","cpu_thermal","acpitz"]:
            if k in ts and ts[k]:
                cpu_temp = f"{max(t.current for t in ts[k]):.0f}°C"; break
        else: cpu_temp = "N/A"
    except: cpu_temp = "N/A"

    vm = psutil.virtual_memory()
    ram_pct = vm.percent
    ram_used = f"{vm.used/1024**3:.1f}"
    ram_tot  = f"{vm.total/1024**3:.1f} GB"
    sw = psutil.swap_memory()
    swap_str = f"{sw.used/1024**3:.1f}/{sw.total/1024**3:.1f} GB"

    try:
        tot, used, _ = shutil.disk_usage(os.path.expanduser("~"))
        disk_pct  = int(used/tot*100)
        disk_used = f"{used/1024**3:.0f}"
        disk_tot  = f"{tot/1024**3:.0f} GB"
    except: pass

    secs = int(time.time()-psutil.boot_time())
    uh,r = divmod(secs,3600); um,_ = divmod(r,60)
    uptime = f"{uh}h {um}m"

    try:
        c1=psutil.net_io_counters(); time.sleep(0.2); c2=psutil.net_io_counters()
        rx=(c2.bytes_recv-c1.bytes_recv)/0.2/1024
        tx=(c2.bytes_sent-c1.bytes_sent)/0.2/1024
        fmt=lambda kb: f"{kb:.0f} KB/s" if kb<1024 else f"{kb/1024:.1f} MB/s"
        net_rx,net_tx = fmt(rx),fmt(tx)
    except: pass

    try:
        procs=[]
        for p in psutil.process_iter(["pid","name","cpu_percent","memory_percent"]):
            try: procs.append(p.info)
            except: pass
        time.sleep(0.15)
        procs2=[]
        for p in psutil.process_iter(["pid","name","cpu_percent","memory_percent"]):
            try: procs2.append(p.info)
            except: pass
        top_procs = sorted(procs2, key=lambda x: x.get("cpu_percent") or 0, reverse=True)[:5]
    except: pass

try:
    raw=subprocess.check_output(
        ["nvidia-smi","--query-gpu=temperature.gpu,utilization.gpu,memory.used,memory.total,clocks.current.graphics",
         "--format=csv,noheader,nounits"],stderr=subprocess.DEVNULL,timeout=2).decode().strip()
    try:
        pw=subprocess.check_output(["nvidia-smi","--query-gpu=power.draw.instant","--format=csv,noheader,nounits"],
            stderr=subprocess.DEVNULL,timeout=2).decode().strip()
        pwr_str=f"{float(pw.split()[0]):.1f} W"
    except:
        try:
            pw=subprocess.check_output(["nvidia-smi","--query-gpu=power.draw","--format=csv,noheader,nounits"],
                stderr=subprocess.DEVNULL,timeout=2).decode().strip()
            pwr_val=float(pw.split()[0])
            pwr_str=f"{pwr_val:.1f} W" if pwr_val < 200 else "N/A"
        except:
            pwr_str="N/A"
    p=[x.strip() for x in raw.split(",")]
    gpu={"temp":f"{float(p[0]):.0f}°C","util":float(p[1]),
         "mem_used":f"{float(p[2])/1024:.1f}","mem_tot":f"{float(p[3])/1024:.1f} GB",
         "mem_pct":int(float(p[2])/float(p[3])*100),
         "clock":f"{float(p[4]):.0f} MHz","power":pwr_str}
except: pass

# ── RENDER ────────────────────────────────────────────────────────────────────
console.print()
console.print(Rule(style="bright_green"))

logo = Text(justify="center")
rows = [
    [("███╗   ██╗","bright_green"),("███████╗","green"),("██╗   ██╗","bright_green"),("██████╗ ","green"),(" ██████╗ ","bright_green")],
    [("████╗  ██║","bright_green"),("██╔════╝","green"),("██║   ██║","bright_green"),("██╔══██╗","green"),("██╔═══██╗","bright_green")],
    [("██╔██╗ ██║","bright_green"),("█████╗  ","green"),("██║   ██║","bright_green"),("██████╔╝","green"),("██║   ██║","bright_green")],
    [("██║╚██╗██║","bright_green"),("██╔══╝  ","green"),("██║   ██║","bright_green"),("██╔══██╗","green"),("██║   ██║","bright_green")],
    [("██║ ╚████║","bright_green"),("███████╗","green"),("╚██████╔╝","bright_green"),("██║  ██║","green"),("╚██████╔╝","bright_green")],
    [("╚═╝  ╚═══╝","dim green"), ("╚══════╝","dim green"),(" ╚═════╝","dim green"), ("╚═╝  ╚═╝","dim green"),(" ╚═════╝","dim green")],
]
for row in rows:
    for txt, sty in row:
        logo.append(txt, style=sty)
    logo.append("\n")

console.print(Align.center(logo))
sub = Text("  ◈  AI TERMINAL INTERFACE  ◈  ", justify="center")
sub.stylize("bold green")
console.print(Align.center(sub))
console.print()
console.print(Rule(style="bright_green"))
console.print()

g = Text(f"  {greet}  ", justify="center")
g.stylize(f"bold {mood}")
console.print(Panel(Align.center(g), border_style="green", box=box.HEAVY, padding=(0,1), expand=True))
console.print()

L = Table(box=None, show_header=False, padding=(0,1), expand=True)
L.add_column("k", style="bold green",   no_wrap=True, width=7)
L.add_column("v", style="bright_green", no_wrap=True)
L.add_row("DATE",   date_str)
L.add_row("TIME",   time_str)
L.add_row("USER",   os.environ.get("USER","kris").upper())
L.add_row("UPTIME", str(uptime))
L.add_row("", "")
L.add_row("NET ↓",  str(net_rx))
L.add_row("NET ↑",  str(net_tx))
L.add_row("SWAP",   str(swap_str))

left_panel = Panel(L, title="[bold bright_green]◈ SYSTEM[/bold bright_green]",
                   border_style="green", box=box.ROUNDED, padding=(0,1))

R = Table(box=None, show_header=False, padding=(0,0), expand=True)
R.add_column("k", style="bold green", no_wrap=True, width=5)
R.add_column("bar", no_wrap=True)
R.add_column("extra", style="dim green", no_wrap=True)

if HAS_PSUTIL:
    R.add_row("CPU", bar(int(cpu_pct)),  f"  {cpu_temp}  {freq_str}")
    R.add_row("",    Text(""),           "")
    R.add_row("RAM", bar(int(ram_pct) if isinstance(ram_pct,(int,float)) else 0),
                     f"  {ram_used}/{ram_tot}")
    R.add_row("",    Text(""),           "")

if gpu:
    R.add_row("GPU",  bar(int(gpu["util"])),  f"  {gpu['temp']}  {gpu['clock']}")
    R.add_row("VRAM", bar(gpu["mem_pct"]),     f"  {gpu['mem_used']}/{gpu['mem_tot']}")
    R.add_row("PWR",  Text(gpu["power"], style="bright_green"), "")
    R.add_row("",     Text(""),                "")

if isinstance(disk_pct, int):
    R.add_row("DISK", bar(disk_pct),  f"  {disk_used}/{disk_tot}")

right_panel = Panel(R, title="[bold bright_green]⚡ HARDWARE[/bold bright_green]",
                    border_style="bright_green", box=box.ROUNDED, padding=(0,1))

grid = Table.grid(expand=True, padding=(0,1))
grid.add_column(ratio=2)
grid.add_column(ratio=3)
grid.add_row(left_panel, right_panel)
console.print(grid)
console.print()

if top_procs:
    pt = Table(box=box.ROUNDED, border_style="green",
               title="[bold green]◈ TOP PROCESSES — by CPU[/bold green]",
               show_header=True, padding=(0,2), expand=True)
    pt.add_column("PID",     style="dim green",         width=7)
    pt.add_column("Process", style="bold bright_green", no_wrap=True)
    pt.add_column("CPU %",   style="bold yellow",       width=7, justify="right")
    pt.add_column("MEM %",   style="bold green",        width=7, justify="right")
    for p in top_procs:
        pt.add_row(str(p.get("pid","?")), (p.get("name") or "?")[:32],
                   f"{p.get('cpu_percent') or 0:.1f}%",
                   f"{p.get('memory_percent') or 0:.1f}%")
    console.print(pt)
    console.print()

q = Text(random.choice(quotes), style="italic dim green", justify="center")
console.print(Align.center(Panel(q, border_style="dim green", box=box.ROUNDED,
                                 padding=(0,2), expand=False)))
console.print()
console.print(Rule(style="dim green"))
console.print()
PYEOF

if [[ -f "$INTERACTIVE" && -x "$VENV_PYTHON" ]]; then
    "$VENV_PYTHON" "$INTERACTIVE"
fi
