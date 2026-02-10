# Remotion Video Design System

This file defines the visual design rules for generated Remotion videos. Claude will use these settings when creating video compositions.

## Project Design File

If your project has a `design.md` or `design-system.md` in the root, the skill will automatically read and apply those design tokens. Otherwise, these defaults are used.

---

## Colors

### Primary Palette
```json
{
  "colors": {
    "navy": "#1E3A5F",
    "primary": "#2C5282",
    "sky": "#A3C4E8",
    "ice": "#E8F1F8",
    "white": "#FFFFFF",
    "offWhite": "#FAFAFA",
    "gray": "#6B7280",
    "darkGray": "#374151"
  }
}
```

### Accent Colors
```json
{
  "accents": {
    "rose": "#F43F5E",
    "roseLight": "#FDA4AF",
    "gold": "#D4A574",
    "goldLight": "#F5E6D3",
    "teal": "#0D9488",
    "purple": "#7C3AED"
  }
}
```

### Gradients
```json
{
  "gradients": {
    "light": "linear-gradient(135deg, offWhite 0%, ice 50%, sky 100%)",
    "elegant": "linear-gradient(135deg, goldLight 0%, offWhite 50%, roseLight 100%)",
    "warm": "linear-gradient(135deg, offWhite 0%, goldLight 100%)",
    "dark": "linear-gradient(180deg, rgba(30,58,95,0.7) 0%, rgba(30,58,95,0.9) 100%)"
  }
}
```

---

## Typography

### Font Families
```json
{
  "fonts": {
    "heading": "'Clash Display', 'Poppins', sans-serif",
    "body": "'Inter', sans-serif",
    "accent": "'Playfair Display', serif"
  }
}
```

### Font Sizes (Portrait 1080x1920)
| Element | Size | Weight | Line Height |
|---------|------|--------|-------------|
| Hero Title | 72-80px | 700 | 1.1 |
| Section Title | 48-56px | 700 | 1.2 |
| Subtitle | 28-32px | 600 | 1.3 |
| Body Large | 24-26px | 400 | 1.5 |
| Body | 18-20px | 400 | 1.5 |
| Label | 14-16px | 500 | 1.4 |
| Caption | 12-14px | 400 | 1.4 |

### Text Styles
```json
{
  "textStyles": {
    "heroTitle": {
      "fontFamily": "heading",
      "fontSize": 72,
      "fontWeight": 700,
      "letterSpacing": "-0.02em",
      "textTransform": "none"
    },
    "sectionTitle": {
      "fontFamily": "heading",
      "fontSize": 48,
      "fontWeight": 700,
      "letterSpacing": "-0.01em"
    },
    "label": {
      "fontFamily": "body",
      "fontSize": 16,
      "fontWeight": 500,
      "letterSpacing": "0.15em",
      "textTransform": "uppercase"
    }
  }
}
```

---

## Layout & Spacing

### Video Dimensions
- **Portrait (Social)**: 1080 x 1920 (9:16)
- **Landscape (YouTube)**: 1920 x 1080 (16:9)
- **Square (Instagram)**: 1080 x 1080 (1:1)

### Spacing Scale
```json
{
  "spacing": {
    "xs": 8,
    "sm": 16,
    "md": 24,
    "lg": 40,
    "xl": 60,
    "2xl": 80,
    "3xl": 120
  }
}
```

### Safe Zones
- **Horizontal Padding**: 50-60px
- **Vertical Padding**: 70-80px
- **Bottom Safe Zone**: 150px (for social media UI)

---

## Animation

### Timing
```json
{
  "animation": {
    "fps": 30,
    "transitionFrames": 18,
    "fadeInFrames": 30,
    "staggerDelay": 10
  }
}
```

### Spring Configs
```json
{
  "springs": {
    "gentle": { "damping": 15, "stiffness": 80 },
    "snappy": { "damping": 12, "stiffness": 100 },
    "smooth": { "damping": 20, "stiffness": 60 },
    "bouncy": { "damping": 10, "stiffness": 120 }
  }
}
```

### Easing
- **Fade In**: `interpolate(frame, [0, 30], [0, 1])`
- **Slide Up**: `translateY(interpolate(spring, [0, 1], [40, 0]))`
- **Scale In**: `scale(spring({ frame, fps, config: { damping: 12 } }))`

---

## Components

### Cards
```json
{
  "card": {
    "background": "rgba(255, 255, 255, 0.9)",
    "borderRadius": 16,
    "padding": "28px 24px",
    "boxShadow": "0 4px 20px rgba(0, 0, 0, 0.05)",
    "borderLeft": "4px solid accent"
  }
}
```

### Buttons / CTAs
```json
{
  "button": {
    "primary": {
      "background": "navy",
      "color": "white",
      "borderRadius": 100,
      "padding": "24px 55px",
      "fontSize": 42,
      "fontWeight": 600
    },
    "secondary": {
      "background": "rose",
      "color": "white",
      "borderRadius": 100,
      "padding": "14px 32px",
      "fontSize": 18,
      "fontWeight": 500
    }
  }
}
```

### Icons
- **Size**: 48-60px for feature icons
- **Style**: Outline stroke (1.5-2px)
- **Color**: Match section accent or white on dark backgrounds

---

## Scene Types

### Hero Scene
- Full-bleed background image or gradient
- Centered logo (80-120px)
- Large title with subtle animation
- Tagline/subtitle below

### Content Scene
- Gradient background
- Section title at top
- Cards or list items with staggered animation
- Supporting text at bottom

### Feature Scene
- Icon or illustration
- Title and description
- Clean, focused layout

### CTA Scene
- Dark overlay on image
- Inverted logo (white)
- Large phone number/contact
- Action prompt badge

---

## Brand Elements

### Logo Usage
- **Light Background**: Use original logo
- **Dark Background**: Use `filter: brightness(0) invert(1)`
- **Sizes**: 60px (small), 80px (medium), 120px (large)

### Decorative Elements
- Subtle gradient shifts on backgrounds
- Rounded corners (16-28px)
- Frosted glass effect: `backdrop-filter: blur(20px)`
- Thin borders: `1px solid rgba(255, 255, 255, 0.15)`

---

## Usage in Remotion

```tsx
// Import design tokens
const COLORS = {
  navy: "#1E3A5F",
  primary: "#2C5282",
  // ... from design system
};

const FONTS = {
  heading: "'Clash Display', sans-serif",
  body: "'Inter', sans-serif",
};

// Use in components
<div style={{
  fontFamily: FONTS.heading,
  fontSize: 48,
  color: COLORS.navy,
}}>
  Section Title
</div>
```
