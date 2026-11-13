from fastapi import FastAPI

app = FastAPI(title="Task API")


@app.get("/")
def accueil():
    return {"message": "Bienvenue sur Task API"}


@app.get("/health")
def health():
    return {"status": "ok"}