from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.metrics.pairwise import cosine_similarity

# --- 1) Load & merge data at startup ---
df_stats = pd.read_json("static/player_stats.json")
df_meta  = pd.read_json("static/player_metadata.json")

df = df_stats.merge(
    df_meta[['PlayerID','Name','PrimaryPosition','Team','Age','MarketValue']],
    on='PlayerID', how='left'
)
df['Name'] = df['Name'].fillna(df['Player'])
df['PrimaryPosition'] = df['PrimaryPosition'].fillna('')
df['Team'] = df['Team'].fillna('')  
df['MarketValue'] = df['MarketValue'].fillna('—')
df['Age'] = df['Age'].fillna(0) 

# --- 2) Metrics by position ---
metrics_by_position = {
    "forward": [
        "Goals","Expected Goals (xG)","Assists","Expected Assists (xA)",
        "Shots (per match)","Shots on Target (per match)",
        "Big Chances Created","Big Chances Missed","Penalties Awarded",
        "Successful Dribbles (per match)","Possession Won Final 3rd (per match)"
    ],
    "midfield": [
        "Goals","Assists","Expected Assists (xA)",
        "Big Chances Created","Accurate Long Balls (per match)",
        "Successful Dribbles (per match)","Possession Won Final 3rd (per match)",
        "Successful Tackles (per match)","Interceptions (per match)",
        "Blocks (per match)","Fouls (per match)"
    ],
    "defense": [
        "Successful Tackles (per match)","Clearances (per match)",
        "Interceptions (per match)","Blocks (per match)",
        "Fouls (per match)","Yellow Card","Red Card"
    ],
    "goalkeeper": [
        "Saves (per match)","Save Percentage",
        "Clean Sheets","Goals Conceded (per match)","Goals Prevented"
    ]
}
ALL_METRICS = sorted({m for mets in metrics_by_position.values() for m in mets})

# --- 3) Z-score normalization once ---
scaler = StandardScaler()
z_scores = pd.DataFrame(
    scaler.fit_transform(df[ALL_METRICS].fillna(0)),
    columns=ALL_METRICS,
    index=df.index
)

def parse_market_value(v):
    if pd.isna(v):
        return np.nan
    if isinstance(v, (int, float)):
        return float(v)
    s = str(v).strip().lower().replace('€','').replace('$','').replace(',','').replace(' ','')
    if s in {'', '—', '-'}:
        return np.nan
    mult = 1.0
    if s.endswith('m'):
        mult = 1e6; s = s[:-1]
    elif s.endswith('k'):
        mult = 1e3; s = s[:-1]
    try:
        return float(s) * mult
    except:
        return np.nan

df['MarketValueNum'] = df['MarketValue'].apply(parse_market_value)

def get_position_group(label: str) -> str:
    p = label.lower()
    if 'keeper' in p:                return 'goalkeeper'
    if 'midfield' in p:              return 'midfield'
    if 'back' in p or 'defender' in p:return 'defense'
    if any(x in p for x in ['winger','striker','forward']): return 'forward'
    return 'midfield'

# --- 4) Similarity calculation ---
def compute_similar_players(player_name: str, top_n: int = 15,
                            age_max: int | None = None,
                            value_max: float | None = None) -> pd.DataFrame:
    if player_name not in df['Name'].values:
        raise ValueError(f"Player '{player_name}' not found.")
    idx = int(df.index[df['Name'] == player_name][0])
    group   = get_position_group(df.at[idx, 'PrimaryPosition'])
    metrics = metrics_by_position[group]

    # Aday havuzu (kendisi hariç)
    candidates = df.index.tolist()
    candidates = [i for i in candidates if i != idx]

    if age_max is not None:
        candidates = [i for i in candidates
                      if (pd.notna(df.at[i,'Age']) and df.at[i,'Age'] > 0 and df.at[i,'Age'] <= age_max)]

    if value_max is not None:
        candidates = [i for i in candidates
                      if (pd.notna(df.at[i,'MarketValueNum']) and df.at[i,'MarketValueNum'] > 0 and df.at[i,'MarketValueNum'] <= value_max)]

    if not candidates:
        return pd.DataFrame(columns=['Name','Age','Team','PrimaryPosition','MarketValue','Similarity'])

    # Yalnızca filtrelenmiş adaylar üzerinden benzerlik
    mat = z_scores.loc[candidates, metrics].fillna(0.0)
    vec = z_scores.loc[[idx], metrics].fillna(0.0)
    sims = cosine_similarity(mat, vec).flatten()
    sims = np.nan_to_num(sims, nan=0.0, posinf=0.0, neginf=0.0)

    order = np.argsort(-sims)[:top_n]
    chosen_idx = [candidates[i] for i in order]

    df_sim = df.loc[chosen_idx, ['Name','Age','Team','PrimaryPosition','MarketValue']].copy()
    df_sim['Similarity'] = sims[order]
    df_sim['Similarity'] = df_sim['Similarity'].fillna(0.0)
    df_sim['Team'] = df_sim['Team'].fillna('')
    df_sim['PrimaryPosition'] = df_sim['PrimaryPosition'].fillna('')
    return df_sim.reset_index(drop=True)

# --- 5) FastAPI setup ---
app = FastAPI()

@app.get("/")
def read_index():
    return FileResponse("static/index.html")

@app.get("/players/search")
def search_players(q: str = Query(..., description="Name substring")):
    matches = df[df['Name'].str.contains(q, case=False)]
    return [{"Name": name} for name in matches['Name'].tolist()]

@app.get("/players/similar")
def similar_endpoint(
    player_name: str = Query(..., description="Exact player name"),
    top_n: int       = Query(10, description="Number of similar players"),
    age_max: int | None = Query(None, description="Max age (inclusive)"),
    value_max: str | None = Query(None, description="Max market value (e.g., 25m, 800k, 12000000)")
):
    try:
        v_max = parse_market_value(value_max) if value_max is not None else None
        df_sim = compute_similar_players(player_name, top_n, age_max=age_max, value_max=v_max)
        return df_sim.to_dict(orient="records")
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")

app.mount(
    "/static",
    StaticFiles(directory="static", html=True),
    name="static"
)
