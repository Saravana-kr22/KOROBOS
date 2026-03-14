# KOROBOS

# Frontend Component & UI Architecture

Version: 1.0\
Owner: Saravana Perumal K

---

## 1. Frontend Architecture Overview

The KOROBOS frontend is a modular React application designed around:

- Reusable UI components
- Widget-driven dashboards
- Microservice API integration
- Scalable state management

Architecture Layers:

UI Layer → Component Layer → Widget Layer → Page Layer → State
Management → API Service Layer → Backend Microservices

---

## 2. Technology Stack

Layer Technology

---

Frontend Framework React / Next.js
Language TypeScript
State Management Zustand / Redux Toolkit
Styling Tailwind CSS
Charts Recharts
Graph Visualization D3.js / Sigma.js
Markdown Editor TipTap / CodeMirror
Build Tool Vite / Next Build

---

## 3. Frontend Folder Structure

    src/

    app/
      layout.tsx
      providers.tsx

    pages/
      dashboard
      notes
      habits
      learning
      health
      analytics
      graph
      settings

    components/
      ui
      layout
      navigation
      charts
      forms
      modals

    widgets/
      HabitWidget
      LearningWidget
      HealthWidget
      KnowledgeWidget
      AIInsightWidget
      TrendChartWidget
      ProgressWidget

    features/
      auth
      notes
      habits
      learning
      health
      analytics

    services/
      apiClient
      authService
      notesService
      habitService
      learningService
      healthService

    store/
      userStore
      dashboardStore
      widgetStore
      analyticsStore

    hooks/
      useAuth
      useDashboard
      useWidgets
      useAnalytics

    utils/
      dateUtils
      chartUtils
      markdownUtils

    types/
      apiTypes
      widgetTypes
      userTypes

---

## 4. Component Hierarchy

    App
    │
    ├── Layout
    │    ├── Sidebar
    │    ├── Topbar
    │    └── MainContainer
    │
    ├── Pages
    │    ├── DashboardPage
    │    ├── NotesPage
    │    ├── HabitPage
    │    ├── LearningPage
    │    ├── HealthPage
    │    ├── AnalyticsPage
    │
    └── Widgets
         ├── HabitWidget
         ├── LearningWidget
         ├── HealthWidget
         ├── AIInsightWidget

---

## 5. Layout Architecture

    AppLayout
    │
    ├── SidebarNavigation
    ├── TopNavigation
    └── ContentArea

Layout Structure

    +----------------------------------------------------+
    | Topbar                                             |
    +-------------------+--------------------------------+
    | Sidebar           | Main Content                   |
    |                   |                                |
    | Dashboard         | Page Content                   |
    | Notes             |                                |
    | Habits            |                                |
    | Learning          |                                |
    | Health            |                                |
    | Analytics         |                                |
    +-------------------+--------------------------------+

---

## 6. UI Component Library

Reusable UI primitives:

    components/ui

Core Components:

- Button.tsx
- Card.tsx
- Input.tsx
- Modal.tsx
- Dropdown.tsx
- Tabs.tsx

---

## 7. Navigation Components

Navigation elements:

    components/navigation

Sidebar:

- Sidebar.tsx
- SidebarItem.tsx
- SidebarGroup.tsx

Top Navigation:

- Topbar.tsx
- SearchBar.tsx
- NotificationMenu.tsx
- ProfileMenu.tsx

---

## 8. Dashboard Widget Engine

Widget Container:

    WidgetContainer.tsx

Responsibilities:

- Drag & drop
- Layout grid
- Resize widgets

Widget Renderer:

    WidgetRenderer.tsx

Example:

```typescript
const widgetMap = {
  habit: HabitWidget,
  learning: LearningWidget,
  health: HealthWidget,
  ai: AIInsightWidget,
};
```

---

## 9. Widget Structure

    HabitWidget/
      HabitWidget.tsx
      HabitWidgetHeader.tsx
      HabitWidgetBody.tsx
      HabitWidgetFooter.tsx

---

## 10. Page Architecture

Dashboard Page:

    DashboardPage
    │
    ├── WidgetContainer
    │    ├── HabitWidget
    │    ├── LearningWidget
    │    ├── HealthWidget
    │    └── AIWidget

Notes Page:

    NotesPage
    │
    ├── NotesSidebar
    ├── MarkdownEditor
    ├── BacklinksPanel
    └── GraphPreview

Habit Page:

    HabitPage
    │
    ├── HabitList
    ├── HabitAnalytics
    └── HabitCreationModal

---

## 11. State Management

Recommended:

- Zustand
- Redux Toolkit

Store Structure:

    store/

    userStore
    dashboardStore
    widgetStore
    habitStore
    notesStore
    analyticsStore

Example:

```typescript
const useWidgetStore = create((set) => ({
  widgets: [],
  addWidget: (widget) => set(...)
}))
```

---

## 12. API Service Layer

API Client:

    services/apiClient.ts

Example:

```typescript
export const api = axios.create({
  baseURL: "/api/v1",
});
```

Services:

- notesService.ts
- habitService.ts
- learningService.ts
- healthService.ts
- analyticsService.ts

---

## 13. Data Fetching Strategy

Recommended library:

- TanStack Query (React Query)

Example:

```typescript
useQuery(["habits"], getHabits);
```

Benefits:

- caching
- background updates
- loading states

---

## 14. Event Driven Updates

Real-time updates using:

- WebSocket
- Server Sent Events (SSE)

Use cases:

- dashboard refresh
- notifications
- analytics updates

---

## 15. Knowledge Graph Components

    components/graph

Files:

- KnowledgeGraph.tsx
- GraphNode.tsx
- GraphEdge.tsx
- GraphControls.tsx

Libraries:

- D3.js
- Sigma.js

---

## 16. Markdown Editor Architecture

    components/editor

Files:

- MarkdownEditor.tsx
- Toolbar.tsx
- BacklinksPanel.tsx

Libraries:

- TipTap
- CodeMirror

---

## 17. Authentication Flow

    Login → JWT Token → Store Token → API Requests

Components:

- authService
- useAuth hook

---

## 18. Routing Architecture

Example routes:

    /dashboard
    /notes
    /habits
    /learning
    /health
    /analytics
    /graph
    /settings

---

## 19. Error Handling System

Components:

- ErrorBoundary.tsx
- apiInterceptor.ts

---

## 20. Performance Optimization

Techniques:

- React.memo
- Lazy loading
- Virtualized lists

Example:

    React.lazy()

---

## 21. Theming System

ThemeProvider controls:

- Dark Mode (Cyberpunk)
- Light Mode

---

## 22. Testing Strategy

Tools:

- Jest
- React Testing Library
- Cypress

Test Types:

- Unit tests
- Integration tests
- UI tests

---

## 23. Build & Deployment

Build tools:

- Vite
- Next Build

Deployment:

- Docker
- CDN
- Cloud Hosting

---

# Final Vision

The KOROBOS UI architecture enables:

- scalable component design
- modular widget dashboards
- microservice-driven APIs
- real-time productivity insights

This architecture allows KOROBOS to function as a **personal
productivity operating system interface**.
