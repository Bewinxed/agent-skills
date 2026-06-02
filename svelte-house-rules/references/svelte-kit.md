# Svelte / SvelteKit engineering

## 8. Reach for `svelte/reactivity` primitives before mirroring state

When the natural shape is "a reactive version of a standard browser/JS object," check `svelte/reactivity` first:

- `SvelteURL`, `SvelteURLSearchParams`
- `SvelteMap`, `SvelteSet`, `SvelteDate`
- `MediaQuery`, `createSubscriber`

A `$state` mirror + imperative `syncFromX()` method around a built-in object is reinventing a worse version of these. Single source of truth in one reactive object beats two-copy patterns with sync points. `createSubscriber` is the escape hatch for event-based external APIs.

Symptom this rule prevents: `page.url` lagging `location.href` after `replaceState`, with a defensive sync overwriting correct in-memory state with stale URL contents.

## 9. URL state: pure helpers + reactive params + two effects

For any flow whose state lives partly in the URL (multi-step form, filterable list, deep-linkable picker), the pattern is:

**Pure helpers** in a `.ts` file with no Svelte runes — runs identically on server (SSR `load`) and client:

```ts
// url-state.ts
export interface FlowInitial { /* shape */ }
export const DEFAULTS: FlowInitial = { /* ... */ };

export function parseFromUrl(url: URL, params: Record<string, string>): FlowInitial { /* ... */ }
export function serializeToParams(s: Partial<FlowInitial>): URLSearchParams {
  const sp = new URLSearchParams();
  if (s.foo !== DEFAULTS.foo) sp.set('foo', String(s.foo)); // omit defaults — short URLs
  return sp;
}

export function stageUrl(stage: Stage, b: FlowInitial): string {
  const sp = serializeToParams(b);
  const q = sp.toString();
  // Route through resolve() so a route rename breaks the build at this line,
  // not at every call site.
  let path: string;
  if (stage === 'one') path = resolve('/flow');
  else path = resolve('/flow/[step]', { step: stage });
  return `${path}${q ? `?${q}` : ''}`;
}
```

**Validation falls back to defaults** rather than throws — a stale shared link should not 500 the page.

**Reactive store** uses `SvelteURLSearchParams` as the source of truth:

```ts
// state.svelte.ts
class FlowStore {
  #params = new SvelteURLSearchParams();
  // class getters off #params — reads track automatically
  get foo() { return this.#params.get('foo') ?? DEFAULTS.foo; }
  set foo(v: string) { this.#params.set('foo', v); }
}
```

**Bidirectional sync via two `$effect`s** in the layout:

```svelte
<script lang="ts">
  // params → URL
  $effect(() => {
    void store.params.toString();
    untrack(() => store.pushParamsToUrl());
  });

  // URL → params (back/forward, deep-link, external goto)
  $effect(() => {
    void page.url;
    untrack(() => store.pullParamsFromUrl());
  });
</script>
```

Both effects guard with string equality so they don't loop on each other.

**Gotcha — never spread the store.** URL-backed values are class getters living on the prototype; `{...store}` produces `{ foo: undefined, ... }` and your serializer happily emits `?foo=undefined`. Read fields individually.

## 10. Anchor over button-goto for navigation CTAs

If a CTA does nothing but route to a URL derivable at render time, render it as an anchor styled as a button.

```svelte
<!-- Right -->
<a href={nextHref} class="btn btn-primary">Continue</a>

<!-- Wrong: invisible to data-sveltekit-preload-data heuristic -->
<button onclick={() => goto(nextHref)} class="btn btn-primary">Continue</button>
```

A button calling `goto` defeats SvelteKit's preload-on-hover, middle-click to new tab, and right-click to open in new tab.

When designing a screen component, plumb `nextHref: string` rather than `onNext: () => void`. The callback contract is what makes a button look obvious and an anchor invisible. Reserve callbacks for CTAs that mutate state, validate, or compute the destination at click time.

When validation gates a CTA: render a disabled button while invalid, swap to an anchor once valid.

For predictive prefetch on touch (no hover signal), schedule `preloadData(url)` in `requestIdleCallback` once the user has settled on the screen.

## 11. Semantic HTML over imperative JS, generally

The pattern from rule 10 extends:

- External URLs → anchor tag with href, not button + `window.location.href = ...`
- Form submits → form with action, not button + `fetch`
- Toggles → input type checkbox or button with aria-pressed, not div + onclick
- Required fields → required attribute, not custom validation only

Test: would a Playwright assertion become a one-line `toHaveAttribute('href', ...)` if the element were semantic? If yes, any test workaround (network interception, `window.location` shim, `defineProperty`) is a symptom — the source is wrong.

## 12. Discriminated unions over parseable string keys for remote-function args

`$app/server` `query()` and `command()` serialize args as JSON. There is no URL-encoding constraint forcing a flat shape.

```ts
// Wrong: regex on both sides, duplicated and drifts on every new case
const PATTERN = /^(\d{4})$|^(\d{4})-(\d{2})$|^(\d{4})-(\d{2})_(\d{4})-(\d{2})$/;

// Right: tagged union, validate with v.variant
const Period = v.variant('kind', [
  v.object({ kind: v.literal('year'), year: v.number() }),
  v.object({ kind: v.literal('month'), year: v.number(), month: v.number() }),
  v.object({ kind: v.literal('range'), from: ..., to: ... }),
]);
```

A `kind`-discriminated union puts the schema in one place and a single switch on the server. Reserve regex for genuinely string-shaped inputs (ISO dates, phone numbers, slugs).

## 13. Remote-function shape

Each `.remote.ts` file lives next to the route that owns it (`src/routes/.../feature.remote.ts`). The shape:

```ts
import { command, query, getRequestEvent } from '$app/server';
import { error } from '@sveltejs/kit';
import * as v from 'valibot';

// 1. Valibot input schema, centralized in $lib/server/.../schemas.ts when reused.
export const InputShape = v.object({ /* ... */ });

// 2. Discriminated result type — failure carries a typed reason code.
export type FailureCode = 'rate_limited' | 'not_found' | 'conflict' | /* ... */;
export type Result =
  | { ok: true; data: T }
  | { ok: false; reason: FailureCode; detail?: string };

// 3. The remote.
export const doThing = command(InputShape, async (input): Promise<Result> => {
  const event = getRequestEvent();
  if (!event.locals.db) error(503, 'database_unavailable');
  // ... business logic, always returning a Result, never throwing for state errors
});
```

The remote stays pure on state errors — return `{ ok: false, reason: 'x' }` so the admin UI that surfaces the broken record can still load the data. Reserve `error(...)` for infrastructure failures (db unavailable, missing platform binding).

## 14. Failfast at the consumer, not inside `query()` / `command()`

Throwing `error()` from `@sveltejs/kit` inside a remote-function body becomes an `UnhandledPromiseRejection` in vite/miniflare — the dev server crashes instead of rendering a 500.

```ts
// Wrong: crashes dev server
export const getRows = query(async () => {
  const rows = await db.select()...;
  for (const r of rows) {
    if (!r.requiredField.trim()) error(500, `row ${r.id}: requiredField empty`);
  }
  return rows;
});

// Right: return data, failfast at the consumer (page/component/load)
export const getRows = query(async () => {
  return await db.select()...;  // pure, always succeeds
});

// In +page.server.ts or a component:
const rows = await getRows();
const broken = rows.find(r => !r.requiredField.trim());
if (broken) error(500, `row ${broken.id}: requiredField empty`);
```

Bonus: a pure remote function keeps admin access alive. Failfast inside the remote would block the admin UI that's meant to *fix* the broken record.

## 15. Markdown columns for admin-authored prose, not typed JSON shapes

When the task is "let an admin author long-form prose" (T&Cs, policy, descriptions, about pages):

- Store: a markdown text column.
- Edit: a real WYSIWYG markdown editor (`carta-md`, Milkdown, TipTap with markdown extension, BlockNote). Avoid a textarea with a preview pane.
- Render: server-side with `marked`, ship sanitized HTML in the payload.

Typed shapes like `{ sections: [{ heading, body, bullets }] }` trade admin UX (one fluid textarea per language) for compile-time section-shape safety nobody asked for.

Structured shapes are right when content is genuinely tabular or fields have distinct validation (pricing tiers, FAQs with searchable indexes). Wrong for prose that's just paragraphs, headings, and bullets.

## 16. Failfast on missing required config. No silent fallback.

When a feature requires admin-authored configuration per entity, missing config throws — the request fails, the page surfaces the error, the admin gets a clear signal.

```svelte
<!-- Wrong: customers see legally-inappropriate generic copy, admin doesn't notice -->
{#if html}
  {@html html}
{:else}
  <GenericFallback />
{/if}

<!-- Right: trust the data contract -->
{@html html}
```

For required admin-authored content: make the column NOT NULL or have the read path throw on empty. For mid-migration safety, enforce at admin save time (entity can't be flipped to "active" until the field is authored).

Public / marketing pages not bound to an entity can have hardcoded content. That's the page's own content, not a fallback.

## 17. No backwards-compat shims when migrating data models

When a feature migrates from shared/generic data to per-entity:

- No seed migrations copying old shared content into every entity's new column.
- No render-time fallbacks that fall back to a generic component when the per-entity field is missing.
- No nullable → NOT NULL two-step rollouts unless explicitly requested.

The deploy moment is when both the schema and the per-entity content are ready. The pre-migration source content gets deleted, not migrated.

SQLite `ADD COLUMN` requires `DEFAULT ''` for NOT NULL — rely on a save-time check at the admin layer, not an `UPDATE` that pretends the old content fits the new model.

## 18. SSR safety: gate libraries that touch `HTMLElement` at module init

Some libraries call `customElements.define(...)` or `extends HTMLElement` at module evaluation time. Even `{#if browser}` around the tag won't save you — the import alone crashes server render.

Vet candidates by checking whether the library evaluates browser-only APIs at the top level. SSR-safe alternatives (e.g. `torph/svelte`'s `TextMorph` for number/text morphing) wrap their work inside lifecycle hooks. Reach for those for any route that server-renders. For routes with `ssr = false` (e.g. anything using `@threlte/core`), the SSR-unsafe library is fine.

## 19. Timezones: `date-fns-tz` at the caller. No string parsing.

```ts
// Wrong: string parsing on toISOString output
const utc = new Date(`${date}T00:00:00+03:00`).toISOString().slice(0, 19).replace('T', ' ');

// Right: date-fns-tz, IANA name
import { fromZonedTime, formatInTimeZone } from 'date-fns-tz';
const zoned = fromZonedTime(`${date}T00:00:00`, 'Asia/Qatar'); // or whatever IANA name
const utc = formatInTimeZone(zoned, 'UTC', 'yyyy-MM-dd HH:mm:ss');
```

Put conversion at the caller (UI layer, where local intent is obvious). Storage stays naive UTC text. Query bodies stay timezone-naive. Format string `'yyyy-MM-dd HH:mm:ss'` matches SQLite's `datetime('now')`.

A shared helper in `$lib/.../time.ts` — one function per direction — gets called from every screen that talks about dates.

## 20. Icons via `unplugin-icons` + Iconify. No inline SVGs for generic glyphs.

- **Default set**: Solar Linear (`~icons/solar/<name>-linear`). Bold-Duotone for filled/accent (`~icons/solar/<name>-bold-duotone`).
- **Brand marks**: Simple Icons (`~icons/simple-icons/<brand>`).
- **Pattern**: direct imports, one per icon. No wrapper component — defeats tree-shaking.

```svelte
<script lang="ts">
  import IconPhone from '~icons/solar/phone-linear';
</script>

<IconPhone class="size-4 text-label-2" aria-hidden="true" />
```

Sizing: `size-3.5` inline-with-text, `size-4` standard UI, `size-5` buttons/chrome, `size-6` prominent. Icons inherit `currentColor` — use token classes, never hard-code stroke colors. Always pass `aria-hidden="true"` unless the icon is the only label.

Keep inline only: bespoke domain illustrations.
