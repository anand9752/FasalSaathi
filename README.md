# 🌾 FasalSaathi - Backend API 🚀

![Python](https://img.shields.io/badge/Python-3.10+-blue?style=for-the-badge&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi)
![SQLite](https://img.shields.io/badge/SQLite-07405E?style=for-the-badge&logo=sqlite&logoColor=white)
![Gemini AI](https://img.shields.io/badge/Gemini_AI-8E75B2?style=for-the-badge&logo=google&logoColor=white)
![Pydantic](https://img.shields.io/badge/Pydantic-E92063?style=for-the-badge&logo=pydantic&logoColor=white)
![Uvicorn](https://img.shields.io/badge/Uvicorn-499848?style=for-the-badge&logo=uvicorn&logoColor=white)

> The robust backend service powering **FasalSaathi**, a next-generation AI-powered smart farming dashboard. This RESTful API handles secure user authentication, complex farm & crop relational data, background cron jobs for weather/market alerts, and asynchronous AI-driven crop recommendations.

![FasalSaathi Backend API Workflow](https://via.placeholder.com/1000x400.gif?text=Backend+API+Workflow+Animation)

---

## 🎯 About

The **FasalSaathi Backend** is engineered with Python 3.10+ and the **FastAPI** framework, ensuring extreme high performance and automatic interactive API documentation. It serves as the central brain of the FasalSaathi ecosystem, interfacing with a SQLite database via SQLAlchemy ORM, and orchestrating interactions with external intelligence like Google's Gemini AI, OpenWeatherMap, and APMC Market APIs.

---

## ✨ Core Features

* **🔐 JWT-based Authentication:** Secure, stateless user sessions with hashed passwords (bcrypt) and short-lived access tokens.
* **🌱 Relational Farm & Crop Management:** Comprehensive CRUD operations allowing farmers to manage multiple land parcels, track crop life cycles, and log historical yield data.
* **🧪 Soil Health & Telemetry Tracking:** APIs to log and analyze temporal data for NPK values, pH, moisture, and temperature.
* **🧠 AI Insights & Conversational Agent (`Ask Sathi`):** Context-aware interactions powered by Google Gemini, capable of providing real-time agricultural advice, pest control strategies, and yield predictions.
* **🌦️ Advanced Weather Integration:** Aggregates and normalizes localized, real-time weather and rainfall data to assist in irrigation scheduling.
* **📈 Market Analytics & Inventory Ledger:** Tracks local market prices, generates historical trend analysis, and manages farm inventory (seeds, fertilizers, equipment).
* **⚙️ Background Task Scheduling:** Automated cron-style jobs using APScheduler to trigger market price drops or severe weather alerts.
* **🔔 Real-time Notifications:** WebSockets/Polling endpoints to push crucial notifications directly to the client.

---

## 🏗️ System Architecture & Project Structure

<details>
<summary><b>Click to explore Directory Structure</b></summary>

```text
FasalSaathi/
├── .env.example             # Template for environment variables
├── requirements.txt         # Python dependencies
├── runtime.txt              # Deployment python version
├── app/                     # Main Application Module
│   ├── main.py              # FastAPI application instance & lifecycle events
│   ├── api/                 # API Routers (Controllers)
│   │   ├── router.py        # Master router aggregator
│   │   └── routes/          # Domain-specific route handlers (auth, crops, farms...)
│   ├── core/                # Core configurations
│   │   ├── config.py        # Pydantic Settings management
│   │   └── security.py      # JWT encoding/decoding, password hashing
│   ├── db/                  # Database connectivity
│   │   └── session.py       # SQLAlchemy engine & session maker
│   ├── models/              # SQLAlchemy ORM Models (Entities)
│   ├── schemas/             # Pydantic Models (DTOs - Data Transfer Objects)
│   └── services/            # Business Logic & 3rd Party Integrations
│       ├── ask_sathi/       # Gemini AI chat orchestration
│       ├── weather_alert.py # APScheduler tasks for weather
│       ├── market_alert.py  # APScheduler tasks for market prices
│       └── seed.py          # Database seeding scripts
└── data/                    # SQLite database files (local dev)
```

</details>

<details>
<summary><b>Database Entity Relationship (Overview)</b></summary>

| Model | Description | Relations |
| :--- | :--- | :--- |
| **User** | System users (farmers) | 1:N Farms, 1:N Notifications |
| **Farm** | Physical land parcels | 1:N Crops, 1:N SoilTests, 1:N Inventory |
| **Crop** | Active or historical crops | N:1 Farm, 1:N CalendarEvents |
| **SoilTest** | Ph, NPK, Moisture logs | N:1 Farm |
| **Inventory** | Stock management | N:1 Farm |
| **Notification**| User alerts | N:1 User |

</details>

---

## 🚀 Development Workflow

<details>
<summary><b>Setup & Installation Guide</b></summary>

### 1. Prerequisites
* Python 3.10+
* `pip` and `virtualenv`

### 2. Environment Setup
```bash
# Clone the repository
git clone <your-repo-url>
cd FasalSaathi

# Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate      # Linux/macOS
# .venv\Scripts\activate       # Windows

# Install required packages
pip install -r requirements.txt
```

### 3. Configuration
Copy the `.env.example` file to a new `.env` file and populate it with your specific API keys and secrets:
```bash
cp .env.example .env
```

**Required `.env` variables:**
```env
APP_ENV=development
API_PREFIX=/api/v1
SECRET_KEY=generate_a_strong_random_string_here
ACCESS_TOKEN_EXPIRE_MINUTES=1440
GEMINI_API_KEY=your_google_gemini_api_key
WEATHER_API_KEY=your_openweather_api_key
```

### 4. Running the Development Server
```bash
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```
*The `--reload` flag enables auto-reloading upon code changes.*

</details>

---

## 📚 API Documentation

FastAPI automatically generates OpenAPI schemas. Access interactive API documentation via your browser once the server is running:

| Documentation Type | URL Path |
| :--- | :--- |
| **Swagger UI** (Interactive testing) | [`http://127.0.0.1:8000/docs`](http://127.0.0.1:8000/docs) |
| **ReDoc** (Static read-only) | [`http://127.0.0.1:8000/redoc`](http://127.0.0.1:8000/redoc) |

### Endpoints Overview
* **`POST /api/v1/auth/token`**: OAuth2 compatible token login.
* **`GET /api/v1/users/me`**: Retrieve current authenticated user profile.
* **`CRUD /api/v1/farms`**: Manage farm profiles.
* **`CRUD /api/v1/crops`**: Manage crop lifecycles.
* **`POST /api/v1/crops/disease-detection`**: Accepts multipart/form-data image uploads for AI disease diagnosis.
* **`GET /api/v1/weather/current`**: Proxy and normalize OpenWeather API data.
* **`POST /api/v1/ask-sathi/ask-sathi`**: Submits user queries and chat history to the Gemini Language Model pipeline.

---

## 🛠️ Contributing

1. Create a feature branch: `git checkout -b feature/my-new-feature`
2. Ensure you format code using `black` and adhere to `flake8` standards.
3. Keep business logic strictly inside the `app/services/` directory; keep `routers` thin.
4. Update Pydantic schemas in `app/schemas/` when modifying API contracts.
5. Submit a Pull Request outlining your changes.

---
*Developed with ❤️ and Python for smarter, data-driven farming.*
