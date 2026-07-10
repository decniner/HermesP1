Has a japanese-teacher Hermes profile + Telegram bot for learning Japanese.
§
Den — Filipino, Kawagoe Japan. IT: web dev & sys eng (Prometheus/Grafana/Ansible). Married, 3 kids (Chloe, Eya). 2 Shiba Inu: Bella (black), Pogi (red). Xiaomi 13T Pro, Toyota Vellfire, Pixel Watch 3. Thrill of the Fight 2 VR — wants brutal boxing critique, no sugarcoating. Values value-for-money, long-term thinking. Prefers tables, practical advice. PayPay user.
§
Workflow: ask clarifying Qs one at a time, no assumptions. EAs: DEN_EA folder + GitHub push always. Books: Phase 1 discovery → Phase 2 write → Phase 3 single HTML page-flip.
§
Delivery: prefers audio/voice for summaries kanban status, cron reports, briefings. Email HTML attachments for detailed reports.
§
Sensei & Pogi textbook repo: github.com/decniner/sensei-pogi-textbook. Skill interactive-study-html for bilingual JP/EN study tools.
§
POGIBOT at ~/projects/POGIBOT/ — Flask + Gemini3.5Flash + DeepSeek VR boxing coach. Cloudflare tunnel: https://garmin-microwave-exports-mesa.trycloudflare.com. SQLite history, model selector, file upload support. Backend:5001.
§
Port 5000 is blocked by Universal.Server on this Windows machine — use 5001+ for Flask. serveo.net works for public tunnels (ssh -R 80:localhost:<port> serveo.net) where ngrok fails on Windows.
§
Gemini free tier: gemini-1.5-flash removed from API. gemini-2.5-flash works with free tier and supports video. Quotas are per-model — switching models can bypass rate limits.
§
QA: must test full pipeline end-to-end through delivery mechanism before reporting. Never ask user to test unverified work.
§
Kanban: user expects projects/tasks to be tracked on the kanban board. Create and complete kanban tasks for deliverables.
§
BrutalMarketEngine at ~/projects/BrutalMarketEngine/ — Streamlit market analyzer (yfinance+ta) port 8501. POGIBOT project: Flask/Gemini3.5Flash/DeepSeek boxing coach with Cloudflare tunnel. Both served via cloudflared for remote access.