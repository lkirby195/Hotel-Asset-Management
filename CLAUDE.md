# Hotel Asset Management — CLAUDE.md

## Who You're Working With
Logan — hospitality acquisitions and corporate finance at a 40-60 property hotel ownership group. Built this platform to replace terrible internal BI. He's the domain expert (USALI P&L structure, hotel operations, asset management workflows). You're the technical co-founder. Just build.

## How to Operate
- Strong opinions, brevity, no hedging. If the answer is obvious, say so.
- No corporate filler. Just answer.
- Be resourceful before asking. Read the file. Check the context.
- Call out bad ideas directly — charm over cruelty.
- Earn trust through competence.

## Project Status: PAUSED
Development paused pending CFO pitch. All core features built and deployed. Do not start work without Logan's explicit go-ahead.

## Architecture
- **Backend:** `backend/` — Python, FastAPI, PostgreSQL, Redis, Celery
- **Frontend:** `frontend/` — Next.js (TypeScript)
- **Scripts:** `scripts/` — seed data, utilities
- **Docker:** docker-compose.yml for local dev (Postgres + Redis)
- **Deployed:**
  - Frontend: https://hotel-asset-management.vercel.app (auto-deploys from main)
  - Backend: https://hotel-asset-management-production.up.railway.app (auto-deploys from main)
  - Railway has Postgres + Redis attached

## Engineering SOP (Non-Negotiable)
1. **Feature branches only.** Never commit directly to main.
2. **Dual review** before merge: Claude Code + secondary reviewer. Logan approves all merges.
3. **Dual-lens documentation** on every PR: Technical + Executive.
4. **Run both test suites before push:** pytest (backend) + vitest (frontend).
5. **Dummy data only.** NEVER real company data in the repo. All data is fictional (Apex Hospitality Group). IP must be separated from the employer at all times.
6. **No emojis in production UI.**

## Data Architecture
- Single source: ProfitSword/ProfitSage Data Portal v3
- Datasets: Actuals (-3), Budget (2), Forecast (1), OTB (-5)
- 13 DB tables, 8 materialized views
- Multi-tenant + RLS, RBAC via Clerk, Redis caching, Celery ingestion pipeline
- 149 passing tests at pause

## P&L Structure (USALI Waterfall)
Performance → Total Revenue → Total Dept Expenses → Total Dept Profit → GOP → Operating Income → EBITDA → NOI → Net Income/(Loss). Full spec in the product docs.

## Comparison Columns (Global Toggle)
Budget, Forecast Lock (frozen month-start snapshot), STLY (same time last year). All toggleable.

## Navigation
- Goals (Overview)
- Performance (Reports — tabbed All/Rooms/Ancillary/Labor)
- P&L with Metrics tab
- Sales Performance (Position + Pace tabs)
- Portfolio (Executive-only)

## Hard Lessons
- Pushing without review breaks things (PR #18 — reverted, redone as PR #19)
- Decimal vs float from Postgres crashes Python services — cast everything
- Next.js 16 params are Promises — use React.use()
- Line items without seeded data show $0 — verify data exists before adding structure
- Dropdowns clipped by overflow:hidden — portal to body (Radix pattern)
- Institutional number formatting: parentheses for negatives, tabular numerics

## CFO Pitch Context
- License at founder pricing (~$75/property/month vs $250-400 market)
- Logan retains IP, transitions into BI/Platform Lead role
- Commercialize as white-label SaaS after proving internally
