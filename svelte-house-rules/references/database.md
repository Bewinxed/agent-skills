# Database conventions (Drizzle + D1 / SQLite)

## 21. Storage shapes

```ts
// drizzle/schema.ts
import { sqliteTable, text, integer, real, check, index } from 'drizzle-orm/sqlite-core';
import { sql } from 'drizzle-orm';

export const things = sqliteTable('things', {
  // IDs: TEXT, app-generated nanoid. EXCEPT slugs that are part of URLs —
  // when a row's id appears in /route/[id], make it the slug and skip the
  // separate slug column.
  id: text('id').primaryKey(),

  // Money: TEXT decimal strings like "175.00". Arithmetic via decimal.js-light.
  // Round UP to 2 decimals at every persist boundary.
  priceQar: text('price_qar').notNull(),

  // Times of day: INTEGER minutes-from-midnight (0..1439).
  startMin: integer('start_min').notNull(),

  // Phones: TEXT E.164 without "+" (libphonenumber-js normalises). Matches WhatsApp.
  phone: text('phone').notNull(),

  // Timestamps: TEXT ISO-8601, SQLite default datetime('now'). UTC stored.
  // Display layer converts via date-fns-tz.
  createdAt: text('created_at').default(sql`(datetime('now'))`).notNull(),

  // Booleans: INTEGER 0/1. No boolean column in SQLite.
  active: integer('active').notNull().default(1),

  // Enums: CHECK constraint table-side, NOT a separate enum table.
  status: text('status').notNull(),
}, (t) => [
  check('things_status_ck', sql`${t.status} IN ('held','confirmed','cancelled')`),
  index('things_active_idx').on(t.active),
]);
```

## 22. Per-request D1 binding

D1 bindings are request-scoped (live on `event.platform.env`), not constructable at module load. Build the `db` per-request in `hooks.server.ts` and stash on `event.locals.db`.

```ts
// $lib/server/db/index.ts
import { drizzle } from 'drizzle-orm/d1';
import * as schema from './schema';

export function createDb(d1: D1Database) {
  return drizzle(d1, { schema });
}
export type DB = ReturnType<typeof createDb>;
```

```ts
// hooks.server.ts
import { createDb } from '$lib/server/db';

export const handle: Handle = async ({ event, resolve }) => {
  if (event.platform?.env.DB) {
    event.locals.db = createDb(event.platform.env.DB);
  }
  return resolve(event);
};
```

Remotes guard with `if (!event.locals.db) error(503, 'database_unavailable')` and move on.

## 23. Atomic state transitions

State flips on shared rows use conditional UPDATE, not read-then-write:

```ts
// Wrong: race-prone
const row = await db.select().from(t).where(eq(t.id, id)).get();
if (row.status === 'held') {
  await db.update(t).set({ status: 'confirmed' }).where(eq(t.id, id)).run();
}

// Right: atomic, race-loser identifies itself via meta.changes
const result = await db
  .update(t)
  .set({ status: 'confirmed', confirmedAt: nowIso })
  .where(and(eq(t.id, id), eq(t.status, 'held')))
  .run();
if (result.meta.changes === 0) {
  // Someone else already flipped it. Branch into the race-loser path.
}
```

Multiple flips that must all land together go in `db.batch([...])`. The batch is the transaction boundary.

## 24. Migrations

`drizzle-kit generate` produces SQL into `drizzle/`. `wrangler d1 migrations apply <name> --local` for dev, `--remote` for prod. Back up the prod DB before applying remote migrations (a `db:backup` script that exports the schema + critical tables is the cheap safety net).
