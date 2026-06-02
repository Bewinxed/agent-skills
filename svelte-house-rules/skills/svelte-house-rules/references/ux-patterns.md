# UX patterns

## 32. Blocked routes get a styled intermediate page, not an instant 307

When a route is gated by a state flag (entity disabled, feature soft-gated, account paused):

- Centralize the check in the highest layout covering all affected subroutes.
- The layout `load` returns the flag — it does not throw or redirect.
- `+layout.svelte` branches: either render the children or render the "unavailable" screen.
- The unavailable screen matches the surrounding visual language (token classes, icon set), includes a manual "go back" link as the primary action, and a soft auto-redirect via `setInterval` + `goto` with a visible countdown.
- Bilingual surfaces wire through the same i18n module the surrounding screens use.

Instant redirects look like a broken link or a back-button reflex; the visitor never sees what happened or why.

## 32b. vaul drawer body: flex + `min-height: 0` + `touch-action: pan-y`

A vaul drawer containing a scrollable form has two failure modes by default:

1. **Footer hides behind the keyboard.** The form pushes the drawer past its max-height because the body flex child can't shrink below its content size. Footer slides out of view under the keyboard.
2. **Inner scroll fights the drawer drag.** vaul's pointer handling tries to interpret a downward swipe as a drag-to-dismiss, so scrolling a long form on iOS is unreliable — the drawer half-closes instead of the content scrolling.

The combo that fixes both:

```css
@utility drawer-body {
  flex: 1 1 auto;
  /* min-height: 0 lets a flex item shrink BELOW its content size,
     so the inner overflow can scroll. Without it the body forces
     the drawer to grow past its max-height. */
  min-height: 0;
  overflow-y: auto;
  overscroll-behavior: contain;
  /* touch-action: pan-y opts this container out of vaul's
     drag-to-dismiss interpretation so iOS vertical scroll works
     inside the form. Drawer's drag handle still works at the top. */
  touch-action: pan-y;
  padding: 12px 18px 18px;
}
```

Drawer structure:

```svelte
<Drawer.Root bind:open>
  <Drawer.Portal>
    <Drawer.Overlay onclick={() => (open = false)} />
    <Drawer.Content>
      <header class="drawer-header"> <!-- drag handle area -->
        <Drawer.Title class="drawer-title">Edit thing</Drawer.Title>
        <Drawer.Close aria-label="Close" class="drawer-close">
          <IconClose class="size-5" aria-hidden="true" />
        </Drawer.Close>
      </header>
      <div class="drawer-body">
        <!-- long scrollable form -->
      </div>
      <footer class="drawer-footer" style="padding-bottom: max(16px, env(safe-area-inset-bottom));">
        <button type="submit">Save</button>
      </footer>
    </Drawer.Content>
  </Drawer.Portal>
</Drawer.Root>
```

The footer's own `padding-bottom: max(16px, env(safe-area-inset-bottom))` covers the home-indicator inset on iPhone.

## 33. vaul drawers with OS-dialog actions: `dismissible={false}`

When a vaul `Drawer.Root` hosts a control that invokes an iOS system dialog (`Notification.requestPermission`, Share sheet, Apple Pay), the drawer appears to dismiss itself the instant the dialog closes — iOS dispatches a tap-through `click` / `touchend` to the page at the original tap coordinates, landing on vaul's overlay.

```svelte
<Drawer.Root dismissible={false} bind:open>
  <Drawer.Content>
    <header>
      <h2>Title</h2>
      <button onclick={() => (open = false)} aria-label="Close">×</button>
    </header>
    <!-- flow -->
    <button onclick={() => (open = false)}>Not now</button>
  </Drawer.Content>
</Drawer.Root>
```

Drop the habit of `onclick={() => (open = false)}` on `Drawer.Overlay` for these flows — it speeds up the phantom-tap close. Multi-step onboarding is better without outside-tap dismissal anyway.

## 34. Form components: bits-ui primitives, not raw inputs

For toggles, switches, comboboxes, popovers, selects — reach for `bits-ui` first. The component already handles focus management, ARIA, keyboard, mobile pointer quirks.

```svelte
<script lang="ts">
  import { Switch } from 'bits-ui';
</script>

<Switch.Root bind:checked={enabled} class="switch">
  <Switch.Thumb class="switch-thumb" />
</Switch.Root>
```

Style the slots, not the underlying primitives.
