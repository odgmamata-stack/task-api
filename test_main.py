import os
import uuid

os.environ["DATABASE_URL"] = "sqlite:///test_taches.db"

from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def email_unique():
    return f"{uuid.uuid4().hex[:8]}@example.com"


def creer_compte_et_jeton():
    email = email_unique()
    mot_de_passe = "MotDePasseTest123"
    client.post("/inscription", json={"email": email, "mot_de_passe": mot_de_passe})
    reponse = client.post(
        "/connexion", data={"username": email, "password": mot_de_passe}
    )
    jeton = reponse.json()["access_token"]
    return {"Authorization": f"Bearer {jeton}"}


def test_health():
    reponse = client.get("/health")
    assert reponse.status_code == 200
    assert reponse.json() == {"status": "ok"}


def test_inscription_email_deja_utilise():
    donnees = {"email": email_unique(), "mot_de_passe": "MotDePasseTest123"}
    assert client.post("/inscription", json=donnees).status_code == 200
    assert client.post("/inscription", json=donnees).status_code == 400


def test_connexion_mauvais_mot_de_passe():
    email = email_unique()
    client.post("/inscription", json={"email": email, "mot_de_passe": "Correct123"})
    reponse = client.post(
        "/connexion", data={"username": email, "password": "Mauvais123"}
    )
    assert reponse.status_code == 401


def test_taches_sans_connexion():
    assert client.get("/taches").status_code == 401


def test_creer_et_lister_tache():
    entetes = creer_compte_et_jeton()
    reponse = client.post("/taches", json={"titre": "Test"}, headers=entetes)
    assert reponse.status_code == 200
    assert reponse.json()["titre"] == "Test"
    liste = client.get("/taches", headers=entetes).json()
    assert len(liste) == 1


def test_modifier_et_supprimer_tache():
    entetes = creer_compte_et_jeton()
    tache = client.post("/taches", json={"titre": "A faire"}, headers=entetes).json()
    url = f"/taches/{tache['id']}"
    modifiee = client.put(
        url, json={"titre": "A faire", "terminee": True}, headers=entetes
    )
    assert modifiee.json()["terminee"] is True
    assert client.delete(url, headers=entetes).status_code == 200
    assert client.get(url, headers=entetes).status_code == 404


def test_un_utilisateur_ne_voit_pas_les_taches_des_autres():
    entetes_a = creer_compte_et_jeton()
    entetes_b = creer_compte_et_jeton()
    tache = client.post("/taches", json={"titre": "Privee"}, headers=entetes_a).json()
    reponse = client.get(f"/taches/{tache['id']}", headers=entetes_b)
    assert reponse.status_code == 404