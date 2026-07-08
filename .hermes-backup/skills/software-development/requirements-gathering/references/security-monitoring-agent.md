# PC Security Monitoring Agent (Personal Windows)

Architecture and patterns from building a personal PC security monitoring agent with learning phase, real-time dashboard, cron-driven scanning, and Telegram alerting.

## Overview

A multi-component system that:
1. **Learns** normal behavior on a Windows PC (processes, connections, files, events)
2. **Monitors** for anomalies after learning phase is complete
3. **Alerts** via Telegram on high-confidence threats
4. **Displays** real-time status via web dashboard

## Architecture

Cron Job (every 15 min) -> security_agent.py scanning processes/connections/files/events -> SQLite baseline.db
Web Server (dashboard_server.py port 8322) -> REST API -> HTML dashboard
State (state.json): phase = learning | monitoring

## Two-Phase Design

### Phase 1: Learning
- Runs silently building baseline of normal behavior
- Every new item logged to baseline tables
- Sample alert sent for user to review format
- User says "start monitoring" to transition

### Phase 2: Monitoring
- Same scans, new items trigger Telegram alerts
- Dashboard shows alert count and details

## Scan Sources

| Scan | Command | Detects |
|------|---------|---------|
| Processes | tasklist /FO CSV | New executables |
| Connections | netstat -ano | New outbound connections |
| Files | os.listdir() on Temp/Desktop/Downloads | .exe/.dll/.ps1/.bat/.vbs/.js/.scr |
| Events | wevtutil qe Security | Failed logins (Event 4625) |

## Dashboard Web UI
- Dark theme, auto-refresh 5s
- Status bar: Phase + event counts
- Start Monitoring button (learning only)
- Stats grid: processes/connections/files/events
- Alerts section with severity coloring
- Activity log

## Files
- security_agent.py: scanning script (cron-executed)
- dashboard_server.py: web server
- dashboard.html: UI
- baseline.db: auto-created SQLite
- state.json: phase state

## Pitfalls
1. Tasklist output varies by locale - CSV parser with strip('"') handles both
2. wevtutil slow - limit queries with /c:5
3. Phase state persists - no undo button on dashboard
4. Dashboard server killed by taskkill /F /IM python.exe - no auto-restart