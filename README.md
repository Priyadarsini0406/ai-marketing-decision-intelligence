# ai-admission-decision-intelligence
AI-driven admission decision intelligence platform that predicts student lead conversion, explains predictions using SHAP, segments students, analyzes admission campaigns and channels, and optimizes admission marketing budget allocation using reinforcement learning.

## Run locally on Windows, macOS, or Linux

Install Node.js 22.12+ and Python 3.12, then run from the project root:

```sh
npm install
npm run install:frontend
```

Create a virtual environment (it must be created separately on each operating system):

```sh
# Windows
py -3.12 -m venv .venv
# macOS / Linux
python3.12 -m venv .venv
```

Install the API dependencies and start both services:

```sh
npm run install:backend
npm run dev
```

`npm start` also starts both services. Open http://127.0.0.1:5173/login.
The portable Python launcher selects the project's `.venv`, an activated virtual environment,
or Python on PATH. Set `DI_PYTHON` to an interpreter path to override this selection.
On Windows PowerShell, use `npm.cmd` if your execution policy blocks `npm.ps1`.
The API uses port 8000 and the frontend forwards `/api` requests to it. Set `BACKEND_URL`
if the API runs elsewhere. A production deployment needs a SvelteKit server adapter
appropriate to its host, plus the FastAPI service.

The frontend runs in modern browsers on Windows, macOS, Linux, Android, and iOS.
Mobile users access the hosted web application; they do not need Node or Python on their device.
The server dependencies need a supported desktop/server operating system.
Model training and source-data features also require their documented datasets and artifacts.

To test from another device on your local network, start the API normally and run the
frontend with `npm --prefix frontend run dev -- --host 0.0.0.0`. Open the computer's
LAN address on port 5173 from the device, and allow that port through the local firewall.
API requests are proxied by the frontend, so the API can stay bound to localhost.
Use this only on a trusted local network; deploy with HTTPS for public access.

## Responsive interface checks

The shared layout uses a navigation drawer below 1024px, compact headers on phones,
scrollable data tables, and layouts that adapt to the available width. Registration
keeps its long form scrollable on short and landscape screens.

```sh
npm run test:responsive
npm run check
npm run build
```

These browser checks cover 320px and 390px phones, landscape, 768px tablets,
1024px laptops, and 1440px desktop screens. They use mocked authentication and do
not require source datasets or a running API. They use Google Chrome by default;
set `PLAYWRIGHT_CHANNEL` to another installed Playwright browser channel if needed.
They check overflow, mobile navigation, notification panels, and text contrast.

All admin pages share the Administration sidebar. Opening a protected admin URL while signed out sends you to admin login and returns you to that page after successful authentication. Access is checked again during navigation; expired admin sessions return to admin login. Redirect destinations are restricted to the application's admin pages.

## Administrator accounts

Create an administrator on a fresh installation from the project root:

```powershell
npm run python -- backend/create_admin.py --email admin@example.com --name Administrator
```

The command prompts for a password of at least 12 characters and confirmation. It does not overwrite an existing account. Administrators can create additional admins on **Manage users**. Public registration cannot create administrators.

Accounts, hashed passwords, eight-hour revocable sessions, datasets, and settings persist in `backend/marketing_ai.db`. This local database is excluded from Git. `DATABASE_URL` can override the database location. The local account created during implementation exists only in this workspace's database; its credentials are supplied separately, not committed to source.

## Connected application pages

Student registrations are stored as user accounts and are visible in the administrator Students directory and the manager Student Leads workspace. Student profile edits and admission enquiries are persisted in the configured database; managers and administrators can review enquiry details and update their status. Uploaded CSV and ZIP datasets are stored in the shared dataset inventory and remain available to administrators after restart. Uploading a dataset does not automatically train a model or replace lead records.

The home page links to login, registration, admin login, privacy, and terms. Password help is available from login and explains administrator-assisted password resets. The Features, How it works, and Customers anchors link to their home page sections.

The authenticated dashboard links to `/dashboard/leads`, `/dashboard/analytics`, and `/dashboard/budget`. These pages read stored leads/predictions, channel metrics, and saved simulations from the API and show empty states when records are unavailable. Overview export downloads stored channel and simulation data; its displayed sample metrics are explicitly labeled demonstration data. Conversion model training is available through `backend/train_model.py` (see [training instructions](data/README.md)); interactive what-if calculations are available at `/dashboard/simulator`. Signing in after opening a protected dashboard page returns regular users to that page.

### Administration

- `/admin/users`: create accounts, change roles and names, reset passwords, and activate/deactivate users. Updates revoke that user's sessions. An administrator cannot disable or demote their own account.
- `/admin/datasets`: upload UTF-8 CSV files, preview the first 50 rows, rename, and delete datasets. Limits: 5 MB, 10,000 rows, 100 unique columns. Uploads are stored separately from existing leads and do not automatically run ingestion or model training.
- `/admin/configuration`: persist organization name, currency, model choice, conversion threshold, test fraction, and random seed. Organization and currency affect reports; the threshold affects the high probability lead count. Model training parameters are saved for future integration: there is currently no training service in this repository.
- `/admin/reports`: view all stored leads, predictions/segments, channel analytics, budget simulations, and dataset inventory; export the complete report as JSON. Empty databases show empty states, not fabricated metrics. The existing admission dashboard remains a demonstration page.

Admin APIs enforce roles on the backend. Existing leads, analytics, and budget APIs now require authentication too. The frontend keeps the session token in session storage; logout invalidates it on the server.

## Validation

```sh
npm run python -- -m unittest discover -s backend -p test_admin.py -v
npm run check
npm run build
npm run test:admin
```

The integration test starts an isolated local API and database, exercising permissions, authentication, account creation/promotion/deactivation, password changes, dataset validation and CRUD, configuration persistence, report data, and session revocation.

The admin browser tests use installed Google Chrome and start a separate frontend on port 5175 and API on port 8011 with a temporary database. They exercise the actual login form, protected redirects, all admin navigation links, user edits, CSV upload/preview/rename/delete, persisted configuration, report download, and logout. They do not modify the local application's accounts or datasets.

## Train with the supplied campaign data

Run `npm run python -- backend/train_model.py` from the project root. This trains and evaluates the conversion model, saves the model and metrics under `backend/artifacts`, and imports the 8,000 supplied leads with out-of-fold predictions into the existing pages. See [data/README.md](data/README.md) for inputs, repeat runs, and limitations.

## User dataset uploads

All signed-in users can open **Upload datasets** in the dashboard (`/dashboard/datasets`). CSV uploads use the authenticated `POST /datasets` endpoint with the same 5 MB, 10,000-row, and 100-column validation as admin uploads. Uploaded files appear in the admin dataset inventory for review. Listing, previewing, renaming, and deleting stored datasets remain admin-only. Uploading does not automatically train a model or replace leads.

Dataset uploads also accept ZIP files containing exactly one CSV (other documentation files are ignored). Both the archive and its uncompressed CSV must be at most 5 MB; CSV row and column limits still apply. Encrypted or invalid ZIPs are rejected.

## Populate channel analytics and budget scenarios

Run `npm run python -- backend/seed_analytics.py` from the project root after importing leads. This updates channel totals from stored lead records and adds 50 illustrative budget scenarios: three 100,000-unit baselines (equal allocation, historical spend mix, and conversion efficiency mix), plus 47 variations in budget and channel emphasis. Repeating the command updates the same named scenarios and channels, preserving unrelated records.

Channel conversion rate is converted lead count / lead count; historical CAC is summed row-level ad spend / converted lead count (null when there are no conversions). This assumes each row's ad spend is additive, as in the imported dataset, not a repeated campaign total. Budget conversions use allocation ? historical conversions / spend for each channel, and CPA is budget / estimated conversions. These are illustrative constant-efficiency projections, not results from the trained conversion model or an RL optimizer. They omit saturation, uncertainty, and changes in channel performance. Source campaign spend is in USD; no exchange-rate conversion is applied.

Refresh admin **Analytics & reports** to see **Channel analytics** and **Budget simulations**. These shared records also appear in the corresponding user dashboard pages.

## Application page coverage

All requested public and marketing pages are linked through the shared login and dashboard. See [page coverage](docs/page-coverage.md) for routes, implemented behavior, model/data limitations, and verification.
