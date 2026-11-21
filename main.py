import os
from datetime import datetime, timedelta, timezone

import jwt
from fastapi import Depends, FastAPI, HTTPException
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pwdlib import PasswordHash
from sqlmodel import Field, Session, SQLModel, create_engine, select

app = FastAPI(title="Task API")

engine = create_engine("sqlite:///taches.db")
hasheur = PasswordHash.recommended()

SECRET_KEY = os.environ.get("SECRET_KEY", "cle-de-developpement-a-changer")
ALGORITHME = "HS256"
DUREE_JETON_MINUTES = 60
schema_oauth2 = OAuth2PasswordBearer(tokenUrl="connexion")


class Utilisateur(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    email: str = Field(unique=True, index=True)
    mot_de_passe_hache: str


class Tache(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    titre: str
    terminee: bool = False
    proprietaire_id: int = Field(foreign_key="utilisateur.id")


class TacheDonnees(SQLModel):
    titre: str
    terminee: bool = False


class UtilisateurCreation(SQLModel):
    email: str
    mot_de_passe: str


class UtilisateurPublic(SQLModel):
    id: int
    email: str


SQLModel.metadata.create_all(engine)


def creer_jeton(utilisateur_id: int) -> str:
    expiration = datetime.now(timezone.utc) + timedelta(minutes=DUREE_JETON_MINUTES)
    contenu = {"sub": str(utilisateur_id), "exp": expiration}
    return jwt.encode(contenu, SECRET_KEY, algorithm=ALGORITHME)


def utilisateur_courant(jeton: str = Depends(schema_oauth2)) -> Utilisateur:
    erreur = HTTPException(
        status_code=401,
        detail="Jeton invalide ou expiré",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        contenu = jwt.decode(jeton, SECRET_KEY, algorithms=[ALGORITHME])
        utilisateur_id = int(contenu["sub"])
    except (jwt.InvalidTokenError, KeyError, ValueError):
        raise erreur
    with Session(engine) as session:
        utilisateur = session.get(Utilisateur, utilisateur_id)
    if not utilisateur:
        raise erreur
    return utilisateur


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


@app.post("/connexion")
def connexion(formulaire: OAuth2PasswordRequestForm = Depends()):
    with Session(engine) as session:
        utilisateur = session.exec(
            select(Utilisateur).where(Utilisateur.email == formulaire.username)
        ).first()
    if not utilisateur or not hasheur.verify(
        formulaire.password, utilisateur.mot_de_passe_hache
    ):
        raise HTTPException(status_code=401, detail="Email ou mot de passe incorrect")
    return {"access_token": creer_jeton(utilisateur.id), "token_type": "bearer"}


@app.post("/taches")
def creer_tache(
    donnees: TacheDonnees, utilisateur: Utilisateur = Depends(utilisateur_courant)
):
    with Session(engine) as session:
        tache = Tache(
            titre=donnees.titre,
            terminee=donnees.terminee,
            proprietaire_id=utilisateur.id,
        )
        session.add(tache)
        session.commit()
        session.refresh(tache)
        return tache


@app.get("/taches")
def lister_taches(utilisateur: Utilisateur = Depends(utilisateur_courant)):
    with Session(engine) as session:
        return session.exec(
            select(Tache).where(Tache.proprietaire_id == utilisateur.id)
        ).all()


@app.get("/taches/{tache_id}")
def lire_tache(
    tache_id: int, utilisateur: Utilisateur = Depends(utilisateur_courant)
):
    with Session(engine) as session:
        tache = session.get(Tache, tache_id)
        if not tache or tache.proprietaire_id != utilisateur.id:
            raise HTTPException(status_code=404, detail="Tâche introuvable")
        return tache


@app.put("/taches/{tache_id}")
def modifier_tache(
    tache_id: int,
    donnees: TacheDonnees,
    utilisateur: Utilisateur = Depends(utilisateur_courant),
):
    with Session(engine) as session:
        tache = session.get(Tache, tache_id)
        if not tache or tache.proprietaire_id != utilisateur.id:
            raise HTTPException(status_code=404, detail="Tâche introuvable")
        tache.titre = donnees.titre
        tache.terminee = donnees.terminee
        session.add(tache)
        session.commit()
        session.refresh(tache)
        return tache


@app.delete("/taches/{tache_id}")
def supprimer_tache(
    tache_id: int, utilisateur: Utilisateur = Depends(utilisateur_courant)
):
    with Session(engine) as session:
        tache = session.get(Tache, tache_id)
        if not tache or tache.proprietaire_id != utilisateur.id:
            raise HTTPException(status_code=404, detail="Tâche introuvable")
        session.delete(tache)
        session.commit()
        return {"message": "Tâche supprimée"}