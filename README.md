# Metin2 Market Scanner

Metin2 Market Scanner is a full-stack application designed to analyze and track item prices in the Metin2 game. It scrapes market data to provide users with insights, price history, and current listings for various in-game items.

## 🚀 Features

- **Automated Scraping:**  Uses Playwright and BeautifulSoup to scrape current market listings.
- **Market Analysis:**  Tracks item prices (Won/Yang) and listings over time.
- **Search & Filtering:**  Search for specific items and filter by server (e.g., Marmara).
- **Price History:**  View historical price trends for items.
- **Top Items:**  See the most frequently listed items.
- **Modern UI:**  Responsive web interface built with Next.js and Tailwind CSS.

## 🛠️ Tech Stack

### Backend
- **Framework:** FastAPI (Python)
- **Database:** SQLite
- **Scraping:** Playwright, BeautifulSoup4
- **ORM:** SQLAlchemy
- **Task Scheduling:** `schedule` library (for automated scraping tasks)

### Frontend
- **Framework:** Next.js (React)
- **Styling:** Tailwind CSS
- **HTTP Client:** Axios
- **Charts:** Chart.js / react-chartjs-2
- **Icons:** Lucide React

## 📂 Project Structure

```
metin2-marketscanner/
├── backend/            # FastAPI backend & Scraper
│   ├── database/       # DB schema and storage
│   ├── routers/        # API endpoints
│   ├── main.py         # App entry point
│   ├── scraper.py      # Core scraping logic
│   └── ...
├── frontend/           # Next.js Frontend
│   ├── app/            # App router pages
│   ├── components/     # UI Components
│   └── ...
└── data/               # SQLite database file location
```

## ⚡ Getting Started

### Prerequisites
- Python 3.8+
- Node.js 18+
- npm or yarn

### 1. Backend Setup

Navigate to the backend folder and install dependencies:

```bash
cd backend
pip install -r ../requirements.txt
```

Create a `.env` file in the `backend/` directory (or rename `.env.example`):

```bash
cp .env.example .env
```

Start the FastAPI server:

```bash
uvicorn main:app --reload
```
The API will run at `http://localhost:8000`.

### 2. Frontend Setup

Navigate to the frontend folder and install dependencies:

```bash
cd frontend
npm install
```

Start the development server:

```bash
npm run dev
```
The application will be available at `http://localhost:3000`.

## 🔒 Security Note

This project uses environment variables for configuration. Ensure you set up your `.env` file correctly in the backend directory. `ALLOWED_ORIGINS` should be set to your frontend's URL (default: `http://localhost:3000`) to prevent CORS issues.

## 📝 License

[MIT](LICENSE)
