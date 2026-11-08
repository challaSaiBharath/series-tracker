# Week 1 Lesson Pack: Foundations (Mon Nov 23 to Sun Nov 29, 2026)

**Mode:** Heavy (about 6.5 hours on weekdays, 6 hours Saturday, 3 hours Sunday).
**Goal of the week:** a topics API that works in memory, with tests, plus your first weekly post.

Put this file in your repo as `docs/WEEK-01.md`.

> **Note (v0.2):** the tracker app already exists, so do the coding exercises below in a separate practice folder, `practice/week1_api/`, not inside `backend/`. That way you rebuild the ideas yourself. Monday's task of reading `backend/app` still applies.

## Daily template (weekdays)

| Time | Block |
|---|---|
| 08:00-09:30 | DSA: 2 problems plus review |
| 09:45-12:00 | Backend lesson and coding |
| 14:00-15:15 | CS fundamentals |
| 15:30-16:15 | AI-tool drill |
| 20:00-20:45 | Communication |

**Rules for every day**
1. Write the first version yourself. Use the AI tool only after you have tried, and verify what it tells you.
2. Log each DSA problem in the `DSA_Log` sheet (date, topic, solved alone Y/N, minutes).
3. Fill Done hrs and Status in the `Timetable` sheet in the evening.
4. For every DSA problem: try for 25 minutes, then read hints, then solve again from scratch the next day if you needed help.

---

## Monday, Nov 23

**Backend: Python for backend (venv, packages, project layout, type hints)**
1. Create a throwaway folder. Make a venv, install one package, run `pip freeze`, then delete the venv and recreate it from `requirements.txt`.
2. Write 5 small functions with type hints and docstrings (for example: parse a date string, sum hours from a list of dicts).
3. Write a `dataclass` called `Topic` (title, track, status). Create 3 objects and print them.
4. Read and write a JSON file with `json.load` and `json.dump`.
5. Read your repo's `backend/app` folder and explain each file out loud.

**DSA: Big-O and complexity**
1. Worksheet: write the time and space complexity of 5 small code snippets you write yourself (a loop, a nested loop, a halving loop, a recursive call, a dict lookup).
2. LeetCode 217 Contains Duplicate: solve it with two nested loops, then with a set. Write down both complexities.
3. LeetCode 136 Single Number.

**CS: How the web works (client and server)**
1. Write one page, in your own words, on what happens between typing a URL and seeing a page.
2. Self-quiz: What is a client? What is a server? Where does the database sit? Why do we need HTTP?

**AI-tool drill:** Paste your type-hinted functions and ask for 3 problems. Check each claim yourself before changing anything.

**Communication:** Write 5 sentences in your README: why you are doing this series and what you will build.

---

## Tuesday, Nov 24

**Backend: Git and GitHub (branches, pull requests, commit messages)**
1. Create a branch `feature/topics-model`.
2. Make 3 separate commits with clear messages (for example: `Add Topic dataclass`, not `update`).
3. Open a pull request to `main` on GitHub (yes, even alone), read the diff, and merge it.
4. Practice `git log --oneline`, `git diff`, `git restore`, and `git stash`.
5. Create a deliberate conflict (edit the same line on two branches) and resolve it.

**DSA: Arrays**
1. LeetCode 283 Move Zeroes
2. LeetCode 26 Remove Duplicates from Sorted Array
3. Review: redo one of yesterday's problems without notes.

**CS: HTTP in depth**
1. Open your browser DevTools, Network tab, load any site, and inspect one request: method, status, request headers, response headers.
2. Self-quiz: What do `Content-Type`, `Authorization`, and `Cache-Control` do? What is the difference between GET and POST?

**AI-tool drill:** Ask the AI to critique your 3 commit messages. Rewrite them yourself.

**Communication:** Rewrite your last 5 commit messages into a clean style you will keep using.

---

## Wednesday, Nov 25

**Backend: HTTP and REST (methods, status codes, JSON, curl/Postman)**
1. Call `http://127.0.0.1:8000/health` with curl, then with Postman or any API client.
2. Call a public test service (for example httpbin.org) with GET, POST with a JSON body, and a bad request. Note each status code.
3. Learn these status codes by heart: 200, 201, 204, 400, 404, 409, 422, 500.
4. Design the topics routes on paper: `GET /topics`, `GET /topics/{id}`, `POST /topics`, `PUT /topics/{id}`, `DELETE /topics/{id}`. Write the expected status code for success and for each error.
5. Save your notes as `docs/http-notes.md`.

**DSA: Strings**
1. LeetCode 242 Valid Anagram
2. LeetCode 125 Valid Palindrome
3. Review: redo one problem from Tuesday.

**CS: DNS**
1. Run `nslookup` (or `dig`) on two domains and read the output.
2. Explain recursive DNS resolution in 5 steps, in your own words.
3. Self-quiz: What does a DNS server return? Why is DNS cached?

**AI-tool drill:** Paste a curl response and ask the AI to explain every line. Check it against the HTTP notes you wrote.

**Communication:** Record a 3-minute explanation of the HTTP methods (no notes), then listen back and write down what was unclear.

---

## Thursday, Nov 26

**Backend: First FastAPI app (routes, path and query params, auto docs)**
1. In `practice/week1_api/`, create `main.py` with a FastAPI app and `GET /topics` returning a hardcoded list.
2. Add `GET /topics/{topic_id}` (path parameter) and a `?track=` query filter.
3. Run it with `uvicorn`, then open `/docs` and test both from the browser.
4. Read how FastAPI uses type hints to validate input. Send a wrong type and read the 422 response.
5. Explain, out loud, how the request travels from uvicorn to your function.

**DSA: Hash maps**
1. LeetCode 1 Two Sum
2. LeetCode 49 Group Anagrams (medium, use hints if needed)
3. Review: redo Tuesday's problems.

**CS: URLs, IP addresses, ports**
1. Break down one URL into scheme, host, port, path, and query.
2. Write down what runs on ports 80, 443, 5432, and 8000.
3. Self-quiz: What is `127.0.0.1`? What does binding a port to `127.0.0.1` do compared to `0.0.0.0`? (This is why the database in `docker-compose.yml` is bound to `127.0.0.1`.)

**AI-tool drill:** Ask the AI for 3 edge cases for your two endpoints. Write the tests yourself.

**Communication:** Make sure a stranger could follow your README "Quick start". Test it by cloning your repo into a new folder and following it.

---

## Friday, Nov 27

**Backend: Request bodies and in-memory CRUD**
1. Create Pydantic models in `practice/week1_api/`: `TopicCreate`, `TopicUpdate`, `TopicOut`.
2. Keep topics in an in-memory dict, with a simple incrementing id.
3. Add `POST /topics` (201), `PUT /topics/{id}`, `DELETE /topics/{id}` (204), and 404 for unknown ids.
4. Write at least 6 tests with `TestClient` (create, list, get, update, delete, not found).
5. Commit on a branch and open a pull request.

**DSA: Hash sets**
1. LeetCode 349 Intersection of Two Arrays
2. LeetCode 128 Longest Consecutive Sequence (medium, use hints if needed)
3. Review: redo any problem you needed hints for.

**CS: Life of a request (browser to server)**
1. Draw the full path: browser, DNS, TCP connection, HTTP request, uvicorn, FastAPI router, your function, response.
2. Add a box at the end for the database (it arrives in Week 2).
3. Self-quiz: Where can a request fail, and which status code would each failure give?

**AI-tool drill:** Ask the AI to review your CRUD code and list bugs. Verify each one by hand before you change anything.

**Communication:** Draft the outline for your weekly post: what I built, what I learned, one mistake I made, what is next.

---

## Saturday, Nov 28 (6 hours, project)

Your repo and `/health` already exist, so this day builds on them.

**Session 1 (3 hours)**
1. Split the practice code into layers: an in-memory repository class, a service, and thin routes.
2. Add `?track=` and `?status=` filters and simple `limit` and `offset`.
3. Return clear error messages for bad input.

**Session 2 (3 hours)**
1. Expand tests to at least 10.
2. Write `docs/API.md` listing every route, its inputs, and its status codes.
3. Open a pull request, review your own diff, and merge.

## Sunday, Nov 29 (about 3 hours)

1. **Weekly review (1 hour):** update the `Weekly` sheet, re-rate any skills that moved (with evidence), and list what slipped.
2. **Project (1 hour):** polish the README and tag a release: `git tag v0.0.1`.
3. **First weekly post (1 hour):** publish it using your outline from Friday.

---

## Definition of done for Week 1

- [ ] 10 or more DSA problems logged
- [ ] Topics CRUD works in memory, with at least 10 passing tests
- [ ] Merged pull requests on GitHub (not just direct commits)
- [ ] `docs/http-notes.md` and `docs/API.md` written
- [ ] First weekly post published
- [ ] Timetable sheet filled in for every day

## If you fall behind

Keep the minimum day: DSA 45 minutes plus one backend block. Do not skip Sunday's review. Move unfinished items to Week 2's weekend instead of cutting sleep.
