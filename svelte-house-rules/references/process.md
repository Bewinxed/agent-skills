# Process discipline

Read before planning. Re-read before declaring done.

## 1. Verify before planning. No hedging.

Before finalizing any plan that:

- Mentions a file to create → `ls` / glob the target directory first.
- References an existing symbol → grep for it, read its source.
- Says "alongside" or "mirrors" → read that pattern's actual file.
- Uses "probably", "should be", "may", "if exists" → those are tells the verification step was skipped. Go do it.

A plan claiming a path exists when it doesn't is worse than asking. Verification lands in the plan as concrete `file:line` references, with no conjecture in the language.

## 2. Adversarial thinking on money / auth / state transitions

For any change touching payment, authentication, or state machines, the first instinct is the robustness audit — the minimal-diff happy-path fix comes second. Walk through:

- **DevTools tampering.** Can the client modify the server's response and reach a state they shouldn't?
- **GET-triggered side effects.** Endpoints that flip state on GET will be hit by prefetch, link previews, image-src crawlers, and email spam scanners. Mutations belong on POST / `command()`.
- **Session / owner binding.** Can someone reach another customer's data by guessing an ID? Cookies are httpOnly + sameSite + secure (in prod) — use them as identity gates.
- **Race conditions.** Read-then-write on shared state is wrong. Two concurrent callers (webhook + page refresh) both pass the "is it already done?" check. Use atomic conditional UPDATE with `WHERE status='held'`; on SQLite/D1, check `meta.changes === 0` for the race-loser.
- **Partial-failure atomicity.** Multiple writes that must all succeed belong in `db.batch([...])` (D1) or a transaction.
- **Response leakage.** Don't return `accessToken` / `secret` / `url` to the client until the state warrants it. Slim payloads to the minimum the caller needs.

## 3. Critical analysis over stenography

When the user proposes an approach, analyze it before adopting. Articulate trade-offs, push back if there's a better path, commit with reasoning. Writing the user's suggestion down as the plan is not collaboration.

## 4. Rewrite broken plans. Don't patch them.

When an audit reveals a plan was structurally wrong (framing wrong, security argument missing, model mismatched) — start fresh. Editing fixes into a broken plan makes it inherit the broken framing.

## 5. Wait for explicit deploy go-ahead

Commit + push freely on request. Then stop. Surface the deploy command and wait for "deploy" / "ship" / "go ahead." If the user said "commit and push and deploy" in one breath, that is the go-ahead — proceed.

## 6. Build before deploy. Clean artifacts.

`wrangler deploy` reads built artifacts; it does not run `vite build`. A `cf:deploy` script that wipes `.svelte-kit/cloudflare` and `.svelte-kit/output` first, then runs build, then `wrangler deploy`, is the safe shape. Verify deploys after by tailing for unexpected exceptions (`bunx wrangler tail --format=pretty`).

Some plugins are idempotent on already-emitted artifacts (e.g. `@oselvar/sveltekit-add-worker-exports` on `_sveltekit_worker.js`), so even a fresh build can emit stale extras unless those directories are removed.

## 7. Check deps before writing utility components

Before writing a new file under `src/lib/components/` for a number tweener, toast, popover, tooltip, modal, debounce, clipboard helper, text morph:

```bash
grep -E 'morph|flow|tween|toast|popover|tooltip|debounce' package.json
grep -rln 'similar-keyword' src --include="*.svelte"
```

If anything matches, read it and use it. Custom is only justified when the existing option doesn't fit. Parallel implementations fragment the design system and skip features the maintainer already paid for.
