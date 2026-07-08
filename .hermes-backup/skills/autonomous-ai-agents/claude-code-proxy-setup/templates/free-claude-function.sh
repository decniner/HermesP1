# Add to ~/.bashrc or ~/.zshrc
# Enables: free-claude "your prompt"

free-claude() {
    export ANTHROPIC_BASE_URL="http://127.0.0.1:8082"
    export ANTHROPIC_API_KEY="bypassed-via-local-proxy"
    export ANTHROPIC_MODEL="claude-3-5-sonnet-20241022"
    export ENABLE_TOOL_SEARCH=true
    claude "$@"
}
