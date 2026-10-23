# Deviations and implementation clarifications

Each entry: date, type, description, effect on results.

## D1 — 2026-10-23 — Administrative (no effect on analysis)
The files tagged `protocol-v1.0` (commit f722990, 2026-10-23T13:32:32+03:00) were uploaded from the pre-freeze package, so the header and status line of `PROTOCOL.md` (and the title line of `README.md`) still read "draft v0.9 — NOT YET FROZEN". Every other line of the protocol is identical to the intended frozen version. A follow-up commit corrects only these lines. **The analysis plan contained in the tagged commit is the binding protocol.** Effect on results: none.
