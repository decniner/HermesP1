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
Verification requirement: after every deploy, MUST HTTP-check (curl) before reporting ready. User corrected 'qa it and make sure its up' — never trust start command alone.
§
POGIBOT at ~/projects/POGIBOT/ — Flask + Gemini2.5Flash + DeepSeek VR boxing coach. Frontend:5500, backend:5001. Kanban t_ee1afc52.
§
Port 5000 is blocked by Universal.Server on this Windows machine — use 5001+ for Flask. serveo.net works for public tunnels (ssh -R 80:localhost:<port> serveo.net) where ngrok fails on Windows.
§
Gemini free tier: gemini-1.5-flash removed from API. gemini-2.5-flash works with free tier and supports video. Quotas are per-model — switching models can bypass rate limits.
§
Strong QA preference: must test everything end-to-end through the actual delivery mechanism (tunnel URL, LAN IP, etc.) before reporting to user. Never ask user to test something that wasn't verified independently. If it fails at any point, fix and re-test before reporting.