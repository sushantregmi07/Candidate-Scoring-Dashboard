# Candidate Scoring Dashboard

An internal candidate scoring and review dashboard for TechKraft's recruitment workflow. Reviewers score candidates across categories, admins have full visibility, and AI-generated summaries provide quick candidate overviews.

## Tech Stack

- **Backend:** Python 3.11, FastAPI, SQLAlchemy 2.0 (async), SQLite (aiosqlite)
- **Frontend:** React 18, Vite, Tailwind CSS, React Router v6
- **Auth:** JWT (python-jose + passlib/bcrypt)
- **Containerization:** Docker Compose

---

## Setup & Run

### Prerequisites

- Docker and Docker Compose installed

### Quick Start

```bash
# 1. Clone the repository
git clone <repository-url>
cd candidate-scoring-dashboard

# 2. Create your .env from the example
cp .env.example .env

# 3. Build and start both services
docker-compose up --build

# 4. Open the app
# Frontend: http://localhost:5173
# Backend API: http://localhost:8000
# API Docs: http://localhost:8000/docs
```

### Default Accounts (Seeded)

| Role     | Username       | Email                  | Password     |
|----------|----------------|------------------------|--------------|
| Admin    | Admin User     | admin@techkraft.com    | admin123     |
| Reviewer | Alice Rivera   | alice@techkraft.com    | reviewer123  |
| Reviewer | Bob Martinez   | bob@techkraft.com      | reviewer123  |

### Running Tests

```bash
docker exec candidatescoringdashboard-backend-1 python -m pytest tests/ -v
```

---

## Example API Calls

### Register a new reviewer

```bash
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username": "Jane Doe", "email": "jane@example.com", "password": "secret1234"}'
```

### Login

```bash
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@techkraft.com", "password": "admin123"}'
```

### List candidates with filters

```bash
# Set TOKEN from the login response
TOKEN="<access_token from login>"

curl http://localhost:8000/candidates?status=new\&page=1\&page_size=10 \
  -H "Authorization: Bearer $TOKEN"
```

### Submit a score

```bash
curl -X POST http://localhost:8000/candidates/<candidate_id>/scores \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"category": "Technical", "score": 4, "note": "Strong Python skills"}'
```

### Generate AI summary

```bash
curl -X POST http://localhost:8000/candidates/<candidate_id>/summary \
  -H "Authorization: Bearer $TOKEN"
```

### Update internal notes (admin only)

```bash
curl -X PATCH http://localhost:8000/candidates/<candidate_id>/notes \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"notes": "Fast-track to final round"}'
```

### Archive a candidate (admin only — soft delete)

```bash
curl -X DELETE http://localhost:8000/candidates/<candidate_id> \
  -H "Authorization: Bearer $TOKEN"
```

This sets the candidate's status to `archived` and records a `deleted_at` timestamp. The row is **not** hard-deleted — it is excluded from listing queries via a `WHERE deleted_at IS NULL` filter.

---

## Debugging Signal

### The Bug

```python
def search_candidates(status: str, keyword: str, page: int, page_size: int):
    all_candidates = db.execute("SELECT * FROM candidates").fetchall()
    filtered = [c for c in all_candidates if c["status"] == status]
    offset = (page - 1) * page_size
    return filtered[offset : offset + page_size]
```

### Why This Breaks at Scale

This pattern has three compounding problems that make it catastrophically inefficient:

1. **Full table scan into application memory.** `SELECT * FROM candidates` with `.fetchall()` deserializes every row into a Python object and holds it in process memory. With 100,000 candidates, this alone can consume hundreds of megabytes per request. Under concurrent load, this creates memory pressure that leads to OOM kills or swap thrashing.

2. **Filtering in Python instead of the database engine.** The list comprehension `[c for c in all_candidates if c["status"] == status]` is O(n) on the full dataset for every single request. The database already has a B-tree index on `status` that can resolve the same filter in O(log n) with zero data transfer for non-matching rows. By filtering in Python, we are paying the cost of serialization, network transfer, and GC allocation for rows we immediately discard.

3. **Pagination is cosmetic, not structural.** Slicing `filtered[offset:offset + page_size]` gives the appearance of pagination, but the full cost has already been paid. Whether the user requests page 1 or page 500, the server fetches all rows, filters all rows, and then throws most of them away. True pagination must happen at the query level so the database only reads and transmits the requested window.

### How Our Implementation Fixes It

Our `candidate_service.list_candidates` constructs a single query that pushes all work to the SQLite engine:

```python
base = select(Candidate).where(Candidate.deleted_at.is_(None))

if status_filter:
    base = base.where(Candidate.status == status_filter)    # uses ix_candidates_status
if role_applied:
    base = base.where(Candidate.role_applied == role_applied)  # uses ix_candidates_role_applied
if keyword:
    base = base.where(or_(
        Candidate.name.ilike(f"%{keyword}%"),
        Candidate.email.ilike(f"%{keyword}%"),
    ))

# Count only matching rows (not all rows)
count_q = select(func.count()).select_from(base.subquery())

# Fetch only the page window
items_q = base.order_by(Candidate.created_at.desc()).limit(page_size).offset(offset)
```

The database uses its indexes to find matching rows, counts them without materializing, and returns only the `page_size` rows for the current page. At 100k rows, this runs in milliseconds instead of seconds, transfers kilobytes instead of megabytes, and scales linearly with page size rather than with table size.

---

## Architecture Decision Records (ADR)

### ADR 1: SQLite over DynamoDB-style Schema

**Context:** The assignment offered a choice between DynamoDB-style storage and SQLite. We needed a database that runs inside Docker with zero external infrastructure, supports relational queries with proper indexes, and demonstrates the filtering/pagination patterns central to the debugging exercise.

**Decision:** SQLite via SQLAlchemy 2.0 async (aiosqlite). WAL mode enabled for concurrent read performance.

**Trade-off:** SQLite is single-writer, which would bottleneck at high write concurrency in production. For an internal tool with a handful of reviewers, this is a non-issue. The migration path to PostgreSQL is a one-line `DATABASE_URL` change thanks to SQLAlchemy's dialect abstraction.

### ADR 2: JWT Authentication with Role Hardcoded at Registration

**Context:** The system requires two roles (reviewer, admin) with different permissions. The assignment explicitly caps the grade if the client can set its own role during registration.

**Decision:** Stateless JWT tokens using python-jose. The `UserRegister` Pydantic schema accepts only `username`, `email`, and `password` — no `role` field exists on the schema at all. The backend hardcodes `role="reviewer"` in the service layer. Admin accounts are created only through the database seed.

**Trade-off:** There is no admin self-registration flow. In a production system, admin provisioning would be handled through a separate admin panel or CLI tool. For this assignment, the seeded admin account demonstrates the pattern without introducing unnecessary complexity.

### ADR 3: Per-User AI Summaries via Separate Table

**Context:** The assignment requires simulating an LLM call with a 2-second delay. Initially the summary was a single column on the `candidates` table, but this created a data leakage issue: a reviewer's generated summary reflected scores from other reviewers they shouldn't see. A reviewer who scored Technical=3 would see a summary saying "average 2.0" because another reviewer scored Technical=1.

**Decision:** Summaries are stored in a dedicated `summaries` table keyed by `(candidate_id, user_id)`. Each user gets their own independent summary. Reviewer summaries are generated only from that reviewer's scores. Admin summaries aggregate all scores with per-category breakdowns showing how many reviewers contributed to each category.

**Trade-off:** This adds one query per candidate detail load (to fetch the user's summary) and stores multiple summary rows per candidate instead of one. The extra storage and query cost is negligible, and the data isolation correctly mirrors the RBAC boundaries already enforced on score visibility.

---

## Learning Reflection

Building this project reinforced the importance of pushing computation to the database layer rather than doing it in application code — a principle that seems obvious but is easy to violate when ORMs make Python-side filtering feel natural. I also explored `useSearchParams` in React Router for the first time to persist filter state in the URL, which turned out to be a much better UX pattern than local component state for list views. Given more time, I would implement the SSE real-time score streaming endpoint and add comprehensive end-to-end tests covering the full auth flow through the React frontend.

---

## Limitations

- **SSE streaming** (`GET /candidates/{id}/stream`) is not implemented. The plan accounted for it as a stretch goal using `asyncio.Queue` per candidate, but time was prioritized on core requirements.
- **No admin registration UI** — admin accounts can only be created via the database seed script. In production, admin provisioning would use a separate CLI tool or admin panel.
- **SQLite single-writer** — adequate for an internal tool but would need to be swapped for PostgreSQL under concurrent write load.
