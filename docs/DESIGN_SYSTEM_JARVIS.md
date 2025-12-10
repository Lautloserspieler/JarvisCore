# 🎨 JARVIS Design System - Futuristic UI Theme

**Version:** 2.0.0  
**Last Updated:** December 10, 2025  
**Theme:** Cyberpunk / Sci-Fi / Arc Reactor Inspired

---

## 🎯 Design Philosophy

> "A sleek, futuristic interface inspired by Tony Stark's JARVIS AI - combining cutting-edge technology aesthetics with functional elegance."

### Core Principles

1. **High-Tech Aesthetics** - Cyan glows, grid overlays, scanlines
2. **Readability First** - High contrast, clear typography
3. **Smooth Animations** - Pulsing glows, floating elements, ripples
4. **Information Density** - Maximize data without clutter
5. **Consistency** - Unified color palette across all components

---

## 🎨 Color Palette

### Base Colors

#### Background Hierarchy

```css
/* Level 0: Darkest - Main background */
--background: hsl(222, 47%, 4%)      /* #060a10 - Deep space black */
--jarvis-dark: hsl(222, 47%, 3%)     /* #050912 - Deeper variant */

/* Level 1: Card backgrounds */
--card: hsl(222, 47%, 7%)            /* #0d1421 - Card surface */

/* Level 2: Elevated surfaces */
--secondary: hsl(210, 80%, 20%)      /* #0a2540 - Deep blue panels */

/* Level 3: Interactive elements */
--muted: hsl(222, 30%, 15%)          /* #1b2332 - Muted backgrounds */
--input: hsl(200, 50%, 15%)          /* #132633 - Input fields */
```

**Python RGB Equivalents:**
```python
COLORS = {
    'bg_main': (6, 10, 16, 255),         # Background
    'bg_dark': (5, 9, 18, 255),          # Jarvis Dark
    'bg_card': (13, 20, 33, 255),        # Cards
    'bg_panel': (10, 37, 64, 255),       # Panels
    'bg_muted': (27, 35, 50, 255),       # Muted
    'bg_input': (19, 38, 51, 255),       # Inputs
}
```

#### Primary Colors - Electric Cyan

```css
/* Core JARVIS cyan - Arc Reactor blue */
--primary: hsl(195, 100%, 50%)           /* #00bfff - Bright cyan */
--jarvis-core: hsl(185, 100%, 60%)       /* #33ffff - Lighter cyan */
--jarvis-glow: hsl(195, 100%, 50%)       /* #00bfff - Glow color */
--accent: hsl(185, 100%, 45%)            /* #00e6e6 - Vibrant cyan */
--jarvis-pulse: hsl(200, 100%, 70%)      /* #66ccff - Pulse effect */
```

**Python RGB:**
```python
COLORS = {
    'cyan_primary': (0, 191, 255, 255),   # Primary cyan
    'cyan_core': (51, 255, 255, 255),     # JARVIS core
    'cyan_glow': (0, 191, 255, 255),      # Glow
    'cyan_accent': (0, 230, 230, 255),    # Accent
    'cyan_pulse': (102, 204, 255, 255),   # Pulse
}
```

#### Text Colors

```css
--foreground: hsl(200, 100%, 95%)        /* #e6f7ff - Almost white */
--muted-foreground: hsl(200, 30%, 60%)   /* #7a99ad - Muted text */
--primary-foreground: hsl(222, 47%, 4%)  /* #060a10 - Text on cyan */
```

**Python RGB:**
```python
COLORS = {
    'text_primary': (230, 247, 255, 255),  # Main text
    'text_muted': (122, 153, 173, 255),    # Secondary text
    'text_dark': (6, 10, 16, 255),         # Text on buttons
}
```

#### Semantic Colors

```css
--destructive: hsl(0, 72%, 51%)          /* #dc2626 - Red error */
--warning: hsl(38, 92%, 50%)             /* #f59e0b - Orange warning */
--success: hsl(142, 76%, 36%)            /* #16a34a - Green success */
```

**Python RGB:**
```python
COLORS = {
    'error': (220, 38, 38, 255),          # Red
    'warning': (245, 158, 11, 255),       # Orange
    'success': (22, 163, 74, 255),        # Green
}
```

#### Border & Effects

```css
--border: hsl(200, 50%, 20%)             /* #1a3d52 - Border color */
--jarvis-grid: hsl(200, 50%, 15%)        /* #132d3d - Grid lines */
--ring: hsl(195, 100%, 50%)              /* #00bfff - Focus ring */
```

**Python RGB:**
```python
COLORS = {
    'border': (26, 61, 82, 255),          # Borders
    'grid': (19, 45, 61, 255),            # Grid overlay
    'focus': (0, 191, 255, 255),          # Focus ring
}
```

### Complete Python Color Dictionary

```python
# desktop/jarvis_theme.py

class JARVISTheme:
    """JARVIS Futuristic Color Palette"""
    
    # Backgrounds (Darkest to Lightest)
    BG_MAIN = (6, 10, 16, 255)           # Deep space black
    BG_DARK = (5, 9, 18, 255)            # Deepest
    BG_CARD = (13, 20, 33, 255)          # Card surface
    BG_PANEL = (10, 37, 64, 255)         # Elevated panels
    BG_MUTED = (27, 35, 50, 255)         # Muted areas
    BG_INPUT = (19, 38, 51, 255)         # Input fields
    
    # Primary - Electric Cyan (JARVIS Core)
    CYAN_PRIMARY = (0, 191, 255, 255)    # Main cyan
    CYAN_CORE = (51, 255, 255, 255)      # Lighter core
    CYAN_GLOW = (0, 191, 255, 255)       # Glow effect
    CYAN_ACCENT = (0, 230, 230, 255)     # Accent cyan
    CYAN_PULSE = (102, 204, 255, 255)    # Pulse animation
    
    # Text
    TEXT_PRIMARY = (230, 247, 255, 255)  # Almost white
    TEXT_MUTED = (122, 153, 173, 255)    # Secondary text
    TEXT_DARK = (6, 10, 16, 255)         # On colored bg
    
    # Semantic
    ERROR = (220, 38, 38, 255)           # Red
    WARNING = (245, 158, 11, 255)        # Orange
    SUCCESS = (22, 163, 74, 255)         # Green
    INFO = (59, 130, 246, 255)           # Blue
    
    # Borders & Effects
    BORDER = (26, 61, 82, 255)           # Border lines
    GRID = (19, 45, 61, 255)             # Grid overlay
    FOCUS = (0, 191, 255, 255)           # Focus ring
    
    # Alpha Variants (for glows)
    CYAN_GLOW_10 = (0, 191, 255, 26)     # 10% opacity
    CYAN_GLOW_30 = (0, 191, 255, 77)     # 30% opacity
    CYAN_GLOW_50 = (0, 191, 255, 128)    # 50% opacity
    CYAN_GLOW_80 = (0, 191, 255, 204)    # 80% opacity
```

---

## 🔤 Typography

### Font Families

#### Orbitron (Headings & Tech Elements)

**Source:** Google Fonts  
**Usage:** Headers, Model Names, Status Text, Tech Labels  
**Weights:** 400, 500, 600, 700, 800, 900  
**Character:** Futuristic, Geometric, Wide Letters

**CSS:**
```css
@import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;500;600;700;800;900&display=swap');

h1, h2, h3, h4, h5, h6 {
  font-family: 'Orbitron', sans-serif;
}
```

**Python (DearPyGui):**
```python
# Download Orbitron-Regular.ttf from Google Fonts
with dpg.font_registry():
    orbitron_large = dpg.add_font("fonts/Orbitron-Bold.ttf", 28)
    orbitron_medium = dpg.add_font("fonts/Orbitron-Medium.ttf", 22)
    orbitron_regular = dpg.add_font("fonts/Orbitron-Regular.ttf", 18)

# Apply to headers
dpg.add_text("J.A.R.V.I.S.", font=orbitron_large)
```

#### Space Grotesk (Body Text)

**Source:** Google Fonts  
**Usage:** Body text, Descriptions, Chat, Logs  
**Weights:** 300, 400, 500, 600, 700  
**Character:** Modern, Readable, Technical

**CSS:**
```css
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;500;600;700&display=swap');

body {
  font-family: 'Space Grotesk', sans-serif;
}
```

**Python:**
```python
with dpg.font_registry():
    space_grotesk = dpg.add_font("fonts/SpaceGrotesk-Regular.ttf", 18)
    space_grotesk_light = dpg.add_font("fonts/SpaceGrotesk-Light.ttf", 16)

dpg.bind_font(space_grotesk)  # Default
```

### Font Scale

| Element | Font | Size | Weight | Usage |
|---------|------|------|--------|-------|
| **Display** | Orbitron | 48px | 900 | Splash screens |
| **H1** | Orbitron | 36px | 700 | Main titles |
| **H2** | Orbitron | 28px | 600 | Section headers |
| **H3** | Orbitron | 22px | 500 | Subsection headers |
| **Body** | Space Grotesk | 18px | 400 | Normal text |
| **Small** | Space Grotesk | 16px | 400 | Helper text |
| **Code** | JetBrains Mono | 16px | 400 | Logs, Code |

---

## ✨ Visual Effects

### 1. Glow Effects

#### Primary Glow (Cyan)

**CSS:**
```css
.glow-primary {
  box-shadow: 0 0 20px hsl(195 100% 50% / 0.5),
              0 0 40px hsl(195 100% 50% / 0.3),
              0 0 60px hsl(195 100% 50% / 0.1);
}
```

**Python (DearPyGui - Simulated with colored border):**
```python
# DearPyGui doesn't support box-shadow directly
# Workaround: Multi-layer border simulation

def create_glowing_element(tag: str, width: int, height: int):
    # Outer glow (largest, most transparent)
    with dpg.child_window(width=width+20, height=height+20, border=False):
        dpg.add_theme_color(dpg.mvThemeCol_ChildBg, (0, 191, 255, 26))  # 10% cyan
        
        # Mid glow
        with dpg.child_window(width=width+10, height=height+10, border=False):
            dpg.add_theme_color(dpg.mvThemeCol_ChildBg, (0, 191, 255, 77))  # 30%
            
            # Inner element
            with dpg.child_window(width=width, height=height, border=True, tag=tag):
                dpg.add_theme_color(dpg.mvThemeCol_Border, (0, 191, 255, 255))  # 100%
                # Content here
```

#### Text Glow

**CSS:**
```css
.glow-text {
  text-shadow: 0 0 10px hsl(195 100% 50% / 0.8),
               0 0 20px hsl(195 100% 50% / 0.5),
               0 0 30px hsl(195 100% 50% / 0.3);
}
```

**Python (Not directly supported - use colored text):**
```python
# Workaround: Use bright cyan for "glow" effect
dpg.add_text("JARVIS ONLINE", color=(51, 255, 255, 255))  # Bright cyan
```

### 2. Grid Overlay

**CSS:**
```css
.grid-overlay {
  background-image: 
    linear-gradient(hsl(200 50% 15% / 0.1) 1px, transparent 1px),
    linear-gradient(90deg, hsl(200 50% 15% / 0.1) 1px, transparent 1px);
  background-size: 50px 50px;
}
```

**Python (DearPyGui - Draw with drawlist):**
```python
def create_grid_overlay(width: int, height: int, grid_size: int = 50):
    """Draw grid overlay using drawlist"""
    with dpg.drawlist(width=width, height=height):
        # Vertical lines
        for x in range(0, width, grid_size):
            dpg.draw_line(
                (x, 0), (x, height),
                color=(19, 45, 61, 26),  # Grid color with alpha
                thickness=1
            )
        
        # Horizontal lines
        for y in range(0, height, grid_size):
            dpg.draw_line(
                (0, y), (width, y),
                color=(19, 45, 61, 26),
                thickness=1
            )
```

### 3. Scanlines Effect

**CSS:**
```css
.scanlines {
  background: repeating-linear-gradient(
    0deg,
    transparent,
    transparent 2px,
    hsl(195 100% 50% / 0.03) 2px,
    hsl(195 100% 50% / 0.03) 4px
  );
}
```

**Python (DearPyGui):**
```python
def create_scanlines(width: int, height: int, spacing: int = 4):
    """Create CRT scanline effect"""
    with dpg.drawlist(width=width, height=height):
        for y in range(0, height, spacing):
            dpg.draw_line(
                (0, y), (width, y),
                color=(0, 191, 255, 8),  # Very transparent cyan
                thickness=2
            )
```

### 4. Animated Border

**CSS:**
```css
.animated-border {
  background: linear-gradient(90deg, 
    hsl(195 100% 50%) 0%, 
    hsl(185 100% 45%) 50%, 
    hsl(195 100% 50%) 100%);
  background-size: 200% 100%;
  animation: border-flow 3s linear infinite;
}

@keyframes border-flow {
  0% { background-position: 0% 50%; }
  100% { background-position: 200% 50%; }
}
```

**Python (Not directly supported - use color cycling):**
```python
import time
import threading

def animate_border(border_tag: str):
    """Cycle border color for animation effect"""
    colors = [
        (0, 191, 255, 255),    # Cyan
        (0, 230, 230, 255),    # Accent
        (51, 255, 255, 255),   # Core
        (0, 230, 230, 255),    # Accent
    ]
    idx = 0
    
    while True:
        dpg.configure_item(border_tag, border_color=colors[idx % len(colors)])
        idx += 1
        time.sleep(0.5)

# Start in thread
threading.Thread(target=animate_border, args=("my_window",), daemon=True).start()
```

---

## 🎬 Animations

### 1. Pulse Glow (Arc Reactor Effect)

**CSS:**
```css
@keyframes pulse-glow {
  0%, 100% {
    opacity: 0.6;
    transform: scale(1);
  }
  50% {
    opacity: 1;
    transform: scale(1.05);
  }
}

.pulse-glow {
  animation: pulse-glow 2s ease-in-out infinite;
}
```

**Usage:** Status indicators, Active model badges, Core UI elements

**Python Implementation:**
```python
import math
import time

def pulse_glow_animation(element_tag: str):
    """Animate opacity for pulsing effect"""
    start_time = time.time()
    
    while True:
        elapsed = time.time() - start_time
        # Calculate pulse (0.6 to 1.0)
        opacity = 0.6 + 0.4 * abs(math.sin(elapsed * math.pi))  # 2s period
        
        # Update element alpha
        color = dpg.get_item_configuration(element_tag).get('color', (255, 255, 255, 255))
        new_color = (*color[:3], int(255 * opacity))
        dpg.configure_item(element_tag, color=new_color)
        
        time.sleep(0.033)  # ~30 FPS
```

### 2. Core Rotate (Loading Spinner)

**CSS:**
```css
@keyframes core-rotate {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.core-rotate {
  animation: core-rotate 3s linear infinite;
}
```

**Python (Draw circle with rotating indicator):**
```python
def draw_loading_spinner(x: int, y: int, radius: int = 30):
    """Draw JARVIS-style loading spinner"""
    angle = (time.time() * 120) % 360  # Rotate at 120 deg/s
    
    with dpg.drawlist():
        # Outer ring
        dpg.draw_circle(
            (x, y), radius,
            color=(0, 191, 255, 128),
            thickness=3,
            fill=(0, 0, 0, 0)
        )
        
        # Rotating arc indicator
        end_x = x + radius * math.cos(math.radians(angle))
        end_y = y + radius * math.sin(math.radians(angle))
        dpg.draw_line((x, y), (end_x, end_y), color=(51, 255, 255, 255), thickness=2)
```

### 3. Float Animation

**CSS:**
```css
@keyframes float {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-10px); }
}

.float {
  animation: float 3s ease-in-out infinite;
}
```

**Usage:** Floating cards, badges, status icons

### 4. Fade In Up (Entry Animation)

**CSS:**
```css
@keyframes fade-in-up {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.fade-in-up {
  animation: fade-in-up 0.5s ease-out;
}
```

**Python (Gradual opacity + position change):**
```python
def fade_in_up(element_tag: str, duration: float = 0.5):
    """Fade in element from below"""
    steps = 30
    delay = duration / steps
    start_y = dpg.get_item_pos(element_tag)[1]
    target_y = start_y - 20
    
    for i in range(steps):
        progress = i / steps
        new_y = start_y + (target_y - start_y) * progress
        opacity = int(255 * progress)
        
        dpg.set_item_pos(element_tag, [dpg.get_item_pos(element_tag)[0], new_y])
        # Update alpha (if applicable)
        
        time.sleep(delay)
```

### 5. Ripple Effect (Button Click)

**CSS:**
```css
@keyframes ripple {
  0% {
    transform: scale(0.8);
    opacity: 1;
  }
  100% {
    transform: scale(2.4);
    opacity: 0;
  }
}
```

**Usage:** Button clicks, interactive elements

---

## 🧩 Component Examples

### 1. JARVIS Header

**Design:**
```
┌──────────────────────────────────────────────────────────────────────┐
│  ◉ J.A.R.V.I.S.               🟢 ONLINE              v2.0.0     │
│     Just A Rather Very Intelligent System                         │
└──────────────────────────────────────────────────────────────────────┘
```

**Python Code:**
```python
with dpg.group(horizontal=True):
    # Arc Reactor Icon (pulsing)
    dpg.add_text("◉", color=JARVISTheme.CYAN_CORE, tag="arc_reactor")
    dpg.bind_item_font(dpg.last_item(), orbitron_large)
    
    dpg.add_spacer(width=10)
    
    # Title
    dpg.add_text("J.A.R.V.I.S.", color=JARVISTheme.CYAN_PRIMARY)
    dpg.bind_item_font(dpg.last_item(), orbitron_large)
    
    dpg.add_spacer(width=200)
    
    # Status
    dpg.add_text("🟢 ONLINE", color=JARVISTheme.SUCCESS, tag="status")
    dpg.bind_item_font(dpg.last_item(), orbitron_medium)
    
    dpg.add_spacer(width=100)
    
    # Version
    dpg.add_text("v2.0.0", color=JARVISTheme.TEXT_MUTED)

# Subtitle
dpg.add_text(
    "    Just A Rather Very Intelligent System",
    color=JARVISTheme.TEXT_MUTED
)

# Start pulse animation on arc reactor
start_pulse_animation("arc_reactor")
```

### 2. Glowing Card

**Python Code:**
```python
with dpg.child_window(width=400, height=200, border=True):
    # Apply cyan border
    dpg.add_theme_color(dpg.mvThemeCol_Border, JARVISTheme.CYAN_PRIMARY)
    dpg.add_theme_color(dpg.mvThemeCol_ChildBg, JARVISTheme.BG_CARD)
    dpg.add_theme_style(dpg.mvStyleVar_ChildRounding, 12)
    dpg.add_theme_style(dpg.mvStyleVar_ChildBorderSize, 2)
    
    # Content
    dpg.add_text("SYSTEM STATUS", color=JARVISTheme.CYAN_CORE)
    dpg.bind_item_font(dpg.last_item(), orbitron_medium)
    
    dpg.add_separator()
    dpg.add_spacer(height=10)
    
    dpg.add_text("CPU: 45.3%", color=JARVISTheme.TEXT_PRIMARY)
    dpg.add_text("RAM: 16.2 GB", color=JARVISTheme.TEXT_PRIMARY)
    dpg.add_text("GPU: 30.1%", color=JARVISTheme.TEXT_PRIMARY)
```

### 3. Futuristic Button

**Python Code:**
```python
# Create themed button
with dpg.theme(tag="theme_jarvis_button") as theme:
    with dpg.theme_component(dpg.mvButton):
        dpg.add_theme_color(dpg.mvThemeCol_Button, JARVISTheme.CYAN_PRIMARY)
        dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, JARVISTheme.CYAN_CORE)
        dpg.add_theme_color(dpg.mvThemeCol_ButtonActive, JARVISTheme.CYAN_ACCENT)
        dpg.add_theme_color(dpg.mvThemeCol_Text, JARVISTheme.TEXT_DARK)
        dpg.add_theme_style(dpg.mvStyleVar_FrameRounding, 8)
        dpg.add_theme_style(dpg.mvStyleVar_FramePadding, 15, 10)

# Apply to button
btn = dpg.add_button(label="▶ EXECUTE", width=150, height=45)
dpg.bind_item_theme(btn, "theme_jarvis_button")
dpg.bind_item_font(btn, orbitron_medium)
```

### 4. Progress Bar with Glow

**Python Code:**
```python
with dpg.theme(tag="theme_progress_cyan") as theme:
    with dpg.theme_component(dpg.mvProgressBar):
        dpg.add_theme_color(dpg.mvThemeCol_PlotHistogram, JARVISTheme.CYAN_PRIMARY)
        dpg.add_theme_color(dpg.mvThemeCol_FrameBg, JARVISTheme.BG_INPUT)
        dpg.add_theme_style(dpg.mvStyleVar_FrameRounding, 10)

progress = dpg.add_progress_bar(
    default_value=0.65,
    width=-1,
    height=30,
    overlay="65.0%"
)
dpg.bind_item_theme(progress, "theme_progress_cyan")
```

---

## 📐 Layout Guidelines

### Spacing System

```python
SPACING = {
    'xs': 4,    # Micro spacing
    'sm': 8,    # Small spacing
    'md': 16,   # Medium spacing (default)
    'lg': 24,   # Large spacing
    'xl': 32,   # Extra large
    'xxl': 48,  # Huge gaps
}
```

### Border Radius

```python
RADIUS = {
    'sm': 4,    # Small elements
    'md': 8,    # Buttons
    'lg': 12,   # Cards
    'xl': 16,   # Panels
    'full': 999, # Circular
}
```

---

## 🚀 Implementation Checklist

### Phase 1: Core Theme
- [ ] Download Orbitron & Space Grotesk fonts
- [ ] Create `jarvis_theme.py` with color palette
- [ ] Apply base theme to all windows
- [ ] Update font bindings

### Phase 2: Components
- [ ] Redesign header with arc reactor icon
- [ ] Create glowing card components
- [ ] Style all buttons with cyan theme
- [ ] Update progress bars

### Phase 3: Effects
- [ ] Add pulse animation to status indicators
- [ ] Implement grid overlay (optional)
- [ ] Add loading spinner with rotation
- [ ] Border glow simulation

### Phase 4: Polish
- [ ] Smooth transitions on tab switches
- [ ] Hover effects on interactive elements
- [ ] Sound effects (optional)
- [ ] Particle effects for background (advanced)

---

## 📚 Resources

### Fonts
- **Orbitron:** https://fonts.google.com/specimen/Orbitron
- **Space Grotesk:** https://fonts.google.com/specimen/Space+Grotesk
- **JetBrains Mono:** https://www.jetbrains.com/lp/mono/

### Color Tools
- **HSL to RGB Converter:** https://www.rapidtables.com/convert/color/hsl-to-rgb.html
- **Coolors Palette:** https://coolors.co/

### Inspiration
- **Iron Man UI:** Arc Reactor, Holographic displays
- **Cyberpunk 2077:** Neon aesthetics
- **Tron Legacy:** Grid overlays, cyan glows

---

**Created:** 2025-12-10  
**Version:** 2.0.0  
**Status:** ✅ Ready for Implementation
