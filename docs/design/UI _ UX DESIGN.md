# **KOROBOS Design System**

**Version: 2.0 (Updated: 2026-03-23)**
**Owner: Saravana Perumal K**
**Backend Integration: 12 Microservices**

---

# **1\. Design System Overview**

## **Purpose**

**The KOROBOS Design System provides a consistent UI framework for building the entire platform across Web (Next.js) and Mobile (React Native).**

**It ensures:**

- **visual consistency** across web and mobile
- **faster UI development** with reusable components
- **reusable components** shared between platforms
- **scalable product design** aligned with 12 backend services
- **cyberpunk intelligence interface** aesthetic
- **accessibility** (WCAG 2.1 AA compliance)

---

## **Design Principles**

### **1\. Visual Intelligence**

**The UI prioritizes insight visualization over data entry.**

**Characteristics:**

- Analytics widgets show trends, not forms
- Knowledge graph visualizes connections
- Dashboards aggregate metrics from all services
- AI insights displayed prominently with confidence scores

**Backend Services:**

- Analytics Service (trends)
- AI Service (insights)
- Dashboard Service (aggregation)
- Graph Service (visualization)

---

### **2\. Cyberpunk Futurism**

**The interface resembles a digital command center with neon aesthetics.**

**Characteristics:**

- Glowing neon blue borders (#00F5FF) on interactive elements
- Glass panels with backdrop blur
- Floating widgets with hover glow effects
- Purple and pink accent highlights
- Dark background (#0A0A0F) for deep space feel

**Implementation:**

- CSS: `backdrop-filter: blur(12px)` for glass effect
- Box-shadow: `0px 0px 20px rgba(0,245,255,0.4)` for neon glow
- Border: `1px solid rgba(0,245,255,0.5)` for glow border

---

### **3\. Modular Widgets**

**Everything is a widget component. Widgets aggregate data from backend services.**

**Widget Categories:**

| Widget                  | Service(s)            | Purpose                          |
| ----------------------- | --------------------- | -------------------------------- |
| **Habit Widget**        | Habit Service         | Daily habit tracking, streaks    |
| **Learning Widget**     | Learning Service      | Session tracking, time logs      |
| **Health Widget**       | Health Service        | Meals, workouts, calories        |
| **Productivity Widget** | Dashboard + Analytics | Aggregated score                 |
| **Insights Widget**     | AI Service            | AI-generated recommendations     |
| **Knowledge Widget**    | Graph Service         | Connected entities visualization |
| **Analytics Widget**    | Analytics Service     | Trends, patterns, correlations   |

---

### **4\. Instant Interaction**

**Primary actions should be reachable in one click or less.**

**Examples:**

- **Create note:** [+] button in header (1 click)
- **Mark habit complete:** [✓] icon in list (1 click)
- **Start learning session:** [Start Timer] button (1 click)
- **Log meal/workout:** Quick action buttons in dashboard (1 click)

**Pattern:** Floating action buttons (FAB) or quick action toolbars for mobile.

---

## **Backend-Frontend Service Mapping**

| Screen        | Primary Service   | Secondary Services                  | Key Endpoints                                          |
| ------------- | ----------------- | ----------------------------------- | ------------------------------------------------------ |
| **Dashboard** | Dashboard Service | Analytics, Habits, Learning, Health | `/overview`, `/daily`, `/weekly`                       |
| **Habits**    | Habit Service     | Database, Graph                     | `/habits`, `/habits/today`, `/habits/{id}/stats`       |
| **Notes**     | Notes Service     | Graph, Search, Database             | `/notes`, `/notes/{id}/backlinks`, `/notes/{id}/links` |
| **Learning**  | Learning Service  | Database, Notes, Graph              | `/sessions`, `/topics`, `/learning/stats`              |
| **Health**    | Health Service    | Analytics, Dashboard                | `/logs`, `/stats`, `/daily`                            |
| **Database**  | Database Service  | Notes                               | `/databases`, `/records`                               |
| **Analytics** | Analytics Service | All services                        | `/productivity`, `/trends`, `/patterns`                |
| **Graph**     | Graph Service     | All services                        | `/neighbors`, `/clusters`, `/subgraph`                 |
| **Search**    | Search Service    | All services                        | `/search`, `/suggest`                                  |
| **Settings**  | Auth Service      | Notification Service                | `/profile`, `/sessions`, `/push-token`                 |

---

# **2\. Design Tokens**

**Design tokens are the core variables used across UI components.**

---

# **2.1 Color System**

## **Primary Colors**

| Token                | Color        | Usage           |
| -------------------- | ------------ | --------------- |
| **primary_neon**     | **\#00F5FF** | **main accent** |
| **primary_dark**     | **\#0A0A0F** | **background**  |
| **secondary_purple** | **\#9D4EDD** | **highlights**  |
| **accent_pink**      | **\#FF006E** | **alerts**      |

---

## **Neutral Colors**

| Token        | Color        |
| ------------ | ------------ |
| **gray_100** | **\#F8F9FA** |
| **gray_300** | **\#CED4DA** |
| **gray_500** | **\#6C757D** |
| **gray_700** | **\#343A40** |
| **gray_900** | **\#121212** |

---

## **Semantic Colors**

| Token       | Usage        |
| ----------- | ------------ |
| **success** | **\#00FF9C** |
| **warning** | **\#FFC300** |
| **error**   | **\#FF3B3B** |
| **info**    | **\#0096FF** |

---

# **2.2 Typography System**

**Primary Font**

**Inter**

**Secondary Font**

**JetBrains Mono**

---

## **Font Scale**

| Token       | Size     |
| ----------- | -------- |
| **display** | **48px** |
| **h1**      | **36px** |
| **h2**      | **30px** |
| **h3**      | **24px** |
| **h4**      | **20px** |
| **body**    | **16px** |
| **caption** | **12px** |

---

## **Font Weights**

| Weight       | Value   |
| ------------ | ------- |
| **regular**  | **400** |
| **medium**   | **500** |
| **semibold** | **600** |
| **bold**     | **700** |

---

# **2.3 Spacing System**

**Spacing uses 8px grid system.**

| Token   | Size     |
| ------- | -------- |
| **xs**  | **4px**  |
| **sm**  | **8px**  |
| **md**  | **16px** |
| **lg**  | **24px** |
| **xl**  | **32px** |
| **xxl** | **48px** |

---

# **2.4 Border Radius**

| Token  | Radius   |
| ------ | -------- |
| **sm** | **6px**  |
| **md** | **12px** |
| **lg** | **18px** |
| **xl** | **24px** |

**Glass widgets typically use 18px radius.**

---

# **2.5 Shadow System**

**Neon glow shadows**

**Example**

**0px 0px 20px rgba(0,245,255,0.4)**

**Used for:**

**• hover effects**
**• active widgets**

---

# **3\. Layout System**

---

# **3.1 Grid System**

**Desktop layout**

**12 column grid**

**Container width**

**1440px**

---

## **Column Settings**

| Parameter   | Value    |
| ----------- | -------- |
| **Columns** | **12**   |
| **Gutter**  | **24px** |
| **Margin**  | **64px** |

---

# **3.2 Widget Grid**

**Dashboard widgets follow:**

**4 column grid**

**Example**

**\+----+----+----+----+**

**| W1 | W2 | W3 | W4 |**

**\+----+----+----+----+**

---

# **4\. Icon System**

**Icons use outline neon style.**

**Recommended library**

**Lucide Icons**

---

**Common icons**

| Icon         | Usage               |
| ------------ | ------------------- |
| **home**     | **dashboard**       |
| **note**     | **notes**           |
| **chart**    | **analytics**       |
| **graph**    | **knowledge graph** |
| **settings** | **settings**        |

---

# **5\. Component Library**

**Components are shared across Web (React) and Mobile (React Native).**

**Location:** `packages/ui/components/` (monorepo structure)

---

## **5.1 Buttons**

**Button Variants:**

```
PRIMARY BUTTON
Background: #00F5FF (neon blue)
Text: #0A0A0F (dark)
Border radius: 12px
Height: 40px (md) | 48px (lg) | 32px (sm)
Padding: 0 16px

States:
  - Default: neon blue
  - Hover: glow effect (0px 0px 20px rgba(0,245,255,0.6))
  - Active: darker blue
  - Disabled: 40% opacity

SECONDARY BUTTON
Background: rgba(255,255,255,0.05)
Border: 1px solid #00F5FF
Text: #00F5FF
Border radius: 12px

States:
  - Hover: background brightens, glow increases
  - Disabled: border opacity reduced

DANGER BUTTON
Background: #FF3B3B (error red)
Text: white
Used for: Delete, reset, destructive actions

GHOST BUTTON
Background: transparent
Border: none
Text: #00F5FF
Used for: Minimal UI, links, secondary actions

ICON BUTTON
Square button with icon
Used for: Quick actions (mark complete, delete, etc.)
```

**Component Path:** `packages/ui/components/Button.tsx`

---

## **5.2 Input Fields**

**Style:** Glassmorphism with neon accent

```
PROPERTIES
Background: rgba(255,255,255,0.05)
Border: 1px solid rgba(0,245,255,0.3)
Border radius: 8px
Height: 40px
Padding: 0 12px
Font: Inter 16px

FOCUS STATE
Border: 1px solid #00F5FF
Box-shadow: 0 0 20px rgba(0,245,255,0.4)

STATES
- Default: glass border
- Focus: neon glow
- Error: border #FF3B3B, error text below
- Success: border #00FF9C
- Disabled: opacity 50%

TYPES
- Text input
- Search input (with debounce 500ms)
- Number input (with spinner)
- Date picker
- Time picker
- Textarea (multiline)
- Select dropdown
- Multi-select (tags)
- Checkbox
- Radio button
- Toggle switch

VALIDATION
- Real-time feedback
- Error message in #FF3B3B below field
- Success checkmark on valid input
```

**Component Path:** `packages/ui/components/Input.tsx`

---

## **5.3 Cards**

**Card Structure:** Glass panels with neon glow

```
PROPERTIES
Background: rgba(10,10,15,0.5) (dark glass)
Backdrop-filter: blur(12px)
Border: 1px solid rgba(0,245,255,0.2)
Border radius: 18px
Padding: 24px

HOVER STATE
Border: 1px solid rgba(0,245,255,0.5)
Box-shadow: 0px 0px 20px rgba(0,245,255,0.3)
Transform: translateY(-2px)

CARD VARIANTS

WIDGET CARD
- Title + metric + chart
- Used in dashboard
- Example: Habit progress, learning hours

STAT CARD
- Single metric display
- Used in overview
- Example: Productivity score, total notes

INTERACTIVE CARD
- Clickable, leading to detail view
- Used in lists
- Example: Habit in list, note in list

ELEVATED CARD
- Higher shadow, more prominence
- Used for featured content
- Example: Top insights, critical alerts
```

**Component Path:** `packages/ui/components/Card.tsx`

---

## **5.4 Typography**

**Implementation:** Tailwind CSS + custom CSS variables

```
HEADINGS
h1: 36px / 600 weight / -0.02em letter-spacing (Display)
h2: 30px / 600 weight (Page title)
h3: 24px / 600 weight (Section header)
h4: 20px / 600 weight (Subsection)

BODY TEXT
Body Large: 16px / 400 weight (default)
Body Regular: 14px / 400 weight
Body Small: 12px / 400 weight (captions)

MONO
Code: 13px / 500 weight / JetBrains Mono (code blocks)

COLOR VARIATIONS
- Default: #F8F9FA (light text on dark)
- Secondary: #6C757D (muted gray)
- Accent: #00F5FF (neon for highlights)
- Error: #FF3B3B
- Success: #00FF9C
```

---

## **5.5 Navigation Sidebar**

**Web Desktop Layout**

```
PROPERTIES
Width: 260px (fixed, collapsible to 60px icon-only)
Background: rgba(10,10,15,0.8) glass
Border-right: 1px solid rgba(0,245,255,0.2)
Position: fixed left, full height
Z-index: 1000

CONTENT
┌─────────────────────┐
│ KOROBOS Logo        │ (40px)
├─────────────────────┤
│ 🏠 Dashboard        │ (48px each item)
│ 📝 Notes            │
│ ✓ Habits            │
│ 📚 Learning         │
│ ❤️ Health           │
│ 📊 Database         │
│ 📈 Analytics        │
│ 🔗 Graph            │
│ 🔍 Search           │
├─────────────────────┤
│ ⚙️ Settings         │ (bottom)
│ 👤 Profile          │
└─────────────────────┘

INTERACTIONS
- Current page: left border highlight (#00F5FF) + bg tint
- Hover: bg rgba(0,245,255,0.1)
- Active: text #00F5FF
- Collapse: toggle button in header

RESPONSIVE
- Desktop 1024px+: visible
- Tablet 768-1023px: collapsible drawer
- Mobile <768px: hidden (bottom nav instead)
```

---

## **5.6 Top Navigation Bar**

**Desktop & Tablet**

```
HEIGHT: 64px
BACKGROUND: rgba(10,10,15,0.8) glass
BORDER-BOTTOM: 1px solid rgba(0,245,255,0.2)

LAYOUT (left to right)
┌────────────────────────────────────────────────────────┐
│ [+] Create | 🔍 Search                    │ 🔔 | 👤   │
└────────────────────────────────────────────────────────┘

COMPONENTS

CREATE BUTTON [+]
- Quick capture modal
- Buttons: [+ Note] [+ Habit] [+ Log] [+ Record]

SEARCH BAR
- Global search with debounce
- Type ahead suggestions
- Placeholder: "Search across all..."
- Keyboard shortcut: Cmd+K

NOTIFICATIONS ICON
- Bell icon with red badge (count)
- Click → notification center modal

USER PROFILE
- Avatar + dropdown
- Options: Profile, Settings, Logout
```

---

## **5.7 Mobile Bottom Navigation**

```
HEIGHT: 60px
POSITION: Fixed bottom
BACKGROUND: rgba(10,10,15,0.9) glass
BORDER-TOP: 1px solid rgba(0,245,255,0.2)

5 TABS
┌──────────────────────────────────────────────┐
│ 📊   │ 📝   │  ✓   │  📚   │  ⚙️            │
│ Dash │ Notes│ Habits│ Learn │ Settings      │
└──────────────────────────────────────────────┘

ACTIVE TAB
- Icon: #00F5FF
- Label: #00F5FF
- Background glow: subtle

INACTIVE TAB
- Icon: #6C757D
- Label: #6C757D

GESTURES
- Swipe left/right: navigate tabs
- Tap: immediate navigation
```

---

## **5.8 Lists & Pagination**

```
LIST ITEM STRUCTURE
┌──────────────────────────────────────────┐
│ [Icon] Title / Label              [→]   │
│ Subtitle or metadata                    │
│ [Optional: status badge, action buttons]│
└──────────────────────────────────────────┘

HOVER STATE (Desktop)
Background: rgba(0,245,255,0.05)
Cursor: pointer

SELECTED STATE
Left border: 3px solid #00F5FF
Background: rgba(0,245,255,0.1)

PAGINATION
┌──────────────────────────────────────────┐
│ [◀]  [1] [2] [3] ... [10]  [▶]           │
│ "Showing 1-20 of 150 results"             │
└──────────────────────────────────────────┘

Implemented as:
- Page-based pagination (backend: page + limit)
- Limit options: 10, 20, 50 per page
- Keyboard: arrow keys navigate
```

---

## **5.9 Modals & Dialogs**

```
PROPERTIES
Background: rgba(0,0,0,0.7) (dark overlay)
Dialog: max-width 500px (sm) | 700px (md) | 900px (lg)
Border radius: 18px
Padding: 32px

STRUCTURE
┌────────────────────────────────┐
│ ✕ Modal Title          [⋯]     │
├────────────────────────────────┤
│                                │
│ Modal Content                  │
│ (forms, text, etc.)            │
│                                │
├────────────────────────────────┤
│ [Cancel]  [Primary Action]     │
└────────────────────────────────┘

ANIMATIONS
- Entrance: fade in + scale 0.95 → 1 (200ms)
- Exit: fade out + scale 1 → 0.95 (200ms)
- Backdrop: fade in/out

INTERACTIONS
- Escape key: closes modal
- Click outside: closes modal
- Tab: cycles through focusable elements
```

---

## **5.10 Badges & Tags**

```
ENTITY TYPE BADGES

Note (📝): Pink background (#FF006E), white text
Habit (✓): Cyan background (#00F5FF), dark text
Learning (📚): Purple background (#9D4EDD), white text
Health (❤️): Rose/pink background, white text
Record (📊): Green background, white text
Insight (💡): Amber background, dark text

PRIORITY BADGES

High (🔴): Red background (#FF3B3B)
Medium (🟡): Amber background (#FFC300)
Low (🟢): Green background (#00FF9C)

TAG/LABEL COMPONENT
[Icon] Text [✕ remove]
Used for: note tags, habit labels, etc.
Background: rgba(0,245,255,0.1)
Border: 1px solid rgba(0,245,255,0.3)
Border-radius: 20px (pill shape)
Padding: 4px 12px
```

---

## **5.11 Progress Indicators**

```
PROGRESS BAR
├─────────────────────────────────┤
│███████████░░░░░░░░░░░░░░░░░░░░│ 35%
└─────────────────────────────────┘

Color: #00F5FF (neon blue)
Background: rgba(255,255,255,0.1)
Height: 4px
Border-radius: 2px

RADIAL PROGRESS (Circular)
Used for: Productivity score, completion %
Background circle: gray
Progress arc: neon blue
Center text: percentage

STREAK INDICATOR
🔥 7 Day Streak
Text: "7 day", "15 day", etc.
Icon: Fire emoji
Color: #FFC300 (warning/streak color)

LOADING SPINNER
⟳ (rotating neon circle)
Color: #00F5FF
Size: 24px (default) | 32px (lg) | 16px (sm)
```

---

## **5.12 Toast Notifications**

```
POSITION: Bottom-right corner
AUTO-DISMISS: 3-5 seconds

VARIANTS

SUCCESS (✓)
Background: #00FF9C
Icon: ✓ checkmark
Text: "Habit created!"
Example: "Note saved", "Workout logged"

ERROR (✗)
Background: #FF3B3B
Icon: ✗ X
Text: "Failed to save"
Actions: [Retry] [Dismiss]

INFO (ℹ)
Background: #0096FF
Icon: ℹ circle
Text: "5 notes created today"

WARNING (⚠)
Background: #FFC300
Icon: ⚠ triangle
Text: "Habit streak broken"
```

---

---

# **6\. Screen Specifications**

## **6.1 Authentication Screens**

### **Login Screen**

**Backend Service:** Auth Service
**API Endpoint:** `POST /api/v1/auth/login`

```
LAYOUT
┌─────────────────────────────────────┐
│                                     │
│      KOROBOS Second Brain           │
│      Your Digital Mind              │
│                                     │
│  ┌─────────────────────────────┐   │
│  │ Email                       │   │
│  │ [___________________]       │   │
│  │                             │   │
│  │ Password                    │   │
│  │ [___________________]  👁️  │   │
│  │                             │   │
│  │ ☑ Remember me              │   │
│  │ [Forgot password?]          │   │
│  │                             │   │
│  │ [Sign In]                   │   │
│  │                             │   │
│  │ [← Google]  [← Apple]      │   │
│  │                             │   │
│  │ Don't have account?         │   │
│  │ [Create one →]              │   │
│  └─────────────────────────────┘   │
│                                     │
└─────────────────────────────────────┘

FIELDS
- Email: type="email", validation pattern
- Password: type="password", show/hide toggle
- Remember me: checkbox
- Forgot password: link to reset flow

ACTIONS
- Sign In: POST /api/v1/auth/login
- OAuth: Google & Apple SSO
- Create account: navigate to /signup

VALIDATION
- Email format: pattern match
- Required fields: marked with *
- Error messages: below field in #FF3B3B

STATES
- Loading: button spinner
- Error: banner at top + field errors
- Success: redirect to dashboard
```

---

### **Dashboard Screen**

**Backend Service:** Dashboard Service + aggregates all
**API Endpoints:** `GET /api/v1/dashboard/overview`, `/daily`, `/weekly`

```
LAYOUT
┌─────────────────────────────────────────────────────┐
│ Dashboard              [Today ▼] [Daily ▼]          │
├─────────────────────────────────────────────────────┤
│                                                     │
│ QUICK METRICS (4-column grid on desktop)            │
│ ┌──────────────────┬──────────────────┐             │
│ │ ✓ Habits         │ 📚 Learning      │             │
│ │ 3 / 5            │ 45 min           │             │
│ │ [███░░░░░░]      │ [████░░░░░░]     │             │
│ │ Complete   today │ This week        │             │
│ └──────────────────┴──────────────────┘             │
│ ┌──────────────────┬──────────────────┐             │
│ │ 💪 Productivity  │ 🍽️ Calorie Balance│             │
│ │ 78 / 100         │ -200 cal         │             │
│ │ [████████░░]     │ Eating well      │             │
│ │ Uptrend: +5%     │ ▼ Deficit        │             │
│ └──────────────────┴──────────────────┘             │
│                                                     │
│ QUICK ACTIONS (Horizontal buttons)                  │
│ [+ New Habit] [📝 Log Note] [📚 Start Learning]    │
│ [🍽️ Log Meal] [💪 Log Workout]                    │
│                                                     │
│ DAILY BREAKDOWN (Tabbed content)                    │
│ ┌───────────────────────────────────────────────┐   │
│ │ [Daily ▼]  [Weekly ▼]                         │   │
│ ├───────────────────────────────────────────────┤   │
│ │                                               │   │
│ │ HABITS TODAY (3/5 completed - 60%)            │   │
│ │ ✓ Morning Jog (7 day streak)                  │   │
│ │ ☐ Meditation (0 day streak)                   │   │
│ │ ✓ Read 30 min (15 day streak)                 │   │
│ │                                               │   │
│ │ LEARNING (45 minutes)                         │   │
│ │ React Fundamentals: 45 min session            │   │
│ │ [View notes] [+ New session]                  │   │
│ │                                               │   │
│ │ HEALTH SUMMARY                                │   │
│ │ Consumed: 2100 cal | Burned: 600 cal          │   │
│ │ Net: +1500 cal 🍽️                            │   │
│ │                                               │   │
│ │ NOTES CREATED TODAY (2)                       │   │
│ │ - React hooks patterns (2h ago)               │   │
│ │ - Grocery list (30m ago)                      │   │
│ │                                               │   │
│ │ DATABASE RECORDS ADDED (1)                    │   │
│ │ - Books DB: "Clean Code" (2h ago)             │   │
│ │                                               │   │
│ └───────────────────────────────────────────────┘   │
│                                                     │
└─────────────────────────────────────────────────────┘

RESPONSIVE BEHAVIOR
- Desktop (1024px+): 4-column grid + sidebar
- Tablet (768-1023px): 2-column grid
- Mobile (<768px): single column, stacked cards

INTERACTIONS
- Card click: navigate to detail screen
- Quick action: open create modal
- Tab switch: reload data for selected period
```

---

### **Habits Screen**

**Backend Service:** Habit Service
**API Endpoints:** `GET /api/v1/habits`, `/habits/today`, `/habits/{id}/stats`

```
LAYOUT
┌─────────────────────────────────────────────────────┐
│ Habits                    [+ New Habit]              │
├─────────────────────────────────────────────────────┤
│                                                     │
│ TODAY'S STATUS: 3/5 completed (60%)                │
│ [███░░░░░░░░░░░░░░░░]                              │
│                                                     │
│ TODAY'S HABITS (Cached from /habits/today)          │
│ ┌─────────────────────────────────────────────────┐│
│ │ ☑ Morning Jog              6:30 AM  7-day      │ │
│ │  [✓ Completed]  [View stats]                    │ │
│ │                                                  │ │
│ │ ☐ Meditation               8:00 AM  0-day      │ │
│ │  [Mark complete]  [View stats]                  │ │
│ │                                                  │ │
│ │ ☑ Read 30 min              Evening  15-day     │ │
│ │  [✓ Completed]  [View stats]                    │ │
│ │                                                  │ │
│ │ ☐ Stretching               Evening  0-day      │ │
│ │  [Mark complete]  [View stats]                  │ │
│ │                                                  │ │
│ │ ☑ Cold Shower              Morning  3-day      │ │
│ │  [✓ Completed]  [View stats]                    │ │
│ └─────────────────────────────────────────────────┘│
│                                                     │
│ ALL HABITS (Paginated: /habits?page=1&limit=20)    │
│ ┌─────────────────────────────────────────────────┐│
│ │ Morning Jog         Daily   ✓ Active            │ │
│ │ Meditation          Daily   ✓ Active            │ │
│ │ Read 30 min         Daily   ✓ Active            │ │
│ │ Stretching          Daily   ✓ Active            │ │
│ │ Cold Shower         Daily   ✓ Active            │ │
│ │ Gym                 Weekly  ✗ Inactive          │ │
│ │                                                  │ │
│ │ [Previous] [1] [2] [Next]  "Page 1 of 2"       │ │
│ └─────────────────────────────────────────────────┘│
│                                                     │
└─────────────────────────────────────────────────────┘

INTERACTIONS
- Mark complete: [✓] checkbox toggle
  → POST /api/v1/habits/{id}/complete
  → Update streak
  → Show success toast

- View stats: navigate to /habits/{id}
  → GET /api/v1/habits/{id}/stats (cached)
  → Show detail page with calendar, streaks, trends

- New habit: [+ button]
  → Open modal for POST /api/v1/habits
  → Form: name, frequency (daily/weekly/custom), time-of-day

- Mobile: swipe to mark complete
```

---

### **Notes Screen**

**Backend Service:** Notes Service
**API Endpoints:** `GET /api/v1/notes`, `POST /api/v1/notes`, `GET /api/v1/notes/{id}/backlinks`

```
LAYOUT
┌─────────────────────────────────────────────────────┐
│ Notes                     [+ New Note] [🔍]          │
├─────────────────────────────────────────────────────┤
│ Filters: [All tags] [React] [Learning] [Ideas]     │
│ Sort: [Latest ▼]                                    │
│ Total: 143 notes | Page 1 of 8                      │
│                                                     │
│ NOTES LIST (Paginated: /notes?page=1&limit=20)     │
│ ┌─────────────────────────────────────────────────┐│
│ │ 📝 React Fundamentals - Components              │ │
│ │ Created: 2 hours ago | 2 backlinks              │ │
│ │ Tags: [React] [Learning]                        │ │
│ │ "Understanding React components, hooks..."     │ │
│ │ [Open] [Edit] [Delete]                          │ │
│ │                                                  │ │
│ │ 📝 Grocery List                                  │ │
│ │ Created: 30 min ago | 0 backlinks               │ │
│ │ Tags: [Personal]                                │ │
│ │ "Milk, eggs, vegetables, rice, chicken..."     │ │
│ │ [Open] [Edit] [Delete]                          │ │
│ │                                                  │ │
│ │ 📝 DSA Interview Tips                            │ │
│ │ Created: Yesterday | 5 backlinks                │ │
│ │ Tags: [Interview] [DSA] [Learning]              │ │
│ │ "Common DSA patterns, two pointers..."          │ │
│ │ [Open] [Edit] [Delete]                          │ │
│ │                                                  │ │
│ │ ... (more notes)                                │ │
│ │ [Previous] [1] [2] [3] ... [8] [Next]          │ │
│ └─────────────────────────────────────────────────┘│
│                                                     │
└─────────────────────────────────────────────────────┘

MARKDOWN EDITOR (Open note: /notes/{id})
┌─────────────────────────────────────────────────────┐
│ ← Back  [Preview] [Save] [Discard] [Delete] [...]  │
├─────────────────────────────────────────────────────┤
│                                                     │
│ Title: [React Fundamentals___________________]     │
│ Tags: [React] [Learning] [+ Add]                   │
│                                                     │
│ EDITOR (left) | PREVIEW (right)                    │
│ ┌──────────────────┬──────────────────┐             │
│ │ # React Funda... │ React Fundamen...│             │
│ │ ## Components    │ Components       │             │
│ │ - Functional     │ • Functional    │             │
│ │ [[Link]]         │ [Link to Hooks] │             │
│ │                  │                  │             │
│ │ [⌘K: link]      │ [Format toolbar] │             │
│ └──────────────────┴──────────────────┘             │
│                                                     │
│ BACKLINKS (Shows notes linking to this note)       │
│ Notes linking to this:                              │
│ - "DSA Interview Tips" (mentions React)             │
│ - "Learning Plan 2026" (references)                 │
│ [View all]                                          │
│                                                     │
│ [Save Draft] [Cancel] [Publish]                    │
└─────────────────────────────────────────────────────┘

INTERACTIONS
- List: paginated, sorted by latest
- Create: POST /api/v1/notes (markdown body)
- Edit: PUT /api/v1/notes/{id}
- Delete: DELETE /api/v1/notes/{id}
- Get backlinks: GET /api/v1/notes/{id}/backlinks
- Create link: POST /api/v1/notes/{source_id}/links
  → form: target_note_id
```

---

### **Learning Screen**

**Backend Service:** Learning Service
**API Endpoints:** `POST /api/v1/learning/session/start`, `/stop`, `/sessions`

```
LAYOUT
┌─────────────────────────────────────────────────────┐
│ Learning                                            │
├─────────────────────────────────────────────────────┤
│                                                     │
│ ACTIVE TIMER (if session in progress)              │
│ ┌─────────────────────────────────────────────────┐│
│ │ React Fundamentals                              │ │
│ │          ⏱️  00:45:23                             │ │
│ │                                                  │ │
│ │      [⏸ Pause]  [⏹ Stop]                        │ │
│ │                                                  │ │
│ │ Started at: 10:00 AM                            │ │
│ │ [+ Link note]                                    │ │
│ └─────────────────────────────────────────────────┘│
│                                                     │
│ QUICK ACTIONS                                       │
│ [+ Start Session] [📝 Log Manual] [+ New Topic]    │
│                                                     │
│ TOPICS (Paginated: /learning/topics?page=1)        │
│ ┌─────────────────────────────────────────────────┐│
│ │ React                                  15h       │ │
│ │ [████████████░░░░░░]                            │ │
│ │ Sessions: 12 | Latest: Today                    │ │
│ │ [View] [Edit] [Delete]                          │ │
│ │                                                  │ │
│ │ Go                                            8h │ │
│ │ [██████░░░░░░░░░░░░]                            │ │
│ │ Sessions: 8 | Latest: 2 days ago                │ │
│ │ [View] [Edit] [Delete]                          │ │
│ │                                                  │ │
│ │ DSA                                          12h │ │
│ │ [███████████░░░░░░░]                            │ │
│ │ Sessions: 10 | Latest: Yesterday                │ │
│ │ [View] [Edit] [Delete]                          │ │
│ └─────────────────────────────────────────────────┘│
│                                                     │
│ RECENT SESSIONS (Paginated: /learning/sessions)    │
│ [📚 React] 1h 15m - Today, 10:00 AM               │
│ [View notes] [Edit] [Delete]                       │
│                                                     │
│ [📚 React] 2h - Yesterday, 2:00 PM                │
│ [View notes] [Edit] [Delete]                       │
│                                                     │
│ ... (paginated)                                     │
│ [Previous] [1] [2] [Next]                          │
│                                                     │
│ STATISTICS                                          │
│ Total: 35h 30m | This week: 12h | Streak: 5 days │
│                                                     │
└─────────────────────────────────────────────────────┘

TIMER INTERACTIONS
- Start: POST /api/v1/learning/session/start
  → form: topic_id
  → Timer starts, shows elapsed time

- Pause: POST /api/v1/learning/session/pause
  → Timer pauses
  → [Resume] button shown

- Resume: POST /api/v1/learning/session/resume
  → Timer resumes

- Stop: POST /api/v1/learning/session/stop
  → Calculates duration
  → Shows save dialog
  → Can link notes: POST /api/v1/learning/sessions/{id}/link-note

- Manual log: POST /api/v1/learning/sessions
  → form: topic_id, duration, date, notes
  → Optional: link notes
```

---

### **Health Screen**

**Backend Service:** Health Service
**API Endpoints:** `POST /api/v1/health/meals`, `/workouts`, `GET /api/v1/health/logs`

```
LAYOUT
┌─────────────────────────────────────────────────────┐
│ Health               [🍽️ Log Meal] [💪 Workout]    │
├─────────────────────────────────────────────────────┤
│                                                     │
│ TODAY'S SUMMARY                                     │
│ Consumed: 2100 cal | Burned: 650 cal | Balance: +1450
│                                                     │
│ MEALS TODAY (Paginated: /health/logs?type=meal)    │
│ ┌─────────────────────────────────────────────────┐│
│ │ Breakfast                      450 cal           │ │
│ │ Eggs, toast, OJ                                 │ │
│ │ P:18g C:45g F:12g             8:30 AM          │ │
│ │ [Edit] [Delete]                                 │ │
│ │                                                  │ │
│ │ Lunch                          620 cal           │ │
│ │ Chicken, rice, broccoli                         │ │
│ │ P:45g C:55g F:18g             1:00 PM          │ │
│ │ [Edit] [Delete]                                 │ │
│ │                                                  │ │
│ │ ... (more meals)                                │ │
│ └─────────────────────────────────────────────────┘│
│ Total meals: 4 | Calories: 2100                    │
│                                                     │
│ WORKOUTS TODAY (Paginated: /health/logs?type=work) │
│ ┌─────────────────────────────────────────────────┐│
│ │ Running                        650 cal           │ │
│ │ 45 minutes at moderate intensity                │ │
│ │                            6:00 AM              │ │
│ │ [Edit] [Delete]                                 │ │
│ └─────────────────────────────────────────────────┘│
│ Total workouts: 1 | Calories burned: 650            │
│                                                     │
│ DAILY CHART                                         │
│ [Calorie intake vs burn over time - line chart]    │
│                                                     │
│ [Previous day] [Today] [Next day]                  │
│                                                     │
└─────────────────────────────────────────────────────┘

LOG MEAL MODAL
┌─────────────────────────────────────────────────────┐
│ ✕ Log Meal                                          │
├─────────────────────────────────────────────────────┤
│ Food Name *                                         │
│ [___________________________]                       │
│                                                     │
│ Calories *                                          │
│ [620  ]                                             │
│                                                     │
│ Macronutrients                                      │
│ Protein (g): [45] | Carbs (g): [55] | Fat (g): [18]
│                                                     │
│ Date & Time                                         │
│ Date: [March 23, 2026 ▼]                           │
│ Time: [1:00 PM ▼]                                  │
│                                                     │
│ Description                                         │
│ [Grilled chicken, white rice, steamed broccoli]   │
│                                                     │
│ [Cancel]  [Log Meal]                               │
└─────────────────────────────────────────────────────┘

INTERACTIONS
- Log meal: POST /api/v1/health/meals
  → form: food_name, calories, protein, carbs, fat, description

- Log workout: POST /api/v1/health/workouts
  → form: workout_type, duration, calories, description

- View history: GET /api/v1/health/logs (with type filter)
- Get stats: GET /api/v1/health/stats
- Get daily: GET /api/v1/health/daily
```

---

### **Database Screen**

**Backend Service:** Database Service
**API Endpoints:** `GET /api/v1/databases`, `/records`, `POST /api/v1/records`

```
LAYOUT (Database List)
┌─────────────────────────────────────────────────────┐
│ Database                    [+ New Database]        │
├─────────────────────────────────────────────────────┤
│ View: [Grid] [List]  Sort: [Recent]                │
│                                                     │
│ GRID VIEW (Paginated: /databases?page=1&limit=12) │
│ ┌──────────────┬──────────────┐                     │
│ │ 📚 Books     │ 🎬 Movies    │                     │
│ │ 45 records   │ 32 records   │                     │
│ │ [View][Edit] │ [View][Edit] │                     │
│ │ [Delete]    │ [Delete]    │                     │
│ └──────────────┴──────────────┘                     │
│ ┌──────────────┬──────────────┐                     │
│ │ 🎓 Courses   │ 🏃 Workouts  │                     │
│ │ 12 records   │ 28 records   │                     │
│ │ [View][Edit] │ [View][Edit] │                     │
│ │ [Delete]    │ [Delete]    │                     │
│ └──────────────┴──────────────┘                     │
│ [Previous] [1] [2] [Next]                           │
│                                                     │
└─────────────────────────────────────────────────────┘

LAYOUT (Records Table)
┌─────────────────────────────────────────────────────┐
│ ← Back | Books          [+ New Record] [View type▼]│
├─────────────────────────────────────────────────────┤
│ Filter: [Status: ▼] [Rating: ▼]                    │
│ Sort: [Title ↑]  Show: [25 records ▼]             │
│                                                     │
│ ┌────────────────────────────────────────────────┐│
│ │ ☐ Title      Author    Status     Rating      │ │
│ ├────────────────────────────────────────────────┤│ │
│ │ ☐ Clean Code Robert    Reading    ★★★★★      │ │
│ │ ☐ Design Pat Gang      Want       ★★★★       │ │
│ │ ☐ Refactoring Martin   Completed  ★★★★★      │ │
│ │ ... (more rows, paginated)                    │ │
│ │ [Previous] [1] [2] [Next]                     │ │
│ └────────────────────────────────────────────────┘│
│                                                     │
│ BULK ACTIONS (if rows selected)                    │
│ [+ Add tag] [✓ Mark complete] [Delete selected]    │
│                                                     │
└─────────────────────────────────────────────────────┘

INTERACTIONS
- List databases: GET /api/v1/databases (paginated)
- Create database: POST /api/v1/databases
- View records: GET /api/v1/records (with filtering/sorting)
- Create record: POST /api/v1/records
  → form: dynamic fields based on database schema
- Filter: property-based (eq, contains, gt, lt)
- Sort: by any property (asc/desc)
```

---

### **Analytics Screen**

**Backend Services:** Analytics Service + AI Service
**API Endpoints:** `GET /api/v1/analytics/*`, `GET /api/v1/ai/insights`, `/recommendations`

```
LAYOUT
┌─────────────────────────────────────────────────────┐
│ Analytics              [Time Period: 30 days ▼]     │
├─────────────────────────────────────────────────────┤
│                                                     │
│ PRODUCTIVITY SCORE                                  │
│ ┌─────────────────────────────────────────────────┐│
│ │ Today: 78 | 30-day avg: 74 | Trend: ↑ +5%      │ │
│ │                                                  │ │
│ │ [Line chart: trend over 30 days]                │ │
│ │    78 ┤            ╱╲                           │ │
│ │    75 ┤  ╱╲       ╱  ╲                          │ │
│ │    72 ┤╱    ╲    ╱    ╲                         │ │
│ │       ├─────┴───┴───────┴──────────────        │ │
│ │       Mar1  5   10  15   20  23                 │ │
│ └─────────────────────────────────────────────────┘│
│                                                     │
│ KEY METRICS (3-column grid)                         │
│ ┌────────────────┬────────────────┬────────────┐   │
│ │ Habit Compl.   │ Learning Hours │ Health     │   │
│ │ 82% (↑ 3%)     │ 35.5h (↓ 2%)   │ +150 cal   │   │
│ │ [View detail]  │ [View detail]  │ [View]     │   │
│ └────────────────┴────────────────┴────────────┘   │
│                                                     │
│ AI INSIGHTS                                         │
│ ┌─────────────────────────────────────────────────┐│
│ │ 💡 You're 15% more consistent with morning     │ │
│ │ habits. Consider scheduling more in morning.   │ │
│ │ Confidence: 92%                                 │ │
│ │ [Dismiss]                                       │ │
│ │                                                  │ │
│ │ 📈 Learning sessions increased 30% vs last m.  │ │
│ │ Keep up the momentum!                           │ │
│ │ Confidence: 87%                                 │ │
│ │ [Dismiss]                                       │ │
│ └─────────────────────────────────────────────────┘│
│                                                     │
│ AI RECOMMENDATIONS (Prioritized)                    │
│ ┌─────────────────────────────────────────────────┐│
│ │ 🔴 HIGH: Meditation skipped 3 days              │ │
│ │ [Start streak]                                  │ │
│ │                                                  │ │
│ │ 🟡 MEDIUM: Add Go learning session              │ │
│ │ [Suggest topic]                                 │ │
│ │                                                  │ │
│ │ 🟡 MEDIUM: No workout in 2 days                 │ │
│ │ [Log workout]                                   │ │
│ └─────────────────────────────────────────────────┘│
│                                                     │
└─────────────────────────────────────────────────────┘

INTERACTIONS
- Productivity score: GET /api/v1/analytics/productivity
- Trends: GET /api/v1/analytics/trends/{metric_type}
- Insights: GET /api/v1/ai/insights (with type filter)
- Recommendations: GET /api/v1/ai/recommendations (with priority filter)
- Time period filter: changes date range for all queries
```

---

### **Knowledge Graph Screen**

**Backend Service:** Graph Service
**API Endpoints:** `GET /api/v1/graph/force-directed-layout`, `/neighbors/{node_id}`

```
LAYOUT
┌─────────────────────────────────────────────────────┐
│ Knowledge Graph        [Layout▼] [Filters▼]        │
├─────────────────────────────────────────────────────┤
│                                                     │
│  (Force-directed visualization canvas)              │
│                                                     │
│               📝 React Hooks                        │
│                      ╱  ╲                           │
│                    ╱      ╲                         │
│          📚React Fund  📝Best Practices            │
│              ╲           ╱     ╱                    │
│                ╳  ╲   ╱  ╲  ╱                     │
│          📝Component   ╳   📝Interview              │
│                      ╱  ╲                          │
│            ✓ Learning   ❤️ Health                  │
│                                                     │
│  LEGEND                                             │
│  📝 Note  📚 Learning  ✓ Habit  ❤️ Health  📊 Rec│
│                                                     │
│  NODE DETAIL (right panel when selected)            │
│  ┌────────────────────────────────┐               │
│  │ React Fundamentals             │               │
│  │ Note | Created: 2 days ago     │               │
│  │                                │               │
│  │ Neighbors: 4 nodes             │               │
│  │ - React Hooks (linked)         │               │
│  │ - Components (linked)          │               │
│  │ - Learning Session (session)   │               │
│  │ - Interview Tips (backlink)    │               │
│  │                                │               │
│  │ [View] [Edit] [Delete]         │               │
│  └────────────────────────────────┘               │
│                                                     │
└─────────────────────────────────────────────────────┘

INTERACTIONS
- Pan: mouse drag
- Zoom: scroll wheel
- Select node: click → show details panel
- Expand neighbors: double-click node
  → GET /api/v1/graph/neighbors/{node_id}
- Open entity: double-click → navigate to detail screen
- Context menu: right-click → delete, etc.
- Cluster detection: toggle filter to color-code clusters
```

---

### **Search Screen**

**Backend Service:** Search Service
**API Endpoints:** `GET /api/v1/search`, `/search/suggest`

```
LAYOUT
┌─────────────────────────────────────────────────────┐
│ Search                                              │
├─────────────────────────────────────────────────────┤
│                                                     │
│ SEARCH BAR                                          │
│ ┌─────────────────────────────────────────────────┐│
│ │ 🔍 React hooks patterns...  [⌫]                │ │
│ └─────────────────────────────────────────────────┘│
│                                                     │
│ AUTOCOMPLETE SUGGESTIONS (Real-time)               │
│ 📝 React Hooks Patterns (note)                    │
│ 📝 React Best Practices (note)                    │
│ 📚 React Learning Session (session)               │
│ ✓ React Fundamentals (habit)                      │
│ [Show more]                                         │
│                                                     │
│ ADVANCED FILTERS                                    │
│ [Type: All ▼] [Date: Any ▼] [Tags: None ▼]       │
│                                                     │
│ RESULTS (32 matches in 0.23s)                      │
│ ┌─────────────────────────────────────────────────┐│
│ │ 📝 React Hooks Patterns                          │ │
│ │ Note | Created: 2 hours ago                      │ │
│ │ "Understanding React hooks like useState..."     │ │
│ │ Tags: [React] [Learning]                         │ │
│ │ [View] [Edit]                                    │ │
│ │                                                  │ │
│ │ 📝 React Fundamentals                            │ │
│ │ Note | Created: Yesterday                        │ │
│ │ "Core React concepts including components..."    │ │
│ │ Tags: [React] [Interview]                        │ │
│ │ [View] [Edit]                                    │ │
│ │                                                  │ │
│ │ ... (paginated)                                 │ │
│ │ [Previous] [1] [2] [3] [Next]                  │ │
│ └─────────────────────────────────────────────────┘│
│                                                     │
└─────────────────────────────────────────────────────┘

INTERACTIONS
- Search: GET /api/v1/search (with debounce 500ms)
- Suggestions: GET /api/v1/search/suggest (as you type)
- Advanced: GET /api/v1/search/advanced (with filters)
- Filters: type, date-range, tags
- Click result: navigate to detail view
```

---

### **Settings Screen**

**Backend Services:** Auth Service + Notification Service
**API Endpoints:** `GET /api/v1/auth/profile`, `/sessions`, `POST /api/v1/notifications/push-token`

```
LAYOUT
┌─────────────────────────────────────────────────────┐
│ Settings                                            │
├─────────────────────────────────────────────────────┤
│                                                     │
│ PROFILE                                             │
│ [👤 Avatar] [Change]                               │
│ Full Name: [John Doe____________________]          │
│ Email: [john@example.com________________]          │
│ ✓ Verified [Resend link]                           │
│ Username: [johndoe_________________]               │
│ Bio: [Lifelong learner & hacker____]               │
│ Joined: March 1, 2026                               │
│ [Save Changes]                                      │
│                                                     │
│ SECURITY                                            │
│ Password: Last changed 30 days ago                  │
│ [Change password] [Reset password]                  │
│                                                     │
│ Two-Factor Auth: ◉ Enabled                         │
│ [Configure 2FA] [View backup codes]                │
│                                                     │
│ ACTIVE SESSIONS (3)                                 │
│ Current: Chrome on Windows                          │
│ IP: 192.168.1.100 | Now                            │
│ [Logout this device]                                │
│                                                     │
│ iPhone 14 (iOS) | 2 hours ago                       │
│ [Logout this device]                                │
│                                                     │
│ Pixel 6 (Android) | Yesterday                       │
│ [Logout this device]                                │
│                                                     │
│ [Logout all other devices]                          │
│                                                     │
│ NOTIFICATIONS                                       │
│ Push Notifications                                  │
│ ☑ Habit reminders                                   │
│ ☑ Learning streaks                                 │
│ ☐ Daily summary                                     │
│ [Save preferences]                                  │
│                                                     │
│ PREFERENCES                                         │
│ Theme: ○ Light ◉ Dark ○ System                     │
│ Language: [English (US) ▼]                         │
│ Timezone: [America/Los_Angeles ▼]                  │
│ [Save preferences]                                  │
│                                                     │
│ DANGER ZONE                                         │
│ [Delete Account] (permanent, irreversible)         │
│                                                     │
└─────────────────────────────────────────────────────┘

INTERACTIONS
- Get profile: GET /api/v1/auth/profile
- Update profile: PUT /api/v1/auth/profile
- Change password: POST /api/v1/auth/password-reset (request + confirm flow)
- Get sessions: GET /api/v1/auth/sessions
- Logout device: POST /api/v1/auth/logout (with device_id)
- Register push token: POST /api/v1/notifications/push-token (mobile only)
- Delete account: DELETE /api/v1/auth/account (with confirmation)
```

---

# **7\. Widget System**

**Widgets are modular, reusable UI components.**

**Widget Types:**

| Widget                  | Service              | Purpose                     | Location                   |
| ----------------------- | -------------------- | --------------------------- | -------------------------- |
| **Habit Widget**        | Habit                | Daily habit tracking        | Dashboard, Habits screen   |
| **Learning Widget**     | Learning             | Session tracking, time logs | Dashboard, Learning screen |
| **Health Widget**       | Health               | Meal/workout aggregates     | Dashboard, Health screen   |
| **Productivity Widget** | Dashboard, Analytics | Aggregated score + trend    | Dashboard                  |
| **Insights Widget**     | AI                   | AI recommendations          | Analytics, Dashboard       |
| **Knowledge Widget**    | Graph                | Connected entities          | Graph screen               |
| **Analytics Widget**    | Analytics            | Trends, patterns            | Analytics screen           |
| **Notification Widget** | Notification         | In-app notifications        | Header, dedicated screen   |

**Widget Grid Structure:**

- Desktop: 4-column responsive grid
- Tablet: 2-column grid
- Mobile: 1-column (stacked)

---

# **8\. Motion & Animations**

**Animation Timing:**

- Quick interactions: 200ms (easing: easeInOutQuad)
- Medium transitions: 300ms (easing: easeInOutCubic)
- Page transitions: 400ms (easing: ease)
- Long animations: 500-800ms (easing: easeInOutCubic)

**Examples:**

- Hover glow: box-shadow transition 300ms
- Widget entrance: fade + scale 200ms
- Graph expansion: node scale + fade 300ms
- Modal appearance: backdrop fade 200ms + dialog scale 300ms

---

# **9\. Dark Mode**

**Default Mode:** Cyberpunk dark

- Background: #0A0A0F
- Text: #F8F9FA
- Accents: neon #00F5FF

**Light Mode (Optional):** Analytical

- Background: #F8F9FA
- Text: #0A0A0F
- Accents: blue #2563EB

**Toggle:** in Settings screen

- Persisted to localStorage
- Respects system preference (prefers-color-scheme)

---

# **10\. Accessibility (WCAG 2.1 Level AA)**

**Color Contrast:**

- Normal text: 4.5:1 minimum
- Large text: 3:1 minimum
- Never use color alone to convey information

**Keyboard Navigation:**

- Tab through all interactive elements
- Visible focus indicator (outline: 2px solid #00F5FF)
- Logical tab order
- Escape key closes modals

**Screen Reader Support:**

- Semantic HTML (button, link, form, nav)
- ARIA labels for icons
- Form labels associated with inputs
- Alt text for images
- List semantics for lists

**Motion:**

- Animations respect prefers-reduced-motion
- No auto-playing videos
- No flashing >3 times/sec
- Meaningful focus management

---

# **11\. Responsive Design**

**Breakpoints:**

- Mobile: <768px (full-width, single column)
- Tablet: 768px-1023px (2-column on larger tablets)
- Desktop: 1024px-1920px (sidebar + main, multi-column)
- TV: 1921px+ (multi-panel dashboard)

**Mobile-Specific:**

- Bottom tab navigation
- Full-screen modals
- Touch targets: 44px minimum
- Larger font sizes
- Horizontal scroll for tables

---

# **12\. Frontend File Structure (React/Next.js)**

```
packages/
├── ui/                          # Shared component library
│   ├── components/
│   │   ├── Button.tsx
│   │   ├── Input.tsx
│   │   ├── Card.tsx
│   │   ├── Modal.tsx
│   │   ├── List.tsx
│   │   ├── Navigation/
│   │   │   ├── Sidebar.tsx
│   │   │   ├── TopNav.tsx
│   │   │   └── BottomNav.tsx (mobile)
│   │   ├── Widgets/
│   │   │   ├── HabitWidget.tsx
│   │   │   ├── LearningWidget.tsx
│   │   │   └── ...
│   │   └── Forms/
│   │       ├── HabitForm.tsx
│   │       ├── NoteEditor.tsx
│   │       └── ...
│   └── styles/
│       ├── globals.css
│       ├── tokens.css (design tokens)
│       └── animations.css

apps/
├── web/                         # Next.js web app
│   ├── src/
│   │   ├── app/
│   │   │   ├── dashboard/
│   │   │   ├── habits/
│   │   │   ├── notes/
│   │   │   ├── learning/
│   │   │   ├── health/
│   │   │   ├── database/
│   │   │   ├── analytics/
│   │   │   ├── graph/
│   │   │   ├── search/
│   │   │   ├── settings/
│   │   │   └── auth/ (login, signup)
│   │   ├── hooks/ (custom React hooks)
│   │   ├── services/ (API clients)
│   │   └── store/ (state management)
│   └── public/

├── mobile/                      # React Native app
│   ├── src/
│   │   ├── screens/ (one per service)
│   │   ├── components/ (shared UI)
│   │   ├── navigation/ (bottom tabs + stack)
│   │   ├── hooks/
│   │   ├── services/ (API + offline)
│   │   └── store/

└── docs/
    └── design/ (THIS FILE)
```

---

# **13\. Component Naming Convention**

**Format:** `ComponentName/Variant`

**Examples:**

- Button/Primary
- Button/Secondary
- Button/Danger
- Card/Widget
- Card/Interactive
- Input/Search
- Input/Email
- List/Habits
- Modal/Create
- Nav/Sidebar

---

# **14\. Design Versioning**

**v1.0:** Core design system (colors, typography, spacing)
**v1.5:** Component library (buttons, inputs, cards)
**v2.0:** Widget system + screens (this version)
**v2.5:** Animations & motion design
**v3.0:** AI interface enhancements

---

# **Final Vision**

**The KOROBOS Design System enables building a cyberpunk intelligence interface that transforms:**

✨ **Widgets into Productivity Instruments**

- Real-time data aggregation
- One-click interactions
- Instant feedback

🎮 **Dashboards into Command Centers**

- Unified metric visualization
- AI-powered insights
- Knowledge connections

🧠 **Knowledge into Visualized Networks**

- Force-directed graph visualization
- Entity clustering and relationships
- Serendipitous discovery

**Result:** A Second Brain Operating System UI

- **Comprehensive:** All 12 backend services integrated
- **Beautiful:** Cyberpunk aesthetic with glass and neon
- **Accessible:** WCAG 2.1 AA compliant
- **Responsive:** Works on web, tablet, and mobile
- **Performant:** Optimized rendering and caching
- **User-Centric:** Instant interactions, visual feedback

---

**This design system is the foundation for building KOROBOS as the ultimate digital second brain.**

# **11\. Design File Structure (Figma)**

**Recommended Figma structure**

**KOROBOS Design System**

**Foundations**

- **Colors**

- **Typography**

- **Spacing**

**Components**

- **Buttons**

- **Inputs**

- **Cards**

- **Navigation**

- **Widgets**

**Patterns**

- **Dashboard**

- **Notes**

- **Analytics**

**Screens**

- **Dashboard**

- **Notes**

- **Graph**

- **Habits**

- **Learning**

---

# **12\. Component Naming Convention**

**Example**

**Button/Primary**

**Button/Secondary**

**Card/Widget**

**Input/Search**

**Nav/Sidebar**

---

# **13\. Frontend Mapping (React)**

**Example component mapping**

**Button → components/ui/Button.tsx**

**Card → components/ui/Card.tsx**

**Sidebar → components/layout/Sidebar.tsx**

**Widget → components/widgets/\***

---

# **14\. Versioning Strategy**

**Design system versions**

**v1.0 → Core components**

**v1.5 → Widget system**

**v2.0 → AI interface**

---

# **Final Vision**

**The KOROBOS Design System enables building a cyberpunk intelligence interface where:**

**• widgets become productivity instruments**
**• dashboards become command centers**
**• knowledge becomes visualized networks**

**The result is a Second Brain Operating System UI.**
