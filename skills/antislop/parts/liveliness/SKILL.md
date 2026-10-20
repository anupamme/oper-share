---
name: liveliness
description: >-
  The liveliness toolkit — three dials, the levers that turn them into visual decisions, how
  to set the dials from a design read — plus the functional patterns list. Load when the
  output is correct but lifeless.
---

## Part 3: Liveliness Toolkit

A filter can remove slop, but it cannot add energy. Removing slop leaves a void, and the model fills that void with its most generic output. Liveliness must be **added** deliberately. This Part is that mechanism: positive requirements, not bans.

### Three Dials (required)

Every design must set three dials explicitly, derived from DESIGN.md or the Design Read, and hold them from the first section to the last:

| Dial | 1 (Calm) | 2 (Balanced) | 3 (Bold) | What it answers |
|---|---|---|---|---|
| **ENERGY** | Linear, GOV.UK | Stripe, Vercel | Awwwards, agency portfolio | How hard does this design say hello? |
| **RHYTHM** | Uniform grid, predictable | Consistent with a few breaks | Asymmetric, mixed compositions | How much do sections change from each other? |
| **MOTION** | Hover states only | Scroll-reveal, transitions | Parallax, pin, choreography | How much motion, and why? |

The anchors (Linear, GOV.UK, Stripe, Vercel, Awwwards) are taste references for judging a value, not things to imitate.

Why three levels and not ten: a model and a reviewer can reliably tell "is this section uniform or varied?" (binary, checkable). They cannot reliably judge "is this a 6 or a 7?" (continuous, uncheckable). Three levels make liveliness enforceable.

Example sets: a designer portfolio sets ENERGY 3, RHYTHM 3, MOTION 2. A public-service site sets ENERGY 1, RHYTHM 1, MOTION 1.

### Levers (how the dials become visual decisions)

These are tools for hitting the dial values, not bans:

- **One focal point per screen**: exactly one element that is clearly the most important on every screen; the rest defer to it
- **Hierarchical contrast**: size, weight, and color are differentiated on purpose, not randomly
- **Whitespace as structure**: empty space separates and sets rhythm, not leftover space
- **One deliberate accent**: one color or gesture used sparingly at the key moment. Zero accents is sterile; an accent everywhere is slop
- **Identity motif**: one pattern, gesture, or typographic voice that is specific and repeated, making the design "belong" to the product

### Design Read (how the dials are set)

Before generating, declare one line:

> Reading this as: `<page kind>` for `<audience>`, in a `<visual language>` style, dial `<ENERGY/RHYTHM/MOTION>`.

Example: *"Reading this as: B2B SaaS landing for technical buyers, with a Linear-style minimalist language, dial ENERGY 1 / RHYTHM 2 / MOTION 1."*

1. **Direction exists** (DESIGN.md or a brief that expresses energy and mood): infer the dials from it and proceed. DESIGN.md may optionally include a line like `Dial: ENERGY 2 / RHYTHM 3 / MOTION 1`; if present, use it directly.
2. **Direction is ambiguous**: ask exactly ONE decisive question, never a question dump. Example: *"Should this feel closer to Linear-clean or Awwwards-experimental?"* Use the answer to set the dials.
3. **No direction and the user cannot be asked**: label the output *"draft without direction"*, set the honest default dials **ENERGY 1 / RHYTHM 1 / MOTION 1** (see R-37), and do not present it as a deliverable.


## Functional Patterns

"What works" means one of these, depending on context:

- **Anchor to a real section**: `href="#pricing"` where `#pricing` exists
- **Scroll to relevant content** for a "Learn more" style link
- **Open a modal or dialog** for a quick action (closable with Escape)
- **Toggle a state**: mobile menu, theme, accordion, tabs
- **External action**: `mailto:`, a real product URL
- **Form submit** with visible feedback

If none of these applies to an element, the element should not exist.

---
