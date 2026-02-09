# SmartBudget AI - MVP Plan

## Goal
An AI powered personal budgeting bot that helps users track expenses, set limits, and get smart spending suggestions.

## Core Features
- User input: income, categories, and expenses
- AI bot suggestions for saving
- Dashboard (React or HTML/CSS)
- Data storage (JSON or Firebase)
- Chat-style interaction for budgeting tips

## MVP Tech Stack
- Frontend: React (JavaScript)
- Backend: FastAPI (Python)
- Database: Firebase or local JSON
- Deployment: GitHub Codespaces → Render (backend) + Vercel (frontend)

- Streamlit, the best way to show a "pop-up" notification without interrupting the user is using st.toast. It appears briefly in the corner (like a phone notification).

You don't need complex backend changes for this. We can simply detect the "Loan settled" keyword in the UI and trigger the notification there.

