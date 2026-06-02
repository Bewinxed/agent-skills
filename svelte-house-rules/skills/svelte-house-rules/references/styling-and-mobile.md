# Styling (Tailwind v4) and mobile

## 25. Tokens in `@theme {}`, not Tailwind config

Tailwind v4 reads `@theme` blocks in CSS to generate utilities. Place tokens in `src/routes/layout.css`:

```css
@import 'tailwindcss';
@plugin '@tailwindcss/forms';
@plugin '@tailwindcss/typography';

@theme {
  /* Tailwind v4 picks up --color-*, --font-*, --animate-* and emits
     bg-label-1, text-accent, font-display, animate-ping-pulse, ... */
  --color-label-1: rgba(255, 255, 255, 0.96);
  --color-label-2: rgba(255, 255, 255, 0.62);
  --color-label-3: rgba(255, 255, 255, 0.42);
  --color-label-4: rgba(255, 255, 255, 0.22);
  --color-separator: rgba(255, 255, 255, 0.14);
  --color-accent: #ff7849;
  --color-accent-text: #101216;

  --font-display: 'Display Font', system-ui, sans-serif;
  --animate-ping-pulse: ping-pulse 1.1s ease-out 2;
}
```

**Compound tokens** (gradients, multi-shadow stacks, composite borders) stay as plain custom properties on `:root` — consumed by `@utility` blocks below.

**Token roles**, not pixel values, in component code: `text-label-1`, `text-label-2`, `text-accent`, `bg-glass`, `rounded-card`, never `text-white/60` or `rounded-[16px]`. The token name carries semantic intent; the value can shift in light mode without component edits.

## 26. Radius scale

```css
:root {
  --r-sheet: 28px;   /* full-bleed sheets */
  --r-card: 16px;    /* cards */
  --r-control: 12px; /* buttons, chips */
  --r-input: 1rem;   /* form inputs (matches OS native) */
  --r-pill: 9999px;  /* fully rounded */
}
```

Call sites: `rounded-[var(--r-card)]`. One token per surface role.

## 27. Light / dark fork via `mode-watcher`

`mode-watcher` writes `class="light"` or `class="dark"` on the html element based on user preference. CSS branches:

```css
:root { /* dark tokens — the default */ }

:root.light,
html.light {
  /* explicit light-mode flip */
  --color-label-1: rgba(20, 22, 26, 0.92);
  /* ... */
}

@media (prefers-color-scheme: light) {
  :root:not(.light):not(.dark) {
    /* system-mode light, same flip */
  }
}
```

The `:not(.light):not(.dark)` guard prevents the media query from overriding an explicit user choice.

## 28. Apple "Liquid Glass" recipe

```css
:root {
  --glass-fill: linear-gradient(180deg, rgba(255,255,255,0.14), rgba(255,255,255,0.08));
  --glass-fill-card: linear-gradient(180deg, rgba(255,255,255,0.10), rgba(255,255,255,0.06));
  --glass-border: 0.5px solid rgba(255,255,255,0.22);
  --glass-shadow:
    inset 0 1px 0 rgba(255,255,255,0.22),
    inset 0 0 40px rgba(255,255,255,0.04),
    0 24px 48px rgba(0,0,0,0.48);
}

@utility glass {
  background: var(--glass-fill);
  border: var(--glass-border);
  backdrop-filter: blur(28px) saturate(160%);
  box-shadow: var(--glass-shadow);
}
```

Cards inside scrolling lists drop the outer drop shadow (it bleeds into gaps and reads as a flat darker bg). Inset highlight + inset glow are enough to read "elevated."

## 29. Accessibility + capability fallbacks

```css
@media (prefers-reduced-transparency: reduce) {
  :root {
    --glass-fill: rgb(28, 30, 36); /* collapse to solid */
    --glass-fill-card: rgb(32, 34, 40);
    --popover-fill: rgb(30, 32, 38);
  }
  .glass, .glass-card, .popover-glass { backdrop-filter: none; }
}

@supports not (backdrop-filter: blur(1px)) {
  /* old WebViews — strip translucency the same way */
}
```

## 30. App-shell defaults (mobile / PWA-friendly)

```html
<!-- app.html -->
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover" />
<meta name="apple-mobile-web-app-capable" content="yes" />
<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent" />
<meta name="theme-color" content="#18120e" media="(prefers-color-scheme: dark)" />
<meta name="theme-color" content="#fcf8f2" media="(prefers-color-scheme: light)" />
```

```css
html, body {
  margin: 0;
  height: 100%;
  touch-action: manipulation;       /* kill double-tap zoom */
  overscroll-behavior-y: none;      /* kill pull-to-refresh on the root */
}
* {
  -webkit-tap-highlight-color: transparent;
}
```

## 30b. `100dvh` over `100vh`. Safe-area utilities. Fixed app shell.

**Use `100dvh`, not `100vh`.** The *dynamic* viewport unit excludes mobile browser chrome (Safari's URL bar at scroll-top, Chrome's bottom bar). `100vh` measures the *largest* viewport (chrome hidden), so a layout using it gets scrolled-off the moment the URL bar appears. For broad-compatibility fallback: `height: 100vh; height: 100dvh;` — the second overrides where supported.

**Safe-area utilities** for plain insets (no extra offset):

```css
@utility pt-safe { padding-top: env(safe-area-inset-top, 0px); }
@utility pb-safe { padding-bottom: env(safe-area-inset-bottom, 0px); }
@utility pl-safe { padding-left: env(safe-area-inset-left, 0px); }
@utility pr-safe { padding-right: env(safe-area-inset-right, 0px); }
@utility top-safe { top: env(safe-area-inset-top, 0px); }
@utility bottom-safe { bottom: env(safe-area-inset-bottom, 0px); }
```

For combined values, spell the `calc()` out at the call site:

```svelte
<div class="pt-[calc(env(safe-area-inset-top,0px)+64px)] pb-[calc(env(safe-area-inset-bottom,0px)+88px)]">
```

**Fixed app shell** — the root container is `position: fixed; inset: 0; overflow: hidden`. This keeps the viewport stable on iOS even with URL-bar toggling, and gives a single owner of root scrolling (the inner main content area).

```css
@utility app-root {
  position: fixed;
  inset: 0;
  overflow: hidden;
  color: var(--color-label-1);
  background: var(--root-bg);
  -webkit-font-smoothing: antialiased;
}
```

Inner scroll containers that shouldn't chain to body:

```svelte
<div class="overflow-y-auto overscroll-contain touch-pan-y">
```

`overscroll-contain` keeps the bounce inside the container. `touch-pan-y` makes pointer intent unambiguous (especially important inside vaul drawers — see ux-patterns rule 32b).

## 31. Software-keyboard inset (iOS) — VisualViewport + focusout fallback

iOS Safari shrinks the *visual* viewport when the keyboard opens but leaves the layout viewport unchanged, so `position: fixed` bottom-anchored chrome stays under the keyboard.

Android Chrome with `<meta name="viewport" content="...interactive-widget=resizes-content">` already shrinks the layout viewport — `--kb-inset` computes to zero there and chrome moves naturally with the resize.

**iOS gotcha**: WebKit fires `visualViewport.resize` reliably on keyboard *open*, but sometimes drops it on *close* (Done button, tap-outside, programmatic blur). Result: `--kb-inset` stuck at the keyboard-open value, bottom chrome hovering above empty space. Belt-and-suspenders: also recompute on `document.focusout` after two rAF ticks so WebKit has finished the viewport reflow before measuring.

```ts
// $lib/dom/keyboardInset.svelte.ts
import { useEventListener, IsMounted } from 'runed';

export function trackKeyboardInset(): void {
  const mounted = new IsMounted();

  const recompute = () => {
    const vv = window.visualViewport;
    if (!vv) return;
    const inset = Math.max(0, window.innerHeight - vv.height - vv.offsetTop);
    document.documentElement.style.setProperty('--kb-inset', `${inset}px`);
  };

  // Listen for resize AND scroll — scroll fires during the lift, resize on settle.
  useEventListener(
    () => (mounted.current ? window.visualViewport : null),
    ['resize', 'scroll'],
    recompute
  );

  // iOS keyboard-close fallback. Two rAF ticks let WebKit's reflow settle
  // before we measure — measuring synchronously reports stale dimensions.
  useEventListener(
    () => (mounted.current ? document : null),
    'focusout',
    () => requestAnimationFrame(() => requestAnimationFrame(recompute))
  );
}
```

Call once from the root layout inside a browser guard.

Consumers:

```css
.bottom-chrome {
  padding-bottom: calc(env(safe-area-inset-bottom, 0px) + var(--kb-inset, 0px));
}
/* Or as a `bottom` offset for absolute-positioned sheets: */
.sheet {
  bottom: calc(max(env(safe-area-inset-bottom, 0px), 14px) + var(--kb-inset, 0px));
}
```
