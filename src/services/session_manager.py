import json
import uuid
import os
import statistics

class SessionManager:
    def __init__(self):
        os.makedirs("data", exist_ok=True)
        self.save_path = "data/save_sessions.json"

        # Charger les sessions si le fichier existe
        if os.path.exists(self.save_path):
            with open(self.save_path, "r") as f:
                try:
                    self.sessions = json.load(f)
                except:
                    self.sessions = {}
        else:
            self.sessions = {}

    # Sauvegarde JSON
    def _save(self):
        with open(self.save_path, "w") as f:
            json.dump(self.sessions, f, indent=4)

    # 1. Créer une session avec backlog par défaut
    def create_session(self, name, players, mode="moyenne", default_backlog=None):
        """
        Crée une session avec un backlog par défaut si aucun backlog n'est fourni.
        """
        session_id = str(uuid.uuid4())

        if default_backlog is None:
            default_backlog = ["Story 1", "Story 2", "Story 3"]  # Backlog par défaut

        self.sessions[session_id] = {
            "name": name,
            "players": players,
            "mode": mode,  # "strict", "moyenne", "mediane"
            "backlog": default_backlog,
            "current_story": default_backlog[0] if default_backlog else None,
            "votes": {},
            "completed": []
        }

        self._save()
        return session_id

    # 2. Rejoindre une session
    def join_session(self, session_id, pseudo):
        if session_id not in self.sessions:
            return False
        if pseudo not in self.sessions[session_id]["players"]:
            self.sessions[session_id]["players"].append(pseudo)
            self._save()
        return True

    # 3. Voter
    def vote(self, session_id, player, value):
        if session_id not in self.sessions:
            return False
        if player not in self.sessions[session_id]["players"]:
            return False

        self.sessions[session_id]["votes"][player] = value
        self._save()
        return True

    # 4. Modifier le mode de vote
    def set_mode(self, session_id, mode):
        if session_id not in self.sessions:
            return False
        if mode not in ["strict", "moyenne", "mediane"]:
            return False

        self.sessions[session_id]["mode"] = mode
        self._save()
        return True

    # 5. Révéler les votes et calculer la valeur
    def reveal_votes(self, session_id):
        if session_id not in self.sessions:
            return {"votes": {}, "validated": False, "mode": None, "calculated_value": None}

        session = self.sessions[session_id]
        votes = session["votes"]
        players = session["players"]
        mode = session.get("mode", "moyenne")

        result = {
            "votes": votes,
            "validated": False,
            "mode": mode,
            "calculated_value": None
        }

        # Vérifier que tous les joueurs ont voté
        if len(votes) != len(players):
            return result

        values = list(votes.values())

        # --- MODE STRICT ---
        if mode == "strict":
            if all(v == values[0] for v in values):
                result["validated"] = True
                result["calculated_value"] = values[0]
            else:
                result["calculated_value"] = "Conflit : votes divergents"
                return result

        # --- MODE MOYENNE ---
        elif mode == "moyenne":
            avg = round(sum(values) / len(values), 2)
            result["validated"] = True
            result["calculated_value"] = avg

        # --- MODE MÉDIANE ---
        elif mode == "mediane":
            med = statistics.median(values)
            result["validated"] = True
            result["calculated_value"] = med

        # Si validé → avancer dans le backlog
        if result["validated"]:
            session["completed"].append(session["current_story"])

            backlog = session["backlog"]
            remaining = [b for b in backlog if b not in session["completed"]]

            session["current_story"] = remaining[0] if remaining else None

            # Reset votes
            session["votes"] = {}
            self._save()

        return result

    # 6. Reprendre toutes les sessions
    def resume_sessions(self):
        return self.sessions
