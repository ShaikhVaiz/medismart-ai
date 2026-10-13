# MediSmart AI — Medicine Reminder & Reorder (starter project)

A Django starter website for personal medicine schedule organisation, stock estimates, family profiles, and local refill request tracking.

## Included and working locally
- Signup, login, logout (Django auth)
- User-owned medicine records and schedules
- Family profiles under the logged-in account
- Daily schedule dashboard
- Taken/skipped log records
- Simple stock decrement when marking a dose taken
- Stock-days estimate and low-stock warning
- Expiry-date warning
- Locally saved refill requests
- Admin panel to add pharmacy directory entries
- Responsive mobile/desktop UI
- Foreground browser notification demo while the dashboard is open

## Not integrated yet
- The refill form does not send a request to a real pharmacy.
- No online medicine catalogue, payment, delivery or prescription verification.
- No SMS/WhatsApp/email/push notification provider.
- Browser reminders are not guaranteed when the browser/device is closed.
- No AI/LLM, prescription OCR or clinical interaction checker is connected.
- Family profiles are owned by one account; caregiver invitations/shared login are not implemented.
- Stock decrement uses one unit per "Taken" click as a demo. Adjust it to your prescribed unit quantity and schedule before real-world use.

## Requirements
- Python 3.10+ recommended
- Internet only needed to install Django; Google Fonts are optional and can be removed from `static/tracker/style.css`.

## Windows setup
Open Command Prompt or PowerShell in the extracted `medismart_ai` folder:

```powershell
py -m venv .venv
.venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt
python manage.py makemigrations tracker
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Open http://127.0.0.1:8000/

- Create a normal account from the website.
- Visit `/admin/` to sign in with the superuser and add Pharmacy entries.
- In the app, add a medicine, stock quantity, daily usage and schedule times such as `08:00, 20:00`.
- Click “Enable browser alerts” on the dashboard and allow notifications. Keep the dashboard open to test reminders.

## Notes before public deployment
This is a learning/demo starter, not a certified medical device or pharmacy platform. Do not enter real patient data until the deployment has been security-reviewed. Use HTTPS, environment-based secrets, `DEBUG=False`, proper `ALLOWED_HOSTS`, backups, secure file handling and a production server. Run `python manage.py check --deploy` after production settings are configured. Review local laws and professional requirements before adding real pharmacy ordering or prescription workflows.

## Planned roadmap
1. Core medicine tracking and account isolation (included)
2. Improve dose quantity/stock reconciliation and tests
3. PWA service worker + push notification provider
4. Caregiver invitations and permission management
5. Pharmacy API/partner portal and order status webhooks
6. OCR with manual verification
7. AI assistant restricted to safe app-navigation and sourced medicine information
8. Production PostgreSQL, monitoring, backups and security review
