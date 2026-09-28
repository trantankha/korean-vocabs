# Korean Vocab — V0.3 Quiz Context

## Goal

V0.3 adds a multiple-choice Active Recall Quiz.

V0.1: manage vocabulary.  
V0.2: study with flashcards.  
V0.3: actively recall vocabulary and receive immediate feedback.

Core loop:

```text
Question → Recall → Choose → Feedback → Learn
```

## Scope

### Included

- Multiple-choice Quiz
- Korean → Vietnamese questions
- Vietnamese → Korean questions
- Mixed directions in one quiz
- Category and level filters
- 5 / 10 / 20 questions
- Four unique choices when enough vocabulary exists
- Distractors from the user's own vocabulary
- Prefer same category + level for distractors
- Randomized answer positions
- Immediate correct/incorrect feedback
- Correct answer and optional example sentence
- Session progress
- Simple completion result
- Integration with V0.2 `vocabulary_progress`
- Responsive mobile-friendly UI
- Backend security tests

### Excluded

- AI question/distractor generation
- Free-text answers
- Listening/speaking/pronunciation
- Timer
- XP, streaks, achievements, leaderboard
- Advanced statistics
- Spaced repetition
- Social features
- Native mobile app

## Relationship to V0.2

Keep Flashcards.

```text
Learning
├── Flashcards
└── Quiz
```

Flashcards allow self-evaluation. Quiz requires a committed answer before revealing correctness.

## Quiz Directions

### Korean → Vietnamese

```text
학교의 뜻은 무엇이에요?

A. 병원
B. 학교
C. 식당
D. 공원
```

### Vietnamese → Korean

```text
"Trường học"은 한국어로 무엇이에요?

A. 병원
B. 학교
C. 식당
D. 공원
```

Directions may be randomized and mixed within a session.

## Quiz Configuration

User selects:

```text
Category: All or specific
Level: All or specific
Questions: 5 / 10 / 20
```

Only the authenticated user's vocabulary may be used.

If fewer eligible vocabulary items exist than requested, use the available amount and explain this clearly.

If fewer than 4 suitable vocabulary items exist for choices, do not fabricate answers. Prefer asking the user to change filters or add vocabulary.

## Distractors

Distractors must come from vocabulary owned by the current user.

Preferred selection:

```text
Same category + same level
        ↓
Same level
        ↓
Any user vocabulary
```

Requirements:

- Correct answer is never a distractor.
- Choices are unique.
- Choice positions are shuffled.
- Do not use AI to create distractors.

## Answer Behavior

After the user selects an answer:

```text
Lock answer
    ↓
Determine correctness
    ↓
Show correct/incorrect feedback
    ↓
Show correct answer
    ↓
Show example if available
    ↓
Enable Next
```

The user cannot change the answer after submission.

Example:

```text
✓ Chính xác!

학교 = Trường học

저는 학교에 가요.

[ Câu tiếp theo ]
```

For an incorrect answer, show the selected answer and the correct answer.

Do not fabricate examples when none exists.

## Progress and Completion

Show:

```text
Question 4 / 10
████████░░░░░░ 40%
```

At completion:

```text
Quiz complete

8 / 10 correct

[ Try again ]
[ Back to learning ]
[ Back to dashboard ]
```

Score is only a session result. No gamification or advanced analytics.

## Learning Progress

Reuse V0.2 `vocabulary_progress`.

```text
Correct answer
    → REMEMBERED

Incorrect answer
    → NOT_REMEMBERED
```

Update the existing:

```text
review_count
remembered_count
not_remembered_count
last_reviewed_at
status
```

Do not create a second progress system.

## API

Recommended:

```http
GET /quiz/questions
```

Query parameters:

```text
category_id
level
limit
```

Example:

```http
GET /quiz/questions?category_id=2&level=BEGINNER&limit=10
```

Backend must authenticate, scope vocabulary to the current user, apply filters, select questions, generate valid distractors, randomize choices, and return quiz data.

Recommended answer endpoint:

```http
POST /quiz/answer
```

Possible request:

```json
{
  "vocabulary_id": 123,
  "direction": "KOREAN_TO_VIETNAMESE",
  "selected_answer": "Trường học"
}
```

The server should determine correctness rather than trusting a client-provided `correct` field.

The backend must validate that the vocabulary belongs to the current user and that the selected answer is valid for the question.

## Security

A user must never be able to:

- Use another user's vocabulary in a quiz
- Record progress for another user's vocabulary
- Submit answers against another user's vocabulary

Add backend tests for cross-user access.

Keep V0.1 security unchanged:

```text
HttpOnly cookie
SameSite=Lax
Origin check for state-changing requests
```

## Session Architecture

No persistent quiz-session table is required.

The active quiz may be frontend-managed. Persist learning results through the existing progress mechanism.

Do not introduce Redis, WebSocket, background jobs, or complex session infrastructure.

## Pages

Add:

```text
/quiz
/quiz/summary
```

Keep all V0.1 and V0.2 pages working.

## UX Principles

The quiz should feel like a learning tool, not a game.

Prioritize:

- Clear questions
- Readable choices
- Immediate feedback
- Low cognitive friction
- Mobile usability

Avoid excessive animation, countdowns, sound effects, confetti, and gamification.

The user should always understand:

```text
What is being asked?
What did I choose?
Was it correct?
What is the correct answer?
What does the word mean?
What do I do next?
```

## Accessibility

- Semantic buttons
- Keyboard-accessible controls
- Visible focus states
- Clear selected/correct/incorrect states
- Adequate contrast
- Do not rely only on color for correctness

## Edge Cases

Handle:

- No vocabulary
- No vocabulary matching filters
- Too few vocabulary items for reliable choices
- Missing example sentence
- API failure
- Fewer available questions than requested

Never expose raw backend errors.

## Definition of Done

### Quiz

- [ ] User can start a quiz
- [ ] Category and level filters work
- [ ] 5 / 10 / 20 question options work
- [ ] Korean → Vietnamese works
- [ ] Vietnamese → Korean works
- [ ] Directions can be mixed
- [ ] Four unique choices appear when enough data exists
- [ ] Correct answer position is randomized
- [ ] Distractors prefer same category and level
- [ ] Answer locks after selection
- [ ] Immediate feedback works
- [ ] Correct answer is displayed
- [ ] Example appears when available
- [ ] Next-question flow works
- [ ] Progress works
- [ ] Completion summary works

### Learning integration

- [ ] Correct answers update V0.2 progress as remembered
- [ ] Incorrect answers update V0.2 progress as not remembered
- [ ] Existing progress rules remain consistent
- [ ] No second progress system is created

### Security

- [ ] Only current user's vocabulary is used
- [ ] Cross-user quiz access is blocked
- [ ] Cross-user progress updates are blocked
- [ ] Backend validates answer integrity
- [ ] Existing authentication/security remains intact

### UX

- [ ] Mobile works
- [ ] Desktop works
- [ ] Loading/error/empty states work
- [ ] Keyboard navigation works
- [ ] Correct/incorrect feedback is not color-only

### Regression

- [ ] V0.1 authentication works
- [ ] V0.1 vocabulary CRUD works
- [ ] V0.1 search/filter/pagination works
- [ ] V0.2 Flashcards work
- [ ] Backend tests pass
- [ ] Frontend production build passes

## Recommended Development Order

```text
1. Review V0.1/V0.2 data model
2. Confirm existing progress model is reused
3. Design quiz question API
4. Implement eligible vocabulary selection
5. Implement distractor selection
6. Implement two directions
7. Implement answer validation
8. Integrate vocabulary_progress
9. Add backend security tests
10. Build /quiz UI
11. Build immediate feedback
12. Build navigation/progress
13. Build summary
14. Mobile/keyboard QA
15. Regression tests
16. Production build
17. Commit V0.3
```

## Product Principle

V0.2 asks:

> Do I think I remember this word?

V0.3 asks:

> Can I actually recall this word when the system tests me?

**Make the learner think before showing the answer.**

## Future Direction

```text
V0.1 Vocabulary management
  ↓
V0.2 Flashcards
  ↓
V0.3 Active Recall Quiz
  ↓
V0.4 Learning experience refinement
  ↓
V0.5 Spaced repetition
  ↓
V0.6 Import / document processing
  ↓
V0.7 AI-assisted learning
  ↓
V0.8 Audio / pronunciation
  ↓
V0.9 Mobile experience
  ↓
V1.0 Complete Korean learning product
```

This roadmap remains provisional and should be reviewed after actual use of each version.
