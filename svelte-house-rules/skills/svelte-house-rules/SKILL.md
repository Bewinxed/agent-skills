---
name: svelte-house-rules
description: Apply when working on Svelte 5 / SvelteKit projects — planning, building UI, writing $app/server query/command remote functions, shaping Drizzle/D1 schemas, migrating data models, wiring navigation CTAs, handling timezones, gating routes, designing admin tools, integrating libraries, deploying to Cloudflare Workers, animating screen-to-screen transitions, building mobile or PWA surfaces, fixing iOS keyboard or safe-area issues, building vaul drawers with forms, or reviewing a diff. Triggers when the project uses Svelte, SvelteKit, Drizzle, D1, Tailwind v4, vaul-svelte, bits-ui, runed, valibot, svelte-sonner, carta-md, date-fns-tz, mode-watcher, paraglide-js, or river.ts. Covers process discipline, library choices, engineering taste (anchor over button-goto, discriminated unions, failfast at consumers), Tailwind v4 styling tokens with mode-watcher light/dark fork, Apple Liquid Glass recipe, animation patterns that avoid layout overlap, and mobile keyboard fixes.
---

# Svelte House Rules

A working set of corrections, library choices, and conventions distilled from one Svelte 5 + SvelteKit + Cloudflare Workers project. Project-neutral.

Each rule names the wrong reflex it replaces, followed by the right move. The reasoning travels with the rule so it survives without the conversation that produced it.

## Route to a reference

Load the reference for the area in play. Don't bulk-load — each one is self-contained.

| Area | Read | When |
|---|---|---|
| Process discipline | `references/process.md` | Before planning. Before deploying. When the user pushes back on an approach. |
| Library choices | `references/libraries.md` | Before reaching for a new dep. Before writing a utility component from scratch. |
| Svelte / SvelteKit engineering | `references/svelte-kit.md` | When writing remote functions, URL-state stores, navigation CTAs, validators, markdown surfaces, timezone code, or icon usage. |
| Database (Drizzle + D1 / SQLite) | `references/database.md` | When shaping schemas, writing migrations, or doing state transitions on shared rows. |
| Styling + mobile | `references/styling-and-mobile.md` | When touching CSS, theme tokens, the app shell, safe-area insets, iOS keyboard offsets, or scroll containers. |
| UX patterns | `references/ux-patterns.md` | When gating routes, hosting OS dialogs inside vaul drawers, or wiring forms inside drawers. |
| Cloudflare Workers + live events | `references/cloudflare.md` | When working with cron, CSRF allowlists, OG tags on SSR-disabled routes, rate-limit DOs, or river.ts SSE. |
| Animations | `references/animations.md` | When animating screen-to-screen transitions, swapping content with directional slides, or anywhere stock Svelte transitions feel jittery. |
| Error handling | `references/error-handling.md` | When wiring `+error.svelte`, `handleError` hooks, status-to-copy humanization, inline error banners, or in-place block error states. |
| Analytics (PostHog) | `references/analytics.md` | When wiring `captureEvent` / `identifyCustomer` / `captureError`, the same-origin `/ingest` proxy, the server-side flush via `waitUntil`, or registering an event taxonomy. |
| Swipe / 3-page carousel / filter popovers | `references/swipe-and-carousel.md` | When building swipe gestures, paged content with peek-then-commit, discriminated-union period pickers, or month-navigator chrome. |

## House style: writing the code

These thread through every rule above. They are short on purpose; they apply universally.

- **No "X, not Y" prose in code comments, commit messages, or docs.** The reader didn't see the wrong version. Name what something IS. If an edit removed something, the final state has no before — there is no removal to narrate.
- **No comments explaining WHAT.** Identifiers do that. Only write a comment when the WHY is non-obvious — a hidden constraint, a subtle invariant, a workaround for a specific bug, behavior that would surprise a reader.
- **No future-proofing.** Three similar lines beats a premature abstraction. Don't design for hypothetical requirements.
- **No error handling for scenarios that can't happen.** Trust internal code and framework guarantees. Validate at system boundaries (user input, external APIs).

## The check before declaring done

Single-pass sweep over the diff. Reach back into the relevant reference if any item raises a question.

**Process** (see `references/process.md`)
- [ ] Verified each file path I claimed existed?
- [ ] If money / auth / state — walked the adversarial questions?
- [ ] Held back from deploying without explicit go-ahead?

**Svelte / SvelteKit** (see `references/svelte-kit.md`)
- [ ] Any button-onclick-goto for known URLs → swapped to anchor with href?
- [ ] Any hand-rolled `$state` mirror around a browser object → `svelte/reactivity` primitive?
- [ ] Any regex on both sides of a remote-query param → discriminated union + `v.variant`?
- [ ] Any `error(500)` inside a `query()` / `command()` body → moved to consumer?
- [ ] Any `{#if x}{@html x}{:else}<Generic/>{/if}` for required content → dropped the fallback?
- [ ] Any new utility component → grepped `package.json` first?
- [ ] Any timezone string parsing → `date-fns-tz` at the caller?
- [ ] Any SSR-mounted library touching `HTMLElement` at module init → SSR-safe alternative?
- [ ] Any inline SVG for a generic glyph → Iconify import?

**Database** (see `references/database.md`)
- [ ] Money as TEXT decimal + `decimal.js-light`?
- [ ] Times as minutes-from-midnight, not strings?
- [ ] Phones E.164 without `+`?
- [ ] State transitions atomic (`WHERE status='X'` + `meta.changes` check)?
- [ ] Multi-write must-all-succeed in `db.batch([...])`?

**Styling** (see `references/styling-and-mobile.md`)
- [ ] Color usage via `text-label-N` / `text-accent` tokens, not hex?
- [ ] Radius via `--r-*` vars, not pixel literals?
- [ ] Light-mode fork covered by `:root.light` + `:root:not(.light):not(.dark)` media query?
- [ ] `prefers-reduced-transparency` + `@supports not (backdrop-filter)` covered if using glass?

**Mobile / PWA** (see `references/styling-and-mobile.md` + `references/ux-patterns.md`)
- [ ] `viewport-fit=cover`, theme-color meta, `touch-action: manipulation`?
- [ ] `100dvh` instead of `100vh` for full-height containers?
- [ ] Safe-area insets composed via `calc(env(safe-area-inset-X, 0px) + N)` where stacked with chrome?
- [ ] `trackKeyboardInset()` called once from the root layout in a browser guard?
- [ ] Bottom chrome consuming `var(--kb-inset, 0px)` + `env(safe-area-inset-bottom)`?
- [ ] vaul drawer body uses the `min-height: 0 / overflow-y: auto / touch-action: pan-y` combo so the form scrolls without fighting drag-to-dismiss?
- [ ] Scrollable containers use `overscroll-contain` + `touch-pan-y` to opt out of root chaining and ambiguous gestures?

**UX** (see `references/ux-patterns.md`)
- [ ] State-gated route → intermediate page with countdown, not 307?
- [ ] vaul drawer hosting OS dialog → `dismissible={false}` + explicit close?

**Animations** (see `references/animations.md`)
- [ ] Screen-to-screen swap uses `{#key}` + absolute keyed child + height morph?
- [ ] Horizontal slides use `slideSide` (translateX as %), not pixel-`fly`?

**Error handling** (see `references/error-handling.md`)
- [ ] `+error.svelte` renders via `humanizeStatus(status, code)` — no raw status strings?
- [ ] `handleError` (client + server) stamps a ref on 5xx and captures to PostHog?
- [ ] Inline errors use `<ErrorBanner>` with a `data-error-code` for tests?
- [ ] Section-level failures use `<ErrorState>` with `onRetry`, not full-page fall-through?

**Analytics** (see `references/analytics.md`)
- [ ] `posthog-js` is dynamically `await import()`'d so it never enters the SSR bundle?
- [ ] `api_host: '/ingest'` proxy in place, `defaults` profile version-pinned?
- [ ] Server captures use `posthog-node` with `flushAt: 1` + `platform.context.waitUntil(shutdown)`?
- [ ] New `captureEvent('…')` call sites added to the project's PostHog event-taxonomy registrar?
- [ ] Errors captured only in 5xx paths (`status >= 500`)?

**Swipe / carousel** (see `references/swipe-and-carousel.md`)
- [ ] Swipe action listens on both `pointerdown` AND `touchstart` (passive: false)?
- [ ] 8px jitter band before direction lock, `touch-action: pan-y` on the node?
- [ ] 3-page carousels shift cached rows on commit so the peeked data survives the swap?
- [ ] Period filters use a `kind`-discriminated `AnalyticsWindow` validated via `v.variant`?

**Prose**
- [ ] No contrast residue in comments / commit messages? Reads cold to a new reader?

## When deploying

1. Wait for explicit go-ahead.
2. Run the clean-and-build script (wipe `.svelte-kit/cloudflare` + `.svelte-kit/output`, then `vite build`, then `wrangler deploy`).
3. Tail the worker for unexpected exceptions immediately after.
4. Scheduled handlers (`scheduled()`) and webhook routes are common sources of silent post-deploy failures — watch for those specifically if either was touched.
