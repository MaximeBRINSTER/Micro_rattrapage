from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from typing import Tuple
from fastapi.security import HTTPBasic
import os

app = FastAPI()
security = HTTPBasic()


def authenticate(username: str, password: str) -> bool:
    with open("Credentials.txt", "r") as f:
        lines = f.readlines()

    for line in lines:

        user, pw = line.strip().split(":")

        if user == username and pw == password:
            return True
        
    return False

def create_file(file_path: str) -> str:
    # Analyser l'url pour obtenir le nom du fichier et le chemin d'accès
    file_path_parts = file_path.split("/")
    file_name = file_path_parts[-1]
    file_path_parts = file_path_parts[:-1]

    # Créer les dossiers si nécesssaire
    user_folder = os.path.expanduser("~")
    for folder in file_path_parts:
        user_folder = os.path.join(user_folder, folder)
        if not os.path.exists(user_folder):
            os.mkdir(user_folder)
    
    # Créer le fichier dans le dossier spécifié 
    file_location = os.path.join(user_folder, file_name)
    if os.path.exists(file_location):
        os.remove(file_location)
    open(file_location, 'a').close()

    return f"Le fichier {file_name} a été créé dans le dossier {user_folder}"

def get_file_location(file_path: str) -> str:
    # Analyser l'url pour obtenir le nom du fichier et le chemin d'accès
    file_path_parts = file_path.split("/")
    file_name = file_path_parts[-1]
    file_path_parts = file_path_parts[:-1]

    # Obtenir le chemin d'accès complet du dossier
    user_folder = os.path.expanduser("~")
    for folder in file_path_parts:
        user_folder = os.path.join(user_folder, folder)
    
    # Obtenir le chemin d'accès complet du fichier
    file_location = os.path.join(user_folder, file_name)
    return file_location

# Créer un nouveau compte utilisateur

@app.post("/user/signup")
async def signup(username: str, password: str):
    # Vérification
    with open("Credentials.txt", "r") as f:
        lines = f.readlines()

    for line in lines:
        if line.startswith(username):
            raise HTTPException(status_code=400, detail="Nom d'utilisateur déjà existant")
    
    with open("Credentials.txt", "a") as f:
        f.write(f"{username}:{password}\n")

@app.get("/user/whoami")
async def get_user_infos(username: str, password: str) -> Tuple[str, str]:
    if authenticate(username, password):
        return (username, password)
    else:
        raise HTTPException(status_code=401, detail="Authentification invalide")

@app.put("/files/{filename:path}")
async def upload_file(filename: str, username: str, password: str) -> str:
    if authenticate(username, password):
        try:
            result = create_file(filename)
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))
        else:
            return {'message':result}

@app.delete("/files/{filename:path}")
async def delete_file(filename: str, username: str, password: str) -> str:
    if authenticate(username, password):
        try:
            file_location = get_file_location(filename)
            os.remove(file_location)
        except FileNotFoundError:
            raise HTTPException(status_code=404, detail="Le fichier n'existe pas")
        else:
            return {'message':f'Le fichier {filename} a été supprimé avec succès'}
    else:
        raise HTTPException(status_code=401, detail="L'authentification a échoué")

@app.get("/files/{filename:path}")
async def get_file(filename: str, username: str, password: str) -> FileResponse:
    if not authenticate(username, password):
        raise HTTPException(status_code=401, detail="L'authentification a échoué")
    
    file_location = get_file_location(filename)

    if os.path.isfile(file_location):
        return FileResponse(file_location)
    else:
        raise HTTPException(status_code=404, detail="Fichier non trouvé")

@app.get("/files/{prefix:path}")
async def get_files(prefix: str, username: str, password: str) -> str:
    if not authenticate(username, password):
        raise HTTPException(status_code=401, detail="L'authentification a échoué")
    user_folder = os.path.expanduser("~")
    path = os.path.join(user_folder, prefix)
    if not os.path.exists(path):
        return []
    
    if os.path.isfile(path):
        return [prefix]
    
    result = []
    for root, dirs, files in os.walk(path):
        for file in files:
            file_location = os.path.join(root, file)
            if os.path.isfile(file_location) and file_location.startswith(user_folder):
                result.append(os.path.relpath(file_location, user_folder))
            # os.path.relpath pour avoir un chemin relatif
    return result