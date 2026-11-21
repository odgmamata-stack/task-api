from fastapi import FastAPI, HTTPException
from sqlmodel import Field, Session, SQLModel, create_engine, select

app = FastAPI(title="Task API")

engine = create_engine("sqlite:///taches.db")


class Tache(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    titre: str
    terminee: bool = False


SQLModel.metadata.create_all(engine)


@app.get("/")
def accueil():
    return {"message": "Bienvenue sur Task API"}


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/taches")
def creer_tache(tache: Tache):
    with Session(engine) as session:
        session.add(tache)
        session.commit()
        session.refresh(tache)
        return tache


@app.get("/taches")
def lister_taches():
    with Session(engine) as session:
        return session.exec(select(Tache)).all()


@app.get("/taches/{tache_id}")
def lire_tache(tache_id: int):
    with Session(engine) as session:
        tache = session.get(Tache, tache_id)
        if not tache:
            raise HTTPException(status_code=404, detail="Tâche introuvable")
        return tache


@app.put("/taches/{tache_id}")
def modifier_tache(tache_id: int, donnees: Tache):
    with Session(engine) as session:
        tache = session.get(Tache, tache_id)
        if not tache:
            raise HTTPException(status_code=404, detail="Tâche introuvable")
        tache.titre = donnees.titre
        tache.terminee = donnees.terminee
        session.add(tache)
        session.commit()
        session.refresh(tache)
        return tache


@app.delete("/taches/{tache_id}")
def supprimer_tache(tache_id: int):
    with Session(engine) as session:
        tache = session.get(Tache, tache_id)
        if not tache:
            raise HTTPException(status_code=404, detail="Tâche introuvable")
        session.delete(tache)
        session.commit()
        return {"message": "Tâche supprimée"}