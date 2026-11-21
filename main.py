from fastapi import FastAPI, HTTPException
from pwdlib import PasswordHash
from sqlmodel import Field, Session, SQLModel, create_engine, select

app = FastAPI(title="Task API")

engine = create_engine("sqlite:///taches.db")
hasheur = PasswordHash.recommended()


class Tache(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    titre: str
    terminee: bool = False


class Utilisateur(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    email: str = Field(unique=True, index=True)
    mot_de_passe_hache: str


class UtilisateurCreation(SQLModel):
    email: str
    mot_de_passe: str


class UtilisateurPublic(SQLModel):
    id: int
    email: str


SQLModel.metadata.create_all(engine)


@app.get("/")
def accueil():
    return {"message": "Bienvenue sur Task API"}


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/inscription", response_model=UtilisateurPublic)
def inscription(donnees: UtilisateurCreation):
    with Session(engine) as session:
        existe = session.exec(
            select(Utilisateur).where(Utilisateur.email == donnees.email)
        ).first()
        if existe:
            raise HTTPException(status_code=400, detail="Email déjà utilisé")
        utilisateur = Utilisateur(
            email=donnees.email,
            mot_de_passe_hache=hasheur.hash(donnees.mot_de_passe),
        )
        session.add(utilisateur)
        session.commit()
        session.refresh(utilisateur)
        return utilisateur


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