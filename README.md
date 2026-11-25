# 💡 Nuru

Jobs, internships and scholarships portal for Uganda. Streamlit + SQLite.

## Features
- Home, Find Jobs (search, filters, sort, details popup), Post a Job, Dashboard, Login/Register, About
- **Excel upload**: same layout as `data/hub_repo.xlsx` (`path, title, url, details`) - parsed into company, location, deadline, type automatically
- **Dashboard**: every posted job appears in a list (close / reopen / delete), plus applications received
- Roles: candidate, employer, admin (admin sees every listing)

## Design assets
- `static/` - your photos, resized for web (served at `/app/static/...`; needs `enableStaticServing = true` in `.streamlit/config.toml`, already set)
- `icons.py` - Lucide icons (lucide.dev), inlined as SVG; swap or add icons in `ICONS`
- Home hero = auto-rotating photo background; "Built for every step" = swipeable carousel (arrows, dots, keyboard, pause on hover)

## Design
White canvas, high-contrast text (WCAG AA), Inter + Poppins, card-based layout with visible description excerpts,
company avatars, deadline countdown chips, hover elevation, category tiles, photo hero + carousel, Lucide icons.
Theme tokens live in `theme_css()` in `app.py`; brand colour is `PURPLE`.

## Live numbers and Excel sync
Every figure on the home page (job/scholarship/organisation counts, "open" counts, category tiles, featured jobs, top organisations)
is read from the database on each view, so new posts and uploads show up immediately.
Dashboard > Bulk upload & export > **Export in hub_repo.xlsx format** gives you the sheet back in the original
`path, title, url, details` layout, including jobs posted in the app. Commit it over `data/hub_repo.xlsx` to make it the new seed.

## WhatsApp
Floating button on every page, footer link, About page, and "Ask / Share on WhatsApp" in each listing popup.
Number is `0791144968` (wa.me/256791144968). Change it with the `NURU_WHATSAPP` secret (international format, no +).

## Run locally
```bash
pip install -r requirements.txt
streamlit run app.py
```

## Deploy
1. Create a GitHub repo, then:
   ```bash
   git init && git add . && git commit -m "Nuru"
   git branch -M main
   git remote add origin https://github.com/<you>/nuru.git
   git push -u origin main
   ```
2. Go to https://share.streamlit.io > **Create app** > pick the repo, branch `main`, main file `app.py` > Deploy.
3. App settings > **Secrets**: `ADMIN_EMAILS = "your@email.com"`. Register with that email to become admin.

## Excel format
| path | title | url | details |
|---|---|---|---|
| Jobs/Banks & Finance | Exim Bank - Credit Officer | https://... | Kampala. Closes 16 Oct 2026. Degree in... |
| Scholarships/Open now | Chevening Scholarships (UK Government) | https://... | Deadline 1 Nov 2026. ... |

Optional richer columns also work: `type, company, category, job_type, work_mode, location, salary_min, salary_max, currency, deadline, description, apply_email`.

## Important: data persistence
Streamlit Community Cloud's disk is **temporary**. `data/nuru.db` resets when the app is redeployed or rebooted;
it is re-seeded from `data/hub_repo.xlsx`, but jobs/users/applications created in the app are lost.
Download backups from Dashboard > Bulk upload & export, or move storage to a hosted database
(Supabase/Postgres or Google Sheets) - only `db.py` needs to change.
