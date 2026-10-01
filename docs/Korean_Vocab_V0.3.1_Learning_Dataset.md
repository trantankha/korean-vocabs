# Korean Vocab — V0.3.1 Learning Dataset

## Purpose

V0.3.1 is a **data-focused release**, not a feature expansion.

Its goal is to provide a reliable Beginner Korean vocabulary dataset so that the existing V0.2 Flashcards and V0.3 Quiz provide a genuinely useful learning experience.

> Improve learning quality through better data before adding more features.

## Target Learner

Initial target:

**Beginner Korean learners**

Prioritize vocabulary useful for daily life, basic communication, Korean classes, living in Korea, and common beginner conversations.

All V0.3.1 seed records use:

```text
Level = BEGINNER
```

Higher levels are deferred to future versions.

## Product Language

The application is **English-first**.

UI/system language:
- English

Learning content:
- Korean vocabulary
- English meaning
- Korean example sentence
- English example translation

Do not hard-code Vietnamese into the UI or seed dataset. Future localization can add other languages.

## Dataset Size

Initial seed:

**250 vocabulary items**

The dataset should prioritize practical usefulness and beginner suitability rather than simply maximizing frequency.

## Categories

Use these canonical categories:

| Category | Target |
|---|---:|
| People & Family | 25 |
| Daily Life | 25 |
| Food & Drinks | 30 |
| Places | 25 |
| School & Study | 25 |
| Transportation | 20 |
| Time & Dates | 25 |
| Actions | 35 |
| Descriptions | 25 |
| Objects & Things | 15 |
| **Total** | **250** |

Small adjustments are acceptable when necessary for data quality. Do not create unnecessary categories just to reach 250.

## Vocabulary Record

Each item should contain at least:

```text
Korean
English meaning
Category
Level
Example sentence in Korean
Example sentence in English
```

Example:

```json
{
  "korean": "학교",
  "meaning": "school",
  "category": "Places",
  "level": "BEGINNER",
  "example_ko": "저는 학교에 가요.",
  "example_en": "I go to school."
}
```

Reuse the existing database model where possible. Do not create a second vocabulary model solely for V0.3.1.

## Meaning Rules

English meanings must be concise, natural, beginner-friendly, and consistent.

Prefer:

```text
학교 → school
친구 → friend
먹다 → to eat
좋다 → good
```

Avoid long dictionary definitions. If a word has several meanings, use the common beginner-relevant meaning.

## Word Selection

Prioritize vocabulary a beginner can realistically encounter or use.

Examples of appropriate candidates:

```text
학교
학생
친구
가족
집
방
책
물
밥
먹다
마시다
가다
오다
보다
좋다
크다
작다
오늘
내일
어제
```

Avoid rare, literary, overly formal, advanced, or redundant vocabulary.

## Part-of-Speech Balance

Include a useful mixture of:
- Nouns
- Verbs
- Adjectives/descriptive verbs
- Time-related expressions
- Practical everyday vocabulary

Do not make the dataset almost entirely nouns.

## Example Sentence Rules

Every item must have one Korean example and one English translation.

Example:

```text
학교

저는 학교에 가요.

I go to school.
```

Examples must be:
- Natural Korean
- Beginner appropriate
- Short
- Practical
- Grammatically correct
- Understandable without advanced grammar

Prefer reusing other Beginner vocabulary where natural.

Do not fabricate examples through AI at runtime.

## Quiz Compatibility

V0.3 supports:

```text
Korean → English
English → Korean
```

Example:

```text
What does 학교 mean?

A. hospital
B. school
C. restaurant
D. station
```

and:

```text
How do you say "school" in Korean?

A. 병원
B. 학교
C. 식당
D. 공원
```

Avoid unnecessary ambiguity.

## Distractor Compatibility

Quiz distractors come from vocabulary available to the user.

Preferred selection:

```text
Same category + same level
        ↓
Same level
        ↓
Any eligible vocabulary
```

Avoid excessive semantic duplication or near-identical English meanings.

## Duplicate and Validation Rules

Before seeding, validate:

```text
duplicate Korean word
duplicate normalized Korean word
empty Korean word
empty English meaning
missing category
missing level
missing example
missing translation
```

Normalization must at least handle accidental leading/trailing whitespace.

Canonical categories are exactly:

```text
People & Family
Daily Life
Food & Drinks
Places
School & Study
Transportation
Time & Dates
Actions
Descriptions
Objects & Things
```

All V0.3.1 levels are:

```text
BEGINNER
```

## Seed Strategy

Seed through the existing backend/database mechanism.

Do not hard-code the 250 records into the frontend.

```text
Seed data
    ↓
Database
    ↓
Backend API
    ↓
Frontend
```

The seeded vocabulary must work with:
- Vocabulary list
- Search
- Filters
- Flashcards
- Quiz

## Idempotency

The seed must be safe to run repeatedly.

```text
First run  → insert missing records
Second run → do not create duplicates
```

Use existing database/ORM conventions. Do not add unnecessary infrastructure.

## Ownership Model

The 250 seed records are **shared system vocabulary**, not personal vocabulary belonging to a particular user.

Keep this distinct from user-created vocabulary.

If the current schema assumes every vocabulary item is user-owned, inspect the existing architecture first and make the smallest safe change needed to support shared seed vocabulary without weakening user isolation.

Do not break existing ownership/security behavior.

## Existing User Vocabulary

V0.3.1 must preserve:
- User vocabulary CRUD
- Search
- Filters
- Flashcards
- Quiz
- Progress tracking

Seed vocabulary complements user-created vocabulary; it does not replace it.

## English-First UI

Dataset-related UI must use English, for example:

```text
Beginner
Places
Food & Drinks
School & Study
Add Vocabulary
Start Quiz
Next Question
Correct
Incorrect
No vocabulary found
```

No Vietnamese system text.

## Technical Validation

Verify:

```text
Total seed records = 250
All levels = BEGINNER
All categories are valid
Korean values are unique
Required fields are non-empty
Seed is idempotent
```

Also verify through the API:

```text
Search finds seeded vocabulary
Category filter works
Level filter works
Flashcards use seeded vocabulary
Quiz uses seeded vocabulary
Quiz distractors can be generated
```

## Quiz Data Test

Manually test at least:

```text
Quiz
Category: All
Level: Beginner
Questions: 10
```

and:

```text
Quiz
Category: Food & Drinks
Level: Beginner
Questions: 10
```

Verify:
- No duplicate questions within a session
- Both directions work
- Distractors are valid
- Correct answer is not duplicated
- Choices are shuffled
- Feedback is correct
- Example sentences display correctly

## Definition of Done

### Dataset
- [ ] 250 Beginner vocabulary items exist
- [ ] Category distribution is approximately correct
- [ ] All meanings are in English
- [ ] Every record has Korean and English example content
- [ ] No duplicate Korean vocabulary
- [ ] No missing required fields

### Backend
- [ ] Seed runs successfully
- [ ] Seed is idempotent
- [ ] Existing user vocabulary remains intact
- [ ] Existing ownership/security rules remain intact
- [ ] Existing APIs continue working

### Learning
- [ ] Flashcards work with seeded vocabulary
- [ ] Quiz works with seeded vocabulary
- [ ] Korean → English works
- [ ] English → Korean works
- [ ] Distractors are sufficiently varied
- [ ] Category/level filtering works

### Regression
- [ ] Existing API tests pass
- [ ] V0.1 features pass
- [ ] V0.2 features pass
- [ ] V0.3 features pass
- [ ] Frontend production build passes
- [ ] Manual smoke test passes

## Explicit Non-Goals

V0.3.1 does NOT include:

```text
❌ New Quiz types
❌ New Flashcard modes
❌ AI-generated vocabulary
❌ AI-generated examples
❌ Audio
❌ Pronunciation
❌ Spaced repetition
❌ Statistics dashboard
❌ XP
❌ Streak
❌ Leaderboard
❌ Public user-generated vocabulary
❌ Translation API
❌ External dictionary integration
❌ Native mobile application
```

This version is about **data quality**, not feature expansion.

## Future Compatibility

The dataset should support future expansion:

```text
V0.3.1
Beginner
250 words
    ↓
Beginner 500+
    ↓
Elementary
    ↓
Intermediate
    ↓
Advanced
```

Future versions may reuse this data for spaced repetition, improved Quiz generation, recommendations, listening, pronunciation, AI assistance, and personalization.

Do not implement those features now.

## Product Principle

A useful learning product needs:

```text
Good UX
+
Good learning method
+
Good content
```

V0.3.1 focuses specifically on:

> **Good content.**

## Agent Instructions

Before implementation:

1. Inspect the current vocabulary schema.
2. Inspect category and level models.
3. Inspect ownership rules.
4. Inspect Flashcard and Quiz data flow.
5. Reuse existing structures where possible.
6. Make the smallest safe database/seed changes.
7. Preserve all existing V0.1–V0.3 behavior.

The goal is:

> **Better learning data with minimal architectural disruption.**
