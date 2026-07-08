# Security Monitoring Agent — Cron-Based Behavioral Baseline Pattern

A reusable pattern for building a personal PC security monitor using cron jobs, Python scripts, a SQLite baseline database, a real-time web dashboard, and Telegram alerting.

## Architecture

```
┌─ Cron Job (every 15 min) ──────────────────┐
│ Python script (security_agent.py)            │
│ 1. Run scans: processes, network, files,    │
│    Windows security events                   │
│ 2. Compare against SQLite baseline           │
│ 3. If LEARNING phase → add to baseline       │
│ 4. If MONITORING phase → alert on NEW items  │
│ 5. Output report (stdout)                    │
└─────────────────────────────────────────────┘
         ↓ stdout captured by cron
┌─ Delivery ─────────────────────────────────┐
│ If LEARNING: output saved, no Telegram msg  │
│ If MONITORING: new items → Telegram alert   │
│ Sample alert sent once early in learning    │
└─────────────────────────────────────────────┘

┌─ Dashboard (Python HTTP server) ──────────┐
│ /api/status  — phase, stats, alert count   │
│ /api/alerts — recent alerts with details   │
│ /api/log    — activity log                  │
│ /api/start-monitoring — switch to MONITOR   │
│ /dashboard  — HTML page (auto-refresh 5s)  │
└─────────────────────────────────────────────┘
```

## Two-Phase Design

### Learning Phase
- Runs from first launch until user clicks "START MONITORING"
- Every scan: records every process, connection, file, and event into SQLite
- Builds a "baseline" of what's normal for THIS PC
- Sends exactly ONE sample alert so the user knows the format
- Dashboard shows: phase label, baseline event count, stats grid, "START MONITORING" button

### Monitoring Phase
- Triggered by: dashboard "START MONITORING" button → sets state.json phase="monitoring"
- Every scan: compares current state against baseline
- Any NEW item (not in baseline) → real alert to Telegram
- Dashboard shows: phase label, alert list, no start button

## Database Schema (SQLite)

```sql
baseline_processes(name, path, first_seen, last_seen, count)
baseline_connections(remote_ip, remote_port, process_name, first_seen, last_seen, count)
baseline_files(path, action, first_seen, last_seen, count)
baseline_events(event_id, source, provider, first_seen, last_seen, count)
alerts(id, type, severity, title, detail, timestamp, investigated)
log(id, type, detail, timestamp)
```

## State Management (state.json)

```json
{"phase": "learning", "started": "ISO8601", "learning_events": 42, "sample_sent": true}
```

## Private IP Filtering (Critical)

When scanning network connections via `netstat -ano`, local LAN traffic (192.168.x.x, 10.x.x.x, 172.x.x.x) dominates the output. These must be filtered OUT during both learning and monitoring to avoid false positives:

```python
if ip.startswith('192.168.') or ip.startswith('10.') or ip.startswith('172.'): continue
if ip.endswith('.255') or ip.startswith('224.') or ip.startswith('239.'): continue
```

Without this filter, the baseline fills with ephemeral LAN connections (port 50,000+) and every monitoring scan triggers 50+ false alerts.

## Deliverables

| Component | File | Purpose |
|-----------|------|---------|
| Scanner | `~/.hermes/scripts/security_agent.py` | Runs scans, manages baseline, outputs alerts |
| Dashboard server | `~/projects/security-monitor/dashboard_server.py` | Serves JSON API + HTML at port 8322 |
| Dashboard HTML | `~/projects/security-monitor/dashboard.html` | Real-time web UI with collapsible About section |
| Cron job | `cronjob(schedule='*/15 * * * *', script='security_agent.py', no_agent=True)` | Periodic scanning + delivery |

## Collapsible About Section

The dashboard includes a detailed "About This Monitor" section (collapsed by default) that explains:
- What the monitor does (in plain language)
- How it works (learning → monitoring)
- How it was built (Python, SQLite, cron, Hermes)
- What data is stored and where
- Limitations (behavioral baseline, not antivirus)

This is essential for users who want to understand the system without reading the script files.
