# 📧 OpenPixel — 24/7 Free Server-Hosted Email Tracking Web Service

A lightweight, server-hosted email tracking web service built with **FastAPI**, **SQLAlchemy**, and **Tailwind CSS**. Deployed on 100% zero-cost cloud platforms (**Render** or **PythonAnywhere**) so it operates **24/7/365 without requiring your laptop to stay open or connected to the internet**.

---

## 🌟 Key Features

- **Public `/tracker.gif` Endpoint**: Delivers an invisible 1x1 transparent GIF with aggressive `Cache-Control` (`no-cache, no-store, must-revalidate`) headers to defeat proxy caching.
- **Deep Header Telemetry**:
  - **Accurate IP Resolution**: Handles cloud reverse proxies, Cloudflare (`CF-Connecting-IP`), and multi-hop load balancers (`X-Forwarded-For`).
  - **Device & Client Classification**: Identifies Desktop vs Mobile vs Tablet, Operating System (Windows, macOS, iOS, Android, Linux), and email client.
  - **Email Proxy Detection**: Flags **Gmail Image Proxy** (`GoogleImageProxy`), Apple Mail Privacy Protection (MPP), Outlook Desktop/Web, and Thunderbird.
  - **Exact ISO/UTC Timestamp**: Precise server-side open timestamp.
- **Minimalist Real-Time Dashboard (`/dashboard`)**:
  - Live KPI cards: Total Opens, Unique Recipients, Active Campaigns, 24-Hour Engagement.
  - Auto-refresh live feed (configurable intervals: 5s, 15s, 30s).
  - Search by recipient, IP, campaign, or device.
  - Full inspection modal for raw `User-Agent` and `Referer` headers.
  - **One-Click CSV Export**: Download your complete tracking audit log.
- **Interactive Tracking Tag Generator**:
  - Auto-detects server domain.
  - Instant generation of **HTML `<img>` tags**, **Markdown embed links**, and **direct URLs**.
  - One-click copy-to-clipboard.
  - Built-in "Send Test Ping" button to verify tracking instantly.
- **Zero Cost & Always On**:
  - Deployable on Render Free Web Services or PythonAnywhere Free Tier.
  - Works with local persistent SQLite or free cloud PostgreSQL (Neon / Supabase).

---

## 📁 Project Architecture

```
email-tracker/
├── main.py              # FastAPI application (endpoints, background task logging, CORS)
├── database.py          # SQLAlchemy SQLite / PostgreSQL models & connection logic
├── utils.py             # 43-byte transparent GIF, IP extractor, User-Agent classifier
├── templates/
│   └── dashboard.html   # Minimalist dashboard (Tailwind CSS, Lucide SVG, Vanilla JS)
├── requirements.txt     # Python production dependencies
├── Procfile             # Render / Railway process launcher
├── render.yaml          # Render Blueprint 1-click configuration
├── wsgi.py              # PythonAnywhere WSGI-to-ASGI adapter (a2wsgi)
├── test_tracker.py      # Automated test suite
└── README.md            # Comprehensive documentation
```

---

## 🚀 Deployment Guide (100% Free, 24/7 Operation)

### Option 1: Deploy to Render.com (Recommended)

Render offers a free Web Service tier. To prevent Render's free tier from entering hibernation (sleeping after 15 minutes of inactivity), we configure a free 5-minute health ping.

#### Step 1: Push Code to GitHub
1. Create a free account at [GitHub.com](https://github.com).
2. Create a new repository (e.g., `openpixel-tracker`).
3. In your local terminal, push the `email-tracker` folder:
   ```bash
   cd email-tracker
   git init
   git add .
   git commit -m "Initial commit of OpenPixel email tracker"
   git branch -M main
   git remote add origin https://github.com/<your-username>/openpixel-tracker.git
   git push -u origin main
   ```

#### Step 2: Create Web Service on Render
1. Sign up at [Render.com](https://render.com) (free).
2. Click **New +** -> **Web Service**.
3. Connect your GitHub repository.
4. Configure the settings:
   - **Name**: `openpixel-tracker` (or any unique name)
   - **Language**: `Python 3`
   - **Branch**: `main`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn main:app --host 0.0.0.0 --port $PORT`
   - **Instance Type**: `Free`
5. Click **Create Web Service**. Within 2 minutes, Render will build and deploy your app at:
   `https://openpixel-tracker.onrender.com`

#### Step 3: Keep It Awake 24/7 (Prevent Free Sleep)
Free Render instances spin down after 15 minutes of inactivity. Set up a free external ping to keep it alive 24/7:
1. Go to [cron-job.org](https://cron-job.org) or [UptimeRobot.com](https://uptimerobot.com) (both 100% free).
2. Add a new monitor / cron job:
   - **URL**: `https://openpixel-tracker.onrender.com/health`
   - **Schedule / Interval**: Every **5 minutes** or **10 minutes**
   - **Method**: `GET`
3. Save. Your service will now stay awake and responsive 24/7/365!

*(Optional: Persistent Database on Render)*
While SQLite handles active memory, free container restarts can reset local storage. For permanent cloud storage on Render:
1. Create a free PostgreSQL database at [Neon.tech](https://neon.tech) or [Supabase.com](https://supabase.com).
2. In your Render Dashboard, go to **Environment** -> **Add Environment Variable**:
   - Key: `DATABASE_URL`
   - Value: `postgresql://user:password@host/dbname`
The app automatically detects PostgreSQL and saves all records permanently!

---

### Option 2: Deploy to PythonAnywhere (Always-On SQLite)

PythonAnywhere provides persistent storage out-of-the-box and does not put your web app to sleep.

1. Sign up for a free account at [PythonAnywhere.com](https://www.pythonanywhere.com).
2. Open a **Bash Console** in PythonAnywhere and clone your repository or upload the files:
   ```bash
   git clone https://github.com/<your-username>/openpixel-tracker.git
   cd openpixel-tracker
   pip3.10 install -r requirements.txt --user
   ```
3. Go to the **Web** tab in PythonAnywhere:
   - Click **Add a new web app**.
   - Choose **Manual configuration** -> **Python 3.10** (or 3.11).
4. In the **WSGI configuration file** link (`/var/www/<username>_pythonanywhere_com_wsgi.py`), replace all contents with:
   ```python
   import sys
   import os

   path = '/home/<username>/openpixel-tracker'
   if path not in sys.path:
       sys.path.insert(0, path)

   from a2wsgi import ASGIMiddleware
   from main import app
   application = ASGIMiddleware(app)
   ```
   *(Replace `<username>` with your PythonAnywhere username)*
5. Click the green **Reload** button at the top of the Web tab.
6. Your tracker is now live at `https://<username>.pythonanywhere.com/dashboard` with permanent SQLite storage!

---

## 💻 Running Locally (Development)

1. Clone or navigate to the directory:
   ```bash
   cd email-tracker
   ```
2. Create and activate a virtual environment (optional):
   ```bash
   python -m venv venv
   # Windows:
   venv\Scripts\activate
   # macOS / Linux:
   source venv/bin/activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Run the automated test suite:
   ```bash
   python test_tracker.py
   ```
5. Start the server:
   ```bash
   uvicorn main:app --reload --port 8000
   ```
6. Open your browser:
   - Dashboard: `http://localhost:8000/dashboard`
   - Health check: `http://localhost:8000/health`
   - Interactive API docs (Swagger): `http://localhost:8000/docs`

---

## ✉️ How to Embed Tracking Pixels in Emails

### 1. In Gmail (Web)
1. Open Gmail and click **Compose**.
2. Write your email content.
3. Open your OpenPixel Dashboard and use the **Generate Tracking Pixel** card:
   - Enter Campaign Name: `client_pitch`
   - Enter Recipient: `john@example.com`
4. Copy the generated **Direct Image URL** or **HTML embed**.
5. In Gmail:
   - Click the **Insert photo** icon (bottom toolbar).
   - Switch to the **Web Address (URL)** tab.
   - Paste the direct image URL (`https://your-service.onrender.com/tracker.gif?cid=client_pitch&recipient=john@example.com`).
   - Click **Insert**.
   *(Because the GIF is 1x1 transparent, it is completely invisible to the recipient!)*

### 2. In HTML Email Templates & Newsletters
Paste the HTML snippet right above the closing `</body>` tag:
```html
<img src="https://your-service.onrender.com/tracker.gif?cid=spring_sale&recipient=sarah@acme.com" 
     width="1" height="1" alt="" style="display:none;width:1px;height:1px;border:0;outline:none;" />
```

### 3. In Cold Outreach Tools / Python / Nodemailer
In your mail sending loop, dynamically format the recipient's email address:
```python
tracking_pixel = f'<img src="https://your-service.onrender.com/tracker.gif?cid=march_leads&recipient={recipient_email}" width="1" height="1" style="display:none;" />'
html_email_content += tracking_pixel
```

---

## 🔍 Understanding Email Client Proxies

When tracking emails, modern email clients handle images differently:
1. **Gmail Image Proxy**:
   - Google routes image requests through its own secure image proxies (`GoogleImageProxy`).
   - The IP address logged belongs to Google's proxy network (e.g. Mountain View, CA).
   - OpenPixel detects this and flags the client as `Gmail Image Proxy` with an appropriate badge so you know the open was genuine via Gmail.
2. **Apple Mail Privacy Protection (iOS 15+, macOS Monterey+)**:
   - Apple proxies image requests through iCloud Private Relay servers.
   - OpenPixel classifies these headers so you can differentiate Apple Mail clients from direct browser views.
3. **Outlook & Desktop Clients**:
   - Requests come directly from the recipient's computer/network, capturing their exact public IP address and Windows/macOS operating system.

---

## 🛡️ License & Privacy
Free and open-source under the MIT License. You have complete ownership of your data—no third-party tracking services or data sharing.
