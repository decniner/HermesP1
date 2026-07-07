"""Security Agent Dashboard — Web UI"""
import http.server, json, sqlite3, os, subprocess, urllib.parse
from pathlib import Path
from datetime import datetime

PORT = 8322
DB = str(Path.home() / 'AppData' / 'Local' / 'hermes' / 'security-agent' / 'baseline.db')
STATE = str(Path.home() / 'AppData' / 'Local' / 'hermes' / 'security-agent' / 'state.json')
HTML_PATH = str(Path.home() / 'projects' / 'security-monitor' / 'dashboard.html')

class Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        
        if path == '/api/status':
            self.send_json(self.get_status())
        elif path == '/api/alerts':
            self.send_json(self.get_alerts())
        elif path == '/api/log':
            self.send_json(self.get_log())
        elif path == '/api/baseline':
            self.send_json(self.get_baseline())
        elif path == '/api/start-monitoring':
            self.start_monitoring()
            self.send_json({'success': True})
        elif path == '/' or path == '/dashboard':
            self.send_html()
        else:
            self.send_response(404); self.end_headers(); self.wfile.write(b'Not found')
    
    def get_status(self):
        state = {'phase': 'learning', 'started': '-', 'events': 0}
        if os.path.exists(STATE):
            with open(STATE) as f:
                try: state = json.load(f)
                except: pass
        stats = {'processes': 0, 'connections': 0, 'files': 0, 'events': 0}
        if os.path.exists(DB):
            try:
                conn = sqlite3.connect(DB)
                c = conn.cursor()
                stats['processes'] = c.execute('SELECT COUNT(*) FROM baseline_processes').fetchone()[0]
                stats['connections'] = c.execute('SELECT COUNT(*) FROM baseline_connections').fetchone()[0]
                stats['files'] = c.execute('SELECT COUNT(*) FROM baseline_files').fetchone()[0]
                stats['events'] = c.execute('SELECT COUNT(*) FROM baseline_events').fetchone()[0]
                alerts = c.execute('SELECT COUNT(*) FROM alerts').fetchone()[0]
                conn.close()
            except: pass
        return {'phase': state.get('phase', 'learning'), 'started': state.get('started', '-'),
                'events': state.get('learning_events', 0), 'stats': stats, 'alerts': alerts}
    
    def get_alerts(self):
        if not os.path.exists(DB): return []
        try:
            conn = sqlite3.connect(DB)
            conn.row_factory = sqlite3.Row
            rows = conn.execute('SELECT * FROM alerts ORDER BY timestamp DESC LIMIT 50').fetchall()
            conn.close()
            return [dict(r) for r in rows]
        except: return []
    
    def get_log(self):
        if not os.path.exists(DB): return []
        try:
            conn = sqlite3.connect(DB)
            conn.row_factory = sqlite3.Row
            rows = conn.execute('SELECT * FROM log ORDER BY timestamp DESC LIMIT 50').fetchall()
            conn.close()
            return [dict(r) for r in rows]
        except: return []
    
    def get_baseline(self):
        if not os.path.exists(DB): return {'processes':[],'connections':[],'files':[],'events':[]}
        try:
            conn = sqlite3.connect(DB)
            conn.row_factory = sqlite3.Row
            result = {
                'processes': [dict(r) for r in conn.execute('SELECT * FROM baseline_processes ORDER BY count DESC LIMIT 30')],
                'connections': [dict(r) for r in conn.execute('SELECT * FROM baseline_connections ORDER BY count DESC LIMIT 30')],
                'files': [dict(r) for r in conn.execute('SELECT * FROM baseline_files ORDER BY last_seen DESC LIMIT 20')],
                'events': [dict(r) for r in conn.execute('SELECT * FROM baseline_events ORDER BY count DESC LIMIT 20')],
            }
            conn.close()
            return result
        except: return {'processes':[],'connections':[],'files':[],'events':[]}
    
    def start_monitoring(self):
        if os.path.exists(STATE):
            with open(STATE) as f:
                state = json.load(f)
            state['phase'] = 'monitoring'
            state['monitoring_started'] = datetime.now().isoformat()
            with open(STATE, 'w') as f:
                json.dump(state, f, indent=2)
    
    def send_json(self, data):
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Cache-Control', 'no-cache')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())
    
    def send_html(self):
        self.send_response(200)
        self.send_header('Content-Type', 'text/html')
        self.end_headers()
        if os.path.exists(HTML_PATH):
            with open(HTML_PATH) as f:
                self.wfile.write(f.read().encode())
        else:
            self.wfile.write(b'<h1>Dashboard page not found</h1>')
    
    def log_message(self, fmt, *args): pass

print(f'🔒 Security Agent Dashboard at http://localhost:{PORT}')
print(f'   Open on phone: http://192.168.3.72:{PORT}/dashboard')
http.server.HTTPServer(('0.0.0.0', PORT), Handler).serve_forever()
