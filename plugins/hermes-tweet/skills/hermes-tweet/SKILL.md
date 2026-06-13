---
name: hermes-tweet
description: Use when installing, configuring, debugging, or operating Hermes Tweet, the native Hermes Agent X/Twitter plugin for read-first social workflows and approval-gated actions.
---

# Hermes Tweet

Use this skill when the user wants Hermes Agent to inspect or automate X/Twitter
through Hermes Tweet.

## Workflow

1. Confirm the user wants Hermes Agent, Hermes Tweet, X/Twitter research, social listening, monitoring, publishing, replies, likes, follows, DMs, draws, media, or trends.
2. For installation, recommend `hermes plugins install Xquik-dev/hermes-tweet --enable`.
3. Tell the user to set `XQUIK_API_KEY` in the Hermes runtime environment or `~/.hermes/.env`; never ask for the key value in chat.
4. Keep `HERMES_TWEET_ENABLE_ACTIONS=false` unless the session intentionally allows account-changing actions after explicit user approval.
5. Use `tweet_explore` first to find a catalog-listed endpoint.
6. Use `tweet_read` only after the endpoint is known and read-only.
7. Use `tweet_action` only for writes, private reads, monitors, webhooks, extraction jobs, draws, or media operations after stating the exact endpoint, payload, and approval reason.

## Checks

- If Hermes lists the plugin as not enabled, run `hermes plugins enable hermes-tweet`.
- If tools are missing, run `hermes tools list` and confirm the `hermes-tweet` toolset is enabled.
- If `tweet_read` is missing, confirm `XQUIK_API_KEY` is configured where Hermes code executes.
- If `tweet_action` is missing, confirm `HERMES_TWEET_ENABLE_ACTIONS=true` only for the approved session.
- If a remote gateway profile is used, configure Hermes Tweet on the remote Hermes host.

## Safety

- Never pass credentials in tool arguments.
- Never include credentials in examples, logs, prompts, issue bodies, or tool input.
- Do not guess endpoint paths.
- Do not retry writes through alternate routes after a policy, auth, or account state error.
- Keep unattended, scheduled, gateway, and cron workflows read-only by default.
