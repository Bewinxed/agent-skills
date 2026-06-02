# Library preferences

The stack converges on a small set of high-quality Svelte-aware libraries. Reach for these before rolling custom.

| Concern | Pick | Notes |
|---|---|---|
| **Headless UI primitives** | `bits-ui` | `Switch`, `Toggle`, `Combobox`, `Popover`, `Select`. Composable, themable, accessible. |
| **Drawers / sheets** | `vaul-svelte` | Multi-stop heights, swipe-to-dismiss. For OS-dialog-hosting flows on iOS, set `dismissible={false}` (see ux-patterns rule 33). |
| **State primitives** | `runed` | `Previous`, `useEventListener`, `IsMounted`, `StateHistory`, `Persisted`, `Debounced`. Pair with `svelte/reactivity`. |
| **Notifications** | `svelte-sonner` | Mount one `<Toaster />` at the layout root, import `toast` from anywhere. Project may layer a tiny `toast.svelte.ts` store on top for pinned-to-control toasts. |
| **Markdown editor** | `carta-md` | WYSIWYG-ish markdown editing. Pair with `marked` for server-side render. |
| **Markdown render** | `marked` | Sanitize before injecting via `{@html}`. |
| **Validation** | `valibot` | Smaller and tree-shakes better than zod. Use `v.pipe`, `v.regex`, `v.variant`, `v.parse`. |
| **ORM (D1 / SQLite)** | `drizzle-orm` | Schema-first, no runtime overhead. `drizzle-kit generate` for migrations, `drizzle-kit studio` for browsing. |
| **i18n** | `@inlang/paraglide-js` for marketing surfaces; per-feature `i18n.ts` exporting `Record<Lang, Strings>` for in-app flows | Marketing benefits from compile-time message extraction; transactional / customer-facing screens often render both languages stacked instead of toggling. |
| **Phone parsing** | `libphonenumber-js` | E.164 normalization. Store as digits without `+`. |
| **Decimals / money** | `decimal.js-light` | All money arithmetic. Round at persist boundary. |
| **Dates / timezones** | `date-fns` + `date-fns-tz` | `fromZonedTime` / `formatInTimeZone`. Conversion at the caller, naive UTC in storage. |
| **Theme (light / dark)** | `mode-watcher` | Writes `class="light|dark"` on `html`. CSS branches on the class. |
| **IDs** | `nanoid` | App-generated string IDs. URL-safe by default. |
| **Crypto / OTP** | `@oslojs/crypto`, `@oslojs/encoding`, `@oslojs/otp` | Minimal, Edge-runtime-safe. |
| **Push (web)** | `@block65/webcrypto-web-push` | WebCrypto-based, works on Cloudflare Workers. |
| **Live events** | `river.ts` | Typed event bus + SSE client/server. `defineEvent(name, { data })` → typed `on(name, cb)`. |
| **Images** | `@sveltejs/enhanced-img` | Pair with `sharp` at build. |
| **3D** | `@threlte/core` + `@threlte/extras` | Three.js wrapper. SSR-disable any route using a `Canvas`. |
| **Maps** | `maplibre-gl` | Open-source. Listen to `MediaQueryListEvent` for theme switching. |
| **QR codes** | `uqr` | Tiny, dependency-free. |
| **Icons** | `unplugin-icons` + Iconify | Solar Linear default, Simple Icons for brand marks. See svelte-kit rule 20. |

## What to skip

- **`zod`** when `valibot` is in deps. They're not both worth having.
- **`lucide-svelte`** — Iconify covers the same ground with better tree-shaking and more sets.
- **`luxon` / `moment`** — `date-fns-tz` is enough.
- **`uuid`** — `nanoid` is shorter, URL-safe, and faster.
- **Custom number tweeners / text morphers** — `torph` is dependency-free and SSR-safe; `@number-flow/svelte` works but extends `HTMLElement` at module init and crashes SSR (svelte-kit rule 18).
