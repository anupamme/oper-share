---
name: delivery-gate
description: >-
  The mandatory gate before delivery: hard-gate checklist, purpose-gate justifications and
  consistency locks, with the evidence required to claim the work is done.
---

## Delivery Gate (Mandatory)

Run this gate BEFORE delivering. Output its status with your deliverable as a **PASS/FAIL report**: one line per item, and every `PASS` backed by concrete evidence (e.g. "R-26 PASS: every button has a real `href` or `onClick`; no dead controls", "R-35 PASS: ran the build and clicked every control: Signup -> /signup, empty form -> validation, mobile menu -> opens, no console errors").
If any item is **FAIL** (or any answer is **yes**), do not deliver: fix it first, then re-run. A report containing a FAIL must never be shipped.

The gate has four blocks: Hard Gate (absolute), Purpose-Gate (technique + written reason), Liveliness (dials + levers), Craftsmanship & Quality Locks (C-1..C-5 plus the consistency locks R-05, R-11, R-15, R-16, R-20, R-21, R-29, R-30, R-31).

### Block 1: Hard Gate (absolute)

Before declaring the design done, answer every question below. All answers must be **no**:

- [ ] Is there an em dash (`—`) anywhere in the text, outside the R-02 carve-out and any voice sample the owner approved under R-37? *(R-02)*
- [ ] Is there any horizontal overflow, text escaping its container, or broken layout on mobile? *(R-03)*
- [ ] Are there any statistics without a real source (10K+ Users, 99.9% Uptime, etc.)? *(R-17)*
- [ ] Are there any fictional testimonials (AI avatars, random names or job titles)? *(R-18)*
- [ ] Were any visual assets (logo, avatar/profile photo, statistics, testimonials, or navigation structure) created without explicit instructions or confirmation, and without an honest placeholder? *(R-23)*
- [ ] Are there navbar links pointing to sections or pages that do not exist? *(R-24)*
- [ ] Is there any text with contrast below the WCAG AA standard (4.5:1 for normal text, 3:1 for large text)? *(R-25)*
- [ ] Are there any buttons, dropdowns, or forms that do nothing, with no real behavior and no `// TODO` + visible label? *(R-26)*
- [ ] Does the UI lack an empty state, loading state, or error state? *(R-27)*
- [ ] Does the FAQ contain generic questions that are not relevant to the product? *(R-28)*
- [ ] Can the UI not be navigated by keyboard (Tab, Enter, Escape) or is there no visible focus state? *(R-32)*
- [ ] Was any feature added by patching source/CSS with an external script instead of writing it in source? *(R-33)*
- [ ] If a theme toggle exists, does one mode (light or dark) break styles, fonts, or layout? *(R-34)*
- [ ] Was the app delivered without being run or built, or without a recorded click-through of every interactive element? *(R-35)*
- [ ] Are there any fabricated security, compliance, performance, or customer claims? *(R-36)*
- [ ] Was the design built without direction and not labeled *"draft without direction"* with honest default dials ENERGY 1 / RHYTHM 1 / MOTION 1? *(R-37)*
- [ ] Is there any realistically-styled content that was fabricated (testimonials, features, statistics, ghost links, fictional team) without a real source? *(R-38)*

### Block 2: Purpose-Gate (technique allowed, reason required)

For each technique, the technique itself is allowed. FAIL if it appears as a default without purpose, or if the reason is not written down:

- [ ] Do gradients/glows appear as a default with no stated hierarchy or brand purpose? *(R-01)*
- [ ] Are there generic icons (sparkle, star, magic, lightning, diamond, robot, orb), an icon set picked for its library look (Lucide-style), or icons irrelevant to their content, with no written relevance? *(R-04)*
- [ ] Is there a large monospace font, uppercase label with wide tracking, or a typeface chosen without a written brand-character reason? *(R-06)*
- [ ] Is there a background grid, blueprint, graph paper, or dot pattern without a written visual-identity purpose? *(R-07)*
- [ ] Are arrows (`→` / `↗`) placed on almost every button purely as decoration, with no written purpose? *(R-08)*
- [ ] Are there capsule badges ("AI Powered", "Beta", "New", "Secure", "Fast") with no real function, or the full capsule + thin border + glow + uppercase combination? *(R-09)*
- [ ] Is glassmorphism applied to more than 1-2 elements simultaneously (navbar + card + modal + sidebar)? *(R-10)*
- [ ] Is a large shadow applied to every component, with no written elevation reason, making the page feel like it is floating? *(R-12)*
- [ ] Is glow applied to cards, buttons, badges, icons, backgrounds, and borders simultaneously? *(R-13)*
- [ ] Do all feature cards have identical size, icon, padding, and layout, with no written hierarchy reason? *(R-14)*
- [ ] Do all elements use template animations simultaneously (Fade Up + Floating + Scale + Bounce) without a written UX purpose, or does the motion contradict the declared MOTION dial? *(R-19)*
- [ ] Are there generic illustrations (Undraw, Storyset, 3D blob) with no written product connection? *(R-22)*

### Block 3: Liveliness (required to be alive, not just clean)

All answers must be **yes**:

- [ ] Are the dials set and explicit (ENERGY / RHYTHM / MOTION declared)?
- [ ] Is the output consistent with the claimed dials? (RHYTHM 3 but uniform sections = FAIL)
- [ ] Is there at least one clear focal point per screen?
- [ ] Is whitespace structural (used to separate and set rhythm), not leftover?
- [ ] Is there one deliberate accent (not zero, not everywhere)?
- [ ] Is there an identity motif (one specific, repeated pattern, gesture, or typographic voice)?
- [ ] Was a Design Read declared before generation?

### Block 4: Craftsmanship & Quality Locks

All answers must be **no**:

- [ ] C-1: Is there any visual or copy decision whose only justification is "it's the AI default"? *(Intentionality)*
- [ ] C-2: Does any interactive element do nothing, with no clear label? *(Functional Completeness)*
- [ ] C-3: Does any section exist only to fill an AI template, not to serve the product's content? *(Content-Driven Composition)*
- [ ] C-4: Does the UI break in any state, theme, breakpoint, or without a mouse? *(Resilience)*
- [ ] C-5: Is any testimonial, statistic, or claim fabricated? *(Evidence Over Claims)*
- [ ] Does the layout follow an AI template (generic Hero+cards, "How It Works" always 3 steps, "Trusted By" logo bar, bento-grid mosaic, fake terminal window, 3 pricing columns, 4-column footer with no variation, uniform section rhythm), or does the section rhythm contradict the declared RHYTHM dial? *(R-05)*
- [ ] Are all elements (buttons, cards, inputs, badges) made pill-shaped with no radius variation? *(R-11)*
- [ ] Are CTAs still generic (Get Started, Learn More, Try Now, Explore, Discover)? *(R-15)*
- [ ] Are there any AI marketing buzzwords (AI Powered, Seamless, Revolutionary, Cutting Edge, etc.)? *(R-16)*
- [ ] Does the design still feel generic even if the logo and product name are swapped? *(R-20)*
- [ ] Was dark mode forced as a default without a branding/user reason, or was a required light/dark toggle deferred with an excuse? *(R-21)*
- [ ] Does the color palette exceed 2-3 core colors + 1 accent without a clear design system? *(R-29)*
- [ ] Does the overall design look like a clone of another popular product (Linear, Vercel, Stripe, Notion, etc.)? *(R-30)*
- [ ] Is there any major visual decision (color, layout, typography, spacing, cards, illustration) whose reason cannot be written in one line? *(R-31)*

If even one answer is **yes** (or **no** in Block 3), do not deliver. Fix it, re-run the gate, and only then ship. Delivery without a clean gate is a failure.
