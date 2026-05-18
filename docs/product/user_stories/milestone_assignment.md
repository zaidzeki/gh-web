# User Story: Strategic Task Alignment (Milestone Assignment)

## 🏁 Goal
As a Maintainer or Project Lead, I want to easily assign Issues and Pull Requests to Milestones within GH-Web, so that I can organize work into strategic goals without leaving the application.

## 🎭 Personas
- **Atlas (Project Lead):** Needs to see how tasks align with high-level releases.
- **Jules (Developer):** Needs to know which milestone their current task belongs to.

## 📖 Scenarios

### Scenario 1: Assigning a task to a milestone
1. User navigates to the **Issues** or **Pull Requests** tab.
2. User sees a "Milestone" column indicating the current assignment.
3. User clicks an "Assign" icon next to a task.
4. An "Assign Milestone" modal appears, listing all open milestones for the repository.
5. User selects a milestone and confirms.
6. The table refreshes, and the milestone badge is updated.

### Scenario 2: Visualizing progress in the Task Inbox
1. User opens the **Dashboard**.
2. The **Unified Task Inbox** displays a milestone badge for each task (if assigned).
3. The badge is color-coded: blue for active, red if the milestone is overdue.

### Scenario 3: Identifying Overdue Goals
1. User navigates to the **Milestones** tab.
2. Milestones past their due date with remaining open items are highlighted with a red border and an "Overdue" warning.

## ✅ Acceptance Criteria
- [ ] Issues and PR tables include a "Milestone" display.
- [ ] "Assign Milestone" action added to Issues and PR tables.
- [ ] Milestone Assignment Modal implemented and functional.
- [ ] Task Inbox items display their assigned milestone.
- [ ] Milestone cards in the "Milestones" tab show an "Overdue" status when applicable.
- [ ] Backend `normalize` function in `tasks` route enriched with milestone data.
