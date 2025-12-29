# NovaRium UI/UX Design Brief for Stitch

> **Purpose**: This document provides comprehensive technical context and design requirements for Stitch AI to generate UI/UX improvement proposals for the NovaRium platform.

---

## 1. PROJECT MISSION

### What is NovaRium?

NovaRium is an **educational A/B testing simulation platform** designed to train aspiring data analysts and product managers. The name combines "Nova" (Latin for "new," symbolizing supernovas that illuminate the cosmos) and "Arium" (Latin suffix meaning "a place for"), representing a training ecosystem where analysts are born.

**Core Value Proposition**:
- "Where Data Analysts are Born" - A hands-on learning environment
- Users design, run, and analyze A/B tests on a simulated e-commerce app (NovaEats)
- Bridges the gap between textbook knowledge and real-world experimentation
- Features real database integration (Supabase PostgreSQL) for authentic data handling

**Target Users**:
1. **Junior Data Analysts** - Learning A/B testing methodology
2. **Product Managers** - Understanding data-driven decision making
3. **Students** - Building portfolio projects

---

## 2. CURRENT ARCHITECTURE

### Tech Stack

| Layer | Technology | Notes |
|-------|------------|-------|
| **Frontend** | Streamlit (Python) | Single-page app with custom CSS |
| **Backend** | FastAPI | RESTful API for target app simulation |
| **Database** | Supabase (PostgreSQL) / DuckDB | Cloud and local options |
| **Visualization** | Plotly Express | Interactive charts |
| **Authentication** | JWT (custom implementation) | Recently added |
| **Styling** | Custom CSS injection | "Cosmic Glass" theme |

### Current UI Structure

```
NovaRium App (src/app.py)
├── Global Sidebar
│   ├── 🔐 Authentication (Login/Signup)
│   └── ⚙️ System Settings
│
├── Navigation Bar (Top)
│   ├── 🌌 NovaRium (Brand/Home)
│   ├── 🛠️ Data Lab (Data Engineering)
│   ├── 🔍 Monitor (Dashboard)
│   ├── 🚀 Master Class (A/B Test Wizard)
│   └── 📚 Retro (Portfolio/History)
│
└── Main Content Pages
    ├── Intro Page (Brand Identity)
    ├── Data Lab (ETL Builder)
    ├── Monitor (Real-time Dashboard)
    ├── Study/Lab (4-Step Experiment Wizard)
    └── Portfolio (Experiment History)
```

### Current Design System ("Cosmic Glass" Theme)

**Color Palette**:
- Primary Background: `#0d0d1a` (Deep Cosmic Dark)
- Glass Effect: `rgba(255, 255, 255, 0.03)` with backdrop blur
- Primary Gradient: `#6366F1` → `#8B5CF6` (Indigo to Violet)
- Accent: `#A78BFA` (Light Purple)
- Success: `#4ADE80` (Green)
- Warning: `#EF4444` (Red)
- Text Primary: `#FFFFFF`
- Text Secondary: `rgba(255, 255, 255, 0.7)`

**Typography**:
- Font Family: 'Plus Jakarta Sans'
- Headings: Bold (700), letter-spacing: -0.02em
- Body: Regular (400), line-height: 1.5

**Component Styles**:
- Cards: Glass morphism with `backdrop-filter: blur(10px)`, rounded corners (20px)
- Buttons: Pill shape (30px radius), gradient for primary
- Inputs: Dark background with subtle borders, purple focus state
- Code Blocks: Dark theme (`#1a1a2e`) with syntax highlighting

---

## 3. KEY FEATURES & PAGES

### Page 1: Data Lab (Data Engineering)
**Purpose**: Teach users how to build data marts from raw data

**Current Components**:
- Multi-select for metrics (DAU, Revenue, CTR, CVR, AOV, ARPU)
- SQL query generator (auto-generated based on selections)
- Data lineage explanation
- ETL execution button

**Data Visualizations**: Code blocks (SQL), text explanations

### Page 2: Monitor (Operations Dashboard)
**Purpose**: Real-time business monitoring and alert system

**Current Components**:
- **Tier 1 - Real-time Pulse**: Active users, today's revenue, system health, event ticker
- **Tier 2 - Business Intelligence**: KPI cards (Revenue, AOV, CVR, Retention), trend charts, funnel
- **Tier 3 - Crisis Detection**: Alert cards with trend analysis, action buttons

**Data Visualizations**:
- `px.area()` - Revenue trends (purple gradient fill)
- `px.bar()` - AOV comparison (blue bars)
- `px.funnel()` - Conversion funnel
- `px.line()` - Alert trend analysis (red with threshold lines)
- Real-time ticker (HTML/CSS animation)
- Metric cards with delta indicators

### Page 3: Master Class (A/B Test Wizard)
**Purpose**: Guided 4-step workflow for designing and analyzing experiments

**Steps**:
1. **Hypothesis**: Define target, hypothesis template builder
2. **Design**: Visual experiment builder (page/component selection, variant preview)
3. **Collection**: Run simulation, real-time data collection
4. **Analysis**: Statistical results, decision recommendation

**Current Components**:
- Step progress indicator (horizontal bar with labels)
- Embedded iframe (Target App preview)
- Form builder (tabs: Design | Strategy)
- Visual component cards (page/element selection)
- Real-time variant preview (HTML rendering)
- Statistical result cards (p-value, confidence intervals)
- Adoption flow (promote winning variant)

**Data Visualizations**:
- Group comparison bar charts
- Confidence interval plots
- Cumulative conversion line charts

### Page 4: Portfolio (Retro)
**Purpose**: View experiment history and learnings

**Components**:
- Experiment cards with status badges
- Historical data tables
- Export functionality

---

## 4. SPECIFIC UX PAIN POINTS

### Critical Issues

1. **Navigation Confusion**
   - Top navbar buttons lack visual hierarchy
   - Active state not prominent enough
   - No breadcrumb for deep navigation

2. **Information Overload**
   - Monitor page has too many metrics visible at once
   - No progressive disclosure of complex data
   - Alert cards are text-heavy

3. **Wizard UX Friction**
   - 4-step wizard tabs are not intuitive
   - Long scroll required in "Design" tab
   - Variant preview is small and gets lost

4. **Mobile Responsiveness**
   - Streamlit's default responsive behavior is limited
   - Charts don't scale well on smaller screens
   - Sidebar collapses awkwardly

5. **Data Visualization Issues**
   - Charts use default Plotly dark theme (not matching app theme)
   - Funnel chart colors don't align with brand palette
   - No consistent chart header styling

6. **Authentication UX**
   - Login/Signup forms are cramped in sidebar
   - No password strength indicator during signup
   - No visual feedback during form submission

### Minor Improvements Needed

- Empty states lack visual interest
- Loading states are plain Streamlit spinners
- Success/error toasts are standard Streamlit widgets
- No onboarding for first-time users
- Code blocks lack copy button styling

---

## 5. DESIGN REQUIREMENTS

### Brand Identity Enhancement

**Mood**: Professional yet approachable, educational, cosmic/space theme, modern SaaS feel

**Design Direction**:
- Maintain "Cosmic Glass" aesthetic but elevate execution
- Add subtle animations for engagement (not distracting)
- Introduce data-first visual hierarchy
- Balance dark theme with enough contrast for readability

### Layout System

**Grid Recommendations**:
- Consider 12-column grid for flexible layouts
- Define consistent spacing scale (4px base unit: 4, 8, 12, 16, 24, 32, 48, 64)
- Create modular card sizes (1x, 2x, 3x width variants)

**Page Templates Needed**:
1. Dashboard template (KPI cards + charts + alerts)
2. Wizard/Form template (step indicator + split layout)
3. Builder template (preview panel + form panel)
4. Data table template (filters + table + pagination)

### Component Style Guide

**Cards**:
- Glass effect with subtle gradient border on hover
- Consistent padding (24px)
- Elevation system (shadow levels 1-3)
- Status variants (default, success, warning, error)

**Buttons**:
- Primary: Gradient fill, glow effect on hover
- Secondary: Ghost style with border
- Tertiary: Text only with underline hover
- Icon buttons: Circular with tooltip

**Data Visualization Styling**:
- Chart background: Transparent (use card background)
- Axis labels: `rgba(255, 255, 255, 0.5)`
- Grid lines: `rgba(255, 255, 255, 0.1)`
- Color scale for data series:
  ```
  Purple (Primary): #8B5CF6
  Blue (Secondary): #3B82F6
  Green (Success): #10B981
  Red (Danger): #EF4444
  Yellow (Warning): #F59E0B
  ```

**Forms**:
- Floating labels for inputs
- Inline validation with color-coded messages
- Password strength meter (gradient bar)
- Select dropdowns with search capability

### Interactive Elements

**Micro-interactions**:
- Button press: Scale down slightly (0.98)
- Card hover: Lift effect with enhanced shadow
- Tab switch: Smooth content fade transition
- Chart hover: Highlight with value tooltip

**Loading States**:
- Skeleton loaders matching component shapes
- Pulsing gradient effect for loading bars
- "Cosmic dust" particle animation for major loads

**Empty States**:
- Illustrated SVG for each empty scenario
- Clear call-to-action button
- Educational tip relevant to the context

### Accessibility

- Minimum contrast ratio: 4.5:1 for text
- Focus indicators for keyboard navigation
- Reduced motion option for animations
- Screen reader friendly chart alternatives (data tables)

---

## 6. SPECIFIC REDESIGN REQUESTS

### Priority 1: Navigation Redesign
- Transform top navbar into a more app-like navigation
- Consider sidebar navigation for main sections
- Add contextual sub-navigation for complex pages

### Priority 2: Monitor Dashboard Overhaul
- Create "Summary → Detail" drill-down experience
- Design alert cards with clearer visual hierarchy
- Add time range selector for all charts

### Priority 3: Experiment Wizard Reimagining
- Redesign step indicator with clearer progress
- Create full-screen "builder mode" for variant design
- Add real-time side-by-side A/B preview

### Priority 4: Authentication Flow
- Design dedicated login/signup page (not sidebar)
- Add social login placeholders (Google, GitHub)
- Create user profile dropdown in header

### Priority 5: Data Visualization Consistency
- Define chart wrapper component with consistent styling
- Create branded empty state for charts
- Design interactive legend component

---

## 7. TECHNICAL CONSTRAINTS

**Streamlit Limitations**:
- No true SPA routing (uses query params/session state)
- Limited CSS specificity control
- Custom components require JavaScript bridge
- Layout options: columns, tabs, expanders, containers
- Native widgets have limited styling options

**What's Possible**:
- Custom CSS injection via `st.markdown()` with `unsafe_allow_html=True`
- Custom components via `streamlit-components`
- JavaScript injection for animations
- External font loading
- SVG/HTML rendering

**What's Difficult**:
- True responsive breakpoints
- Complex animations without iframe
- Custom dropdown implementations
- Drag-and-drop interfaces

---

## 8. DELIVERABLES REQUESTED

1. **Color Palette Refinement**
   - Extended color system with semantic naming
   - Light mode variant (optional)

2. **Component Library Specs**
   - Button variants with states
   - Card variants
   - Form field styles
   - Alert/Toast designs

3. **Page Mockups** (High Priority)
   - Monitor Dashboard (redesigned)
   - Experiment Wizard (reimagined)
   - Login/Signup page (new)

4. **Interaction Specs**
   - Hover/Active/Focus states
   - Transition timings
   - Loading animations

5. **Icon Recommendations**
   - Icon style (outline vs filled)
   - Icon library suggestion (Heroicons, Phosphor, etc.)

---

## APPENDIX: Current CSS Reference

```css
/* Key CSS Variables (to be established) */
:root {
  --color-bg-primary: #0d0d1a;
  --color-bg-card: rgba(255, 255, 255, 0.03);
  --color-border: rgba(255, 255, 255, 0.08);
  --color-border-hover: rgba(255, 255, 255, 0.2);
  --color-primary: #8B5CF6;
  --color-primary-gradient: linear-gradient(135deg, #6366F1 0%, #8B5CF6 100%);
  --color-text: #ffffff;
  --color-text-muted: rgba(255, 255, 255, 0.7);
  --radius-sm: 8px;
  --radius-md: 12px;
  --radius-lg: 20px;
  --radius-full: 9999px;
  --shadow-glow: 0 0 20px rgba(139, 92, 246, 0.3);
}
```

---

**Document Version**: 1.0
**Last Updated**: 2025-12-30
**Prepared By**: NovaRium Development Team
