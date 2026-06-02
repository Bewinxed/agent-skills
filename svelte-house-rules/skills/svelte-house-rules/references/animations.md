# Animations that don't overlap or snap

Svelte's stock `transition:` / `in:` / `out:` directives have two real-world failure modes that bite hard the first time:

1. **Layout contention.** During a transition, the outgoing element still occupies layout space until its transition completes. The incoming element pushes alongside, so the user sees both shift before settling. With horizontal slides this reads as a jitter; with height changes it reads as a snap.
2. **`fly` snap-disappear.** Stock `fly` takes a fixed pixel `x`. If the element is wider than `x` (a 480px sheet flying out by 280px), there are 200px still visible at unmount time — the rest disappears in a frame and reads as a jagging cut.

The fix is a three-part combo. None of the parts is optional.

## 40. Combo: `{#key}` + absolute keyed child + height morph on the relative wrapper

```svelte
<script lang="ts">
  import { fly } from 'svelte/transition';
  import { cubicOut } from 'svelte/easing';
  import { page } from '$app/state';
  import { Previous } from 'runed';

  // Direction-aware: compare indices in an ordered list. runed.Previous
  // hands you the prior value without manual tracking.
  const ORDER: Record<string, number> = { one: 0, two: 1, three: 2 };
  const prev = new Previous(() => current);
  const direction = $derived.by<'forward' | 'back'>(() => {
    const p = prev.current;
    if (!p) return 'forward';
    return (ORDER[current] ?? 0) < (ORDER[p] ?? 0) ? 'back' : 'forward';
  });
  const enterX = $derived(direction === 'forward' ? 320 : -320);
  const exitX = $derived(direction === 'forward' ? -320 : 320);

  // The keyed child is absolute-positioned (rule 3 below), so it doesn't
  // contribute to the parent's flow height. Bind clientHeight and apply
  // it to the relative wrapper. Two explicit pixel values always
  // interpolate cleanly — `height: auto` does not.
  let activeHeight = $state(0);

  const routeKey = $derived(page.url.pathname);
</script>

<!-- 1. The OUTER wrapper has `overflow-hidden`. Without it, the absolute child
        paints at its full content height while the wrapper's box is still
        animating, so later siblings overlap. -->
<div class="relative overflow-hidden"
     style:height="{activeHeight}px"
     style:transition="height 320ms cubic-bezier(0.33, 1, 0.68, 1)">

  <!-- 2. The `{#key}` block forces remount on identity change. Without it,
          Svelte reuses the same element and there's no in/out transition. -->
  {#key routeKey}
    <!-- 3. The keyed child is `absolute inset-x-0 top-0`. This is what keeps
            in-flight old + new from contending for layout space — they
            stack on top of each other instead of pushing siblings. -->
    <!-- 4. `bind:clientHeight` reports the NEW child's natural height the
            moment it mounts, which feeds the wrapper's morph. -->
    <div bind:clientHeight={activeHeight}
         class="absolute inset-x-0 top-0"
         in:fly={{ x: enterX, duration: 320, easing: cubicOut }}
         out:fly={{ x: exitX, duration: 320, easing: cubicOut }}>
      {@render children()}
    </div>
  {/key}
</div>
```

Why each piece matters — drop any one and a class of bug returns:

| Piece | Drop it and you get |
|---|---|
| `{#key value}` | Svelte reuses the same element; the new content swaps in with no transition. |
| `position: absolute` on the keyed child | Old + new claim layout space simultaneously; siblings get pushed during the transition. |
| `bind:clientHeight` → `style:height` morph | Wrapper holds whatever the last child measured; tall→short reads as content cut off, short→tall reads as content bursting out. |
| `overflow-hidden` on the wrapper | Absolute child paints full-size while wrapper is still growing; bottom siblings overlap during the slide. |

## 41. `slideSide` custom transition — `translateX(%)` for full off-screen exits

Stock `fly`'s pixel-based `x` snaps when the element is wider than the offset. A custom transition that uses `translateX` as a percentage of the element's own width guarantees full off-screen movement at any viewport size:

```ts
// $lib/dom/slideTransition.ts
import { cubicOut } from 'svelte/easing';

export type SlideSideParams = {
  direction?: 1 | -1;
  from?: 'left' | 'right';
  to?: 'left' | 'right';
  duration?: number;
  easing?: (t: number) => number;
};

export function slideSide(_node: Element, params: SlideSideParams = {}) {
  const { duration = 320, easing = cubicOut } = params;
  let direction: 1 | -1 = 1;
  if (params.direction !== undefined) direction = params.direction;
  else if (params.from) direction = params.from === 'right' ? 1 : -1;
  else if (params.to) direction = params.to === 'right' ? 1 : -1;

  return {
    duration,
    easing,
    // u runs 0→1 from "in place" to "out of view".
    // Svelte drives it correctly for in: vs out: directions.
    css: (_t: number, u: number) => `transform: translateX(${u * direction * 100}%)`,
  };
}
```

Usage:

```svelte
{#key routeKey}
  <div class="absolute inset-x-0 top-0"
       in:slideSide={{ direction: direction === 'forward' ? 1 : -1, duration: 320 }}
       out:slideSide={{ direction: direction === 'forward' ? -1 : 1, duration: 280 }}>
    {@render children()}
  </div>
{/key}
```

## 42. `createPaginator` — direction from an ordered list

Manual direction tracking is bug-prone (set the value, *then* derive direction, but `Previous` already updated…). Pair the slide transition with a paginator that computes direction by index comparison:

```ts
// $lib/dom/slideTransition.ts
type Direction = 'forward' | 'back';

export function createPaginator<T extends string | number>(
  getCurrent: () => T,
  setCurrent: (v: T) => void,
  order: readonly T[]
) {
  return (next: T): Direction => {
    const current = getCurrent();
    if (current === next) { setCurrent(next); return 'forward'; }
    const a = order.indexOf(current);
    const b = order.indexOf(next);
    const direction: Direction = a >= 0 && b >= 0 && b < a ? 'back' : 'forward';
    setCurrent(next);
    return direction;
  };
}
```

```svelte
<script lang="ts">
  const paginate = createPaginator(
    () => view,
    (v) => (view = v),
    ['list', 'detail', 'edit'] as const
  );
  let direction: 1 | -1 = $state(1);

  function open(v: 'list' | 'detail' | 'edit') {
    direction = paginate(v) === 'forward' ? 1 : -1;
  }
</script>
```

## 43. `transition:slide` for height-only reveals

When only the vertical dimension changes (a collapsible row in a form, an expandable accordion, an inline error message appearing under a field), Svelte's built-in `transition:slide` is correct — there's no horizontal direction, no contention with siblings beyond the height it animates itself.

```svelte
{#if showExtraField}
  <label class="flex flex-col gap-1" transition:slide={{ duration: 220, easing: cubicOut }}>
    <span>Note</span>
    <textarea bind:value={note}></textarea>
  </label>
{/if}
```

Keep durations consistent: ~180–220ms for inline reveals, 280–320ms for screen-to-screen slides. Easing default is `cubicOut` for entrances and `cubic-bezier(0.33, 1, 0.68, 1)` for height morphs.

## 44. Skip `document.startViewTransition` for screen-to-screen flow

`startViewTransition` looks attractive — declarative, browser-native — but in practice it clashes with:

- SvelteKit's navigation blocking on `navigation.complete`,
- CSS transitions on persistent chrome (chip indicators, header underlines) that paint during the VT snapshot,
- any imperative state mutation timed around the same event loop tick.

The keyed-absolute + height-morph combo above gives you the same effect with full control over what animates and what stays. Reserve VTs for static page-to-page navigations where the elements being morphed have stable identity across routes.

## Animation checklist

- [ ] `{#key}` block wraps the swapping content?
- [ ] Keyed child is `position: absolute`?
- [ ] Outer wrapper has `overflow-hidden`?
- [ ] Wrapper height morphs via `bind:clientHeight` → `style:height` + CSS transition?
- [ ] Horizontal slides use `slideSide` (`translateX(%)`) or pixel-`fly` with a value larger than the element's width?
- [ ] Direction comes from `createPaginator` (or `runed.Previous` index compare), not a manual setter?
- [ ] Inline height-only reveals use `transition:slide`?
- [ ] No `document.startViewTransition` wrapping route changes?
