# Vosouš API (FastAPI)
API pro webovou aplikaci na učení slovíček cizího jazyka ve formě kvízu.

## Funkce
- Seznam slovíček s překladem
- Náhodné slovíčko s překladem
- Detail jednoho slovíčka
- Založení nového slovíčka s překladem

## Technologie
- Python 3.12+
- Fastapi
- Pydantic
- DB: PostgreSQL


## Rychlý start

### Klon a instalace
```bash
git clone <repo-url>
cd <repo>
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```
### .env
```
API_ACCESS_URL = ["http://localhost:8501"]
# Database
SUPABASE_URL = url k PostgreSQL
SUPABASE_ANON_KEY = ANON Key database
```

### Start
```bash
uvicorn app.main:app --reload
```

# Endpointy:
SWAGGER
```url
http://127.0.0.1:8000/docs
```

## Health
- GET /health - stav služby
## Word
- GET /words/{language_from}/{language_to} - seznam slovíček pro určitý jazyky
- GET /word/{word_id} - detail jednoho slova
- POST /word - založení nového sloíčka s překladem
- GET /word/random/{id_seed} - vrací náhodné slovíčko z databáze
