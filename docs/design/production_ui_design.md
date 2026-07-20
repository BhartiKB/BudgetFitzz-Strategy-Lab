# Production UI design

## Purpose

The Production route is an original, manifest-driven workspace for taking one
planned BudgetFitzz asset from approved evidence through provider selection,
generation, validation, human approval, and preserved versions. It does not
claim that an external provider generated media unless provenance records show
that it did.

## Visual system

- **Base:** warm ivory reading surfaces, charcoal editorial sections, and
  restrained forest/sage continuity with the rest of the application.
- **Accents:** muted coral, dusty lavender, and citrus status highlights.
- **Type:** existing editorial display face for key statements; existing UI face
  for labels, controls, metrics, and provenance.
- **Shape:** 12–16px rounded containers, thin low-contrast dividers, generous
  spacing, and image/video-first compositions.
- **Motion:** short progressive-rise reveals and existing hover elevation only;
  the `prefers-reduced-motion` rule disables meaningful animation and transition
  time without hiding content.

## Information sequence

1. The dark hero states the approval safeguard and leads to the import controls.
2. The five-stage horizontal path explains why each generated asset exists.
3. The asset brief binds the selected plan item to its exact prompt metadata,
   active media, and approved caption.
4. The capability selector reads real provider state from the generated
   manifest rather than advertising availability.
5. Existing prompt export, manual import, validation, approval, provenance,
   and version history components remain the functional production controls.

## Accessibility and responsive behaviour

Controls use native buttons, links, labels, and selects. The desktop rail is
replaced by the existing primary mobile navigation at the small breakpoint. The
pipeline scrolls horizontally rather than compressing its explanatory text;
the asset workspace and provider selector stack; form controls retain their
normal native layout. The UI remains useful at a 390px viewport.
