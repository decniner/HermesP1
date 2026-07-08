// Claude Code → OpenRouter proxy - v2 with model listing support
const http = require('http');
const https = require('https');

const PORT = 9099;
const OR_KEY = process.env.OPENROUTER_KEY || '';

// Map Claude model names to OpenRouter model names
const MODEL_MAP = {
  'claude-sonnet-4-6-20251014': 'qwen/qwen-2.5-coder-32b-instruct',
  'claude-sonnet-4-6': 'qwen/qwen-2.5-coder-32b-instruct',
  'claude-sonnet-4-20250515': 'qwen/qwen-2.5-coder-32b-instruct',
  'claude-3-5-sonnet-20241022': 'qwen/qwen-2.5-coder-32b-instruct',
  'claude-3-opus-20240229': 'deepseek/deepseek-chat',
  'claude-3-haiku-20240307': 'qwen/qwen-2.5-coder-32b-instruct',
  'claude-haiku-4-5-20251001': 'qwen/qwen-2.5-coder-32b-instruct',
  'claude-opus-4-8': 'deepseek/deepseek-chat',
  'claude-opus-4-8[1m]': 'deepseek/deepseek-chat',
  'claude-opus-4-7': 'deepseek/deepseek-chat',
  'claude-haiku-latest': 'qwen/qwen-2.5-coder-32b-instruct',
  'claude-sonnet-latest': 'qwen/qwen-2.5-coder-32b-instruct',
  'claude-opus-latest': 'deepseek/deepseek-chat',
};

const MODEL_LIST_RESPONSE = {
  data: Object.keys(MODEL_MAP).map(id => ({
    id,
    object: 'model',
    created: Date.now(),
    owned_by: 'openrouter-proxy',
    permission: [{allow_create_engine: false, allow_sampling: true, allow_logprobs: false, allow_search_indices: false, allow_view: true, allow_fine_tuning: false, organization: {id: ''}, group: null, is_blocking: false}],
    pricing: {prompt: '0', completion: '0'},
    root: id,
    parent: null,
    context_length: 128000,
  }))
};

const server = http.createServer((req, res) => {
  const logLine = `${req.method} ${req.url}`;
  console.log('→', logLine);

  // Model listing endpoint
  if (req.method === 'GET' && (req.url === '/v1/models' || req.url.startsWith('/v1/models?'))) {
    res.writeHead(200, {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'});
    res.end(JSON.stringify(MODEL_LIST_RESPONSE));
    return;
  }

  // Messages endpoint
  if (req.method === 'POST' && req.url === '/v1/messages') {
    let body = '';
    req.on('data', chunk => body += chunk);
    req.on('end', () => {
      try {
        const data = JSON.parse(body);
        const origModel = data.model;
        const mappedModel = MODEL_MAP[origModel] || 'qwen/qwen-2.5-coder-32b-instruct';
        console.log(`  Model: ${origModel} → ${mappedModel}`);

        data.model = mappedModel;

        const apiKey = req.headers['x-api-key'] || OR_KEY;
        if (!apiKey) {
          res.writeHead(401, {'Content-Type': 'application/json'});
          res.end(JSON.stringify({error: {message: 'No API key. Set x-api-key header or OPENROUTER_KEY env var.'}}));
          return;
        }

        const opts = {
          hostname: 'openrouter.ai',
          path: '/api/v1/messages',
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${apiKey}`,
            'anthropic-version': '2023-06-01',
          }
        };

        const proxyReq = https.request(opts, proxyRes => {
          console.log(`  Response: ${proxyRes.statusCode}`);
          let respBody = '';
          proxyRes.on('data', c => respBody += c);
          proxyRes.on('end', () => {
            res.writeHead(proxyRes.statusCode, proxyRes.headers);
            res.end(respBody);
          });
        });

        proxyReq.on('error', e => {
          console.error('  Error:', e.message);
          res.writeHead(502, {'Content-Type': 'application/json'});
          res.end(JSON.stringify({error: {message: e.message}}));
        });

        proxyReq.write(JSON.stringify(data));
        proxyReq.end();
      } catch (e) {
        console.error('  Parse error:', e.message);
        res.writeHead(400, {'Content-Type': 'application/json'});
        res.end(JSON.stringify({error: {message: 'Bad request: ' + e.message}}));
      }
    });
    return;
  }

  // Health check
  if (req.url === '/health') {
    res.writeHead(200, {'Content-Type': 'text/plain'});
    res.end('OK');
    return;
  }

  res.writeHead(404);
  res.end();
});

server.listen(PORT, () => {
  console.log(`\nClaude Code → OpenRouter proxy running on :${PORT}`);
  console.log(`Set: ANTHROPIC_BASE_URL=http://localhost:${PORT}`);
  console.log(`Set: ANTHROPIC_API_KEY=sk-or-v1-...\n`);
});
