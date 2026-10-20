# Proxy Setup

## When to recommend a proxy

A proxy is optional for a small validation or shallow crawl. Recommend considering one for many queries, higher concurrency, grid coverage, repeated crawls, or when Google blocks the local connection. Explain that provider quality, geography, volume, and Google behavior all affect results.

## Provider choice

The skill does not recommend or link to proxy vendors. If the user asks which provider to use, say that provider quality, geography, and price vary, and suggest they compare providers themselves before entering a URL.

## Credential entry

Run:

```bash
bash "$SKILL_DIR/scripts/configure-proxy.sh"
```

The helper accepts HTTP, HTTPS, SOCKS5, and SOCKS5H URLs. The user enters one URL at a time and submits a blank entry to finish.

If interactive input is unavailable through the agent's terminal tool, give the user the command above to run in their own terminal. Wait for completion and continue using only the resulting file path. Never ask them to paste the proxy URL into chat as a fallback.

The file is stored at:

```text
${XDG_CONFIG_HOME:-$HOME/.config}/google-maps-scraper/proxies.txt
```

It is plaintext protected by `0600` filesystem permissions. Never open or print it. The helper prints the command the user can use to remove it.
