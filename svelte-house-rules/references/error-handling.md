# Error handling

Two surfaces: full-page errors (`+error.svelte`) and inline errors (banner / block). Both consume the same `humanizeStatus` map so the copy stays consistent.

## 45. Humanize status + code into copy. Don't render raw status.

Map HTTP status + short app-error code to a friendly title, body, and a recovery action. The codes are the short identifiers thrown via `error(401, 'unauthorized')`, `error(503, 'database_unavailable')`, etc.

```ts
// $lib/errors/humanize.ts
export type ErrorAction = { label: string; href: string };
export type HumanError = { title: string; body: string; action?: ErrorAction };

const CODE_COPY: Record<string, HumanError> = {
  unauthorized: {
    title: "You're signed out",
    body: 'Your session ended. Sign in to keep going.',
    action: { label: 'Sign in', href: '/account/login' },
  },
  forbidden: {
    title: "You don't have access",
    body: 'This area is reserved for a different role.',
    action: { label: 'Back home', href: '/' },
  },
  database_unavailable: {
    title: 'Temporarily unavailable',
    body: 'Our database is taking a short break. Please try again in a moment.',
  },
  // ...
};

const STATUS_COPY: Record<number, HumanError> = {
  401: { /* … */ },
  403: { /* … */ },
  404: { /* … */ },
  409: { title: 'Something just changed', body: 'Another change happened while you were here. Reload to see the latest state.' },
  429: { title: 'Too many requests', body: 'You did that a bit too quickly. Wait a moment, then try again.' },
  500: { /* … */ },
  503: { /* … */ },
};

export function humanizeStatus(status: number, code?: string): HumanError {
  if (code && CODE_COPY[code]) return CODE_COPY[code];
  if (STATUS_COPY[status]) return STATUS_COPY[status];
  return status >= 500 ? DEFAULT_5XX : DEFAULT_4XX;
}
```

Provide a **shell-specific variant** (`humanizeStatusAdmin`) that rewrites the recovery action — 401 in `/admin` should land on `/admin/login`, not the customer login. The base map stays one file; the variants just override the action.

## 46. `+error.svelte` reads `page.status` + `page.error.code` + `page.error.ref`

```svelte
<script lang="ts">
  import { page } from '$app/state';
  import { humanizeStatus } from '$lib/errors/humanize';

  const status = $derived(page.status);
  const code = $derived(page.error?.code);
  const ref = $derived(page.error?.ref);
  const copy = $derived(humanizeStatus(status, code));
</script>

<main class="app-root flex flex-col items-center justify-center px-6">
  <div class="glass flex w-full max-w-[420px] flex-col items-center gap-3 p-8 text-center">
    <div class="font-display text-7xl text-label-1" aria-hidden="true">{status}</div>
    <h1 class="font-display text-xl text-label-1">{copy.title}</h1>
    <p class="text-sm text-label-2">{copy.body}</p>
    {#if ref}
      <p class="font-mono text-[11px] text-label-3 uppercase">ref: {ref}</p>
    {/if}
    {#if copy.action}
      <a href={copy.action.href} class="btn-accent">{copy.action.label}</a>
    {:else}
      <button onclick={() => location.reload()} class="btn-accent">Try again</button>
    {/if}
  </div>
</main>
```

The `ref` is what `handleError` stamps on 5xx responses (see rule 47). Render it so users can paste it into a support ticket.

Per-shell error pages: `src/routes/+error.svelte` (customer), `src/routes/admin/+error.svelte` (admin), each importing the matching humanize variant.

## 47. `handleError` mirrors client + server. Stamp a ref on 5xx.

Both `hooks.server.ts` and `hooks.client.ts` define a `handleError`. The shape is identical so a `wrangler tail` grep and a DevTools console grep look the same. Only 5xx errors get a ref and a PostHog capture — 4xx are user-driven and noise in alerting.

```ts
// hooks.client.ts
import type { HandleClientError } from '@sveltejs/kit';
import { captureError } from '$lib/analytics';

export const handleError: HandleClientError = ({ error, event, status, message }) => {
  const isServer5xx = status >= 500;
  const ref = isServer5xx ? crypto.randomUUID().slice(0, 8) : undefined;

  if (isServer5xx) {
    console.error('[client error]', {
      ref,
      status,
      path: event.url.pathname,
      route: event.route?.id,
      message: error instanceof Error ? error.message : String(error),
    });
    void captureError(error, { ref, status, url: event.url.pathname, route: event.route?.id, source: 'client' });
  }

  return {
    message: isServer5xx ? 'Unexpected error' : message,
    code: isServer5xx ? undefined : message, // 4xx: `message` IS the short code thrown via error(403, 'forbidden')
    ref,
  };
};
```

Server `handleError` mirrors this but calls `serverCaptureError(err, ctx, event.platform)` so the PostHog flush rides on `platform.context.waitUntil(...)` (see `analytics.md`).

Declare the shape in `app.d.ts`:

```ts
declare namespace App {
  interface Error {
    message: string;
    code?: string;
    ref?: string;
  }
}
```

## 48. Inline error banner — drop-in for scattered `<p class="text-rose-300">` patterns

```svelte
<!-- $lib/components/ErrorBanner.svelte -->
<script lang="ts">
  import IconDanger from '~icons/solar/danger-triangle-linear';
  type Props = {
    message: string;
    dataTestid?: string;
    dataErrorCode?: string;
    class?: string;
  };
  let { message, dataTestid, dataErrorCode, class: klass = '' }: Props = $props();
</script>

<div
  role="alert"
  data-testid={dataTestid}
  data-error-code={dataErrorCode}
  class={`flex items-start gap-2 tint-surface px-3 py-2.5 text-sm text-label-1 tint-danger ${klass}`}
>
  <IconDanger class="mt-0.5 size-4 shrink-0 text-rose-300" aria-hidden="true" />
  <span class="leading-snug">{message}</span>
</div>
```

`data-error-code` is the discriminator e2e tests select on — the literal short code the server returned (`'rate_limited'`, `'slot_taken'`). Don't gate tests on copy strings.

## 49. Full-block error state — for sections that fail inside a working dashboard

When a dashboard's table fails but the rest of the page is fine, don't fall through to `+error.svelte` (lose all chrome). Render an in-place block instead:

```svelte
<!-- $lib/components/ErrorState.svelte -->
<script lang="ts">
  import IconDanger from '~icons/solar/danger-triangle-linear';
  type Props = {
    title?: string;
    message: string;
    onRetry?: () => void;
    class?: string;
  };
  let { title = "Couldn't load this", message, onRetry, class: klass = '' }: Props = $props();
</script>

<div role="alert" class={`glass-card flex flex-col items-center gap-3 rounded-2xl p-6 text-center ${klass}`}>
  <IconDanger class="size-7 text-rose-300" aria-hidden="true" />
  <div class="flex flex-col gap-1">
    <p class="text-sm font-semibold text-label-1">{title}</p>
    <p class="text-sm text-label-2">{message}</p>
  </div>
  {#if onRetry}
    <button type="button" onclick={onRetry} class="btn-secondary">Try again</button>
  {/if}
</div>
```

Pair with the remote function's `Result` discriminated union (see svelte-kit rule 13) — `{ ok: false, reason }` flows straight into `<ErrorState message={humanizeReason(reason)} onRetry={refetch} />`.
