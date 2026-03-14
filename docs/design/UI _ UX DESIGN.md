# **KOROBOS Design System**

**Version: 1.0**  
**Owner: Saravana Perumal K**

---

# **1\. Design System Overview**

## **Purpose**

**The KOROBOS Design System provides a consistent UI framework for building the entire platform.**

**It ensures:**

**• visual consistency**  
**• faster UI development**  
**• reusable components**  
**• scalable product design**

---

## **Design Principles**

### **1\. Visual Intelligence**

**The UI prioritizes insight visualization over data entry.**

**Examples**

**• analytics widgets**  
**• knowledge graph**  
**• trend dashboards**

---

### **2\. Cyberpunk Futurism**

**The interface resembles a digital command center.**

**Characteristics**

**• glowing borders**  
**• glass panels**  
**• floating widgets**

---

### **3\. Modular Widgets**

**Everything is a widget component.**

**Examples**

**• habit widget**  
**• learning widget**  
**• analytics widget**

---

### **4\. Instant Interaction**

**Primary actions should be reachable in one click.**

**Examples**

**Create note**  
**Mark habit complete**  
**Log learning**

---

# **2\. Design Tokens**

**Design tokens are the core variables used across UI components.**

---

# **2.1 Color System**

## **Primary Colors**

| Token | Color | Usage |
| ----- | ----- | ----- |
| **primary\_neon** | **\#00F5FF** | **main accent** |
| **primary\_dark** | **\#0A0A0F** | **background** |
| **secondary\_purple** | **\#9D4EDD** | **highlights** |
| **accent\_pink** | **\#FF006E** | **alerts** |

---

## **Neutral Colors**

| Token | Color |
| ----- | ----- |
| **gray\_100** | **\#F8F9FA** |
| **gray\_300** | **\#CED4DA** |
| **gray\_500** | **\#6C757D** |
| **gray\_700** | **\#343A40** |
| **gray\_900** | **\#121212** |

---

## **Semantic Colors**

| Token | Usage |
| ----- | ----- |
| **success** | **\#00FF9C** |
| **warning** | **\#FFC300** |
| **error** | **\#FF3B3B** |
| **info** | **\#0096FF** |

---

# **2.2 Typography System**

**Primary Font**

**Inter**

**Secondary Font**

**JetBrains Mono**

---

## **Font Scale**

| Token | Size |
| ----- | ----- |
| **display** | **48px** |
| **h1** | **36px** |
| **h2** | **30px** |
| **h3** | **24px** |
| **h4** | **20px** |
| **body** | **16px** |
| **caption** | **12px** |

---

## **Font Weights**

| Weight | Value |
| ----- | ----- |
| **regular** | **400** |
| **medium** | **500** |
| **semibold** | **600** |
| **bold** | **700** |

---

# **2.3 Spacing System**

**Spacing uses 8px grid system.**

| Token | Size |
| ----- | ----- |
| **xs** | **4px** |
| **sm** | **8px** |
| **md** | **16px** |
| **lg** | **24px** |
| **xl** | **32px** |
| **xxl** | **48px** |

---

# **2.4 Border Radius**

| Token | Radius |
| ----- | ----- |
| **sm** | **6px** |
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

| Parameter | Value |
| ----- | ----- |
| **Columns** | **12** |
| **Gutter** | **24px** |
| **Margin** | **64px** |

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

| Icon | Usage |
| ----- | ----- |
| **home** | **dashboard** |
| **note** | **notes** |
| **chart** | **analytics** |
| **graph** | **knowledge graph** |
| **settings** | **settings** |

---

# **5\. Component Library**

---

# **5.1 Buttons**

**Primary Button**

**Background: neon blue**

**Text: white**

**Border radius: 12px**

**Example**

**\+----------------+**

**| Create Note |**

**\+----------------+**

---

**Secondary Button**

**Glass background**

**Neon border**

**Example**

**\+----------------+**

**| Add Widget |**

**\+----------------+**

---

**Ghost Button**

**Used for minimal UI.**

**transparent background**

---

# **5.2 Input Fields**

**Style**

**Glassmorphism**

**background: rgba(255,255,255,0.05)**

**border: 1px solid neon**

**Example**

**\+---------------------------+**

**| Search notes... |**

**\+---------------------------+**

---

# **5.3 Cards**

**Cards are used for widgets.**

**Properties**

**background: glass panel**

**blur: 12px**

**border: neon glow**

**Example**

**\+----------------------+**

**| Habit Progress |**

**| 80% Completed |**

**\+----------------------+**

---

# **5.4 Navigation Sidebar**

**Structure**

**\+------------------+**

**| Logo |**

**| Dashboard |**

**| Notes |**

**| Habits |**

**| Learning |**

**| Health |**

**| Graph |**

**| Analytics |**

**| Settings |**

**\+------------------+**

---

# **5.5 Top Navigation Bar**

**Contains**

**Search**  
**Quick capture**  
**Notifications**  
**Profile**

**\+----------------------------------------+**

**| Search | Capture | Notifications | Profile |**

**\+----------------------------------------+**

---

# **5.6 Tabs**

**Example**

**Notes | Graph | Backlinks**

---

# **5.7 Toggle Switch**

**Example**

**AI Insights ON / OFF**

---

# **5.8 Progress Indicators**

**Types**

**• progress bars**  
**• radial progress**  
**• streak indicators**

**Example**

**Habit Completion**

**████████░░ 80%**

---

# **6\. Widget System**

**Widgets are the core UI building blocks.**

**Examples**

| Widget | Purpose |
| ----- | ----- |
| **Habit Widget** | **habit progress** |
| **Learning Widget** | **learning analytics** |
| **Health Widget** | **calories** |
| **Knowledge Widget** | **notes** |
| **AI Widget** | **insights** |

---

## **Widget Structure**

**\+--------------------------+**

**| Widget Title |**

**| Metric |**

**| Chart |**

**\+--------------------------+**

---

# **7\. Motion Design**

**Animation duration**

**200ms – 300ms**

---

**Examples**

**Hover glow**  
**Graph expansion**  
**Widget loading**

---

# **8\. Micro Interactions**

**Examples**

**Hover widget → glow**

**Click node → expand**

**Add note → animation**

---

# **9\. Dark Mode**

**Default mode**

**Cyberpunk dark**

---

**Optional theme**

**Light analytical mode**

---

# **10\. Accessibility**

**Standards**

**WCAG 2.1**

**Requirements**

**• keyboard navigation**  
**• high contrast**  
**• readable fonts**

---

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
