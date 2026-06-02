# Cloudflare Workers + live events

## 35. Self-dispatch via service binding for cron / internal POSTs

A worker fetching its own public hostname triggers CF's loop detection (522). Use a service binding bound to the worker itself, then `event.platform.env.SELF.fetch(...)`:

```jsonc
// wrangler.jsonc
"services": [{ "binding": "SELF", "service": "your-worker-name" }]
```

```ts
// scheduled() in $lib/server/index.ts
export async function scheduled(event, env) {
  await env.SELF.fetch('https://internal/api/cron/cleanup', { method: 'POST' });
}
```

## 36. CSRF: allowlist legitimate cross-origin POSTs

SvelteKit's built-in `csrf.checkOrigin` blocks any cross-origin form POST — too aggressive for payment-gateway callbacks, OAuth returns, webhook deliveries. Pattern: disable the built-in in `svelte.config.js`, re-implement in `hooks.server.ts` with a path allowlist.

```ts
const CSRF_ALLOWLIST = new Set<string>(['/api/payment/callback']);
const GUARDED_CT = new Set([
  'application/x-www-form-urlencoded',
  'multipart/form-data',
  'text/plain',
]);

function isCsrfBlocked(request: Request, url: URL, pathname: string): boolean {
  if (!['POST','PUT','PATCH','DELETE'].includes(request.method)) return false;
  if (CSRF_ALLOWLIST.has(pathname)) return false;
  const ct = (request.headers.get('content-type') ?? '').split(';')[0].trim().toLowerCase();
  if (!GUARDED_CT.has(ct)) return false;
  return request.headers.get('origin') !== url.origin;
}
```

Allowlisted endpoints authenticate by other means (HMAC signature, shared secret).

## 37. SSR-disabled routes still get OG meta via `transformPageChunk`

Routes that disable SSR (e.g. anything using `@threlte/core`, since three.js can't SSR) can't use `<svelte:head>` for the initial HTML response — the head is rendered client-side after hydration, after social crawlers have already scraped. Inject in `hooks.server.ts`:

```ts
export const handle: Handle = ({ event, resolve }) => {
  if (event.url.pathname.startsWith('/share-route/')) {
    const { title, description, image } = computeOg(event);
    return resolve(event, {
      transformPageChunk: ({ html }) =>
        html.replace(
          '</head>',
          `<meta property="og:title" content="${escapeHtml(title)}" />
           <meta property="og:description" content="${escapeHtml(description)}" />
           <meta property="og:image" content="${escapeHtml(image)}" />
           </head>`
        ),
    });
  }
  return resolve(event);
};
```

Static OG images on R2 (or any CDN) + personalized title/description via this path is the working pattern. **Don't** reach for satori / resvg-wasm / workers-og — runtime WASM is blocked on the standard CF Workers tier.

## 38. Rate-limit counters: Durable Object with atomic `checkAndIncrement`

A single global DO with one method that atomically checks a set of keys against their limits and increments. Wrong shape: per-key DOs (each one is a request hop). Right shape: one DO, one batched RPC, one storage transaction.

```ts
// $lib/server/abuse.ts
export interface AbuseKey { key: string; limit: number; windowSeconds: number; }
export type AbuseResult = { ok: true } | { ok: false; violated: string };

export async function checkAndIncrement(
  platform: App.Platform | undefined,
  keys: AbuseKey[]
): Promise<AbuseResult> {
  return hubClient(platform).checkAndIncrement(keys);
}
```

Compose keys per flow (e.g. `holds:active:session:{sid}`, `attempts:ip:{ip}:hour:{floor(epoch/3600)}`). Surface the violated key to the caller so error messages can be specific.

## 39. Live events: typed event bus via `river.ts`

```ts
// $lib/hub-events.ts
import { RiverEvents } from 'river.ts';

const eventShape = {
  data: {} as { assetId: string; payload: Record<string, unknown> },
};

export const hubEvents = new RiverEvents()
  .defineEvent('thing_held', eventShape)
  .defineEvent('thing_confirmed', eventShape)
  .defineEvent('thing_cancelled', eventShape)
  .build();

export type HubEventName = 'thing_held' | 'thing_confirmed' | 'thing_cancelled';
```

Server broadcasts via `hubEvents.broadcast(name, payload)`. Client subscribes via `hubEvents.on(name, cb)`. The shape file is the single source of truth — drift between server emitter and client subscriber is a type error, not a runtime mystery.

When live counters are needed alongside event fan-out, the DO can host both — but RPC counters and SSE broadcasts can also split cleanly if the DO is busy.
