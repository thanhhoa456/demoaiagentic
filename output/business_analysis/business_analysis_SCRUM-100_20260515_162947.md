## Business Analysis – Jira SCRUM‑100  

### 1. Scope  

| **In‑Scope** | **Out‑of‑Scope** |
|--------------|-----------------|
| • Patient‑centric view of **healthcare providers** (list + detail). | • Provider onboarding / registration workflow. |
| • **Filtering** of providers by specialty, location, rating, fee, etc. | • Provider credential verification / licensing checks. |
| • **Sorting** of provider list (fee, rating). | • Billing, payment processing, insurance claims. |
| • **Provider detail page** showing available appointment slots. | • Appointment rescheduling / cancellation (unless directly related to booking). |
| • **Appointment booking** using only slots that are truly free at the moment of selection. | • Loyalty / rewards program, promotional discounts. |
| • **Concurrency control** – prevent double‑booking of the same slot. | • Multi‑step wizard flows, step‑by‑step guided booking (if not part of the current UI). |
| • Integration with **My Appointments** (“Lịch của tôi”) to display confirmed bookings. | • Patient profile management (personal data, preferences). |
| • Basic **authentication** – patient must be logged‑in to see provider list and book. | • Administrative dashboards, reporting, analytics. |

> **Definition of “Done” for this story** – All acceptance criteria are automated‑tested, code reviewed, documentation updated, and the feature is deployable to the **Testing** environment.

---

### 2. Refined Acceptance Criteria  

| **AC** | **Refined Acceptance Criteria** (testable) |
|--------|--------------------------------------------|
| **AC1 – View Provider List** | 1.1 The patient must be **authenticated** (valid session / token). <br>1.2 The system returns a ** paginated** list of providers (default page size = 20). <br>1.3 Each provider card/row contains: <br> • Specialty (e.g., “Cardiology”) <br> • Years of experience (e.g., “12 yrs”) <br> • Overall rating (e.g., ★4.5) <br> • Check‑up fee (currency format) <br> • Current hospital/clinic name <br> • City / location (e.g., “Hanoi”) |
| **AC2 – Filter & Sort** | 2.1 **Filter** can be applied by any combination of the following fields: <br> • Specialty (exact match or contains) <br> • Location (city, clinic name) <br> • Rating (>=, <=, =) <br> • Fee range (min‑max) <br>2.2 **Sort** options: <br> • Check‑up fee (ascending / descending) <br> • Rating (ascending / descending) <br>2.3 The UI must reflect the active filter(s) and sort order in the URL or UI state, and the list must update accordingly without full page reload (AJAX). |
| **AC3 – View Provider Details** | 3.1 Clicking a provider card navigates to **/providers/{providerId}**. <br>3.2 The detail page shows: <br> • Provider header (name, specialty, rating, fee, clinic) <br> • Short bio (optional) <br> • **Available appointment slots** (list of date‑time strings). <br>3.3 Slots are **real‑time** – they reflect the current availability at the moment of page load. |
| **AC4 – Book Appointment** | 4.1 The patient selects **one** slot from the list. <br>4.2 The system validates that the slot is still **available** at the moment of submission (race‑condition safe). <br>4.3 On successful booking: <br> • An appointment record is created with status **“Confirmed”**. <br> • The appointment appears instantly in the **My Appointments** list (with date, time, provider, status). <br> • A confirmation message (toast / banner) is displayed. <br>4.4 The UI redirects back to the provider list or detail page (configurable). |
| **AC5 – Handle Concurrent Booking** | 5.1 When two or more patients attempt to book the **same slot** simultaneously: <br> • The first request that reaches the booking service secures the slot and returns **success**. <br> • Subsequent requests receive a **“Slot unavailable”** error (HTTP 409/400) with a friendly message (“This time slot is no longer available”). <br>5.2 The error message must be displayed in the UI and logged for audit. <br>5.3 No duplicate appointment records may exist for the same provider‑slot combination. |

---

### 3. Test Scope  

| **Test Type** | **Coverage** | **Examples** |
|---------------|--------------|--------------|
| **Unit Tests** | Service layer (booking, provider repository) | Verify that booking service checks slot availability atomically; ensure concurrency guard (e.g., DB row‑level lock or version column). |
| **API / Integration Tests** | REST endpoints for provider list, filter, sort, detail, book | • GET /providers → correct pagination, filter params, sort order.<br>• POST /appointments → success and conflict handling. |
| **UI / End‑to‑End Tests** | UI flow (Cypress / Playwright) | • Log in → see provider list.<br>• Apply filters → list updates.<br>• Sort → order changes.<br>• Click provider → detail page loads slots.<br>• Select slot → booking succeeds, appears in My Appointments.<br>• Simulate two concurrent bookings → only one succeeds. |
| **Negative / Edge Cases** | Validation, security, data integrity | • Unauthenticated access → 401.<br>• Invalid filter parameters → 400.<br>• Selecting an already‑booked slot (should be prevented).<br>• Extremely high request rate (load test concurrency). |
| **Non‑Functional** | Performance, security, usability | • Response time < 2 s for provider list (10 k providers).<br>• Concurrency test: 100 simultaneous booking attempts → no double‑booking.<br>• Accessibility compliance for list and detail pages. |
| **Regression** | Ensure existing patient flow (e.g., view appointments) not broken. | Run full regression suite after any change. |

*Test data*: Use a **seeded** database with known provider/ slot records. For concurrency testing, employ scripted parallel requests (e.g., using JMeter or a custom Node.js script).

---

### 4. Risks  

| **Risk** | **Impact** | **Likelihood** | **Mitigation** |
|----------|------------|----------------|----------------|
| **Concurrent booking race condition** – two users can book the same slot before the system checks availability. | High (double‑booking, data integrity) | Medium | Use **optimistic locking** (version column) or **pessimistic DB locks** on the slot row; wrap booking in a transaction; add a “slot version” check in the API. |
| **Stale slot data** – provider’s availability changes (cancellation, no‑show) after the list is rendered. | Medium | Medium | Refresh slot list on the detail page just before booking (or provide a “Refresh” button). Use real‑time updates (WebSocket / Server‑Sent Events) if high‑frequency changes are expected. |
| **Performance bottleneck** when loading a large provider list (tens of thousands). | Medium | Low‑Medium | Implement server‑side pagination, caching of provider metadata, and indexed DB queries on filter/sort fields. |
| **Incorrect filtering/sorting logic** leading to missing or duplicate providers. | Low | Low | Write comprehensive unit tests for filter/sort engine; use well‑defined query parameters. |
| **Security / Authentication bypass** – unauthenticated users could view or book appointments. | High | Low | Enforce authentication at the API gateway; return 401 for unauthenticated calls; audit logs. |
| **Internationalisation / Time‑zone handling** – slots displayed in wrong zone for users in different regions. | Medium | Low | Store all times in UTC; display in user’s local zone; test with multiple zones. |
| **Dependency on external provider data service** (if providers are not stored locally). | High | Medium | Abstract provider data access behind a service interface; include fallback / mock in tests. |

---

### 5. Dependencies  

| **Dependency** | **Description** | **Owner / Notes** |
|----------------|-----------------|-------------------|
| **User Authentication Service** | Validates patient login, provides user context for API calls. | Must return a stable user‑ID; token expiration handling. |
| **Provider Data Service** | Supplies provider catalogue (specialty, experience, rating, fee, location). May be a separate micro‑service or DB view. | Needs to be versioned; expose endpoints for list, filter, detail. |
| **Appointment / Slot Availability Service** | Determines which slots are free at any moment, handles concurrency. | Must be atomic; may use DB row‑level lock or a dedicated scheduling engine. |
| **My Appointments UI Component** | Displays confirmed appointments; must be updated after successful booking. | Depends on appointment service’s “list” endpoint. |
| **Database (SQL/NoSQL)** | Persists providers, slots, appointments, user sessions. | Indexes on provider fields (specialty, location, rating) and on appointment slot‑time + provider‑ID to enforce uniqueness. |
| **Frontend Framework** (React/Angular/Vue) | Renders provider list, filters, sorting, detail page, booking form. | Must support async data fetching and state management for filters/sort. |
| **Third‑party Calendar / Scheduling Library** (optional) | May be used to generate slot options or handle recurring slots. | If used, ensure it respects concurrency checks. |
| **Testing Environment** | Separate from production; contains test data setups. | Must be refreshed before each test cycle. |

---

## Summary  

The **patient‑centric provider & booking** feature is **fully in scope** and can be delivered with a clear set of functional requirements (list, filter/sort, detail view, book, concurrency protection) and non‑functional considerations (performance, security, usability).  

The **acceptance criteria** have been refined to be **measurable** and **testable**.  

A **comprehensive test plan** covers unit, API, UI, negative, and non‑functional scenarios, including a dedicated strategy for concurrency validation.  

Key **risks**—particularly around race conditions and stale data—are identified and mitigated through atomic transactions and real‑time slot refresh.  

All **dependencies** (auth, provider data, slot availability, UI components, database) are explicitly listed, enabling the development team to verify that the required services are available and properly integrated before testing begins.  

With these artifacts in place, the team can move forward to implementation, sprint planning, and systematic verification that the story meets the business goal of “conveniently scheduling a medical check‑up without booking conflicts.”