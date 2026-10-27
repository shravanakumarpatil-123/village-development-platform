# Gram Setu — Frontend

React app (built with Vite) that talks to your FastAPI backend.

## Setup

1. Make sure your backend is running first (`uvicorn app.main:app --reload` from the `Backend` folder).
2. Open a terminal in this `Frontend` folder and run:
   ```
   npm install
   npm run dev
   ```
3. Open the URL it prints — usually `http://localhost:5173`.

## Notes
- `.env` has `VITE_API_URL` pointing at `http://127.0.0.1:8000` — change if your backend runs elsewhere.
- Official accounts require the `OFFICIAL_REGISTRATION_CODE` set in the backend's `.env`.
- Citizens set a village at registration; officials see a "Villages" overview first, then drill into each village's complaints.
