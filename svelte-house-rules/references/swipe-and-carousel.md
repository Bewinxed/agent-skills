# Swipe gestures, 3-page carousel, and filter popovers

## 54. Swipe action: horizontal-lock with 8px jitter band, threshold-based commit

The shape that survives iOS Safari testing: a Svelte action that listens on `pointerdown` AND `touchstart` (passive: false), routes move/end events to window listeners, locks direction after 8px of travel, and commits if `|dx| > threshold * width`.

```ts
// $lib/dom/swipeAction.ts
import type { Action } from 'svelte/action';

export interface SwipeOptions {
  /** Called after the slide-out completes; mutate state inside. */
  onCommit?: (direction: 'next' | 'prev') => void;
  /** Fraction of node width to trigger commit. Default 0.3. */
  threshold?: number;
  /** When true, gestures are ignored. Use during an in-flight commit. */
  disabled?: boolean;
}

const OUT_MS = 220;
const IN_MS = 240;
const SPRING_MS = 180;
const EASE = 'cubic-bezier(0.2, 0.8, 0.4, 1)';
```

Five details make this work on iOS:

1. **`touchstart` AND `pointerdown` both wired.** Inside glass-blurred containers, iOS Safari sometimes suppresses pointer events; touch events still fire. Listen to both, dedupe by tracking whether a drag is already active.
2. **Window-level `move` / `end` listeners with `passive: false`.** Lets `preventDefault()` stick from the first move event so the browser doesn't start a horizontal page scroll mid-drag.
3. **8px jitter band before locking direction.** Below the band, do nothing. Above it, lock to the dominant axis (`|dx| > |dy| * 1.5` → horizontal; else give up and let vertical scroll win).
4. **`touch-action: pan-y` on the node.** Tells the browser the gesture is vertical-only by default — horizontal goes through our handler. Without this, mobile Safari fights us.
5. **Skip text-editing surfaces (`input, select, textarea`).** There a horizontal drag means "select text," not "swipe." Buttons and anchors don't need the guard — a short tap still fires `click` (browsers cancel click when pointermove preventDefaults from the first move event).

## 55. `animateCommit` — slide out, mutate, jump opposite, slide back

Pair the swipe action with an imperative animation that tap-driven nav (prev/next/Today buttons) can share, so both gesture and tap go through one code path:

```ts
export async function animateCommit(
  node: HTMLElement,
  direction: 'next' | 'prev',
  onCommit?: () => void,
  startDx: number = 0,
): Promise<void> {
  const width = node.offsetWidth;
  const off = direction === 'next' ? -width : width;

  // Slide out (continuing from any in-progress drag offset).
  setTransform(node, startDx, null);
  await nextFrame();
  setTransform(node, off, OUT_MS);
  await waitForTransitionEnd(node);

  // Mutate state. Children re-render with the new period's data.
  onCommit?.();

  // Two frames: one to commit the no-transition jump,
  // a second so the new layout is laid out before transitioning in.
  setTransform(node, -off, null);
  await nextFrame();
  await nextFrame();

  setTransform(node, 0, IN_MS);
  await waitForTransitionEnd(node);
  setTransform(node, 0, null);
}
```

The two-frame wait before sliding back is load-bearing: the new children need a paint at `transform: ∓100%` before you transition them to `0`, or you get a flash of the post-transition position.

## 56. 3-page carousel strip (SwiftUI TabView pattern)

The "virtualized" slide list for paged content: pre-render the previous, current, and next pages side by side in a strip, idle the strip at `translateX(-V)` where `V` is one viewport width. The center cell is on screen; prev sits off-screen left, next off-screen right, ready to peek in during a drag.

```svelte
<script lang="ts">
  let period = $state<AnalyticsWindow>(currentMonthWindow());
  const prevPeriod = $derived(shiftWindow(period, -1));
  const nextPeriod = $derived(shiftWindow(period, 1));

  let stripEl = $state<HTMLDivElement | null>(null);
  let dragPx = $state(0);
  let committing = $state(false);

  // Three remote queries: prev / current / next. Each cached so the
  // peek shows real data, not a spinner, while the swipe is in flight.
  const qPrev = listThings({ period: prevPeriod });
  const qCurrent = listThings({ period });
  const qNext = listThings({ period: nextPeriod });

  let cachePrev = $state<Rows | undefined>(undefined);
  let cacheCurrent = $state<Rows | undefined>(undefined);
  let cacheNext = $state<Rows | undefined>(undefined);
  $effect(() => { if (qPrev.current) cachePrev = qPrev.current; });
  $effect(() => { if (qCurrent.current) cacheCurrent = qCurrent.current; });
  $effect(() => { if (qNext.current) cacheNext = qNext.current; });

  function pageWidth(): number {
    return stripEl ? stripEl.offsetWidth / 3 : 0;
  }

  function setStrip(dx: number, transitionMs: number | null) {
    if (!stripEl) return;
    stripEl.style.transition = transitionMs === null ? '' : `transform ${transitionMs}ms ${EASE}`;
    const v = pageWidth();
    stripEl.style.transform = `translateX(${-v + dx}px)`;
  }

  // Shift cached rows to follow the period change, so the cell that
  // the user just swiped to keeps the data they saw during the peek.
  function shiftCaches(direction: 'next' | 'prev') {
    if (direction === 'next') {
      cachePrev = cacheCurrent;
      cacheCurrent = cacheNext;
      cacheNext = undefined; // qNext re-resolves with the new args
    } else {
      cacheNext = cacheCurrent;
      cacheCurrent = cachePrev;
      cachePrev = undefined;
    }
  }

  async function commitSwipe(direction: 'next' | 'prev', startDx: number) {
    if (!stripEl || committing) return;
    committing = true;
    try {
      const v = pageWidth();
      const targetDx = direction === 'next' ? -v : v;
      setStrip(startDx, null);
      await new Promise((r) => requestAnimationFrame(r));
      setStrip(targetDx, OUT_MS);
      await waitForTransform(stripEl);

      // Single tick: shift caches AND period AND reset transform.
      // Order: cache shift first so the new center cell renders with
      // the right data before the period prop changes.
      shiftCaches(direction);
      period = direction === 'next' ? nextPeriod : prevPeriod;
      setStrip(0, null);
    } finally {
      committing = false;
    }
  }
</script>

<div class="overflow-hidden">
  <div bind:this={stripEl}
       use:swipeAction={{
         onCommit: (dir) => commitSwipe(dir, dragPx),
         disabled: committing,
       }}
       class="flex w-[300%]"
       style:will-change="transform">
    <section class="w-1/3"><PageView rows={cachePrev} pending={!cachePrev} /></section>
    <section class="w-1/3"><PageView rows={cacheCurrent} pending={!cacheCurrent} /></section>
    <section class="w-1/3"><PageView rows={cacheNext} pending={!cacheNext} /></section>
  </div>
</div>
```

Why the cache shift matters: on commit, the new center cell's *remote query* doesn't resolve for a tick — but the user just SAW that data in the side cell during the peek. Hand them their own cache. The previously-empty far side re-resolves in the background.

This is the closest pattern in the codebase to a "virtualized list" — windowed rendering of N=3 around a sliding index. For genuine long lists, the project hasn't needed a virtualizer yet; reach for `@tanstack/svelte-virtual` if the list grows past a few hundred rows.

## 57. Period picker: discriminated `AnalyticsWindow`, popover panel, ordered nav

The filter shape is a tagged union — `year`, `month`, `range`, `relative` — validated by valibot's `v.variant` (see svelte-kit rule 12). The picker renders a popover panel with a year stepper + 12-month grid + range toggle; the surrounding chrome (trigger button, MonthNavigator's prev/next/Today) is the consumer's responsibility.

```ts
// types
export type YearMonth = { year: number; month: number /* 1..12 */ };
export type AnalyticsWindow =
  | { kind: 'year'; year: number }
  | { kind: 'month'; year: number; month: number }
  | { kind: 'range'; start: YearMonth; end: YearMonth }
  | { kind: 'relative'; preset: 'last_7_days' | 'last_30_days' | 'this_year' };
```

Helpers stay pure (no Svelte runes) so SSR `load` functions can resolve windows too:

```ts
// $lib/components/period/util.ts
export function resolveExplicitWindow(
  window: AnalyticsWindow,
): { fromDate: string; toDate: string } | null {
  if (window.kind === 'year') {
    return { fromDate: `${window.year}-01-01`, toDate: `${window.year}-12-31` };
  }
  if (window.kind === 'month') {
    return {
      fromDate: monthFirstDay(window),
      toDate: lastDayOfMonth(window.year, window.month - 1),
    };
  }
  if (window.kind === 'range') {
    const earlier = ymCompare(window.start, window.end) <= 0 ? window.start : window.end;
    const later = earlier === window.start ? window.end : window.start;
    return {
      fromDate: monthFirstDay(earlier),
      toDate: lastDayOfMonth(later.year, later.month - 1),
    };
  }
  return null; // 'relative' needs DB-side MIN/MAX
}

export function shiftWindow(window: AnalyticsWindow, delta: number): AnalyticsWindow {
  // shift forward/back by one unit (month for month-kind, year for year-kind, etc.)
}
```

The `relative` kind returns `null` because relative bounds depend on data the server has (earliest / latest row date). Resolve it server-side in the `load` function.

## 58. Sister-component: `MonthNavigator`

Consumes the same `AnalyticsWindow` and offers prev / next / "Today" + a filter chip that opens the popover. The chip's label is derived from the current window's kind so the user always sees what they're filtered on (`"March 2026"`, `"2026"`, `"Mar–Jun 2026"`). Use the same `Previous` + index-compare paginator pattern from animation rule 42 for directional micro-animations on the label.
