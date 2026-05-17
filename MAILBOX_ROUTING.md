# MAILBOX_ROUTING.md — the inbox → inject/result routing rule

Established 2026-05-17 (workstream 2). This file describes the
top-level repo structure and the routing ritual that keeps `mailbox/`
healthy.

---

## Top-level structure

```
mailbox/   pure INBOX — sector teams drop new files here. Cleaned at every
           stage commit after relevant files have been cloned out.

inject/    OUTBOX → LEAP. One subdirectory per sector. Adapter
           (build_canonical.py) + injector (inject_to_leap.py,
           CanonicalInjector subclass) + canonical CSVs + guides.
           Long-lived. Edits here flow upstream into LEAP via COM.

result/    OUTBOX ← LEAP. One subdirectory per harvest cycle
           (result/<YYYYMMDD>/). Probes (CanonicalProber subclasses)
           + result CSVs + joined CSVs + per-cycle SOP docs.
           Append-only as new harvests run.

infeas/    SCRATCH — diagnostic .sqlite snapshots for infeasibility
           triage. Separate from inbox/outbox model; stays put.

nemo_read/ LIBRARY source.
docs/      Reference documentation.
tests/     pytest suites.
```

`mailbox/` is the only one of these that grows AND shrinks. The
others are append-only (or near-enough).

---

## The routing ritual

When the user drops files in `mailbox/<YYYYMMDD>/`:

1. **Inspect.** Read what was dropped; understand its purpose. Confirm
   with the user if anything is ambiguous (§A.9 applies here too —
   even for non-COM work, confirm intent).

2. **Classify each file.** Possible destinations:
   - **inject-side** (CSV row authoring, supply data, demand updates,
     anything that flows upstream into LEAP) → `inject/<domain>/`
   - **result-side** (probe outputs, harvested CSVs, analysis scripts
     on completed results) → `result/<YYYYMMDD>/`
   - **diagnostic-only** (one-off probe outputs that won't be reused)
     → stays in mailbox until sweep
   - **truly raw user-drop** (.leap, .xlsx the user wants archived,
     etc.) → may stay in mailbox/, or be moved to a date subfolder

3. **Clone, don't move.** Use plain `cp` (or `git add` after `cp`) so
   the file exists in BOTH `mailbox/<date>/` and its destination.
   Originals stay in mailbox as an audit trail until the next sweep.

4. **Update the relevant artifacts.** If the file changes a canonical
   CSV / authoring guide / SOP, edit those in `inject/` or
   `result/` — not in `mailbox/`.

5. **At stage-commit time: sweep.** Before committing:
   - Confirm every file in `mailbox/<date>/` has either been cloned
     to its destination OR is intentionally archive-only.
   - `git rm` the swept files in the same commit. Diff shows
     deletions; user reviews before approving.
   - Empty date folders left behind: `git rm -r mailbox/<date>/`.

The user (yyuwonogit) reviews diffs before approving any commit
involving `git rm`, so the sweep is not destructive without consent.

---

## Why this exists

Before 2026-05-17 the `mailbox/` folder was overloaded — it held
sector authoring pipelines (`bioenergy/`, `fossil/`, `power/`) AND
result-harvest cycles (`20260505/`, `20260513/`) AND raw user drops
(`.xlsx` files etc.). One folder, three meanings. Hard to reason
about, especially for new sessions trying to figure out where
something lives.

Now:
- A file in `inject/<domain>/` = part of a sector's authoring pipeline
- A file in `result/<YYYYMMDD>/` = part of a harvest cycle's outputs
- A file in `mailbox/` = unrouted, waiting for the next session to
  classify

---

## See also

- [CLAUDE.md §3](CLAUDE.md) — repo layout
- [CLAUDE.md §5](CLAUDE.md) — adding a new mailbox domain (now
  routes to `inject/<new_domain>/`)
- [docs/FLOWS.md](docs/FLOWS.md) — the three standardised flows
  (inject / results harvest / infeasibility triage); all three
  start with "user drops in mailbox" and route from there.
