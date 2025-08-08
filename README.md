# 🎯 Player Similarity Calculator

A web application for finding **similar football players** based on their statistics and visually comparing them using **position-specific metrics**.

- **Frontend:** HTML, TailwindCSS, Chart.js  
- **Backend:** FastAPI, Pandas, scikit-learn  
- **Data:** `player_stats.json` (statistics) + `player_metadata.json` (identity info)

---

## 🚀 Features

- **Search with live suggestions** for quick player selection
- **Cosine similarity** with **z-score normalization** for similarity calculation
- **Position-specific metrics** for accurate comparison
- **Radar chart** to visualize two players' metrics
- **Filters:**
  - Maximum age
  - Maximum market value (`25m`, `800k` format)
- Player photos and basic information display

---

## 🗂 Project Structure
```
├── static/
│ ├── index.html # Frontend main file
│ ├── player_stats.json # Player statistics data
│ ├── player_metadata.json # Player identity data
├── main.py # FastAPI backend
└── README.md # Project documentation
```
---

## ⚙️ Installation & Run

### 1️⃣ Install dependencies
pip install fastapi uvicorn pandas numpy scikit-learn

### 2️⃣ Start the server
uvicorn main:app --reload

### 3️⃣ Open in browser
http://127.0.0.1:8000/

---

## 🔄 How It Works

1. **Frontend** (`index.html`)
   - Loads player statistics and metadata from `/static` directory.
   - Allows searching for a player with live suggestions.
   - Lets users set optional filters (maximum age, maximum market value).
   - Sends a request to the backend `/players/similar` endpoint to get the most similar players.

2. **Backend** (`main.py`)
   - Reads `player_stats.json` and `player_metadata.json` and merges them using `PlayerID`.
   - Assigns a **position group** (forward, midfield, defense, goalkeeper) for each player.
   - Selects the relevant metrics for the player's position.
   - Normalizes metric values using **z-score normalization**.
   - Calculates **cosine similarity** between the selected player and all other players.

3. **Visualization**
   - The frontend displays the similar players in a **table** (with avatar, name, age, position, team, market value, similarity score).
   - A **radar chart** compares the selected player with the chosen similar player.

---

## 📌 API Endpoints

### `/`
- **GET** — Returns the main page (`index.html`).

### `/players/search`
- **GET** — Searches for players by name substring.  
- **Parameters:**
  - `q` *(string, required)* — Substring of the player name to search for.

### `/players/similar`
- **GET** — Returns a list of similar players for the given player.  
- **Parameters:**
  - `player_name` *(string, required)* — Exact name of the player.
  - `top_n` *(int, optional, default=10)* — Number of similar players to return.
  - `age_max` *(int, optional)* — Maximum age filter.
  - `value_max` *(string, optional)* — Maximum market value (`25m`, `800k`, etc.).

---

## 📈 Technologies Used

- **Backend:** [FastAPI](https://fastapi.tiangolo.com/), [pandas](https://pandas.pydata.org/), [numpy](https://numpy.org/), [scikit-learn](https://scikit-learn.org/)
- **Frontend:** [TailwindCSS](https://tailwindcss.com/), [Chart.js](https://www.chartjs.org/)
- **Data Format:** JSON

---

## 📄 License

This project is licensed under the [MIT](LICENSE) License.

---
