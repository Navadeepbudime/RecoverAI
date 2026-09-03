# Problems and Solutions

## Problem 1: Local package managers were not ready for verification

### Problem
The local machine did not have the Python backend dependencies installed, and the `npm` command failed before it could run frontend installation or build commands.

### Context
This happened during the initial repository inspection before implementation.

### Root Cause
`python -m pip show flask pytest sqlalchemy flask-sqlalchemy pydantic` reported missing Python packages. `npm --version` failed because Node could not find `C:\Users\navad\AppData\Roaming\npm\node_modules\npm\bin\npm-cli.js`.

### How I Investigated
I checked `python --version`, `node --version`, `npm --version`, and `python -m pip show` for the required backend libraries.

### Solution
I added explicit dependency manifests in `backend/requirements.txt` and `frontend/package.json`, kept demo configuration simple, and documented the normal setup commands in `README.md`.

### Why This Solution
The repository should define reproducible dependencies instead of relying on globally installed packages. Fixing the user's global npm installation is outside the project source tree.

### Result
The project now contains the dependency definitions needed to install and verify the app in a properly configured local environment.

### Lesson Learned
Buildathon demos need a dependency manifest and demo mode because judge or developer machines often differ.

### Technical Evidence
Commands: `npm --version`, `python -m pip show flask pytest sqlalchemy flask-sqlalchemy pydantic`. Files: `backend/requirements.txt`, `frontend/package.json`, `README.md`.

## Problem 2: Pure business tests would import web and database dependencies unnecessarily

### Problem
Backend business logic tests would import the `app` package, which initially imported Flask at package import time. The agent and policy modules also pulled recovery enums through the SQLAlchemy model package.

### Context
This was noticed after adding tests for scoring, policy guardrails, and invalid AI output handling.

### Root Cause
`backend/app/__init__.py` imported Flask, Flask-CORS, database extensions, and routes at module load time. In addition, `RecoveryAction` and `CaseStatus` lived in `models/entities.py`, so importing the agent or policy engine required `flask_sqlalchemy`.

### How I Investigated
I reviewed the package import path used by `backend/tests/test_business_logic.py`, traced how Python resolves `app.agents.recovery_agent`, and ran a direct import smoke check.

### Solution
Moved Flask-related imports inside `create_app` and moved dependency-free enums to `backend/app/domain.py`.

### Why This Solution
Pure business logic modules should remain importable without booting the web framework or database extension. This keeps tests faster and isolates deterministic logic from web dependencies.

### Result
Scoring, recommendation validation, and policy modules can be imported without immediately creating a Flask app or SQLAlchemy extension.

### Lesson Learned
Application factories should keep package imports light, especially when the project has independently testable domain logic.

### Technical Evidence
Files: `backend/app/__init__.py`, `backend/app/domain.py`, `backend/app/agents/recovery_agent.py`, `backend/app/policies/engine.py`, `backend/tests/test_business_logic.py`. Command: `python -c "from app.services.scoring import score_recovery; from app.agents.recovery_agent import RecoveryRecommendation; from app.policies.engine import PolicyEngine; print('business imports ok')"`.

## Problem 3: Simulator state initialization happened during render

### Problem
The React simulator initialized component state from loaded API data during the render path.

### Context
This was found while reviewing the frontend pages before final verification.

### Root Cause
`Simulator.jsx` called `setForm(policy.data)` directly when rendering if form state was empty.

### How I Investigated
I read the component after wiring the policy API into the simulator and checked the state initialization path.

### Solution
Moved the form initialization into a `useEffect` that runs when `policy.data` changes.

### Why This Solution
React state updates that derive from asynchronous data should happen in effects, not during render.

### Result
The simulator avoids render-time state updates and is safer under React strict rendering.

### Lesson Learned
Even small demo interfaces should keep React state transitions predictable.

### Technical Evidence
File: `frontend/src/pages/Simulator.jsx`.

## Problem 4: PostgreSQL driver pin was incompatible with Python 3.14

### Problem
Installing backend dependencies failed after network access was allowed.

### Context
This happened while installing `backend/requirements.txt` into the project-local virtual environment.

### Root Cause
`psycopg[binary]==3.2.9` did not have a compatible `psycopg-binary` distribution for the installed Python 3.14 runtime.

### How I Investigated
I read the pip resolver error, which listed available compatible versions starting at `3.2.10` and including `3.3.5`.

### Solution
Updated the PostgreSQL driver requirement to `psycopg[binary]==3.3.5`.

### Why This Solution
Keeping `psycopg` preserves SQLAlchemy PostgreSQL compatibility while selecting a version that supports the local runtime.

### Result
The dependency manifest no longer pins an unavailable binary distribution for Python 3.14.

### Lesson Learned
Dependency pins should be verified against the runtime version used by the project.

### Technical Evidence
File: `backend/requirements.txt`. Command: `backend\\.venv\\Scripts\\python -m pip install -r backend\\requirements.txt`.

## Problem 5: Frontend build was blocked by pnpm build-script approval

### Problem
The frontend dependency install completed but Vite could not build because pnpm ignored the `esbuild` postinstall script.

### Context
This happened while installing and building the React frontend with pnpm because the local `npm` command was broken.

### Root Cause
Pnpm's dependency safety policy required explicit approval before running `esbuild`'s native binary install script.

### How I Investigated
I read the pnpm error message, checked `pnpm approve-builds --help`, and verified that `esbuild` was the only pending build script.

### Solution
Ran `pnpm approve-builds --all`, then restored dependencies with `pnpm install --frozen-lockfile` and invoked Vite directly with `node_modules\\.bin\\vite.cmd build`.

### Why This Solution
Approving the specific dependency build path lets Vite install its required compiler binary while preserving pnpm's safety model.

### Result
The frontend production build completed successfully.

### Lesson Learned
Modern frontend package managers may block native build scripts by default, so build verification needs to account for package-manager safety controls.

### Technical Evidence
Commands: `pnpm approve-builds --all`, `pnpm install --frozen-lockfile`, `node_modules\\.bin\\vite.cmd build`. Files: `frontend/package.json`, `frontend/pnpm-lock.yaml`, `frontend/pnpm-workspace.yaml`.

## Problem 6: Gemini API key was exposed in .env.example

### Problem
The real Gemini API key was committed to `.env.example`, which is tracked by git and visible to anyone with repository access.

### Context
Found during a project audit when reviewing `.env.example` line 10.

### Root Cause
The developer placed an actual API key (`AQ.Ab8RN6I...`) directly in the example file instead of leaving the value blank.

### How I Investigated
Read `.env.example` and noticed the `GEMINI_API_KEY` field contained a real key instead of being empty or containing a placeholder comment.

### Solution
Cleared the key from `.env.example` and set it to blank. Added a comment directing users to https://aistudio.google.com/apikey.

### Why This Solution
`.env.example` is a template committed to version control. It must never contain real secrets. The actual key belongs in `.env` (which is gitignored).

### Result
No real credentials are exposed in tracked files.

### Lesson Learned
Example environment files should always contain empty values or clearly marked placeholders, never actual credentials.

### Technical Evidence
File: `.env.example`. The key was on line 10 before the fix.

## Problem 7: Missing vite.config.js prevented React JSX transformation

### Problem
The frontend had no `vite.config.js`, meaning the `@vitejs/plugin-react` dependency was installed but never activated.

### Context
Found during the project audit. The `package.json` listed `@vitejs/plugin-react` as a dependency, but no configuration file loaded it.

### Root Cause
The initial project setup created `postcss.config.js` and `tailwind.config.js` but omitted the Vite configuration that connects the React plugin.

### How I Investigated
Searched the frontend directory for `vite.config` files and found none. Confirmed that `@vitejs/plugin-react` was in `package.json` but unused.

### Solution
Created `frontend/vite.config.js` with the React plugin enabled.

### Why This Solution
Vite needs an explicit configuration to load the React plugin for JSX transformation, Fast Refresh, and other React-specific build features.

### Result
The React plugin is now properly loaded during development and production builds.

### Lesson Learned
Always verify that framework plugins listed in dependencies are actually loaded by the build tool configuration.

### Technical Evidence
File: `frontend/vite.config.js`. Dependency: `@vitejs/plugin-react` in `frontend/package.json`.

## Problem 8: Simulator page failed to display updated calculation when values changed

### Problem
When changing values in the Recovery Simulator and clicking "Run Simulation", the expected recovery showed as ₹0 or blank, and clearing an input field caused backend HTTP 500 errors.

### Context
Occurred when testing the Recovery Simulator in the web UI under various policy settings.

### Root Cause
1. In `backend/app/services/simulator.py`, the return payload had been nested under `result["simulated"]`, while `frontend/src/pages/Simulator.jsx` was attempting to read top-level keys `result.expected_recovery`, `result.stopped_cases`, and `result.escalated_cases`, resulting in `undefined`.
2. The backend parser invoked `int(policy_payload.get(...))` directly on user input without handling empty strings (`""`) that occur when a user clears an input field in the UI, raising unhandled `ValueError`.
3. The frontend was missing inputs for `escalation_threshold` and `auto_retry_enabled`, and lacked side-by-side baseline comparison against the active merchant policy.

### How I Investigated
1. Inspected `frontend/src/pages/Simulator.jsx` and traced the expected object structure from `api.simulate(form)`.
2. Inspected `backend/app/services/simulator.py` and tested edge-case inputs with Python CLI, observing `ValueError: invalid literal for int() with base 10: ''`.

### Solution
1. Implemented `_safe_int` and `_safe_float` helpers in `simulator.py` that gracefully fall back to policy defaults on empty or malformed inputs.
2. Updated the return dictionary to provide both flat top-level keys for backward compatibility and structured `current`, `simulated`, and `delta` objects.
3. Upgraded `Simulator.jsx` with full controls (including escalation threshold and auto-retry toggle), preset configurations ("Strict Guardrails", "Maximize Recovery"), and side-by-side before/after comparison with net impact delta calculation.

### Why This Solution
Guarantees resilience against user typing patterns in the UI, maintains contract compatibility with the frontend, and directly provides the buildathon-required comparison between current policy and proposed policy.

### Result
The simulator dynamically recomputes expected recovery, stopped cases, and escalations immediately when values or presets are changed, displaying a clear before/after comparison.

### Lesson Learned
API endpoints that accept form inputs from numeric text fields must always anticipate empty strings and provide safe fallback parsing.

### Technical Evidence
Files: `backend/app/services/simulator.py`, `frontend/src/pages/Simulator.jsx`, `backend/tests/test_simulator.py`. Tests: 18 passed in `pytest`.

## Problem 9: datetime.utcnow deprecation warnings in SQLAlchemy entities

### Problem
When running pytest in Python 3.14 with SQLAlchemy 2.0, 14 deprecation warnings were raised across all test suites: `DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC)`.

### Context
Occurred when adding unit tests for the AI agent and evaluation framework in `backend/tests/`.

### Root Cause
SQLAlchemy column default attributes in `backend/app/models/entities.py` were bound directly to `datetime.utcnow`, which is deprecated since Python 3.12.

### How I Investigated
Observed the 14 pytest warning summaries pointing to `SQLAlchemy/sql/schema.py` line 3624 calling `fn()` where `fn = datetime.utcnow`.

### Solution
Created a `utc_now()` helper function returning `datetime.now(timezone.utc)` and updated all 6 column defaults and `onupdate` handlers in `entities.py`.

### Why This Solution
Ensures forward compatibility with Python 3.12, 3.13, and 3.14 without generating deprecation noise during automated testing or server startup.

### Result
All deprecation warnings eliminated; test suite executes with 0 warnings.

### Lesson Learned
Always use timezone-aware `datetime.now(timezone.utc)` for ORM timestamps in modern Python.

### Technical Evidence
File: `backend/app/models/entities.py`. Pytest output: 27 passed, 0 entity warnings.

## Problem 10: Strict Pydantic Literal validation rejected case-variant priority strings from LLM

### Problem
When testing structured JSON output from Gemini and external clients, responses containing `"priority": "high"` or `"critical"` failed Pydantic validation because `Literal["LOW", "MEDIUM", "HIGH", "CRITICAL"]` performs case-sensitive matching.

### Context
Occurred when validating simulated LLM outputs against `RecoveryRecommendation`.

### Root Cause
LLMs often emit lowercase or mixed-case priority strings (`"high"`, `"High"`) unless constrained by strict enum schemas, triggering a Pydantic `ValidationError`.

### How I Investigated
Observed schema parsing behavior when passing dictionary payloads with lowercase priority strings into `RecoveryRecommendation.from_dict()`.

### Solution
Added a `@field_validator("priority", mode="before")` pre-processor to `RecoveryRecommendation` that normalizes string input by stripping whitespace and converting to uppercase, defaulting to `"MEDIUM"` if unknown.

### Why This Solution
Provides resilient schema normalization at the boundary without breaking strict type guarantees for downstream consumers.

### Result
Both uppercase and lowercase priority strings from LLM providers parse cleanly into valid Pydantic models.

### Lesson Learned
When designing Pydantic schemas for LLM JSON outputs, use `mode="before"` field validators for case-insensitive normalization of enum-like fields.

### Technical Evidence
Files: `backend/app/agents/schemas.py`, `backend/tests/test_agent_and_evaluation.py`.
