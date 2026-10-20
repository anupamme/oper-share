# Visual review — offline artifact contract

Use a visual report to make a consequential comparison easier to inspect, not to
create another policy layer or replace implementation. The owner appreciates these
reports more often at meaningful design checkpoints (2026-10-04).

## Delivery

- One complete `.html` file in the owning workspace folder; existing work/plan
  location first. Honor an explicit output path. Do not hide the only artifact
  in an OS temp directory or create a separate directory map without request.
- Self-contained CSS and inline SVG/HTML diagrams. Use system fonts. No external
  scripts, fonts, analytics, CDN dependencies, fetches or remote assets.
- User-facing language follows the owner; workspace method documents stay English.
- Use the host's local HTML preview when available; no separate server required.
  Test the rendered page, real controls and relevant links; inspect browser errors.
  Do not claim it is self-contained based on the file extension alone.

## Content that earns the visual

A readable report should answer:

1. **What is the real goal?** Requested result and the boundary of this review.
2. **What was wrong?** Concrete evidence, not labels such as "messy" or "bad".
3. **What changed / is proposed?** Before→after responsibilities, paths or flow.
4. **Why this choice?** Owner decisions, alternative and meaningful trade-off.
5. **What is verified?** Exact scope, current evidence and unexercised claims.
6. **What remains?** Open work clearly separated from delivered changes.

For each material change/candidate show a short title, status, problem, response
and relevant source links. Distinguish implemented, proposed, owner-decided and
unverified; do not color an entire redesign green because a test suite passed.

## Visuals and navigation

Use the diagram that fits: before/after flow for responsibility changes, grouped
cards for decisions, a timeline for migration, or a matrix for evidence coverage.
A diagram is an explanation, not a precise inventory unless that was checked.

Keep semantic headings and landmarks, text alternatives for SVG, readable contrast,
visible keyboard focus and responsive stacking. Status uses text as well as color.
Native details/anchors can provide compact progressive disclosure without scripts.
If adding filters or a theme control, test them through real browser interactions;
do not add decorative controls that do nothing.

Use honest language. A hypothesis can remain uncertain; a simulated viewpoint is
not independent evidence, a format gate is not a semantic audit, and a local test
is not proof a client's rules were loaded. No mandatory scores or arbitrary
confidence percentages.

## Verification

- Parse/inspect the final HTML for external dependencies and correct artifact paths.
- Open the delivered page; inspect desktop and narrow viewport rendering.
- Exercise actual navigation/disclosure and verify relevant links resolve.
- Check console/network failures and horizontal overflow; fix the final version
  and repeat affected checks.
- Keep the report's date/evidence aligned with the final tested checkpoint.
  Later implementation changes require updating the report where material.

The visual is a review surface, not proof of model behavior or permission to
publish. Keep the executable acceptance evidence in the owning task record.
