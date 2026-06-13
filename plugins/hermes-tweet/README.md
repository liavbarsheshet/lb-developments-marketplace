# hermes-tweet

Guides Hermes Agent X/Twitter work through Hermes Tweet with read-first workflows and approval-gated actions.

Hermes Tweet is a native Hermes Agent plugin for X/Twitter search, account reads,
monitoring, publishing, replies, likes, follows, DMs, draws, media, and trend
workflows. Use this Claude Code plugin when you need installation guidance,
operating rules, or safety checks for Hermes Tweet.

## Install Hermes Tweet

```bash
hermes plugins install Xquik-dev/hermes-tweet --enable
```

Set `XQUIK_API_KEY` in the Hermes runtime environment or `~/.hermes/.env`.
Keep `HERMES_TWEET_ENABLE_ACTIONS=false` unless the session intentionally allows
account-changing actions after explicit user approval.

## API

| Invocation | Mode | Description |
| --- | --- | --- |
| `/hermes-tweet:hermes-tweet` | Explicit | Load Hermes Tweet install, routing, and safety guidance for Hermes Agent X/Twitter workflows. |
| _"install Hermes Tweet in Hermes Agent"_ | Implicit | Explain the install path, enablement check, and runtime environment setup. |
| _"use X/Twitter from Hermes Agent"_ | Implicit | Choose read-first tool flow and keep action routes approval-gated. |
| _"debug Hermes Tweet tools"_ | Implicit | Check plugin enablement, `tweet_explore`, `tweet_read`, and `tweet_action` gating. |

## Operating Rules

- Use `tweet_explore` first to find the catalog-listed endpoint.
- Use `tweet_read` only for public read-only endpoints after `XQUIK_API_KEY` is configured.
- Use `tweet_action` only for writes, private reads, monitors, webhooks, extraction jobs, draws, or media operations after explicit approval.
- Never request or expose credentials in chat.
- Keep unattended, scheduled, gateway, and cron workflows read-only by default.

## Links

- [Hermes Tweet source](https://github.com/Xquik-dev/hermes-tweet)
- [Hermes Tweet package](https://pypi.org/project/hermes-tweet/)
- [Hermes Agent](https://github.com/NousResearch/hermes-agent)
