"""Real-time Kanban + Cron web server"""
import http.server, json, subprocess, os, urllib.parse, re

PORT = 8321
HTML_PATH = r'C:\Users\decni\projects\hermes-kanban\kanban.html'

# Load DeepSeek API key from .env
DEEPSEEK_API_KEY = ''
env_path = r'C:\Users\decni\AppData\Local\hermes\.env'
if os.path.exists(env_path):
    with open(env_path) as f:
        for line in f:
            m = re.match(r'^DEEPSEEK_API_KEY=(.+)', line.strip())
            if m:
                DEEPSEEK_API_KEY = m.group(1).strip("'\"")
                break

class Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        
        if path == '/kanban.json':
            self.send_json(self._run('hermes', 'kanban', 'list', '--json', '--archived'))
        elif path == '/cron.json':
            self.send_json(self._parse_cron(self._run('hermes', 'cron', 'list')))
        elif path == '/balance.json':
            self.send_json(self._fetch_balance())
        elif path == '/' or path == '/kanban':
            self.send_html()
        else:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b'Not found')
    
    def _run(self, *cmd):
        try:
            r = subprocess.run(list(cmd), capture_output=True, text=True, timeout=10)
            return r.stdout or json.dumps({'error':'empty'})
        except Exception as e:
            return json.dumps({'error':str(e)})
    
    def _parse_cron(self, raw):
        jobs = []
        lines = raw.strip().split('\n')
        current = None
        for line in lines:
            raw_line = line
            l = line.strip()
            if not l or l.startswith('┌') or l.startswith('└') or l.startswith('│'):
                continue
            if l.startswith('(') or 'Scheduled Jobs' in l:
                continue
            
            # Job ID line: "  290ba24346ca [active]" (has leading spaces + bracket)
            if l[0].isalnum() and '[' in l and ']' in l and len(l) > 4:
                if current: jobs.append(current)
                current = {'id': l.split()[0], 'state': l.split('[')[1].split(']')[0], 'enabled': 'active' in l}
                continue
            
            if current is None:
                continue
                
            if 'Name:' in l:
                current['name'] = l.split('Name:')[1].strip()
            elif 'Schedule:' in l:
                current['schedule'] = l.split('Schedule:')[1].strip()
            elif 'Next run:' in l:
                current['next_run_at'] = l.split('Next run:')[1].strip()
            elif 'Last run:' in l:
                parts = l.split('Last run:')[1].strip()
                if 'never' in parts.lower():
                    current['last_run_at'] = None
                    current['last_status'] = None
                else:
                    # Remove trailing status word if present
                    ts = parts
                    status = 'ok'
                    for s in ['ok', 'fail']:
                        if parts.endswith('  '+s):
                            ts = parts[:-(len(s)+2)].strip()
                            status = s
                            break
                    current['last_run_at'] = ts
                    current['last_status'] = status
            elif 'Script:' in l:
                current['script'] = l.split('Script:')[1].strip()
            elif 'Mode:' in l:
                current['mode'] = l.split('Mode:')[1].strip()
        if current: jobs.append(current)
        return json.dumps(jobs)
    
    def _fetch_balance(self):
        try:
            if not DEEPSEEK_API_KEY:
                return json.dumps({'error': 'No API key'})
            import urllib.request
            req = urllib.request.Request(
                'https://api.deepseek.com/user/balance',
                headers={'Authorization': 'Bearer ' + DEEPSEEK_API_KEY}
            )
            with urllib.request.urlopen(req, timeout=10) as resp:
                return resp.read().decode()
        except Exception as e:
            return json.dumps({'error': str(e)})
    
    def send_json(self, data):
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Cache-Control', 'no-cache')
        self.end_headers()
        self.wfile.write(data.encode())
    
    def send_html(self):
        self.send_response(200)
        self.send_header('Content-Type', 'text/html')
        self.end_headers()
        if os.path.exists(HTML_PATH):
            with open(HTML_PATH) as f:
                self.wfile.write(f.read().encode())
        else:
            self.wfile.write(b'<h1>Page not found</h1>')
    
    def log_message(self, fmt, *args):
        pass

print(f'📋 Kanban + Cron server at http://localhost:{PORT}')
print(f'   Open on phone: http://192.168.3.72:{PORT}')
http.server.HTTPServer(('0.0.0.0', PORT), Handler).serve_forever()
