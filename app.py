import sys
import os
# Ajouter le dossier src à la liste des chemins Python
sys.path.append(os.path.join(os.path.dirname(__file__), "src"))
from flask import Flask, request, jsonify, render_template
from services.session_manager import SessionManager


#Implémentation des routes API
app = Flask(__name__, template_folder="templates")
manager = SessionManager()

# Route pour le front
@app.route('/')
def index():
    return render_template("index.html")

# 1. Creation de la session
@app.route('/api/session/create', methods=['POST'])
def create_session():
    data = request.json
    session_name = data.get("session_name")
    players = data.get("players")
    rule = data.get("rule")  # mode strict, mediane, moyenne...

    session_id = manager.create_session(session_name, players, rule)

    return jsonify({"session_id": session_id}), 201



# 2. Rejoindre une session

@app.route('/api/session/join', methods=['POST'])
def join_session():
    data = request.json
    session_id = data.get("session_id")
    pseudo = data.get("pseudo")

    success = manager.join_session(session_id, pseudo)

    return jsonify({"success": success})



# 3. Charger un backlog JSON

@app.route('/api/backlog/load', methods=['POST'])
def load_backlog():
    data = request.json
    session_id = data.get("session_id")
    backlog = data.get("backlog")  # liste JSON

    manager.load_backlog(session_id, backlog)
    return jsonify({"message": "Backlog chargé"})



# 4. Voter pour une story

@app.route('/api/vote', methods=['POST'])
def vote():
    data = request.json
    session_id = data.get("session_id")
    player = data.get("player")
    value = data.get("value")  # valeur de la carte

    manager.vote(session_id, player, value)

    return jsonify({"message": "Vote enregistré"})



# 5. Révéler les votes + calcul règle

@app.route('/api/votes/reveal', methods=['GET'])
def reveal():
    session_id = request.args.get("session_id")

    result = manager.reveal_votes(session_id)
    return jsonify(result)


# 6. Sauvegarder une partie

@app.route('/api/session/save', methods=['POST'])
def save_session():
    data = request.json
    session_id = data.get("session_id")

    manager.save_session(session_id)
    return jsonify({"message": "Session sauvegardée"})


# 7. Reprendre une partie

@app.route('/api/session/resume', methods=['GET'])
def resume():
    saved = manager.resume_session()
    return jsonify(saved)


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)