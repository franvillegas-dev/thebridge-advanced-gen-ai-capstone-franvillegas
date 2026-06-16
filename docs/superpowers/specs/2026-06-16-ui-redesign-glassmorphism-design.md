# UI Redesign: Elegant Modern Glassmorphism

## Objective
Update the UI to an elegant, modern style using glassmorphism where sections are clearly distinguishable.

## Structural Changes (already applied)
- `/` redirects to `/dashboard`
- Navigation: Dashboard → Tasks → Calendar (Home removed)
- `/dashboard` renders `DashboardHome` content (KPIs, today's tasks, today's events)

## Design System Changes

### Sidebar / Navigation
- Background: `bg-background/80 backdrop-blur-xl` with subtle right border
- Logo "Agile Agent" with icon + refined typography
- Nav items with lucide icons:
  - Dashboard → `LayoutDashboard`
  - Tasks → `ListChecks`
  - Calendar → `CalendarDays`
- Active state: `bg-primary/10` + left colored border (`border-l-2 border-primary`)
- Hover: `bg-accent/50` with smooth transition

### Glass Card Component (core pattern)
Reusable pattern applied across all sections:
- `bg-background/60 backdrop-blur-md border border-border/40 rounded-xl shadow-sm p-6`
- Consistent spacing between sections (`space-y-8` or `gap-8`)
- Subtle hover lift: `hover:shadow-md transition-shadow`

### Dashboard Page
- **KPI Cards**: Individual glass cards with icon + value + label, arranged in responsive grid
- **Today's Tasks section**: Glass container with header, task cards inside
- **Today's Events section**: Glass container with header, event cards with colored bullets

### Tasks Page
- Task cards as glass cards with left color border based on priority (low=grey, medium=blue, high=orange, critical=red)
- Status badges with refined styling (glass background + subtle border)

### Calendar Page
- Events grouped by date in glass cards
- Each event: colored bullet (deadline=red, milestone=blue, default=green) + title + type label

### Chat Panel (slide-out)
- Panel background: `bg-background/90 backdrop-blur-xl border-l border-border/40`
- User messages: `bg-primary/15 backdrop-blur-sm`
- Assistant messages: `bg-muted/30 backdrop-blur-sm`
- Input: glass background with border

### Color / Typography
- Keep existing CSS variables (OKLCH palette) and font stack
- No color changes — let glass effects do the heavy lifting
- Section headers: `text-base font-semibold text-foreground` with lucide icon prefix

## Implementation Order
1. Create reusable `GlassCard` component
2. Update sidebar with active state + icons
3. Update Dashboard (KPI cards, sections)
4. Update TaskCard component
5. Update CalendarView
6. Update ChatPanel

## GlassCard Component API
```tsx
<GlassCard className="..." hover? asChild?>
  {children}
</GlassCard>
```
- `asChild` for polymorphic usage (e.g., wrapping a Link)
- `hover` prop for optional lift effect on hover
- Default: white/transparent glass with border

## Files to Touch
- `frontend/components/ui/card.tsx` — or create new `GlassCard`
- `frontend/app/layout.tsx` — sidebar icons + active state
- `frontend/components/dashboard/DashboardHome.tsx` — wrap sections in glass cards
- `frontend/components/dashboard/KpiCard.tsx` — glass styling
- `frontend/components/tasks/TaskCard.tsx` — glass + priority border
- `frontend/components/calendar/CalendarView.tsx` — glass wrapping
- `frontend/components/chat/ChatPanel.tsx` — glass for messages
- `frontend/components/chat/ChatMessage.tsx` — glass bubbles
