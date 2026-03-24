---
phase: 4
level: 2
researched_at: 2026-03-24
---

# Phase 4 Research: Coolify Networking

## Questions Investigated
1. Why can't the bot container resolve `lavalink:2333`?
2. How does Coolify handle Docker Compose multi-service networking?
3. What is the correct way to deploy both services so they can talk to each other?

## Findings

### Root Cause
`[Name or service not known]` = Docker DNS cannot resolve the hostname `lavalink`. This happens when the two containers are **not on the same Docker network**. Docker's embedded DNS (`127.0.0.11`) only resolves container names for containers sharing a user-defined network.

**Most likely scenario:** Lavalink and the bot were deployed as **separate Coolify resources/applications**, which puts them on separate auto-generated networks.

### How Coolify Networks Work

| Deployment Type | Network Behavior |
|-----------------|-----------------|
| Both services in ONE Docker Compose resource | ✅ Single shared network, service names resolve naturally (`lavalink:2333` works) |
| Each service as a SEPARATE Coolify resource | ❌ Separate networks, service names don't resolve across them |
| Separate resources + "Connect to Predefined Network" | ⚠️ Works, but Coolify renames services to `lavalink-<uuid>` |

### Recommended Fix: Single Docker Compose Resource

Deploy **both** `lavalink` and `music_bot` as **one resource** from the same `docker-compose.yml`. Coolify auto-creates a shared network for all services in one Compose file:
- Services reference each other by service name (`LAVALINK_HOST=lavalink`)
- No UUID suffixes needed
- Clean and maintainable

**Sources:**
- [Coolify Docs — Service Discovery](https://coolify.io/docs)
- [Coolify GitHub Issues — Cross-Stack Networking](https://github.com/coollabsio/coolify/issues)

**Recommendation:** Delete any separate lavalink/bot resources in Coolify. Redeploy as ONE Docker Compose resource pointing to this repo.

### Docker Compose Network Verification
Our current `docker-compose.yml` correctly defines a shared `lavalink_network` with both services on it. The fix is purely a **Coolify deployment configuration** issue, not a code issue.

However, there is one improvement: add an explicit `healthcheck` on the `lavalink` service so `depends_on` can wait for Lavalink to be *ready* (not just started). This prevents the race condition where the bot starts before Lavalink is accepting connections.

## Decisions Made
| Decision | Choice | Rationale |
|----------|--------|-----------|
| Deployment topology | Single Compose resource | Simplest, most reliable; service names work naturally |
| Lavalink readiness | Add healthcheck | `depends_on: condition: service_healthy` ensures bot starts after Lavalink is ready |
| Network naming | Keep `lavalink_network` | Explicit network definition is fine and recommended |

## Changes Required

### `docker-compose.yml`
Add `healthcheck` to `lavalink` service + update `depends_on` in `bot` service:
```yaml
lavalink:
  healthcheck:
    test: ["CMD-SHELL", "curl -f http://localhost:2333/version || exit 1"]
    interval: 15s
    timeout: 5s
    retries: 5
    start_period: 30s

bot:
  depends_on:
    lavalink:
      condition: service_healthy
```

## Anti-Patterns to Avoid
- Deploying as separate Coolify resources and using "Connect to Predefined Network" — adds UUID suffix complexity
- Setting `LAVALINK_HOST` to a container IP — IPs change on restart

## Ready for Planning
- [x] Root cause identified (separate Coolify resources = separate networks)
- [x] Correct deployment approach selected (single Compose resource)
- [x] docker-compose.yml improvement identified (healthcheck)
- [x] No code changes needed in bot.py
