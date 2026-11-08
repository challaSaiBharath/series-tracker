# Research notes (Nov 8, 2026) and what changed because of them

These are the web sources I read before building v0.2. Most are practitioner blogs, vendor pages, and repositories, not peer-reviewed studies, so treat them as guidance and not proof.

## 1. Backend roadmap for 2026
Sources: Scrimba, Educative, and Scaler backend roadmap guides, and several others (search "backend developer roadmap 2026").
- Result: the five tracks in the plan (one language in depth, databases, APIs, testing, deployment, observability, projects, DSA, CS basics) match what the guides cover. No tracks were added.
- Check for yourself: some guides assume about 10-15 study hours a week. Your Heavy weeks are about 41 hours. Keep the weekly rest day and the minimum-day rule.
- Optional later: Kubernetes basics appear in some guides; the plan stops at Docker.

## 2. DSA order and size
Sources: Educative NeetCode guide, NeetCode roadmap repositories, and pattern-order write-ups.
- The common order is arrays and hashing, two pointers, sliding window, stack, binary search, linked list, trees, tries, heap, backtracking, graphs, then DP. The plan's order matches, with sorting added early.
- One guide advises against finishing a whole category before touching the next. The plan already mixes in review days.
- Change made: the app's DSA target is now 150 (the size of the NeetCode 150 list), not 140.

## 3. Spaced repetition for coding problems
Sources: several interview-prep tools and write-ups (PatternBank, LeetCode Recall Tracker, InterviewPrepCli, a DEV Community post).
- Common schedule: 1, 3, 7, 14, then 30 days, sooner when you struggled or needed hints.
- Not used: a claimed "200-300% better retention" figure appears in one post without a source.
- Change made: DSA problems now follow 3, 7, 14, 30 days (1 day if you needed help), with Remembered / Struggled buttons and a "reviews due" list.

## 4. Streak and habit design
Sources: Smashing Magazine (Feb 2026) on streak UX, plus habit-tracker articles citing the 2010 UCL habit-formation study (about 66 days to automaticity, wide variation).
- Streak systems work better with recovery mechanisms (grace days, freezes) and a consistency rate that never resets.
- Change made: the streak forgives one missed day per Mon-Sun week, the dashboard shows a 14-day consistency rate and a total-hours count that never resets, missed days appear as a catch-up list ("not a penalty"), and a "Minimum day" button counts a 45-minute DSA session.

## 5. Accessibility (WCAG 2.2)
Sources: W3C "What's new in WCAG 2.2", Deque, and others.
- Target Size (Minimum), Level AA: interactive controls should be at least 24 by 24 CSS pixels, or spaced out enough. 44 by 44 is the stricter AAA goal.
- Change made: checkboxes enlarged to 24 px, small buttons at least 32 px tall, a thicker focus outline, keyboard focus moves to the page content when you change sections.
- Not done: I tested visually in Chrome only, not with a screen reader.

## 6. Test tooling
- Starlette's newer versions warn that `starlette.testclient` with `httpx` is deprecated and ask for `httpx2`. I installed `httpx2` and the warning went away (31 tests pass).
- The `@app.middleware` decorator is marked deprecated in Starlette's source, with `add_middleware` as the recommended route. The app now uses `add_middleware`.
- The gitleaks version pinned in `.pre-commit-config.yaml` dates from 2024; run `pre-commit autoupdate`.

## 7. Localhost security (engineering judgement, not a single source)
- A no-login app on localhost can still be reached by web pages in your browser. A Host allowlist blocks DNS rebinding, and an Origin / Sec-Fetch-Site check blocks cross-site writes (including other apps on a different localhost port).
- Change made: `app/security.py`, with tests, plus detection rule 3. These do not replace keeping the app on your own computer.
