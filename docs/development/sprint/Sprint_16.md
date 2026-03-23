# KOROBOS — Sprint 16 Execution Plan

## Frontend Platform (Web + Android React Native)

Version: 2.0 (Updated: 2026-03-23)
Owner: Saravana Perumal
Backend Lead: [Backend Team]

**Status:** Planning & Architecture Phase
**Aligned with:** 12 Production Microservices + API Gateway

---

# 1. Sprint Objective

Sprint 16 implements the **Frontend Platform**, delivering a unified user experience across:

- Web (React / Next.js)
- Android (React Native)
- Future iOS (React Native reusable)

This sprint transforms **12 production microservices** into a **fully integrated, user-friendly second brain platform**.

**Backend Foundation:**

- 12 microservices (Auth, Habit, Notes, Learning, Health, Analytics, AI, Dashboard, Database, Graph, Search, Notification)
- API Gateway with auth middleware
- PostgreSQL + Redis + Kafka + Meilisearch + ClickHouse
- Event-driven architecture with real-time updates

---

# 2. Core Goals

Frontend platform must:

- ✅ Integrate all 12 microservices seamlessly
- ✅ Provide unified design system across web + mobile
- ✅ Support cross-platform UI components (shared where possible)
- ✅ Ensure high performance (caching, pagination, lazy loading)
- ✅ Support offline-first mobile experience (sync queue, local storage)
- ✅ Provide scalable, maintainable architecture
- ✅ Enable real-time features (Kafka/WebSocket integration)
- ✅ Deliver accessible, responsive UI (WCAG 2.1 AA)

---

# 3. Platform Architecture

        Web App (Next.js)
        Mobile App (React Native)
        ↓
        Shared Design System
        ↓
        API Layer (Gateway)
        ↓
        Backend Services

---

# 4. Technology Stack

Web:

- Next.js (React)
- TypeScript
- TailwindCSS / ShadCN UI

Mobile:

- React Native
- Expo (optional)
- TypeScript

Shared:

- Zustand / Redux Toolkit (state)
- Axios / React Query (API)
- React Hook Form

---

# 5. Frontend Monorepo Structure

        frontend/

        apps/
            web/
            mobile/

        packages/
            ui/
            hooks/
            services/
            store/
            utils/
            types/

---

# 6. Design System

Components:

- Buttons
- Inputs
- Cards
- Modals
- Lists
- Charts
- Navigation

Principles:

- consistency
- accessibility
- responsiveness
- dark/light mode

---

# 7. Navigation Architecture

Web:

- Sidebar navigation
- Top header
- Page routing

Mobile:

- Bottom tabs
- Stack navigation
- Drawer (optional)

---

# 8. Core Screens (Based on 12 Microservices)

## 1. Authentication Flow

- Login/Signup screens (Auth Service)
- Password reset flow
- Email verification
- Session management

## 2. Dashboard (Aggregates all services)

- Overview card: habits completed, learning minutes, calorie balance, productivity score
- Daily breakdown: metrics for all tracked items
- Weekly trends: habit consistency, learning hours, productivity
- Quick action buttons (new habit, note, session, log meal)

## 3. Habits (Habit Service)

- Habit list: create/edit/delete with pagination
- Today's habits: quick completion tracking (cached for performance)
- Habit detail: stats (completion rate, current/longest streaks, consistency)
- Habit creation: flexible scheduling (daily/weekly/custom days, time-of-day)
- Visual: streaks display, weekly consistency heatmap

## 4. Notes (Notes Service)

- Paginated note list with search and tags
- Markdown editor with live preview
- Backlinks section: shows which notes reference this note
- Note creation with tagging
- Note stats: total created today
- Mobile: optimized editor for touch input

## 5. Learning (Learning Service)

- Topics management: CRUD with pagination
- Live timer session: start/pause/resume/stop for active learning
- Manual session logging: input duration + notes
- Session history: paginated list with linked notes
- Link notes to sessions: associate learning with knowledge
- Learning stats: total hours, current streak, topic distribution pie chart
- Mobile: simplified timer UI with larger buttons

## 6. Health (Health Service)

- Meal logging: food name, calories, macros (protein/carbs/fat)
- Workout logging: type, duration, calories
- Log history: filter by type (meals/workouts)
- Daily stats: calories consumed, burned, net balance
- Total stats: aggregates

## 7. Database (Database Service)

- Database list: CRUD with pagination
- Database schema editor: add/edit/delete properties (text/number/boolean/date/select/relation)
- Record table view: rows with dynamic columns
- Record kanban view: group by select properties (coming soon)
- Record calendar view: events by date property (coming soon)
- Filtering: by any property with operators (eq, contains, gt, lt, etc.)
- Sorting: by any property (asc/desc)

## 8. Analytics & Insights (Analytics + AI Services)

- Productivity score: with trend over 30-90 days
- Habit trends: completion rate over time
- Learning hours: weekly/monthly totals
- Health trends: calories, workouts
- AI Insights: behavioral, performance, health, knowledge (with confidence scores)
- AI Recommendations: habit, learning, health, productivity (with priority levels)

## 9. Knowledge Graph (Graph Service)

- Force-directed visualization: all entity nodes connected
- Node types: notes, habits, learning topics, health logs, database records
- Interactive: click node → see neighbors → traverse graph
- Related entities finder: "Find related notes" with depth control
- Knowledge clusters: detect and visualize entity groups
- Connected habits finder: shows habits connected to a note via learning sessions

## 10. Search (Search Service)

- Unified search: across notes, habits, learning, records, meals, workouts
- Advanced filters: type, date range, tags (for notes)
- Autocomplete suggestions: real-time as user types
- Full-text powered by Meilisearch

## 11. Settings & Account (Auth + Notification Services)

- User profile: name, email, avatar
- Password management: change/reset
- Email verification: resend link
- Sessions: list active devices, logout from device
- Push notifications: register token, toggle channels
- Account security: unlock options

## 12. Notifications (Notification Service)

- In-app notification center: modal/drawer
- Notification list: paginated with read/unread
- Mark as read/delete
- Multi-channel: in-app, email, push (by platform: iOS/Android)

---

# 9. State Management

**Global State (Zustand/Redux Toolkit):**

```
Auth:
  - user: UserResponse
  - accessToken: string
  - refreshToken: string
  - isAuthenticated: boolean
  - isLoading: boolean
  - error: string | null

User Data:
  - profile: UserResponse
  - sessions: SessionResponse[]

Dashboard:
  - dailyMetrics: DailyMetrics
  - overview: OverviewResponse
  - weeklyData: WeeklyResponse

Habits:
  - habits: HabitResponse[]
  - todayHabits: HabitTodayResponse (with caching)
  - habitStats: HabitStatsResponse

Notes:
  - notes: NoteResponse[]
  - currentNote: NoteResponse | null
  - backlinks: NoteLinkResponse[]

Theme:
  - isDarkMode: boolean
  - theme: 'light' | 'dark'
```

**Local State:**

- Form state (React Hook Form)
- Component UI state (modals, tabs, filters)
- Temporary input values
- Search/filter state

**Cache Strategy:**

- React Query for server state caching
- Automatic cache invalidation via Kafka events
- Redis caching on backend (2-min TTL for dashboard, habits/today endpoint)
- Local storage for theme, user preferences

---

# 10. API Layer

**Centralized API Client (axios + React Query):**

```typescript
// Base configuration
- Base URL: http://api.korobos.local/api/v1
- Default headers: Content-Type: application/json
- Auth header injection: Authorization: Bearer {accessToken}

// Features:
- Token refresh: Automatic refresh on 401 response
- Error handling: Standardized error responses with status codes
- Retries: Exponential backoff (3 retries max)
- Caching: React Query with stale-while-revalidate
- Rate limiting: Handle 429 responses gracefully
- Request/response interceptors for logging
```

**Service Modules:**

```
api/
  ├── auth.ts         // Auth Service endpoints
  ├── habits.ts       // Habit Service + caching
  ├── notes.ts        // Notes Service + pagination
  ├── learning.ts     // Learning Service (timer + sessions)
  ├── health.ts       // Health Service
  ├── database.ts     // Database Service (CRUD + filtering)
  ├── analytics.ts    // Analytics Service
  ├── ai.ts           // AI Service (insights + recommendations)
  ├── graph.ts        // Graph Service (visualization)
  ├── search.ts       // Search Service (full-text + autocomplete)
  ├── dashboard.ts    // Dashboard Service (aggregates)
  └── notifications.ts // Notification Service
```

---

# 11. Authentication Integration

**Web:**

- JWT tokens stored in httpOnly cookies (secure, auto-sent with requests)
- Refresh token stored separately
- Session management: list devices, logout from device

**Mobile (React Native):**

- Secure storage: AsyncStorage + react-native-encrypted-storage
- JWT stored encrypted on device
- Refresh token rotation on each auth
- Biometric authentication optional: Face ID / fingerprint

**Auth Flow:**

1. User signs up/logs in (POST /api/v1/auth/signup or /login)
2. Receive access_token + refresh_token + user data
3. Store tokens securely
4. Inject token in all subsequent requests
5. On 401: Refresh token (POST /api/v1/auth/refresh)
6. On refresh failure: Clear tokens, redirect to login
7. Logout: POST /api/v1/auth/logout, clear local storage

---

# 12. Offline Support (Mobile)

**Architecture:**

```
Local Storage (SQLite/AsyncStorage)
    ↓
Sync Queue (Persist failed requests)
    ↓
Network Detection (monitor online/offline)
    ↓
Background Sync (retry when online)
```

**Features:**

- Offline data caching: Cache all habit, note, learning, health data locally
- Sync queue: Queue failed mutations (POST/PUT/DELETE) with timestamps
- Retry mechanism: Exponential backoff, max 5 retries per request
- Conflict resolution: Server-wins for sync conflicts (timestamp-based)
- Real-time sync: Retry every 30s when network returns
- User feedback: Toast notifications for sync status

**Supported Offline Operations:**

```
✓ Create/Edit habits (queued)
✓ Create/Edit notes (queued)
✓ Log learning sessions (queued)
✓ Log meals/workouts (queued)
✓ Create database records (queued)
✗ Real-time features (graph, insights, search - require network)
```

**Implementation:**

- WatermelonDB for local SQLite database
- Persist-gate middleware for Redux/Zustand
- Network listener: react-native-netinfo or native equivalents

---

# 13. Performance Optimization

**Strategies:**

```
Lazy Loading:
  - Route-based code splitting (Next.js dynamic imports)
  - Component lazy loading (React.lazy + Suspense)
  - Image optimization (next/image, compression)
  - List virtualization for long lists (react-window)

Caching:
  - React Query: stale-while-revalidate (30s, 1m, 5m configs per endpoint)
  - localStorage: theme, user preferences, pagination state
  - Backend Redis: habits/today (2m TTL), dashboard (2m TTL), analytics (5m TTL)
  - HTTP caching headers from API Gateway

Memoization:
  - useMemo for expensive calculations (habit stats, chart data)
  - useCallback for event handlers
  - React.memo for pure components

Rendering:
  - Server-side rendering (Next.js) for initial load
  - Pagination (page-based, 20-50 items per page) instead of infinite scroll
  - Debounced search (500ms for search input)
  - Batch state updates (React.unstable_batchedUpdates)

Metrics:
  - Web Vitals monitoring (LCP, FID, CLS)
  - Backend request latency tracking
  - Cache hit rate monitoring
```

---

# 14. Shared UI Components (Monorepo)

**Shared Components Library (`packages/ui/`):**

```
components/
  ├── Button/
  ├── Input/
  ├── Card/
  ├── Modal/
  ├── List/
  ├── Tabs/
  ├── Pagination/
  ├── Loading/
  ├── Avatar/
  ├── Badge/
  ├── Toast/
  └── Form/
```

**Web-Only Components:**

- Sidebar navigation
- Complex data tables with sorting/filtering
- D3-based graph visualization

**Mobile-Only Components:**

- Bottom tab navigation
- Pull-to-refresh
- Native modal (uses React Native)

**Shared Logic:**

- API hooks (useHabits, useNotes, useLearning, etc.)
- Form utilities (useForm, validation)
- State management (Zustand stores)

---

# 15. Charts & Visualization

**Libraries:**

```
Web:
  - Recharts: line, bar, pie charts (analytics, dashboard)
  - React Flow: interactive graph visualization (knowledge graph)
  - D3.js: force-directed layout for graph nodes

Mobile:
  - Victory Native: line, bar, pie charts
  - react-native-svg: custom visualizations
  - Simple 2D layout for graph (no D3)
```

**Use Cases:**

```
Dashboard:
  - Productivity score trend (line chart, 30 days)
  - Habit completion rate (bar chart)
  - Learning hours distribution (pie chart)

Analytics Screen:
  - Habit trends over time (line chart)
  - Learning hours by topic (bar chart)
  - Health metrics (calories, workouts)
  - Correlation patterns (heatmap)

Learning Stats:
  - Hours by topic (pie/bar)
  - Session frequency (line chart)

Knowledge Graph:
  - Force-directed network (web only)
  - Cluster visualization
```

---

# 16. Search UI

**Implementation:**

```
Search Component:
  - Instant search (debounced 500ms)
  - Type ahead: query → autocomplete suggestions (GET /search/suggest)
  - Search results: paginated list with type icon/badge

Advanced Search:
  - Filters: type (note/habit/learning/record/meal/workout)
  - Date range picker: from/to dates
  - Tags filter (for notes)
  - Sort: relevance, date (newest first)

Results Page:
  - Results per type: show entity icon, title, snippet, created date
  - Pagination: 10-20 results per page
  - Empty state: helpful suggestions
```

**Integration:**

```
- Meilisearch backend (instant, typo-tolerant)
- Rate limited: 200 req/min
- Indexes: notes, habits, learning, records, meals, workouts
```

---

# 17. Knowledge Graph Visualization

**Web (Interactive):**

```
Technology: React Flow + D3 force-directed layout

Features:
  - Node types: notes (📝), habits (✓), learning (📚), health (❤️), records (📊)
  - Click node → expand neighbors (paginated)
  - Drag to pan, scroll to zoom
  - Double-click node → navigate to detail
  - Right-click → context menu (delete, view related)
  - Force-directed simulation: auto-layout based on connections
  - Cluster detection: color-code related entity groups

API Integration:
  - GET /graph/force-directed-layout → nodes[], edges[], layout data
  - GET /graph/neighbors/{node_id} → expand on demand
  - GET /graph/find-knowledge-clusters → cluster detection
```

**Mobile (Simplified):**

```
- Node detail view with neighbor list
- Related entities: tap to navigate
- No force-directed (too complex for mobile)
- Simple BFS traversal UI
```

---

# 18. Notifications

**In-App Notifications:**

```
- Toast: short-lived (3-5s) status messages (success, error, info)
- Modal: persistent, requires user action (important alerts)
- Badge: unread count on settings icon
- Notification center: drawer/modal with paginated list
```

**Push Notifications (Mobile Only):**

```
Process:
  1. On app startup: get device push token (FCM/APNs)
  2. Register token: POST /notifications/push-token (platform: android/ios)
  3. Backend publishes event → Notification Service → FCM/APNs
  4. User receives push → app opens to relevant screen

Supported:
  - Habit reminders
  - Learning session reminders
  - Habit streaks lost (warning)
  - AI insights/recommendations (daily summary)
```

**Email Notifications:**

```
- Password reset link
- Email verification
- Daily summary (optional)
- Configured in backend Notification Service
```

---

# 19. Theming

**Dark/Light Mode:**

```
Using TailwindCSS + CSS Variables:

App Level:
  - Toggle in settings
  - Persist theme to localStorage
  - System preference detection (prefers-color-scheme)
  - Smooth transition (0.3s)

Colors:
  Light:
    - Background: white
    - Text: dark gray/black
    - Accents: blue
    - Cards: light gray bg

  Dark:
    - Background: dark gray/charcoal
    - Text: white/light gray
    - Accents: cyan/bright blue
    - Cards: darker bg with subtle borders

Components:
  - All components support both themes
  - Use CSS custom properties for easy switching
  - Test both themes for accessibility (contrast ratios)
```

---

# 20. Security

**Frontend Security:**

```
Authentication:
  - JWT in httpOnly cookies (web) / encrypted storage (mobile)
  - Automatic token refresh on 401
  - Refresh token rotation per auth
  - Logout clears all tokens and state

Input Validation & Sanitization:
  - Validate on client (email, phone, dates)
  - Sanitize markdown input (DOMPurify) before display
  - Prevent XSS: React auto-escapes, never use dangerouslySetInnerHTML
  - SQL injection: N/A (JSON API)

API Security:
  - HTTPS only (enforce in production)
  - Rate limiting: respect 429 responses
  - CORS: configured at API Gateway
  - Content-Security-Policy headers

Data Handling:
  - Never store sensitive data (passwords, credit cards) in frontend
  - Clear sensitive state on logout
  - Disable copy-paste on sensitive inputs (optional)
  - Biometric for sensitive operations (optional mobile)

Error Handling:
  - Don't expose sensitive errors to user
  - Log errors server-side for debugging
  - Show user-friendly error messages

Push Notifications:
  - Tokens stored securely
  - Token refresh on app reinstall
  - Revoke tokens on logout
```

---

# 21. Testing Strategy

**Unit Tests (Jest):**

```
Coverage targets: >80% for business logic

Tests:
  - API service modules (habits.ts, notes.ts, etc.)
  - State management (Zustand/Redux stores)
  - Utility functions (formatters, validators)
  - Custom hooks (useHabits, useLearning, etc.)
  - Form validation (React Hook Form)
```

**Component Tests (React Testing Library):**

```
Test each screen and major component:

  - Dashboard: metrics rendering, quick actions work
  - Habits screen: list, create, edit, delete, mark complete
  - Notes screen: list, create, edit, delete, backlinks display
  - Learning screen: timer (start/pause/resume/stop), sessions, note linking
  - Health screen: meal/workout logging, stats display
  - Database screen: CRUD operations, filtering, sorting
  - Search: query input, suggestions, results
  - Graph visualization: nodes render, click expands neighbors
  - Auth screens: signup, login, password reset flows
  - Settings: profile edit, session management
```

**Integration Tests:**

```
Test API integration (mocked backend):

  - Auth flow: signup → login → token refresh → logout
  - Create habit → complete → view stats
  - Create note → link note → view backlinks
  - Start learning session → stop → session saved
  - Log meal/workout → daily stats updated
  - Create database → add properties → create records → filter/sort
  - Search: query → results display
  - Offline: create item offline → sync when online
```

**E2E Tests (Cypress/Playwright - optional for Sprint 16):**

```
Full user journeys:
  - User signup → create habit → complete habit → view dashboard
  - Create note → create learning session → link note to session
  - Log meals → log workout → view health stats
  - Search across all entity types
```

---

# 22. CI/CD Pipeline

**Build Process:**

```
Web (Next.js):
  1. Install dependencies: npm ci
  2. Lint: eslint . --fix-unused-eslint-disable
  3. Type check: tsc --noEmit
  4. Build: next build
  5. Test: jest --coverage (>80% required)
  6. E2E: cypress run (optional)
  7. Build image: docker build
  8. Push to registry

Mobile (React Native):
  1. Install dependencies: npm ci
  2. Lint: eslint .
  3. Type check: tsc --noEmit
  4. Test: jest --coverage
  5. Build APK/IPA: expo build (if using Expo)
  6. Distribute to TestFlight/Google Play
```

**Deployment:**

```
Staging:
  - Deploy on every merge to develop
  - Run smoke tests against staging backend
  - Manual QA testing window (24h)

Production:
  - Manual trigger from release/* branch
  - All tests must pass
  - Staging approval required
  - Rollback plan: previous Docker image tag
```

**GitHub Actions Configuration:**

```yaml
name: Frontend CI/CD

on:
  push:
    branches: [develop, main]
  pull_request:
    branches: [develop]

jobs:
  lint-test-build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
        with:
          node-version: 18
      - run: npm ci
      - run: npm run lint
      - run: npm run type-check
      - run: npm run test -- --coverage
      - run: npm run build
      - run: npm run e2e (optional)
```

---

# 23. Observability & Monitoring

**Frontend Logging:**

```
Using structured logging (pino/winston):

  Log Levels:
    - INFO: user actions (page nav, button click, form submit)
    - WARN: API errors, validation failures, missing data
    - ERROR: crashes, unhandled exceptions

  What to Log:
    - API request/response (method, path, status, duration)
    - Auth events (login, logout, token refresh)
    - Form submissions
    - Error stacktraces

  Where to Send:
    - Local: console.log in dev
    - Remote: Sentry or internal logging service in prod
```

**Performance Monitoring:**

```
Using web-vitals library:

  Metrics:
    - LCP (Largest Contentful Paint): <2.5s target
    - FID (First Input Delay): <100ms target
    - CLS (Cumulative Layout Shift): <0.1 target
    - TTFB (Time to First Byte): <600ms target
    - FCP (First Contentful Paint): <1.8s target

  Send to:
    - Google Analytics
    - DataDog / NewRelic dashboard
    - Custom metrics service

  Tracked Per Screen:
    - Dashboard load time
    - List pagination (habit, note, learning, health)
    - Search latency
    - Graph visualization render time
```

**API Performance Tracking:**

```
Measure at API layer:

  - Request duration (ms)
  - Response size (bytes)
  - HTTP status codes distribution
  - Retry counts
  - Cache hit rate
  - Rate limit hits (429 responses)

  Dashboard:
    - Visualize: API latency trends, slow endpoints
    - Alerts: endpoint exceeds 1s, error rate >5%
```

---

# 24. Backend Integration Checklist

**Auth Service:**

- [ ] Login/signup endpoints working
- [ ] Token refresh working
- [ ] Session list working
- [ ] Password reset flow working
- [ ] Email verification flow working

**Habit Service:**

- [ ] Create habit with scheduling
- [ ] Get today's habits (cached endpoint)
- [ ] Mark habit complete
- [ ] Get habit stats (cached)
- [ ] Pagination working on list

**Notes Service:**

- [ ] Create/edit note with markdown
- [ ] Note links (forward references)
- [ ] Backlinks display (notes referencing this note)
- [ ] Pagination working
- [ ] Tag management working

**Learning Service:**

- [ ] Start/pause/resume/stop timer session
- [ ] Manual session logging
- [ ] Topic CRUD
- [ ] Link note to session
- [ ] Get session notes
- [ ] Learning stats calculation

**Health Service:**

- [ ] Log meal with macros
- [ ] Log workout
- [ ] Health stats calculation
- [ ] Daily stats working
- [ ] Log history filtering

**Database Service:**

- [ ] Create database
- [ ] Add properties (text/number/boolean/date/select)
- [ ] CRUD records
- [ ] Filtering by property
- [ ] Sorting by property
- [ ] Pagination working

**Dashboard Service:**

- [ ] Overview endpoint (quick metrics)
- [ ] Daily endpoint (full breakdown)
- [ ] Weekly endpoint (trends)
- [ ] Caching working
- [ ] Cache invalidation on events

**Analytics Service:**

- [ ] Productivity score calculation
- [ ] Trend queries (habits, learning, health)
- [ ] Pattern/anomaly detection
- [ ] Correlation analysis
- [ ] Caching performance OK

**AI Service:**

- [ ] Get insights (with type filter)
- [ ] Get recommendations (with category filter)
- [ ] Summary endpoint (combined)
- [ ] Confidence scores present
- [ ] Caching working

**Graph Service:**

- [ ] Get node neighbors
- [ ] Get subgraph (BFS)
- [ ] Graph stats
- [ ] Find related notes
- [ ] Find knowledge clusters
- [ ] Force-directed layout data

**Search Service:**

- [ ] Basic search (keyword)
- [ ] Type filtering
- [ ] Date range filtering
- [ ] Tag filtering
- [ ] Autocomplete suggestions
- [ ] Rate limiting handled

**Notification Service:**

- [ ] Register push token
- [ ] Notification list (paginated)
- [ ] Mark as read
- [ ] Delete notification
- [ ] Push payload handling (mobile)

---

# 25. Sprint Validation Checklist

**Screens Implemented & Functional:**

- [ ] Auth (login, signup, password reset, email verification)
- [ ] Dashboard (overview, daily, weekly tabs)
- [ ] Habits (list, today, detail, create/edit)
- [ ] Notes (list, create/edit, backlinks, tags)
- [ ] Learning (topics, timer, sessions, link notes)
- [ ] Health (meals, workouts, logs, stats)
- [ ] Database (CRUD, properties, records, filtering, sorting)
- [ ] Analytics (productivity, trends, patterns, insights, recommendations)
- [ ] Knowledge Graph (visualization, neighbors, clusters)
- [ ] Search (unified, advanced, autocomplete)
- [ ] Settings (profile, sessions, push tokens)
- [ ] Notifications (center, in-app, mark read)

**Web App (React/Next.js):**

- [ ] All 12 screens implemented
- [ ] Responsive design (desktop, tablet)
- [ ] Dark/light mode working
- [ ] Navigation working (sidebar + top)
- [ ] Forms working with validation
- [ ] API integration complete
- [ ] Performance optimized (<3s LCP)
- [ ] Tests >80% coverage
- [ ] No console errors/warnings

**Mobile App (React Native):**

- [ ] All screens implemented (simplified where needed)
- [ ] Bottom tab navigation working
- [ ] Stack navigation working
- [ ] Forms optimized for mobile
- [ ] Offline sync queue working
- [ ] Push notifications working
- [ ] Performance optimized (<2s startup)
- [ ] Tests >70% coverage
- [ ] No errors on Android + iOS

**API Integration:**

- [ ] All 12 services' endpoints integrated
- [ ] Token refresh working
- [ ] Error handling for all failures
- [ ] Rate limiting handling (429)
- [ ] Caching strategy working
- [ ] Pagination working across all list screens
- [ ] Filtering/sorting working (database, search)

**Cross-Platform:**

- [ ] Shared components working on both web and mobile
- [ ] Shared API client working
- [ ] State management synced
- [ ] Authentication unified

**Performance:**

- [ ] Web: LCP <2.5s, FID <100ms, CLS <0.1
- [ ] Mobile: App startup <2s, list scrolling smooth (60fps)
- [ ] API: Request latency <500ms median
- [ ] Caching: Cache hit rate >70%
- [ ] Bundle size: Web <250KB gzipped

**Security:**

- [ ] Tokens stored securely
- [ ] No sensitive data in localStorage
- [ ] XSS prevention (DOMPurify on markdown)
- [ ] CORS working
- [ ] Input validation on all forms
- [ ] HTTPS enforced in production

**Quality:**

- [ ] Unit tests: >80% coverage
- [ ] Integration tests: all critical flows
- [ ] E2E tests: main user journeys (optional)
- [ ] Manual QA: all screens tested
- [ ] Accessibility: WCAG 2.1 AA
- [ ] No TypeScript errors

---

# Final Outcome

After Sprint 16, KOROBOS will have:

✅ **Full Frontend Platform**

- Web app (React/Next.js): responsive, desktop-first
- Mobile app (React Native): iOS & Android ready
- Unified authentication and session management

✅ **Complete Service Integration**

- All 12 microservices fully integrated
- Real-time event handling via Kafka
- Offline-first sync for mobile

✅ **Unified UI/UX**

- Consistent design system across web and mobile
- Dark/light mode support
- Fully responsive and accessible

✅ **Complete Product Usability**

- End-to-end workflows for all 12 services
- Real-time dashboard and insights
- Knowledge graph visualization
- Full-text search across all domains

✅ **Production Ready**

- Performance optimized
- Comprehensive testing
- Monitoring and observability
- Security hardened

**This completes the end-to-end KOROBOS second brain platform.**
The system enables users to track habits, manage knowledge, monitor learning, track health, and gain AI-powered insights—all in one unified interface.
