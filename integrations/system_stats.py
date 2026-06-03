"""System stats — CPU, RAM, disk, top processes, network."""
import os
import subprocess
import shutil
from pathlib import Path


def system_stats() -> dict:
    """Return current system resource usage.

    Uses /proc filesystem and shell commands — works on Linux without psutil.
    """
    result: dict = {}

    # ── CPU ──
    try:
        with open("/proc/stat") as f:
            line = f.readline()
        fields = list(map(int, line.split()[1:]))
        total = sum(fields)
        idle = fields[3] + fields[4]  # idle + iowait
        result["cpu"] = {
            "usage_pct": round((1 - idle / total) * 100, 1),
            "cores": os.cpu_count(),
        }
        # load average
        load = os.getloadavg()
        result["cpu"]["load_1m"]  = round(load[0], 2)
        result["cpu"]["load_5m"]  = round(load[1], 2)
        result["cpu"]["load_15m"] = round(load[2], 2)
    except Exception as e:
        result["cpu"] = {"error": str(e)}

    # ── RAM ──
    try:
        meminfo = {}
        with open("/proc/meminfo") as f:
            for line in f:
                key, val = line.split(":")
                meminfo[key.strip()] = int(val.split()[0])  # kB
        total_mb  = meminfo["MemTotal"] // 1024
        avail_mb  = meminfo["MemAvailable"] // 1024
        used_mb   = total_mb - avail_mb
        result["memory"] = {
            "total_mb":    total_mb,
            "used_mb":     used_mb,
            "available_mb": avail_mb,
            "usage_pct":   round(used_mb / total_mb * 100, 1),
        }
    except Exception as e:
        result["memory"] = {"error": str(e)}

    # ── Disk ──
    try:
        disks = []
        for part in _disk_partitions():
            try:
                usage = shutil.disk_usage(part["mountpoint"])
                disks.append({
                    "device":     part["device"],
                    "mountpoint": part["mountpoint"],
                    "total_gb":   round(usage.total / 1e9, 1),
                    "used_gb":    round(usage.used / 1e9, 1),
                    "free_gb":    round(usage.free / 1e9, 1),
                    "usage_pct":  round(usage.used / usage.total * 100, 1),
                })
            except (PermissionError, OSError):
                pass
        result["disk"] = disks
    except Exception as e:
        result["disk"] = {"error": str(e)}

    # ── Top processes (by CPU) ──
    try:
        ps = subprocess.run(
            ["ps", "aux", "--sort=-%cpu"],
            capture_output=True, text=True, timeout=5
        )
        lines = ps.stdout.strip().splitlines()
        procs = []
        for line in lines[1:11]:  # skip header, top 10
            parts = line.split(None, 10)
            if len(parts) >= 11:
                procs.append({
                    "pid":  parts[1],
                    "cpu":  parts[2],
                    "mem":  parts[3],
                    "cmd":  parts[10][:60],
                })
        result["top_processes"] = procs
    except Exception as e:
        result["top_processes"] = {"error": str(e)}

    # ── Uptime ──
    try:
        with open("/proc/uptime") as f:
            secs = float(f.read().split()[0])
        days  = int(secs // 86400)
        hours = int((secs % 86400) // 3600)
        mins  = int((secs % 3600) // 60)
        result["uptime"] = f"{days}d {hours}h {mins}m"
    except Exception:
        pass

    return result


def _disk_partitions() -> list[dict]:
    partitions = []
    try:
        with open("/proc/mounts") as f:
            for line in f:
                parts = line.split()
                if len(parts) >= 2:
                    device, mountpoint = parts[0], parts[1]
                    if mountpoint.startswith("/") and not mountpoint.startswith("/sys") \
                            and not mountpoint.startswith("/proc") and not mountpoint.startswith("/dev"):
                        partitions.append({"device": device, "mountpoint": mountpoint})
    except Exception:
        pass
    return partitions[:6]
