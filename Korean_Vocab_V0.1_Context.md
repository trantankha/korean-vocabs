# Korean Vocab — V0.1 Product Context

## 1. Project Overview

**Korean Vocab** is a personal web application for learning and managing Korean vocabulary.

V0.1 is intentionally small. Its purpose is to establish a clean full-stack foundation and deliver a usable vocabulary management experience before introducing flashcards, quizzes, spaced repetition, AI, OCR, or mobile features.

### Core principle

> Build a small product that works end-to-end before adding advanced learning features.

---

# 2. V0.1 Goal

By the end of V0.1, a user should be able to:

1. Create an account.
2. Log in and log out.
3. View their vocabulary.
4. Add a Korean vocabulary item.
5. Edit a vocabulary item.
6. Delete a vocabulary item.
7. Search vocabulary.
8. Filter vocabulary by category and level.
9. View vocabulary details.
10. See a simple dashboard with basic vocabulary statistics.

The application should work as a complete full-stack product from browser to API to database.

---

# 3. Target User

V0.1 focuses on a single primary user type:

**Korean learner**

The first version is optimized for personal use rather than a public social learning platform.

There is no need for admin users, teachers, classrooms, social features, or multi-user collaboration beyond basic account isolation.

---

# 4. V0.1 Features

## 4.1 Authentication

### Included

- Register
- Login
- Logout
- Password hashing
- Authentication-protected application pages
- Each user can access only their own vocabulary

### Basic user data

```text
User
- id
- email
- password_hash
- created_at
```

### Not included

- Google login
- Kakao login
- Apple login
- Email verification
- Password reset email
- Two-factor authentication
- Social profiles
- Roles and permissions

---

# 5. Vocabulary Management

The main feature of V0.1 is vocabulary CRUD.

## 5.1 Vocabulary fields

Each vocabulary item contains:

```text
Vocabulary
- id
- user_id
- word
- meaning
- example
- category_id
- level
- created_at
- updated_at
```

## 5.2 Word

Example:

```text
학교
```

The word is the Korean vocabulary item. V0.1 validates this field by trimming leading/trailing whitespace and checking that the resulting value is non-empty. V0.1 does not enforce a Hangul-only character rule.

For V0.1, do not build automatic dictionary lookup.

---

## 5.3 Meaning

Example:

```text
Trường học
```

The meaning is manually entered by the user.

---

## 5.4 Example sentence

Example:

```text
저는 학교에 가요.
```

This field is optional.

The user may leave it empty.

---

## 5.5 Category

Example categories:

```text
사람 — People
장소 — Places
음식 — Food
학교 — School
일상 — Daily life
교통 — Transportation
```

Categories are used for organizing and filtering vocabulary.

For V0.1, categories can be predefined seed data.

Users do not need to create custom categories yet.

---

## 5.6 Level

V0.1 uses simple Korean-learning levels:

```text
BEGINNER
INTERMEDIATE
ADVANCED
```

The initial focus is:

```text
BEGINNER
```

The system should still store the level so that the application can expand later.

---

# 6. Vocabulary CRUD

## Create

User can add a vocabulary item.

Example:

```text
Word:
학교

Meaning:
Trường học

Example:
저는 학교에 가요.

Category:
장소

Level:
BEGINNER
```

After successful creation, the vocabulary appears in the vocabulary list.

---

## Read

User can:

- View vocabulary list
- View vocabulary details

The list should show useful information without becoming visually overloaded.

Example:

```text
학교
Trường học
장소 · BEGINNER
```

---

## Update

User can edit an existing vocabulary item.

The edit form should contain the same core fields as the create form.

---

## Delete

User can delete a vocabulary item.

Deletion should require a confirmation step to reduce accidental deletion.

Example:

```text
Delete this vocabulary?

[Cancel] [Delete]
```

---

# 7. Search

 V0.1 includes basic server-side search.

User can search by:

- Korean word
- Meaning

Example:

```text
Search: 학교
```

Result:

```text
학교
Trường học
```

Search does not need:

- Full-text search engine
- Fuzzy AI search
- Semantic search
- Search suggestions
- Search history

Simple database filtering is enough.

---

# 8. Filtering

Vocabulary can be filtered by:

## Category

```text
All
People
Places
Food
School
Daily life
Transportation
```

## Level

```text
All
Beginner
Intermediate
Advanced
```

Search and filters should be usable together.

Example:

```text
Search: 먹

Category: 음식

Level: BEGINNER
```

---

# 9. Dashboard

V0.1 includes a simple dashboard.

The dashboard should provide basic information such as:

```text
Total vocabulary
Beginner words
Intermediate words
Advanced words
Categories used
```

Example:

```text
Korean Vocab

Total words
128

Beginner
100

Intermediate
28

Advanced
0
```

A simple category breakdown may also be shown.

### Important

The dashboard is informational only.

Do not build advanced analytics in V0.1.

---

# 10. Main Pages

V0.1 should contain only these main pages.

## `/login`

Login page.

## `/register`

Registration page.

## `/dashboard`

Basic vocabulary statistics.

## `/vocabulary`

Vocabulary list, search, and filters.

## `/vocabulary/new`

Create vocabulary.

## `/vocabulary/[id]`

Vocabulary detail.

## `/vocabulary/[id]/edit`

Edit vocabulary.

No additional pages are required for V0.1.

---

# 11. UI Requirements

The UI should be:

- Simple
- Clean
- Responsive
- Easy to understand
- Suitable for a Korean-learning application
- Desktop-first but usable on mobile screens

Use reusable components.

Example:

```text
Button
Input
Select
Card
Modal
Table/List
EmptyState
LoadingState
ErrorState
```

Do not spend excessive time on visual effects.

The priority is usability and clean implementation.

---

# 12. Empty States

The application must handle empty data properly.

Example:

```text
No vocabulary yet.

Start building your Korean vocabulary collection.

[Add vocabulary]
```

Do not show an empty table with no explanation.

---

# 13. Loading and Error States

Important API operations should have:

- Loading state
- Success state
- Error state

Example:

```text
Saving...
```

and:

```text
Failed to save vocabulary.
Please try again.
```

Do not expose raw backend errors to users.

---

# 14. Backend API

The backend should provide a simple REST API.

Possible endpoints:

## Authentication

```http
POST /auth/register
POST /auth/login
POST /auth/logout
GET  /auth/me
```

## Vocabulary

```http
GET    /vocabularies
POST   /vocabularies
GET    /vocabularies/{id}
PUT    /vocabularies/{id}
DELETE /vocabularies/{id}
```

## Categories

```http
GET /categories
```

Filtering/search can use query parameters.

Example:

```http
GET /vocabularies?search=학교&category_id=1&level=BEGINNER
```

The exact API naming can be adjusted during implementation, but the API should remain simple.

---

# 15. Database

Recommended database:

```text
PostgreSQL
```

Initial tables:

```text
users
categories
vocabularies
```

Relationship:

```text
users
  │
  └──< vocabularies >── categories
```

A vocabulary belongs to exactly one user.

A vocabulary belongs to one category.

Category records can be shared by users.

---

# 16. Recommended Tech Stack

## Frontend

```text
Next.js
TypeScript
Tailwind CSS
shadcn/ui
```

## Backend

```text
FastAPI
SQLAlchemy
```

## Database

```text
PostgreSQL
```

## Authentication

Use a straightforward token-based authentication approach.

Do not introduce an authentication framework with unnecessary complexity unless implementation requires it.

---

# 17. What V0.1 MUST NOT Include

The following features are explicitly outside the V0.1 scope.

## Learning features

- Flashcards
- Quiz
- Multiple-choice questions
- Spaced repetition
- Review scheduling
- Learning streaks
- XP
- Points
- Achievements
- Daily goals
- Study sessions
- Pronunciation scoring

## AI

- AI-generated example sentences
- AI explanations
- AI vocabulary recommendations
- Chatbot
- AI tutor
- Semantic search
- Automatic difficulty classification

## Korean language services

- Dictionary API
- Automatic translation API
- Papago integration
- Naver dictionary integration
- Text-to-speech
- Speech-to-text
- Pronunciation analysis

## Document processing

- PDF import
- OCR
- Image-to-vocabulary
- Excel import/export
- CSV import/export

These may become future features.

## Social features

- Friends
- Following
- Public vocabulary
- Sharing vocabulary
- Comments
- Likes
- Leaderboards
- Community

## Account features

- Social login
- Email verification
- Password reset
- 2FA
- Profile customization

## Platform expansion

- Mobile application
- React Native
- Native iOS/Android
- Browser extension

## Infrastructure

Do not introduce these unless there is a concrete need:

- Redis
- WebSocket
- Microservices
- Kubernetes
- Message queues
- Complex caching
- Event-driven architecture

---

# 18. Non-Goals

V0.1 is NOT intended to be:

- A complete Korean learning platform
- A replacement for a Korean dictionary
- An AI tutor
- A social network
- A commercial SaaS product
- A mobile application
- A highly scalable enterprise system

The goal is a clean, useful vocabulary management application.

---

# 19. Definition of Done

V0.1 is considered complete when all of the following work:

### Authentication

- [ ] User can register
- [ ] User can log in
- [ ] User can log out
- [ ] Protected pages require authentication
- [ ] Users cannot access another user's vocabulary

### Vocabulary

- [ ] User can create vocabulary
- [ ] User can view vocabulary
- [ ] User can view vocabulary details
- [ ] User can edit vocabulary
- [ ] User can delete vocabulary
- [ ] Delete confirmation works

### Search & Filter

- [ ] Search by Korean word works
- [ ] Search by meaning works
- [ ] Category filter works
- [ ] Level filter works
- [ ] Search and filters can be combined

### Dashboard

- [ ] Total vocabulary count is shown
- [ ] Vocabulary count by level is shown
- [ ] Basic category information is shown

### UX

- [ ] Empty states exist
- [ ] Loading states exist
- [ ] API errors are handled
- [ ] Forms validate required fields
- [ ] UI works on desktop
- [ ] UI is usable on mobile-sized screens

---

# 20. Suggested Development Order

Do not build everything simultaneously.

Follow this order:

```text
1. Project setup
        ↓
2. PostgreSQL + SQLAlchemy
        ↓
3. Database models
        ↓
4. FastAPI structure
        ↓
5. Authentication
        ↓
6. Vocabulary CRUD API
        ↓
7. Next.js setup
        ↓
8. Authentication UI
        ↓
9. Vocabulary list
        ↓
10. Add vocabulary
        ↓
11. Edit/Delete vocabulary
        ↓
12. Search + filters
        ↓
13. Dashboard
        ↓
14. UX polish
        ↓
15. V0.1 testing
```

---

# 21. Future Roadmap

After V0.1 is stable, future versions can expand gradually.

```text
V0.1
Vocabulary management
        ↓
V0.2
Flashcards
        ↓
V0.3
Quiz
        ↓
V0.4
Learning progress
        ↓
V0.5
Spaced repetition
        ↓
V0.6
CSV/PDF vocabulary import
        ↓
V0.7
AI-assisted vocabulary
        ↓
V0.8
Pronunciation / TTS
        ↓
V0.9
Mobile experience
        ↓
V1.0
More complete Korean learning platform
```

The roadmap is intentionally flexible. A future feature should only be added after the previous version is stable.

---

# 22. Product Rule

When considering a new feature, ask:

1. Does this solve a real problem for Korean vocabulary learning?
2. Is it necessary for the current version?
3. Can it be implemented without making the architecture unnecessarily complex?
4. Can the current version still be completed if we postpone it?

If the feature is not necessary, postpone it.

> **Finish small. Then expand.**


# 23. V0.1 Decisions That Are Explicitly Locked

This section resolves implementation ambiguities before development begins.

## 23.1 Search and filtering: server-side

Search and filtering are performed by the backend/database.

The frontend must NOT download the user's entire vocabulary collection and filter it locally.

The API is responsible for:

- Search by `word`
- Search by `meaning`
- Filter by `category_id`
- Filter by `level`
- Pagination

Example:

```http
GET /vocabularies?search=학교&category_id=1&level=BEGINNER&page=1&limit=20
```

The backend returns only the requested page.

This keeps the frontend simple and prevents unnecessary data transfer as the vocabulary collection grows.

---

## 23.2 Required vocabulary fields

The validation rules for V0.1 are:

| Field | Required | Rule |
|---|---|---|
| `word` | Yes | Non-empty Korean vocabulary |
| `meaning` | Yes | Non-empty meaning |
| `example` | No | Optional example sentence |
| `category_id` | Yes | Must reference an existing category |
| `level` | Yes | Must be one of the supported levels |

Therefore, every vocabulary item belongs to exactly one category and has exactly one level.

The frontend form and backend API must enforce the same required/optional rules.

The backend remains the final authority for validation.

---

## 23.3 Categories

Categories are shared across users.

V0.1 categories are predefined seed data.

Users cannot create, edit, or delete categories.

Example:

```text
People
Places
Food
School
Daily life
Transportation
```

The exact initial category list can be adjusted before seeding, but the ownership rule does not change.

---

## 23.4 Meaning of "categories used"

The dashboard metric `categories used` means:

> The number of predefined categories that contain at least one vocabulary item belonging to the current user.

Example:

```text
User vocabulary:

Food          12 words
School         8 words
Places         5 words
People         0 words
Transportation 0 words
```

Then:

```text
Categories used = 3
```

The dashboard may also display a simple category breakdown:

```text
Food           12
School          8
Places          5
```

No advanced analytics are required.

---

## 23.5 Authentication and token storage

V0.1 uses an HTTP-only authentication cookie.

The frontend must NOT store authentication tokens in:

```text
localStorage
sessionStorage
```

### Authentication flow

```text
Login
  ↓
FastAPI validates credentials
  ↓
Server issues authentication token
  ↓
Token is stored in an HttpOnly cookie
  ↓
Browser automatically sends cookie with API requests
```

The frontend does not directly read the authentication token.

### Cookie rules

Production:

```text
HttpOnly = true
Secure = true
SameSite = Lax
```

Development on localhost may use:

```text
HttpOnly = true
Secure = false
SameSite = Lax
```

CORS must allow credentials when frontend and backend run on separate development origins.

### Logout

Logout calls the backend:

```http
POST /auth/logout
```

The backend clears the authentication cookie.

V0.1 does not implement a refresh-token system.

The authentication token should have a finite expiration time.

The exact expiration duration can be configured through environment variables.

### Important limitation

Because V0.1 does not maintain a server-side session/revocation store, clearing the cookie ends the browser session, but an already-issued token remains technically valid until it expires if it is copied elsewhere.

This is acceptable for V0.1.

If stronger session revocation is needed later, introduce a server-side session table or refresh-token system in a future version rather than complicating V0.1 now.

---

## 23.6 User data isolation

Every vocabulary query must be scoped to the authenticated user's identity.

The backend must enforce:

```text
current_user.id == vocabulary.user_id
```

for all vocabulary operations.

This applies to:

```text
GET list
GET detail
POST create
PUT update
DELETE delete
```

The frontend must never be treated as the security boundary.

Example:

```http
GET /vocabularies/123
```

If vocabulary `123` belongs to another user, the backend must not return it.

The same rule applies to update and delete operations.

This must be covered by backend tests.

Recommended tests include:

```text
User A creates vocabulary A

User B:
- cannot read vocabulary A
- cannot update vocabulary A
- cannot delete vocabulary A
```

---

## 23.7 Pagination

Pagination is included in V0.1 and is performed server-side.

Default:

```text
page = 1
limit = 20
```

The API should return enough metadata for the frontend to render pagination.

Example response shape:

```json
{
  "items": [],
  "page": 1,
  "limit": 20,
  "total": 128,
  "total_pages": 7
}
```

The exact response schema can be adjusted during implementation.

V0.1 does not require infinite scrolling.

A simple pagination UI is sufficient:

```text
< Previous   1  2  3  4   Next >
```

---

## 23.8 Updated API behavior

The vocabulary endpoint therefore becomes:

```http
GET /vocabularies
```

Supported query parameters:

```text
search
category_id
level
page
limit
```

Example:

```http
GET /vocabularies?search=먹&category_id=2&level=BEGINNER&page=1&limit=20
```

All filtering, searching, sorting, and pagination happen on the server.

---

# 24. Updated V0.1 Scope Summary

The final V0.1 scope is:

```text
Authentication
    ↓
Dashboard
    ↓
Vocabulary CRUD
    ↓
Server-side Search
    ↓
Server-side Filtering
    ↓
Server-side Pagination
```

Data model:

```text
User
  │
  └──< Vocabulary >── Category

Vocabulary
  ├── word          required
  ├── meaning       required
  ├── example       optional
  ├── category_id   required
  └── level         required
```

Security model:

```text
HttpOnly Cookie
       ↓
Authenticated User
       ↓
user_id scoped queries
       ↓
Vocabulary access
```

The following decisions are now considered part of the V0.1 specification and should not be changed casually during implementation.


---

# 23.9 Sorting

Sorting is performed by the backend/database.

The default vocabulary ordering is:

```text
created_at DESC
```

Therefore, the newest vocabulary items appear first.

V0.1 does not require user-selectable sorting in the UI.

The API may support an explicit `sort` parameter so the contract can be extended without changing the endpoint.

Supported V0.1 values:

```text
sort=created_at_desc
sort=created_at_asc
```

If `sort` is omitted:

```text
created_at_desc
```

is used.

The backend must whitelist supported sort values. Arbitrary database column names must never be accepted from the client.

Example:

```http
GET /vocabularies?sort=created_at_desc&page=1&limit=20
```

---

# 23.10 Pagination limit

The server enforces a maximum page size.

Default:

```text
limit = 20
```

Maximum:

```text
limit = 100
```

If the client requests:

```http
GET /vocabularies?limit=5000
```

the backend must not execute an unbounded 5000-item query.

The API should either:

- clamp the value to `100`, or
- return a validation error.

V0.1 will use validation and return a clear `400`/`422`-style validation response for values outside the allowed range.

Allowed range:

```text
1 <= limit <= 100
```

The backend remains the authority for this constraint.

---

# 23.11 CSRF protection for cookie authentication

Because authentication uses an HttpOnly cookie, V0.1 includes a minimum CSRF defense for state-changing requests.

State-changing requests include:

```text
POST
PUT
PATCH
DELETE
```

The backend checks the request `Origin` header against an explicit allowlist of trusted frontend origins.

Example development origin:

```text
http://localhost:3000
```

The production frontend origin is configured through environment variables rather than hard-coded into application logic.

Requests with an invalid or untrusted `Origin` are rejected for state-changing operations.

Safe/read-only requests such as:

```text
GET
HEAD
OPTIONS
```

do not require the same write-request Origin check.

### SameSite

The authentication cookie uses:

```text
SameSite=Lax
```

for V0.1.

This is compatible with the planned deployment where frontend and backend are controlled by the same application/site context and does not require cross-site cookie behavior.

If the eventual production architecture requires genuinely cross-site frontend/backend authentication, the cookie policy must be revisited before deployment rather than silently changing it during implementation.

### Important

CORS configuration and CSRF protection are separate concerns.

CORS controls which browser origins are allowed to make credentialed requests.

The Origin check provides an additional server-side defense against unwanted cross-origin state-changing requests.

Both must be configured deliberately.

---

# 23.12 Vocabulary validation clarification

The phrase:

```text
Non-empty Korean vocabulary
```

does NOT mean:

> The backend must reject every character that is not Hangul.

For V0.1, validation is intentionally simple.

The `word` field must:

1. Exist.
2. Be a string.
3. Be trimmed.
4. Not be empty after trimming.

Example:

```text
"학교"       → valid
" 학교 "     → stored as "학교" after trimming
"123"        → not rejected solely because it is not Hangul
"ABC"        → not rejected solely because it is not Hangul
"   "        → invalid
""           → invalid
```

The purpose of V0.1 validation is to prevent empty/meaningless form values, not to build a Korean-language linguistic validator.

The frontend may provide Korean-oriented UX hints, but the backend must not impose an unnecessary Hangul-only restriction.

---

# 23.13 Final vocabulary endpoint contract

The V0.1 list endpoint supports:

```http
GET /vocabularies
```

Query parameters:

```text
search
category_id
level
sort
page
limit
```

Defaults:

```text
page = 1
limit = 20
sort = created_at_desc
```

Constraints:

```text
1 <= page
1 <= limit <= 100
```

Example:

```http
GET /vocabularies?search=먹&category_id=2&level=BEGINNER&sort=created_at_desc&page=1&limit=20
```

All of the following happen server-side:

```text
Search
Filtering
Sorting
Pagination
```

---

# 23.14 Final V0.1 implementation decisions

The implementation contract is now:

```text
Search
  → Server-side

Filter
  → Server-side

Sort
  → Server-side
  → Default: created_at DESC

Pagination
  → Server-side
  → Default: 20
  → Maximum: 100

Authentication
  → HttpOnly cookie

Cookie
  → SameSite=Lax

CSRF
  → Origin allowlist for POST/PUT/PATCH/DELETE

Vocabulary word validation
  → trim + non-empty
  → no Hangul-only restriction

Categories
  → predefined/shared
  → category_id required

Level
  → required

User isolation
  → backend user_id scoping
```

These decisions complete the remaining V0.1 ambiguities. The next implementation step can therefore begin with the database schema and API contract without needing another architecture decision round.
