# **CortexOS**

# **Widget Component Library**

Version: 1.0  
Owner: Saravana Perumal K

---

# **1\. Widget System Overview**

Widgets are **self-contained UI components** that display real-time insights and allow quick interaction with CortexOS modules.

Characteristics

 - modular  
 - draggable  
 - resizable  
 - data-driven  
 - real-time updates

Each widget communicates with backend services via the **Dashboard Service aggregation layer**.

---

# **2\. Widget Architecture**

All widgets follow a standardized structure.

    +--------------------------------+
    | Widget Header                  |
    | Title        Actions           |
    +--------------------------------+
    | Widget Body                    |
    | Metrics / Charts / Controls    |
    +--------------------------------+
    | Widget Footer (optional)       |
    | Navigation / Quick Actions     |
    +--------------------------------+


---

# **3\. Widget Layout System**

Widgets follow a **grid layout**.

Desktop dashboard

12 column grid

Widget sizes

| Size | Columns |
| ----- | ----- |
| Small | 3 |
| Medium | 6 |
| Large | 9 |
| Full | 12 |

---

# **4\. Core Widget Types**

The system consists of **15 primary widgets**.

### **Productivity Widgets**

1. Habit Widget  
2. Learning Widget  
3. Health Widget  
4. Knowledge Activity Widget  
5. Productivity Score Widget

### **Insight Widgets**

6. AI Insight Widget  
7. Weekly Progress Widget  
8. Goal Tracker Widget

### **Visualization Widgets**

9. Trend Chart Widget  
10. Progress Ring Widget  
11. Activity Timeline Widget

### **Utility Widgets**

12. Quick Capture Widget  
13. Task Widget  
14. Notification Widget  
15. Focus Mode Widget

---

# **5\. Widget Base Component**

All widgets extend a **BaseWidget component**.

Example React interface

```typescript
interface WidgetProps {
  id: string
  title: string
  size: "small" | "medium" | "large" | "full"
  refreshInterval?: number
}
```

---

# **6\. Habit Widget**

Purpose

Display daily habit progress.

---

## **Layout**

    +----------------------------+
    | Habit Progress             |
    +----------------------------+

    Workout      ✔
    Study        ✔
    Meditation   ✖

    Completion
    ████████░░ 80%

---

## **Features**

 - mark habit complete  
 - view streak  
 - quick navigation

---

## **Data Source**

Habit Service

API

`GET /habits/today`

---

# **7\. Learning Widget**

Purpose

Track learning progress.

---

## **Layout**

    +----------------------------+
    | Learning Tracker           |
    +----------------------------+

    Today
    3 Hours

    Recent Topics
    AI
    System Design

    [ Log Session ]


## **Metrics**

 - learning hours today  
 - weekly learning time  
 - active topics

---

# **8\. Health Widget**

Purpose

Display fitness metrics.

---

## **Layout**

    +----------------------------+
    | Health Summary             |
    +----------------------------+

    Calories Today
    1850

    Workout
    Running 30 min

---

## **Data Source**

Health Service

API

`GET /health/summary`

---

# **9\. Knowledge Activity Widget**

Purpose

Display knowledge activity.

---

## **Layout**

    +----------------------------+
    | Knowledge Activity         |
    +----------------------------+

    Notes Created Today
    5

    Active Topics
    AI
    Product Design

---

## **Features**

 - open note editor  
 - explore graph

---

# **10\. Productivity Score Widget**

Purpose

Show productivity performance.

---

## **Layout**

    +----------------------------+
    | Productivity Score         |
    +----------------------------+

    Score
    82 / 100

    Trend
    ↑ +6%

---

## **Calculation Inputs**

 - habits  
 - learning sessions  
 - activity logs

Computed by **Analytics Service**.

---

# **11\. AI Insight Widget**

Purpose

Display AI-generated insights.

---

## **Layout**

    +----------------------------+
    | AI Insight                 |
    +----------------------------+

    You studied more this week.

    Suggestion
    Review Deep Learning notes.

---

## **Backend Flow**

Event data → AI Service → Insight generation.

---

# **12\. Weekly Progress Widget**

Purpose

Show weekly performance.

---

## **Layout**

    +----------------------------+
    | Weekly Progress            |
    +----------------------------+

    Mon ████
    Tue ██████
    Wed ███
    Thu ███████
    Fri ████

---

# **13\. Goal Tracker Widget**

Purpose

Track personal goals.

---

## **Layout**

    +----------------------------+
    | Goals                      |
    +----------------------------+

    Learn ML
    ████████░░ 80%

    Run 50km
    ██████░░░░ 60%

---

# **14\. Trend Chart Widget**

Purpose

Display trends.

---

## **Layout**


    +----------------------------+
    | Productivity Trend         |
    +----------------------------+

    Chart

Types

 - line chart  
 - bar chart  
 - area chart

---

# **15\. Progress Ring Widget**

Purpose

Visual completion indicator.

---

## **Layout**

    +----------------------------+
    | Daily Completion           |
    +----------------------------+

        75%
      (Ring Chart)

---

# **16\. Activity Timeline Widget**

Purpose

Show user activity timeline.

---

## **Layout**

    +----------------------------+
    | Activity Timeline          |
    +----------------------------+

    9:00  Logged Learning
    10:30 Created Note
    12:00 Workout

---

# **17\. Quick Capture Widget**

Purpose

Instant idea capture.

---

## **Layout**

    +----------------------------+
    | Quick Capture              |
    +----------------------------+

    Write idea...

    [ Save Note ]

Shortcut

    CTRL \+ SPACE

---

# **18\. Task Widget**

Purpose

Display tasks.

---

## **Layout**

    +----------------------------+
    | Tasks                      |
    +----------------------------+

    [ ] Review ML paper
    [ ] Write blog
    [ ] Workout

---

# **19\. Notification Widget**

Purpose

Show reminders.

---

## **Layout**

    +----------------------------+
    | Notifications              |
    +----------------------------+

    Habit Reminder
    Workout Reminder
    Learning Reminder

---

# **20\. Focus Mode Widget**

Purpose

Help users focus.

---

## **Layout**

    +----------------------------+
    | Focus Mode                 |
    +----------------------------+

    Pomodoro Timer

    25:00

    [ Start ]

---

# **21\. Widget Customization**

Users can modify dashboard.

Options

    Add Widget
    Remove Widget
    Resize Widget
    Drag Widget

---

# **22\. Widget State Management**

Frontend state stored in:

    Redux / Zustand store

Example state

```typescript
{
  widgets: [
    { id: "habit", size: "small", position: 1 },
    { id: "learning", size: "medium", position: 2 }
  ]
}
```

---

# **23\. Widget Data Refresh**

Widgets refresh automatically.

Default interval

    30 seconds

---

# **24\. Widget Performance Optimization**

Techniques

 - lazy loading  
 - virtualization  
 - caching

---

# **25\. Widget Folder Structure (React)**

Example structure

    src/

    widgets/
      HabitWidget
      LearningWidget
      HealthWidget
      KnowledgeWidget
      AIInsightWidget

    components/
      WidgetContainer
      WidgetHeader
      WidgetBody

---

# **Final Widget System Vision**

The CortexOS dashboard becomes a **modular productivity cockpit** where:

 - each widget is a data instrument  
 - insights are always visible  
 - users customize their control center

