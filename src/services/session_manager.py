import json
import uuid
import os

class SessionManager:
    def __init__(self):
        os.makedirs("data", exist_ok=True)
        self.save_path = "data/save_sessions.json"
        
        # Charger fichier si existe
        if os.path.exists(self.save_path):
            with open(self.save_path, "r") as f:
                try:
                    self.sessions = json.load(f)
                except:
                    self.sessions = {}
        else:
            self.sessions = {}

    #  Sauvegarde JSON
    def _save(self):
        with open(self.save_path, "w") as f:
            json.dump(self.sessions, f, indent=4)

    # 1️. Créer une session
    def create_session(self, name, players, rule="strict"):
        session_id = str(uuid.uuid4())
        self.sessions[session_id] = {
            "name": name,
            "players": players,
            "rule": rule,
            "backlog": [],
            "current_story": None,
            "votes": {},
            "completed": []
        }
        self._save()
        return session_id

    # 2️. Rejoindre une session
    def join_session(self, session_id, pseudo):
        if session_id not in self.sessions:
            return False
        if pseudo not in self.sessions[session_id]["players"]:
            self.sessions[session_id]["players"].append(pseudo)
            self._save()
        return True

    # 3️. Charger backlog
    def load_backlog(self, session_id, backlog):
        if session_id not in self.sessions:
            return False
        self.sessions[session_id]["backlog"] = backlog
        if backlog:
            self.sessions[session_id]["current_story"] = backlog[0]
        self._save()
        return True

    # 4️. Voter
    def vote(self, session_id, player, value):
        if session_id not in self.sessions:
            return False
        self.sessions[session_id]["votes"][player] = value
        self._save()
        return True

    # 5️. Révéler votes (mode strict)
    def reveal_votes(self, session_id):
        if session_id not in self.sessions:
            return {"votes": {}, "validated": False}

        session = self.sessions[session_id]
        votes = session["votes"]
        result = {"votes": votes, "validated": False}

        # Vérifier que tous les joueurs ont voté
        if len(votes) == len(session["players"]):
            values = list(votes.values())
            # Vérifier unanimité
            if all(v == values[0] for v in values):
                result["validated"] = True
                # Ajouter story aux complétées
                session["completed"].append(session["current_story"])
                # Passer à la story suivante
                backlog = session["backlog"]
                remaining = [b for b in backlog if b not in session["completed"]]
                session["current_story"] = remaining[0] if remaining else None
                session["votes"] = {}  # réinitialiser votes
                self._save()

        return result

    # 6️. Sauvegarder session
    def save_session(self, session_id):
        self._save()
        return True

    # 7️. Reprendre session
    def resume_session(self):
        return self.sessions
