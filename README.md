# ai-marketing-decision-intelligence
AI-driven marketing decision intelligence platform that predicts lead conversion, explains predictions using SHAP, segments customers, analyzes campaigns and channels, and optimizes marketing budget allocation using reinforcement learning.

## Run locally (Windows PowerShell)

Start the API from the project root:

```powershell
cd backend
..\.venv\Scripts\python.exe -m uvicorn main:app --host 127.0.0.1 --port 8000
```

Start the frontend in a second terminal:

```powershell
cd frontend
npm.cmd install
npm.cmd run dev -- --host 127.0.0.1
```

Open http://127.0.0.1:5173/admin/login. Normal login also directs administrators to the admin area. The frontend forwards `/api` requests to the backend; set `BACKEND_URL` in the frontend server environment if the API runs elsewhere. A production deployment needs a SvelteKit server adapter appropriate to its host, plus the FastAPI service.

All admin pages share the Administration sidebar. Opening a protected admin URL while signed out sends you to admin login and returns you to that page after successful authentication. Access is checked again during navigation; expired admin sessions return to admin login. Redirect destinations are restricted to the application's admin pages.

## Administrator accounts

Create an administrator on a fresh installation from `backend`:

```powershell
..\.venv\Scripts\python.exe create_admin.py --email admin@example.com --name Administrator
```

The command prompts for a password of at least 12 characters and confirmation. It does not overwrite an existing account. Administrators can create additional admins on **Manage users**. Public registration cannot create administrators.

Accounts, hashed passwords, eight-hour revocable sessions, datasets, and settings persist in `backend/marketing_ai.db`. This local database is excluded from Git. `DATABASE_URL` can override the database location. The local account created during implementation exists only in this workspace's database; its credentials are supplied separately, not committed to source.

## Admin pages

- `/admin/users`: create accounts, change roles and names, reset passwords, and activate/deactivate users. Updates revoke that user's sessions. An administrator cannot disable or demote their own account.
- `/admin/datasets`: upload UTF-8 CSV files, preview the first 50 rows, rename, and delete datasets. Limits: 5 MB, 10,000 rows, 100 unique columns. Uploads are stored separately from existing leads and do not automatically run ingestion or model training.
- `/admin/configuration`: persist organization name, currency, model choice, conversion threshold, test fraction, and random seed. Organization and currency affect reports; the threshold affects the high probability lead count. Model training parameters are saved for future integration: there is currently no training service in this repository.
- `/admin/reports`: view all stored leads, predictions/segments, channel analytics, budget simulations, and dataset inventory; export the complete report as JSON. Empty databases show empty states, not fabricated metrics. The existing marketing dashboard remains a demonstration page.

Admin APIs enforce roles on the backend. Existing leads, analytics, and budget APIs now require authentication too. The frontend keeps the session token in session storage; logout invalidates it on the server.

## Validation

```powershell
cd backend
..\.venv\Scripts\python.exe -m unittest test_admin -v
cd ../frontend
npm.cmd run check
npm.cmd run build
npm.cmd run test:admin
```

The integration test starts an isolated local API and database, exercising permissions, authentication, account creation/promotion/deactivation, password changes, dataset validation and CRUD, configuration persistence, report data, and session revocation.

The admin browser tests use installed Google Chrome and start a separate frontend on port 5175 and API on port 8011 with a temporary database. They exercise the actual login form, protected redirects, all admin navigation links, user edits, CSV upload/preview/rename/delete, persisted configuration, report download, and logout. They do not modify the local application's accounts or datasets.
