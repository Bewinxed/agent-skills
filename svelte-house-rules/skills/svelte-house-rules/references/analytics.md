# Analytics (PostHog)

Both client and server route every capture through a thin wrapper. The wrapper survives missing config (dev without a PostHog project) and SSR safety (no `window` at import time).

## 50. Client wrapper: lazy import, single init, no-op without key

```ts
// $lib/analytics.ts
import { browser } from '$app/environment';
import { env as publicEnv } from '$env/dynamic/public';

let initialised = false;

async function ph() {
  if (!browser) return null;                          // SSR-safe — never touches window
  if (!publicEnv.PUBLIC_POSTHOG_KEY) return null;     // dev without a project — no-op everywhere
  const mod = await import('posthog-js');             // lazy: posthog-js stays out of SSR bundle
  const posthog = mod.default;
  if (!initialised) {
    posthog.init(publicEnv.PUBLIC_POSTHOG_KEY, {
      // Same-origin reverse proxy through hooks.server.ts → recovers
      // the 30–50% of events that content blockers drop when posthog-js
      // calls *.posthog.com directly.
      api_host: '/ingest',
      // ui_host stays public so "view in PostHog" deep-links from the
      // toolbar still target the real dashboard, not our proxy.
      ui_host: publicEnv.PUBLIC_POSTHOG_HOST ?? 'https://eu.i.posthog.com',
      // Version-pinned defaults — opts into Error Tracking autocapture
      // ($exception events from window.onerror + unhandled rejections)
      // without auto-opting into whatever PostHog flips on next.
      defaults: '2026-01-30',
      // SvelteKit client nav doesn't fire a real pageview; afterNavigate
      // in +layout.svelte captures `page_viewed` manually. Auto would double-count.
      capture_pageview: false,
      capture_pageleave: true,
      persistence: 'localStorage+cookie',
      session_recording: { maskAllInputs: false },
    });
    initialised = true;
  }
  return posthog;
}

export async function captureEvent(name: string, properties: Record<string, unknown> = {}) {
  const p = await ph();
  if (!p) return;
  p.capture(name, properties);
}

export async function identifyCustomer(phoneE164: string, props: { name?: string; email?: string | null } = {}) {
  const p = await ph();
  if (!p) return;
  p.identify(phoneE164, { name: props.name, email: props.email ?? undefined });
}

export async function captureError(err: unknown, ctx: Record<string, unknown> = {}) {
  const p = await ph();
  if (!p) return;
  p.captureException(err, ctx);
}

export async function resetAnalytics() {
  const p = await ph();
  if (!p) return;
  p.reset();
}
```

Three properties of this wrapper are load-bearing:

- **Dynamic `import('posthog-js')`** — keeps the SDK out of the SSR bundle. Importing it eagerly inside any module that touches `$lib/analytics` would crash workers / SSR.
- **`api_host: '/ingest'`** — a same-origin reverse proxy in `hooks.server.ts` that forwards to `eu.i.posthog.com`. Recovers events lost to ad blockers / tracker lists.
- **`defaults: 'YYYY-MM-DD'`** — version-pinned defaults profile. Reviews and bumps are explicit; PostHog flipping a new default on doesn't surprise prod.

Customer flow stays anonymous until `identifyCustomer({ phone, … })` fires from contact-form submit. Use E.164 phone (no `+`) as the distinct_id so prior anonymous events merge. Admin uses the admin row id; calls `identifyAdmin` on login success and `resetAnalytics` on logout.

## 51. Server wrapper: build fresh per call, flush via `waitUntil`

Workers have no long-lived process — PostHog's batching wants `flushAt: 1, flushInterval: 0` to send the single event before the request ends, and the shutdown promise must ride on `platform.context.waitUntil(...)` to actually complete.

```ts
// $lib/server/analytics.ts
import { PostHog } from 'posthog-node';
import { env as publicEnv } from '$env/dynamic/public';

export type ErrorContext = {
  ref?: string;
  status?: number;
  url?: string;
  route?: string | null;
  distinctId?: string;
} & Record<string, unknown>;

export function serverCaptureError(
  err: unknown,
  ctx: ErrorContext,
  platform: App.Platform | undefined,
): void {
  if (!publicEnv.PUBLIC_POSTHOG_KEY) return;
  const { distinctId, ...properties } = ctx;
  const posthog = new PostHog(publicEnv.PUBLIC_POSTHOG_KEY, {
    host: publicEnv.PUBLIC_POSTHOG_HOST ?? 'https://eu.i.posthog.com',
    flushAt: 1,
    flushInterval: 0,
  });
  posthog.captureException(err, distinctId ?? 'server', properties);
  const shutdown = posthog.shutdown();
  if (platform?.context?.waitUntil) {
    platform.context.waitUntil(shutdown);
  } else {
    void shutdown.catch(() => {});
  }
}
```

Use the **public** project token (`PUBLIC_POSTHOG_KEY`) on the server too — PostHog project tokens are write-only and safe to share. The personal API key (`POSTHOG_PERSONAL_API_KEY`) is for management scripts only, never request handlers.

## 52. Event taxonomy: register, describe, verify

PostHog auto-creates event definitions on first capture, but the description / verified / tags fields stay blank until they're PATCHed via the management API. A `scripts/posthog/register-events.ts` script keeps the catalog authoritative:

```ts
interface EventDef { name: string; description: string; tags?: string[]; }

const CATALOG: EventDef[] = [
  { name: 'page_viewed', description: 'SvelteKit afterNavigate pageview …' },
  { name: 'booking_initiated', description: '…' },
  // … keep in sync with captureEvent('…') call sites — `rg "captureEvent\(['\"]"`
];
```

The script:
1. Resolves the current project via `/api/projects/@current/`.
2. Seeds any missing definitions with a synthetic capture (tagged `$is_event_registration: true` so they're trivially filterable out of dashboards) — PostHog needs the event to exist before it can be PATCHed.
3. PATCHes each definition with `description` + `verified: true`. Tags require a paid plan; degrade gracefully if rejected.

Re-run after adding new `captureEvent(...)` call sites. PostHog-reserved events (`$pageview`, `$exception`, `$identify`) are managed by PostHog and excluded from the catalog.

Other scripts that pair with this:

- `provision-insights.ts` — sets up dashboards / insights / alerts from code.
- `sync-project-settings.ts` — syncs project-level config (autocapture allowlist, group analytics, etc.).
- `annotate-deploy.ts` — runs after `wrangler deploy` to post a deploy annotation to PostHog so funnel anomalies line up against releases.

## 53. Capture errors in 5xx paths only

`captureError` (client) and `serverCaptureError` (server) fire from the matching `handleError` (see error-handling rule 47). 4xx errors are user-driven (not signed in, hit rate limit, mistyped URL) — capturing them inflates error rates and drowns real signal. The `handleError` branch on `status >= 500` is the only call site that should hit `captureException`.

PostHog autocapture already catches `window.onerror` and unhandled promise rejections (via the `defaults` profile). The explicit `captureException` calls exist because SvelteKit `load` / render failures swallow exceptions before they reach those handlers.
