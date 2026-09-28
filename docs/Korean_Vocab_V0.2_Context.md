# Korean Vocab — V0.2 Flashcard Context

## 1. Goal

V0.2 upgrades Korean Vocab from vocabulary management into basic active learning.

V0.1 answers: **Can I manage my vocabulary?**

V0.2 answers: **Can I actively study the vocabulary I saved?**

Core learning loop:

```text
See → Recall → Reveal → Judge → Record
```

---

## 2. V0.2 Scope

### Included

- Flashcard study mode
- Study filters: category, level
- Session sizes: 5 / 10 / 20 cards
- Korean word shown first
- Explicit "Show answer" action
- Meaning and optional example revealed
- `REMEMBERED` / `NOT_REMEMBERED`
- Next / previous navigation
- Session progress
- Session completion summary
- Persistent basic learning progress
- Basic dashboard learning statistics
- Responsive mobile-friendly study UI

### Explicitly excluded

- Quiz / multiple choice / typing tests
- Spaced repetition, SM-2, FSRS
- AI
- Translation APIs
- TTS / speech recognition / pronunciation scoring
- XP, streaks, achievements, leaderboards
- Social features / public decks
- Native mobile app
- Redis, WebSocket, background jobs, or other new infrastructure

---

## 3. Study Flow

```text
Dashboard
  ↓
Study Vocabulary
  ↓
Select category / level / number of cards
  ↓
Flashcard
  ↓
Show answer
  ↓
Remembered / Not remembered
  ↓
Next card
  ↓
Session complete
  ↓
Summary
```

The existing V0.1 CRUD functionality must continue to work unchanged.

---

## 4. Starting a Session

Required options:

```text
Category: All or a specific category
Level: All or a specific level
Cards: 5 / 10 / 20
```

Only vocabulary belonging to the authenticated user may be selected.

If fewer matching words exist than requested, study only the available number.

Example:

```text
Requested: 20
Matching vocabulary: 7
Actual session: 7
```

The UI must make this clear.

---

## 5. Flashcard Behavior

Initial state:

```text
┌──────────────────────────────┐
│                              │
│             학교             │
│                              │
│        [ Show answer ]       │
│                              │
└──────────────────────────────┘

Card 1 of 10
```

After reveal:

```text
학교

Trường học

저는 학교에 가요.

[ Chưa nhớ ]   [ Đã nhớ ]
```

The answer must remain visually hidden until the user explicitly reveals it.

This is a UX requirement, not a security boundary; V0.2 does not require cryptographic hiding from browser developer tools.

---

## 6. Result Recording

Each answered card has exactly one current session result:

```text
REMEMBERED
NOT_REMEMBERED
```

If the user navigates backward and changes an answer, the latest answer is the result used in the session summary.

The same card must not be counted multiple times merely because the user navigated back and forth.

---

## 7. Session Progress

Display simple progress:

```text
Card 4 / 10
████████░░░░░░ 40%
```

Optional:

```text
Remembered: 2
Not remembered: 1
Remaining: 6
```

No advanced analytics.

---

## 8. Session Summary

Example:

```text
Session complete

10 cards studied

Remembered        7
Not remembered    3

70% remembered

[ Study again ]
[ Back to dashboard ]
```

Formula:

```text
remembered / answered × 100
```

This percentage is only a session statistic, not a long-term mastery score.

---

## 9. Persistent Progress

Add:

```text
vocabulary_progress
```

Recommended fields:

```text
id
user_id
vocabulary_id
status
review_count
remembered_count
not_remembered_count
last_reviewed_at
created_at
updated_at
```

Statuses:

```text
NEW
LEARNING
MASTERED
```

Initial simple transition:

```text
NEW → LEARNING
```

A simple mastery rule may be:

```text
remembered_count >= 3 → MASTERED
```

The threshold must be configurable in backend code.

Do not implement a sophisticated learning algorithm in V0.2.

If a vocabulary has no progress record, treat it as `NEW`. Its progress record may be created on the first study action.

---

## 10. Study Card API

Add without breaking V0.1 APIs:

```http
GET /study/cards
```

Query parameters:

```text
category_id
level
limit
```

Example:

```http
GET /study/cards?category_id=2&level=BEGINNER&limit=10
```

Backend responsibilities:

- Authenticate the user
- Scope results to `current_user.id`
- Apply category filter
- Apply level filter
- Limit the result
- Return only the user's vocabulary

Cards may be selected randomly.

V0.2 does not prioritize previously forgotten words.

---

## 11. Progress API

Add:

```http
POST /study/progress
```

Example:

```json
{
  "vocabulary_id": 123,
  "result": "REMEMBERED"
}
```

or:

```json
{
  "vocabulary_id": 123,
  "result": "NOT_REMEMBERED"
}
```

Backend updates:

```text
review_count
remembered_count
not_remembered_count
last_reviewed_at
status
```

Optional:

```http
GET /study/progress
```

This may return:

```json
{
  "total": 100,
  "new": 70,
  "learning": 25,
  "mastered": 5
}
```

Only implement this endpoint if it provides value to the dashboard.

---

## 12. Security

Progress is private to each user.

The backend must enforce:

```text
progress.user_id == current_user.id
```

and the referenced vocabulary must belong to that same user.

A user must never be able to:

- Read another user's progress
- Modify another user's progress
- Delete another user's progress
- Study another user's vocabulary

Add backend tests for cross-user access.

Existing V0.1 HttpOnly cookie authentication and Origin/CSRF protection remain unchanged.

---

## 13. Session Architecture

A persistent study-session table is **not required** in V0.2.

The active session may be managed by the frontend.

The backend persists vocabulary learning results.

Do not introduce:

- Redis
- WebSocket
- background jobs
- session infrastructure

---

## 14. Dashboard

Add a small learning section:

```text
Learning

100 total words

70 New
25 Learning
5 Mastered

[ Start studying ]
```

Keep the dashboard simple.

---

## 15. Pages

Add:

```text
/study
/study/summary
```

Keep existing V0.1 pages unchanged:

```text
/login
/register
/dashboard
/vocabulary
/vocabulary/new
/vocabulary/[id]
/vocabulary/[id]/edit
```

---

## 16. UX Requirements

The flashcard should prioritize:

- Current word
- Reveal action
- Answer actions
- Progress
- Navigation

Also provide:

- Loading states
- Empty states
- Error states
- Keyboard-accessible controls
- Visible focus states
- Adequate contrast
- Mobile layout
- Desktop layout

Empty study example:

```text
No vocabulary matches your filters.

Try another category or level.
```

---

## 17. Edge Cases

### No vocabulary

```text
You don't have any vocabulary yet.

[ Add vocabulary ]
```

### No matching vocabulary

```text
No vocabulary matches these filters.
```

### Fewer cards than requested

Clearly tell the user that fewer matching words are available.

### API failure

Show a friendly error. Never expose raw backend errors.

---

## 18. Definition of Done

### Study

- [ ] Authenticated user can enter Flashcard mode
- [ ] Category filter works
- [ ] Level filter works
- [ ] 5 / 10 / 20 card options work
- [ ] Only current user's vocabulary is selected
- [ ] Korean word appears first
- [ ] Answer is explicitly revealed
- [ ] Example is shown when available
- [ ] Remembered works
- [ ] Not Remembered works
- [ ] Next / previous navigation works
- [ ] Progress is displayed
- [ ] Session summary is displayed

### Persistence

- [ ] Study result persists
- [ ] Review count updates
- [ ] Remembered count updates
- [ ] Not remembered count updates
- [ ] Last reviewed timestamp updates
- [ ] Status updates
- [ ] Existing V0.1 vocabulary remains intact

### Security

- [ ] Cross-user vocabulary access is blocked
- [ ] Cross-user progress access is blocked
- [ ] Backend tests cover isolation
- [ ] V0.1 authentication/security remains intact

### UX

- [ ] Empty states work
- [ ] Loading states work
- [ ] Error states work
- [ ] Mobile layout works
- [ ] Desktop layout works
- [ ] Important controls are keyboard accessible

### Regression

- [ ] V0.1 auth still works
- [ ] V0.1 CRUD still works
- [ ] V0.1 search/filter/pagination still works
- [ ] Backend tests pass
- [ ] Frontend production build passes

---

## 19. Development Order

```text
1. Finalize progress schema
2. Create migration
3. Implement study-card API
4. Implement progress API
5. Test user isolation
6. Build /study UI
7. Build reveal interaction
8. Build answer actions
9. Build session progress
10. Build summary
11. Update dashboard
12. Mobile/responsive polish
13. Regression testing
14. Production build
15. Commit V0.2
```

---

## 20. Product Principle

V0.1 stores knowledge.

V0.2 lets the user practice that knowledge.

Do not turn Flashcards into a complete learning algorithm.

> **V0.2 should make existing vocabulary useful, not make the application complicated.**

---

## 21. Future Direction

```text
V0.1  Vocabulary management
  ↓
V0.2  Flashcards
  ↓
V0.3  Quiz / active recall
  ↓
V0.4  Learning progress
  ↓
V0.5  Spaced repetition
  ↓
V0.6  Import / document processing
  ↓
V0.7  AI-assisted learning
  ↓
V0.8  Pronunciation / audio
  ↓
V0.9  Mobile experience
  ↓
V1.0  Complete Korean learning product
```

Future versions remain subject to review after actual usage of the previous version.
