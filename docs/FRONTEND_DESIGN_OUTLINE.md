# C/AI Arena Frontend - Design Outline

**Phase:** Week 13 Design (Build in Week 21-23)  
**Technology Stack:** React + TypeScript + Tailwind CSS  
**Status:** Design Phase (No code yet)

---

## Design Philosophy

- **Clean & Professional:** Suitable for research & enterprise use
- **Data-Focused:** Tables, charts, and statistics front-and-center
- **Dark Mode:** Default dark theme with light mode toggle
- **Responsive:** Mobile-friendly where practical
- **Accessible:** WCAG 2.1 AA compliance target

---

## App Shell

```
┌─────────────────────────────────────────────────────────────────┐
│                    C/AI Arena Optimization                      │
├────────────┬──────────────────────────────────────────────────┤
│            │                                                   │
│ Sidebar    │                 Main Content                     │
│ - Dashboard│                                                   │
│ - Benchmark│                                                   │
│ - Experiment                                                   │
│ - Results  │                                                   │
│ - Settings │                                                   │
│            │                                                   │
│ [Avatar]   │                                                   │
│ [Logout]   │                                                   │
│            │                                                   │
└────────────┴──────────────────────────────────────────────────┘
```

### Sidebar Navigation

```
LOGO
────────────────
📊 Dashboard
📋 Benchmarks
🧪 Experiments
📈 Results
⚙️ Settings

────────────────
👤 Profile
🔐 Account
🚪 Logout
```

### Topbar

```
[Search] [🔔 Notifications] [🌙 Theme] [👤 User Menu]
```

---

## Tab 1: Dashboard

### Overview Cards (Hero Section)

```
┌──────────┬──────────────┬──────────────┬──────────────┐
│ Total    │ Active       │ Completed    │ System       │
│ Expts: 42│ Expts: 3     │ Expts: 35    │ Health: ✅   │
├──────────┴──────────────┴──────────────┴──────────────┤
│                                                       │
│         Recent Experiments (Table)                   │
│ ┌─────────┬──────────┬────────┬──────────┬────────┐ │
│ │ Name    │ Benchmark│ Status │ Progress │ Action │ │
│ ├─────────┼──────────┼────────┼──────────┼────────┤ │
│ │ Exp 1   │ Math v1  │Running │ 75%      │ View   │ │
│ │ Exp 2   │ Code v2  │Complete│ 100%     │ View   │ │
│ │ Exp 3   │ Math v1  │Created │ 0%       │ Queue  │ │
│ └─────────┴──────────┴────────┴──────────┴────────┘ │
│                                                       │
├───────────────────┬────────────────────────────────┤
│  Top Candidates   │  System Metrics                 │
│  1. Claude Opus   │  • CPU: 35%                     │
│  2. GPT-4         │  • Memory: 42%                  │
│  3. Claude Sonnet │  • Database: Healthy            │
│  4. Gemini Pro    │  • API Response: 142ms (avg)    │
└───────────────────┴────────────────────────────────┘
```

### Components

- **StatCard** (4x: Total, Active, Completed, Health)
- **ExperimentTable** (status, progress bar, actions)
- **TopCandidateBadge** (rank + name)
- **MetricsWidget** (system health gauge)

---

## Tab 2: Benchmarks

### Left Sidebar (Benchmark List)

```
[+ Create New Benchmark]

Search: ________________

📌 All (5)
├─ Math Reasoning (v3, 50 tasks)
├─ Code Generation (v2, 100 tasks)
├─ Creative Writing (v1, 25 tasks)
├─ Multilingual (v4, 200 tasks)
└─ Few-shot Learning (v1, 30 tasks)

[Archive] [Deleted]
```

### Main Content (Benchmark Detail)

```
┌─────────────────────────────────────┐
│ Math Reasoning Benchmark             │
├─────────────────────────────────────┤
│ Description: Test mathematical...    │
│ Language: Python                     │
│ Difficulty: Advanced                 │
│ Versions: 3                          │
│ Tasks: 50 total                      │
│                                      │
│ [Edit] [Delete] [Version History]   │
├─────────────────────────────────────┤
│                                      │
│ Versions                             │
│ ┌──────┬─────────┬──────────────────┐│
│ │Ver   │ Tasks   │ Created          ││
│ ├──────┼─────────┼──────────────────┤│
│ │v3    │ 50      │ Oct 21, 2026     ││
│ │v2    │ 45      │ Oct 18, 2026     ││
│ │v1    │ 30      │ Oct 15, 2026     ││
│ └──────┴─────────┴──────────────────┘│
│                                      │
│ Tasks Preview (first 10)             │
│ ┌──────┬──────────┬──────────────┐  │
│ │Task  │Input     │Expected Out  │  │
│ ├──────┼──────────┼──────────────┤  │
│ │1     │"2+2"     │"4"           │  │
│ │2     │"15*3"    │"45"          │  │
│ │3     │"100/2"   │"50"          │  │
│ │...   │...       │...           │  │
│ └──────┴──────────┴──────────────┘  │
│                                      │
│ [Download as CSV] [Clone] [Delete]   │
└─────────────────────────────────────┘
```

### Create Benchmark Modal

```
┌─────────────────────────────────────┐
│ Create New Benchmark                 │
├─────────────────────────────────────┤
│                                      │
│ Name: [_____________________]        │
│                                      │
│ Description:                         │
│ [_____________________________]       │
│ [_____________________________]       │
│                                      │
│ Language: [Dropdown: Python]         │
│ Difficulty: [Dropdown: Advanced]     │
│                                      │
│             [Cancel] [Create]        │
└─────────────────────────────────────┘
```

### Components

- **BenchmarkCard** (minimal preview)
- **BenchmarkDetail** (full info)
- **VersionTable** (version history)
- **TaskPreviewTable** (sample tasks)
- **CreateBenchmarkModal** (form)

---

## Tab 3: Experiments

### Experiments List View

```
[+ Create New Experiment]

Filters: [Status ▼] [Benchmark ▼] [Date Range ▼]

┌─────────────────────────────────────────────────────────┐
│ Experiment Name     │ Benchmark │ Status │ Progress    │
├─────────────────────────────────────────────────────────┤
│ Opus vs GPT-4       │ Math v1   │ Running│ ████░░░░░░ │
│ Sonnet Testing      │ Code v2   │ Complete│ ██████████ │
│ Multilingual Demo   │ Multiln v1│ Created │ ░░░░░░░░░░ │
│ Creative Output     │ Writing v1│ Failed  │ ██░░░░░░░░ │
└─────────────────────────────────────────────────────────┘

[Previous] [1][2][3] [Next]
```

### Experiment Detail View

```
┌──────────────────────────────────────────────────────┐
│ Experiment: Opus vs GPT-4                            │
├──────────────────────────────────────────────────────┤
│ Status: Running | Progress: 75% (3/4 complete)      │
│ Benchmark: Math Reasoning (v1) | Tasks: 50          │
│ Started: Oct 21, 10:05 | Estimated: Oct 21, 10:45  │
│                                                      │
│ [Cancel] [Download Results] [View Stats]            │
├──────────────────────────────────────────────────────┤
│                                                      │
│ Executions In Progress                              │
│ ┌────────────────────────────────────────────────┐  │
│ │Claude Opus     [████░░░░░░] 80% (40/50 tasks) │  │
│ │  • Score: TBD                                  │  │
│ │  • Time Remaining: ~5 min                      │  │
│ │  • [View Logs]                                 │  │
│ ├────────────────────────────────────────────────┤  │
│ │GPT-4          [██████░░░░] 60% (30/50 tasks)  │  │
│ │  • Score: TBD                                  │  │
│ │  • Time Remaining: ~8 min                      │  │
│ │  • [View Logs]                                 │  │
│ ├────────────────────────────────────────────────┤  │
│ │Claude Sonnet   [██████████] 100% (50/50 tasks)│  │
│ │  • Score: 92.5                                 │  │
│ │  • Completed: 5 min ago                        │  │
│ │  • [View Logs]                                 │  │
│ └────────────────────────────────────────────────┘  │
│                                                      │
└──────────────────────────────────────────────────────┘
```

### Create Experiment Modal

```
┌──────────────────────────────────────────────┐
│ Create New Experiment                         │
├──────────────────────────────────────────────┤
│                                               │
│ Name: [_________________________]             │
│                                               │
│ Description: [_____________________]         │
│             [_____________________]         │
│                                               │
│ Benchmark: [Dropdown: Math v1]              │
│                                               │
│ Candidates: [Checkboxes]                    │
│ ☑ Claude Opus                               │
│ ☑ GPT-4                                     │
│ ☐ Claude Sonnet                             │
│ ☐ Gemini Pro                                │
│                                               │
│ Runs Per Candidate: [_____] (default: 1)    │
│                                               │
│        [Cancel] [Create & Queue]             │
└──────────────────────────────────────────────┘
```

### Execution Log View (Modal)

```
┌─────────────────────────────────────┐
│ Logs: Claude Opus                    │
├─────────────────────────────────────┤
│                                     │
│ 10:05:00 INFO Starting execution   │
│ 10:05:02 INFO Task 1/50 complete   │
│ 10:05:04 INFO Task 2/50 complete   │
│ 10:05:06 INFO Task 3/50 complete   │
│ ...                                 │
│ [Auto-scroll: ON] [Download]        │
│                                     │
└─────────────────────────────────────┘
```

### Components

- **ExperimentListTable** (search, filter, paginate)
- **ExperimentDetailCard** (status, progress)
- **ExecutionProgressBar** (task progress)
- **CreateExperimentModal** (form with multi-select)
- **LogViewer** (auto-scrolling log display)

---

## Tab 4: Results & Leaderboard

### Results Overview

```
Experiment: Opus vs GPT-4 (Math v1)

┌──────────────────────────────────────────────────────┐
│ Results Summary                                       │
├──────────────────────────────────────────────────────┤
│ Total Tasks: 50 | Successful: 49 | Failed: 1        │
├──────────────────────────────────────────────────────┤
│                                                      │
│ Scores:                                              │
│ ┌────────────────┬────────────┬────────────────────┐│
│ │Candidate       │Score       │Confidence (95%)    ││
│ ├────────────────┼────────────┼────────────────────┤│
│ │Claude Opus     │95.5        │93.2 - 97.8        ││
│ │GPT-4          │92.3        │89.1 - 95.5        ││
│ │Claude Sonnet   │89.7        │86.4 - 93.0        ││
│ └────────────────┴────────────┴────────────────────┘│
│                                                      │
│ Statistical Significance:                           │
│ • Opus vs GPT-4: p = 0.0234 ✓ (significant)        │
│ • Opus vs Sonnet: p = 0.0001 ✓ (highly significant)│
│ • GPT-4 vs Sonnet: p = 0.189 ✗ (not significant)   │
│                                                      │
│ [Download CSV] [View Detailed Stats] [Compare]      │
└──────────────────────────────────────────────────────┘
```

### Leaderboard View

```
Leaderboard: Math Reasoning Benchmark

Sort by: [Score ▼] | Filter: [All Time ▼]

┌────┬─────────────────┬────────┬────────┬──────┬──────┐
│Rank│ Candidate       │ Score  │Expts   │Wins  │ Loss │
├────┼─────────────────┼────────┼────────┼──────┼──────┤
│ 1  │ Claude Opus     │ 95.5   │  5     │  4   │  0   │
│ 2  │ GPT-4           │ 92.3   │  5     │  1   │  3   │
│ 3  │ Claude Sonnet   │ 89.7   │  4     │  0   │  4   │
│ 4  │ Gemini Pro      │ 88.2   │  3     │  0   │  3   │
│ 5  │ LLaMA 2         │ 72.1   │  2     │  0   │  2   │
└────┴─────────────────┴────────┴────────┴──────┴──────┘

Click row to see detailed stats
```

### Comparison Chart

```
Detailed Comparison: Opus vs GPT-4

Metrics:
┌─────────────────────────────────────┐
│ Score: Opus 95.5 vs GPT-4 92.3      │ 
│ ▓▓▓▓▓▓▓▓▓▓░░░░░░░░░░               │
│                                     │
│ Accuracy: Opus 0.955 vs 0.923       │
│ ▓▓▓▓▓▓▓▓▓▓░░░░░░░░░░               │
│                                     │
│ Speed (avg): Opus 2.34s vs 3.21s    │
│ ▓▓▓▓░░░░░░░░░░░░░░░░               │
│                                     │
│ Failure Rate: Opus 0% vs GPT-4 2%   │
│ ▓░░░░░░░░░░░░░░░░░░░░              │
│                                     │
│ Statistical Significance: p < 0.05 ✓│
│ Difference: 3.2 ± 1.8 (95% CI)      │
│ Effect Size: 0.45 (medium)          │
└─────────────────────────────────────┘

[Download Report]
```

### Components

- **ResultsSummaryCard** (overview stats)
- **ScoreTable** (candidate scores + CI)
- **StatisticalSignificanceRow** (p-values)
- **LeaderboardTable** (ranking)
- **ComparisonChart** (metric bars)
- **DetailedReportModal** (full analysis)

---

## Tab 5: Settings

### Settings Panels

```
┌────────────────────────────────────────┐
│ Settings                                │
├────────────────────────────────────────┤
│                                         │
│ System Configuration                   │
│ ┌──────────────────────────────────┐  │
│ │ Environment: Development         │  │
│ │ Database: PostgreSQL ✓           │  │
│ │ Queue System: Memory             │  │
│ │ Max Concurrent: 5                │  │
│ │ Log Level: [DEBUG ▼]             │  │
│ │ Log Format: [text ▼]             │  │
│ │                  [Save Changes]  │  │
│ └──────────────────────────────────┘  │
│                                         │
│ API Configuration                      │
│ ┌──────────────────────────────────┐  │
│ │ API Key: [***hidden***] [Copy]   │  │
│ │ Token Expiry: 3600 seconds       │  │
│ │ Rate Limit: 100 req/min          │  │
│ │ [Rotate Token]                   │  │
│ └──────────────────────────────────┘  │
│                                         │
│ User Preferences                       │
│ ┌──────────────────────────────────┐  │
│ │ Theme: [Dark ▼]                  │  │
│ │ Timezone: [UTC ▼]                │  │
│ │ Notifications: [✓ Enabled]       │  │
│ │ Results Export Format: [CSV ▼]   │  │
│ │                  [Save Preferences] │
│ └──────────────────────────────────┘  │
│                                         │
│ Danger Zone                            │
│ ┌──────────────────────────────────┐  │
│ │ [Clear Cache] [Reset Settings]   │  │
│ │ [Sign Out]    [Delete Account]   │  │
│ └──────────────────────────────────┘  │
└────────────────────────────────────────┘
```

### Components

- **SettingsPanel** (grouped settings)
- **ToggleSwitch** (on/off controls)
- **SelectDropdown** (multi-option)
- **TextInput** (configuration values)
- **SaveButton** (with confirmation)

---

## Design System

### Colors (Dark Theme)

```
Primary:     #3B82F6 (Blue)
Secondary:   #10B981 (Green)
Success:     #10B981 (Green)
Warning:     #F59E0B (Amber)
Error:       #EF4444 (Red)
Background:  #0F172A (Dark Blue)
Surface:     #1E293B (Slightly Lighter)
Border:      #334155 (Gray)
Text:        #E2E8F0 (Light Gray)
Muted:       #94A3B8 (Medium Gray)
```

### Typography

```
Headers:     Inter, 600 weight
Body:        Inter, 400 weight
Code:        Fira Code, monospace
Size Scale:  12px, 14px, 16px, 18px, 20px, 24px, 32px
Line Height: 1.5 (body), 1.3 (headers)
```

### Spacing

```
xs:  4px
sm:  8px
md:  16px
lg:  24px
xl:  32px
2xl: 48px
```

### Components

- **Button** (primary, secondary, danger, ghost, sizes)
- **Card** (container with shadow)
- **Table** (sortable, paginated, filterable)
- **Modal** (overlay, forms)
- **Dropdown/Select** (searchable)
- **Checkbox/Radio** (form inputs)
- **Input** (text, number, date, email)
- **Tabs** (navigation)
- **Progress Bar** (execution progress)
- **Badge** (status indicators)
- **Toast/Alert** (notifications)

---

## Layout Responsive

```
Desktop (>1024px):
  • Sidebar: Fixed left 240px
  • Content: Full width
  • Tables: Full columns visible

Tablet (768px - 1024px):
  • Sidebar: Collapsible hamburger
  • Content: Adjusted width
  • Tables: Horizontal scroll

Mobile (<768px):
  • Sidebar: Hidden (modal)
  • Content: Full width
  • Tables: Stacked/card layout
```

---

## State Management (Zustand/Redux)

```typescript
// Auth state
- user info
- authentication status
- token expiration

// Experiments state
- list + filters
- selected experiment
- execution logs
- results cache

// Benchmarks state
- list + filters
- selected benchmark
- version history

// Results state
- experiment results
- leaderboard data
- comparison stats

// UI state
- notifications
- modal open/close
- theme
- sidebar collapsed
```

---

## Performance Considerations

- Lazy load tabs (Dashboard loaded first)
- Virtualize long tables (1000+ rows)
- Debounce search/filter inputs
- Cache API results in memory
- Progressive data loading (skeleton screens)
- Image optimization (logs, charts as SVG)

---

## Accessibility

- Keyboard navigation (Tab, Enter, Escape)
- ARIA labels on interactive elements
- Color contrast ratios ≥ 4.5:1
- Focus indicators visible
- Screen reader support

---

## Icon Set

Use: Heroicons or Lucide Icons

```
Dashboard:     📊
Benchmarks:    📋
Experiments:   🧪
Results:       📈
Settings:      ⚙️
Search:        🔍
Filter:        🔽
Sort:          ↕️
Success:       ✓
Error:         ✗
Loading:       ⏳
Status:        ● (colored dots)
```

---

## Build Plan (Week 21-23)

```
Week 21:
├── Scaffold React project (Vite)
├── Setup Tailwind + component library
├── Create base components (Button, Card, Table)
├── Build sidebar + navigation
└── Implement Dashboard tab

Week 22:
├── Build Benchmarks tab
├── Build Experiments tab
├── Implement API client
├── Add forms + modals
└── Setup state management

Week 23:
├── Build Results tab
├── Build Settings tab
├── Add charts/visualizations
├── Testing + bug fixes
├── Polish UI/UX
└── Performance optimization
```

---

**Design Phase Complete - Ready for Development**

Next: Weeks 13-20 Backend Development (Kubernetes, Distributed Systems, Ranking)  
Then: Week 21-23 Frontend Implementation