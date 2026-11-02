# COMP 3613 Assignment 2 - Test Plans and UAT

**Student:** Zion Bruce
**Student ID:** 816046608
**Project:** ScholarNet (Research Platform)

## 1. User Acceptance Test (UAT) Plan

Based on the wireframes from Assignment 1. These tests are performed manually by the user.

| Test ID | Workflow | Pre-conditions | Test Steps | Success Criteria |
|---------|----------|----------------|------------|------------------|
| UAT-1 | Register | Not signed in | 1. Go to `/register`<br>2. Fill username, email, password<br>3. Click Register | Redirected to `/login` with a success message |
| UAT-2 | Login | Registered account | 1. Go to `/login`<br>2. Enter credentials<br>3. Click Sign in | Redirected to `/` and navbar shows user |
| UAT-3 | Browse | Not signed in | 1. Go to `/publications` | List of publications shown, pagination visible |
| UAT-4 | Search | Not signed in | 1. Type a query<br>2. Click Search | Only matching publications are shown |
| UAT-5 | Year Filter | Not signed in | 1. Select year 2023<br>2. Click Search | Only 2023 publications shown |
| UAT-6 | View Details | Not signed in | 1. Click View Details on a card | Title, authors, DOI, abstract, citations shown |
| UAT-7 | Author Graph | Not signed in | 1. Go to `/authors/graph` | Network graph renders with nodes and lines |
| UAT-8 | Manage | Signed in as author | 1. Go to `/manage/publications` | Only publications where user is first author are shown |
| UAT-9 | Upload | Signed in as author | 1. Click Upload<br>2. Fill form<br>3. Save | Publication appears in the manage list |

---

## 2. Unit Test Plan

Tests run in isolation, mocking external dependencies (no database).

| Test ID | Target | Test Case | Expected Output |
|---------|--------|-----------|-----------------|
| UT-1 | `User` model | Instantiate user | Fields match input |
| UT-2 | `User` model | Hash password | Plaintext does not equal stored password |
| UT-3 | `User` model | Verify password | Returns True for correct, False for wrong |
| UT-4 | `AuthService` | Login with valid credentials | Returns JWT token |
| UT-5 | `AuthService` | Login with wrong password | Returns None |
| UT-6 | `AuthService` | Login with unknown user | Returns None |
| UT-7 | `PublicationService` | Search delegations | Calls repository with correct args |
| UT-8 | `PublicationService` | Author Graph query | Calls repository sources |

---

## 3. Integration Test Plan

Tests running against a real (in-memory) SQLite database to verify persistence and queries.

| Test ID | Components | Test Case | Expected Output |
|---------|------------|-----------|-----------------|
| IT-1 | UserRepo + DB | Create user | User record exists with ID |
| IT-2 | UserRepo + DB | Find by username | Returns correct user object |
| IT-3 | UserRepo + DB | Find by unknown username | Returns None |
| IT-4 | PublicationRepo + DB | Create publication | Publication is retrievable by ID |
| IT-5 | PublicationRepo + DB | Search by title | Returns list of matches |
| IT-6 | PublicationRepo + DB | Search by year | Returns only publications from that year |
| IT-7 | PublicationRepo + DB | Duplicate DOI | Raises IntegrityError |

---

## 4. User Acceptance Testing (UAT) Report

*Status: PASSED*

| Test ID | Workflow | Status | Notes |
|---------|----------|--------|-------|
| UAT-1 | Register | ✅ Pass | User created, redirected to login. |
| UAT-2 | Login | ✅ Pass | Session cookie set, redirected to home. |
| UAT-3 | Browse | ✅ Pass | 12 seeded publications visible. |
| UAT-4 | Search | ✅ Pass | Filtering works correctly. |
| UAT-5 | Year Filter | ✅ Pass | Filtering by year returns correct subset. |
| UAT-6 | View Details | ✅ Pass | All metadata and citations visible. |
| UAT-7 | Author Graph | ✅ Pass | Graph rendered, nodes highlight on search. |
| UAT-8 | Manage | ✅ Pass | Author-only view works. |
| UAT-9 | Upload | ✅ Pass | Form saves, returns to list with new item. |