"""
@file app.py
@brief Application de Planning Poker temps réel avec Flask et Socket.IO
@author
@date 2025

Cette application permet d'organiser des sessions de Planning Poker
avec plusieurs règles de consensus (strict, moyenne, médiane),
une gestion du backlog via JSON et une communication temps réel.
"""


import os
import json
import uuid
from flask import Flask, render_template, redirect, url_for, request, session
from flask_socketio import SocketIO, join_room, leave_room, emit

# Fichier : app.py (Ajouter cette fonction utilitaire)

def calculate_consensus(votes, session_type):
    """
    @brief Calcule le résultat final d'un vote selon la règle choisie.

    @param votes Dictionnaire des votes {pseudo: valeur}
    @param session_type Type de règle ('strict', 'average', 'median')
    @return tuple (resultat_final, details_du_calcul)

    Les votes spéciaux ('?', '☕️') sont ignorés dans les calculs numériques.
    """
     
    # Étape 1 : Nettoyer et convertir les votes en nombres
    # On ignore les votes spéciaux ('?', '☕️') pour le calcul mathématique.
    numeric_votes = []
    
    # Définir les valeurs numériques pour les chaînes spéciales comme '0.5'
    value_map = {'0.5': 0.5}
    
    for vote in votes.values():
        if vote in value_map:
            numeric_votes.append(value_map[vote])
        else:
            try:
                # Convertir les chaînes standard ('1', '2', '5', etc.) en float
                numeric_votes.append(float(vote))
            except ValueError:
                # Ignorer les votes non numériques ('?', '☕️')
                pass
                
    if not numeric_votes:
        # Si aucun vote numérique n'est soumis
        return "N/A (Non numérique)", "Aucun vote numérique soumis pour le calcul."

    # Étape 2 : Calcul basé sur le type de session
    
    # --- Règle 1 : Strict (Consensus Total) ---
    if session_type == 'strict':
        # Vérifie si tous les votes numériques sont identiques
        if len(set(numeric_votes)) == 1:
            result = str(numeric_votes[0])
            details = "Consensus atteint : Tous les votes numériques sont identiques."
        else:
            result = "NO CONSENSUS"
            details = "Divergence détectée. Le vote est relancé par l'admin."
    
    # --- Règle 2 : Moyenne (Simple moyenne) ---
    elif session_type == 'average':
        average = sum(numeric_votes) / len(numeric_votes)
        # Trouver la carte la plus proche de la moyenne dans l'ensemble Fibonacci standard (0, 1, 2, 3, 5, 8, 13...)
        
        # NOTE : Pour l'instant, renvoyons la moyenne brute arrondie à 1 décimale
        result = round(average, 1)
        details = f"Moyenne simple des votes numériques ({len(numeric_votes)}) : {result}"

    # --- Règle 3 : Médiane ---
    elif session_type == 'median':
        numeric_votes.sort()
        n = len(numeric_votes)
        
        if n % 2 == 1:
            # Nombre impair : le milieu exact
            median = numeric_votes[n // 2]
        else:
            # Nombre pair : moyenne des deux du milieu
            mid1 = numeric_votes[n // 2 - 1]
            mid2 = numeric_votes[n // 2]
            median = (mid1 + mid2) / 2
            
        result = str(median)
        details = f"Médiane des votes numériques ({len(numeric_votes)}) : {result}"
        
    else:
        # Cas par défaut ou erreur
        result = "N/A (Règle Inconnue)"
        details = "Le type de session spécifié n'est pas reconnu."

    return str(result), details

# --- Configuration de Flask ---
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'une_cle_secrete_par_defaut')
socketio = SocketIO(app)
# Stocke les états de toutes les salles
rooms = {}

# --- Routes Flask Classiques (Gestion des pages) ---

@app.route('/')
def home():
    """
    @brief Page d'accueil de l'application.

    Permet de créer ou rejoindre une session de Planning Poker.
    """
    # Cette page contiendra les formulaires pour 'Créer' ou 'Rejoindre'
    return render_template('home.html') 

@app.route('/create_room', methods=['POST'])
def create_room():
    """
    @brief Création d'une nouvelle salle Planning Poker.

    - Génère un identifiant unique de salle
    - Charge et valide le backlog JSON
    - Définit l'utilisateur comme administrateur
    """
    # 1. Récupération des données du formulaire
    username = request.form['username']
    session_name = request.form['session_name']
    session_type = request.form['session_type']
    backlog_file = request.files.get('backlog_file')
    
    # 2. Gestion et parsing du fichier JSON
    parsed_backlog = []
    if backlog_file and backlog_file.filename.endswith('.json'):
        try:
            # Lire le contenu du fichier
            file_content = backlog_file.read().decode('utf-8')
            backlog_data = json.loads(file_content)
            
            # Formater le backlog en ajoutant la structure de vote vide
            for item in backlog_data:
                # Assurez-vous que l'item contient au moins un 'name' (ou 'nom') et une 'description'
                parsed_backlog.append({
                    "name": item.get('name') or item.get('nom', 'Tâche sans nom'),
                    "description": item.get('description', 'Pas de description fournie.'),
                    "votes": {} # Dictionnaire vide pour les votes des participants
                })
        except json.JSONDecodeError:
            print("Erreur: Le fichier téléchargé n'est pas un JSON valide.")
            # Gérer l'erreur utilisateur
            return "Erreur: Le fichier backlog n'est pas un JSON valide.", 400
        except Exception as e:
            print(f"Erreur lors du traitement du fichier: {e}")
            return "Erreur lors du traitement du fichier.", 500

    # 3. Création et initialisation de la salle
    room_id = str(uuid.uuid4()).split('-')[0].upper()
    
    rooms[room_id] = {
        # ------------------ Métadonnées de la Session ------------------
        "session_name": session_name,          # Nom convivial de la session
        "session_type": session_type,          # Règle de consensus (strict, median, average)
        "admin_name": username,                # Pseudo de l'administrateur
        "admin_sid": None,                # ID de connexion SocketIO de l'admin (pour contrôle)
        
        # ------------------ Backlog et Progression ------------------
        "backlog": parsed_backlog,             # Liste des tâches chargées
        "current_story_index": 0,              # Index de la tâche actuellement votée
        
        # ------------------ État de la Manche en Cours ------------------
        "votes": {},                           # {'pseudo': 'valeur'} - Stocke les votes des participants
        "is_revealed": False,                  # Indique si les cartes sont retournées
        
        # ------------------ État du Jeu et du Timer ------------------
        "is_started": False,                   # Le jeu commence en pause (non démarré)
        "use_timer": False,                    # Par défaut, pas de timer
        "timer_duration": 60,                  # Durée par défaut si le timer est activé (en secondes)
        "timer_end_time": None,                # Timestamp de fin du timer (pour synchronisation serveur/client)
        
        # ------------------ Participants ------------------
        "participants": {}                     # {'sid': 'pseudo'} - Liste des participants connectés
    }
    
    # 4. Stocker le nom de l'utilisateur dans la session Flask
    session['username'] = username
    
    print(f"Salle créée: {room_id} | Session: {session_name} par {username}")
    return redirect(url_for('room', room_id=room_id))

@app.route('/join_room', methods=['POST'])
def join_existing_room():
    """
    @brief Rejoindre une salle existante via son identifiant.
    """
    # 1. Récupération des données du formulaire
    room_id = request.form['room_id'].upper()
    username = request.form['username']
    # session_name est ignoré pour la logique de jointure, mais on le récupère
    session_name = request.form.get('session_name', 'Session Inconnue')
    
    # 2. Vérification de l'existence de la salle
    if room_id in rooms:
        # Stocker le pseudo dans la session Flask
        session['username'] = username
        print(f"Tentative de jointure de salle: {room_id} | Session: {session_name} par {username}")
        # Redirection vers la page de la salle, où l'événement SocketIO 'join' sera géré
        return redirect(url_for('room', room_id=room_id))
    else:
        # Gérer l'erreur si la salle n'existe pas
        # NOTE: Pour une meilleure UX, vous devriez afficher ce message sur la page home.
        return f"Erreur: La session avec l'ID **{room_id}** n'existe pas.", 404


@app.route('/room/<room_id>')
def room(room_id):
    """
    @brief Page principale d'une salle Planning Poker.
    """
    # Assurez-vous que l'utilisateur a un nom stocké dans la session
    if 'username' not in session or room_id not in rooms:
        return redirect(url_for('home'))
        
    return render_template('room.html', 
                           room_id=room_id, 
                           username=session['username'])

# --- Gestion des Événements SocketIO (Temps Réel) ---

@socketio.on('join')
def on_join(data):
    """
    @brief Gestion de la connexion d'un participant à une salle.
    """
    username = data.get('username')
    room_id = data.get('room_id')
    
    if room_id in rooms and username:
        room_data = rooms[room_id] # Référence aux données de la salle
        
        # 1. Joindre le canal de la salle
        join_room(room_id)
        
        # 2. Enregistrer l'utilisateur (sid) et son nom dans la salle
        room_data['participants'][request.sid] = username
        
        # 3. CORRECTION 2 : Définir l'admin_sid si c'est la première connexion de l'admin
        # Nous supposons que l'administrateur est le premier à se connecter via SocketIO
        # ET que son nom correspond au 'admin_name' défini à la création de la salle.
        if room_data['admin_sid'] is None and username == room_data['admin_name']:
             room_data['admin_sid'] = request.sid
        
        # Enregistrer le pseudo dans la structure : { 'sid': 'pseudo' }
        rooms[room_id]['participants'][request.sid] = username
        
        # Envoyer la liste complète des participants (pseudos)
        # On utilise values() pour avoir uniquement les pseudos dans le front
        current_participants = list(rooms[room_id]['participants'].values())
        
        emit('status', 
             {'msg': f'{username} a rejoint la salle.',
              'participants': current_participants, # <- Envoi des PSEUDOS
              'current_state': rooms[room_id]}, 
             room=room_id)
        
        print(f"{username} a rejoint la salle {room_id}")
    else:
        emit('error', {'msg': 'Erreur lors de la jointure de la salle.'})

@socketio.on('disconnect')
def on_disconnect():
    """
    @brief Gestion de la déconnexion d'un participant.
    """
    # Trouver l'utilisateur et la salle qu'il quitte
    for room_id, room_data in rooms.items():
        if request.sid in room_data['participants']:
            # On récupère le pseudo (username) grâce au request.sid
            username = room_data['participants'].pop(request.sid)
            
            # Retirer le vote de l'utilisateur (on avait besoin de la clé 'username' ici)
            # NOTE: Pour gérer les votes plus tard, il faudra stocker le vote par PSEUDO ou SID.
            # Simplifions pour l'instant la structure de vote par PSEUDO pour la clarté :
            if username in room_data['votes']:
                 room_data['votes'].pop(username)
                 
            current_participants = list(room_data['participants'].values())
                 
            # Notifier la salle que l'utilisateur est parti
            emit('status', 
                 {'msg': f'{username} a quitté la salle.',
                  'participants': current_participants, # <- Envoi des PSEUDOS mis à jour
                  'current_state': room_data}, 
                 room=room_id)
            
            leave_room(room_id)
            print(f"{username} a quitté la salle {room_id}")
            return

# ... (Après on_join, on_disconnect, et submit_vote)

@socketio.on('start_session')
def on_start_session(data):
    """ @brief Démarre la session de vote, avec ou sans timer."""
    room_id = data.get('room_id')
    use_timer = data.get('use_timer', False)
    duration = data.get('duration', 60)
    
    if room_id in rooms and request.sid == rooms[room_id].get('admin_sid'):
        room_data = rooms[room_id]
        
        if not room_data['backlog']:
             return emit('error', {'msg': 'Le backlog est vide. Impossible de démarrer.'}, room=request.sid)

        room_data['is_started'] = True
        room_data['use_timer'] = use_timer
        room_data['timer_duration'] = int(duration)
        room_data['is_revealed'] = False
        room_data['votes'] = {} # Réinitialisation des votes au démarrage
        
        emit('session_started', {
            'is_started': True,
            'use_timer': use_timer,
            'duration': room_data['timer_duration'],
            'current_story': room_data['backlog'][room_data['current_story_index']]
        }, room=room_id)
        
        # Si un timer est utilisé, on lance la logique de fin de timer
        if use_timer:
            # NOTE: La logique de décompte réel (thread) est complexe et sera simplifiée en JS pour l'instant
            # mais le serveur doit garder une trace pour la révélation automatique
            pass # Ici, dans un vrai système, vous lanceriez un thread pour la révélation auto


@socketio.on('reveal_votes')
def on_reveal_votes(data):
    """ @brief Révèle les votes (manuellement ou par timer) et calcule le consensus."""
    room_id = data.get('room_id')
    
    if room_id in rooms and request.sid == rooms[room_id].get('admin_sid'):
        room_data = rooms[room_id]
        
        if room_data['is_revealed']:
             return 

        room_data['is_revealed'] = True
        current_index = room_data['current_story_index']
        
        # --- CALCUL DU RÉSULTAT ---
        final_result, calculation_details = calculate_consensus(
            room_data['votes'], 
            room_data['session_type']
        )
        
        # --- ENREGISTREMENT DU RÉSULTAT DANS LE BACKLOG ---
        if current_index < len(room_data['backlog']):
            # Assurez-vous que l'index est valide
            room_data['backlog'][current_index]['final_vote'] = final_result
            room_data['backlog'][current_index]['consensus_rule'] = room_data['session_type']
            room_data['backlog'][current_index]['votes_submitted'] = room_data['votes'] # Optionnel: Sauvegarde des votes bruts
        # ---------------------------------------------------
        
        # 1. Émettre l'événement de révélation avec le résultat
        emit('votes_revealed', {
            'votes': room_data['votes'],
            'result': final_result,
            'details': calculation_details
        }, room=room_id)
        
        # 2. Envoyer un message de statut général
        emit('status', 
             {'msg': f"Les votes ont été révélés. Résultat ({room_data['session_type']}) : {final_result}",
              'participants': list(room_data['participants'].values()),
              'current_state': room_data}, 
             room=room_id)
        
        print(f"Votes révélés dans la salle {room_id}. Résultat: {final_result}")
    else:
        emit('error', {'msg': 'Seul l\'administrateur peut révéler les votes.'}, room=request.sid)

@socketio.on('next_task')

def on_next_task(data):
    """ @brief Passe à la tâche suivante (Admin only)."""
    room_id = data.get('room_id')
    
    if room_id in rooms and request.sid == rooms[room_id].get('admin_sid'):
        room_data = rooms[room_id]
        current_index = room_data['current_story_index']
        
        # VÉRIFICATION: S'assurer que le vote a été révélé avant de passer à la tâche suivante
        if not room_data['is_revealed']:
            emit('error', {'msg': "Veuillez d'abord révéler les votes pour la tâche actuelle."}, room=request.sid)
            return

        # 2. Vérification si toutes les tâches sont terminées
        if current_index + 1 >= len(room_data['backlog']):
            emit('session_ended', {'msg': 'Toutes les tâches du backlog ont été estimées !'}, room=room_id)
            return
            
        # 3. Préparation de la nouvelle manche
        room_data['current_story_index'] += 1
        new_index = room_data['current_story_index']
        room_data['votes'] = {}
        room_data['is_revealed'] = False
        
        use_timer = room_data.get('use_timer', False)
        duration = room_data.get('timer_duration', 60)

        emit('new_round', {
            'current_story': room_data['backlog'][new_index],
            'index': new_index,
            'use_timer': use_timer,     # <-- DOIT ÊTRE PRÉSENT
            'duration': duration
        }, room=room_id)
        
        # Envoyer un message de statut général
        emit('status', {
            'msg': f"Passage à la tâche suivante : {room_data['backlog'][new_index]['name']}.",
            'participants': list(room_data['participants'].values()),
            'current_state': room_data,
            'use_timer': use_timer,     # <-- AJOUT
            'duration': duration
        },  room=room_id)
        
# Fichier : app.py

@socketio.on('restart_vote')
def on_restart_vote(data):
    """ @brief Relance le vote pour la tâche actuelle (Admin only)."""
    room_id = data.get('room_id')
    
    if room_id in rooms and request.sid == rooms[room_id].get('admin_sid'):
        room_data = rooms[room_id]
        use_timer = room_data.get('use_timer', False)
        duration = room_data.get('timer_duration', 60)
        room_data['votes'] = {}
        room_data['is_revealed'] = False
        
        emit('vote_restarted',{
            'use_timer': use_timer,     # <-- AJOUT
            'duration': duration
        }, room=room_id)
        
        # Envoyer un message de statut général
        emit('status', 
             {'msg': "Le vote a été relancé par l'administrateur. Veuillez voter à nouveau.",
              'participants': list(room_data['participants'].values()),
              'current_state': room_data}, 
             room=room_id)

@socketio.on('submit_vote')
def on_submit_vote(data):
    """
    @brief Enregistrement du vote d'un participant.
    """
    room_id = data.get('room_id')
    username = data.get('username')
    vote = data.get('vote')
    
    # Vérification (la salle doit exister et la session doit être démarrée)
    if room_id in rooms and rooms[room_id].get('is_started'):
        room_data = rooms[room_id]
        
        # S'assurer que le vote n'est pas soumis après la révélation
        if room_data.get('is_revealed'):
             return emit('error', {'msg': "Impossible de voter après la révélation."}, room=request.sid)

        # Enregistre le vote
        if username in room_data['participants'].values():
            room_data['votes'][username] = vote
            
            participants_count = len(room_data['participants'])
            votes_count = len(room_data['votes'])
            
            current_participants = list(room_data['participants'].values())

            # --- ÉMISSION CRUCIALE ---
            # Envoyer l'événement pour mettre à jour l'interface de TOUS les clients.
            emit('vote_submitted', {
                'msg': f'{username} a voté.',
                'participants': current_participants,
                'current_state': room_data, # <--- ENVOI DE L'ÉTAT MIS À JOUR
                'voted_all': (participants_count == votes_count)
            }, room=room_id)
            
            print(f"Vote enregistré pour {username} dans la salle {room_id}: {vote}")
                
    else:
        emit('error', {'msg': "Impossible de voter. Session non démarrée ou salle introuvable."}, room=request.sid)

# Fichier : app.py (Ajouter cette nouvelle fonction SocketIO)

@socketio.on('request_backlog_download')
def on_request_backlog_download(data):
    """
    @brief Envoie le backlog finalisé à l'administrateur.
    """
    room_id = data.get('room_id')
    
    if room_id in rooms and request.sid == rooms[room_id].get('admin_sid'):
        room_data = rooms[room_id]
        
        # Émettre l'événement de téléchargement UNIQUEMENT à l'admin demandeur
        emit('backlog_updated', {
            'backlog_data': room_data['backlog']
        }, room=request.sid) 
        
        print(f"Admin de la salle {room_id} a demandé le téléchargement du backlog.")
    else:
        emit('error', {'msg': "Action réservée à l'administrateur."}, room=request.sid)


if __name__ == '__main__':
    """
    @brief Point d'entrée principal de l'application.
    """
    # Utiliser 'run' de socketio pour que les WebSockets fonctionnent correctement
    socketio.run(app, debug=True)