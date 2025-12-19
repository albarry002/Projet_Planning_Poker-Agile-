/*
@file main.js
@brief Gestion de l'interface en temps réel pour la salle de Planning Poker
@description
Ce fichier gère :
- La connexion à Socket.IO
- L'envoi et la réception des événements de session et de vote
- La mise à jour de l'interface utilisateur (participants, votes, backlog)
- Les contrôles admin (démarrer, révéler, relancer, passer à la tâche suivante, télécharger le backlog)
*/


const socket = io();


// --- GESTION DE LA CONNEXION ---
socket.on('connect', function() {
    console.log(`Connecté au serveur SocketIO comme ${USERNAME} !`);

    socket.emit('join', { 
        room_id: ROOM_ID,
        username: USERNAME
    });
    
    if (window.setupCardDeck) {
        window.setupCardDeck();
    }
});

// --- ÉVÉNEMENT STATUS (MISE À JOUR GÉNÉRALE) ---
socket.on('status', function(data) {
    console.log(data.msg);
    currentState = data.current_state;
    isAdmin = (USERNAME === currentState.admin_name);

    if (window.updateAdminControls) {
        window.updateAdminControls(); 
    }
    
    // Affiche le nom de la session
    document.getElementById('session-title').textContent = currentState.session_name;
    
    // Affiche des participants et de l'état de vote
    if (window.updateParticipantsAndVotes) {
        window.updateParticipantsAndVotes(data.participants, currentState.votes); 
    }
    
    // Affiche les messages de statut
    const messagesDiv = document.getElementById('messages');
    messagesDiv.innerHTML += `<p><em>${data.msg}</em></p>`;
    messagesDiv.scrollTop = messagesDiv.scrollHeight; 

    // Affichage du backlog et de la tâche courante
    if (window.updateBacklogList && window.updateCurrentStory) {
        window.updateBacklogList(currentState.backlog, currentState.current_story_index);
        window.updateCurrentStory(currentState);
    }
    
    // Gérer l'état de démarrage de la session
    if (currentState.is_started) {
        document.getElementById('start-controls').style.display = 'none';
    }
});

// --- ÉVÉNEMENTS DE CONTRÔLE DE SESSION (ADMIN) ---
// Clic sur Démarrer la Session
document.getElementById('start-session-btn').addEventListener('click', () => {
    const useTimer = document.getElementById('use-timer-checkbox').checked;
    const duration = document.getElementById('timer-duration').value;
    
    socket.emit('start_session', {
        room_id: ROOM_ID,
        use_timer: useTimer,
        duration: duration
    });
});

// Événement du serveur : La session est démarrée
socket.on('session_started', (data) => {
    document.getElementById('start-controls').style.display = 'none';
    if (window.resetInterfaceForNewRound) {
        window.resetInterfaceForNewRound();
    }

    if (data.use_timer && window.startTimer) {
        window.startTimer(data.duration);
    }
});

// Evenement sur le bouton reveler les Votes
document.getElementById('reveal-votes-btn').addEventListener('click', () => {
    socket.emit('reveal_votes', { room_id: ROOM_ID });
});

// Evenement sur le bouton Tâche Suivante
document.getElementById('next-task-btn').addEventListener('click', () => {
    socket.emit('next_task', { room_id: ROOM_ID });
});

// evenement sur le bouton Relancer le Vote
document.getElementById('restart-vote-btn').addEventListener('click', () => {
    socket.emit('restart_vote', { room_id: ROOM_ID });
});

// Evenement sur le bouton Télécharger le Backlog (Admin seulement)
document.getElementById('download-backlog-btn').addEventListener('click', () => {
    socket.emit('request_backlog_download', { room_id: ROOM_ID });
});

// --- GESTION DES VOTES ---

socket.on('vote_submitted', (data) => {
    if (window.updateParticipantsAndVotes) {
         window.updateParticipantsAndVotes(data.participants, data.current_state.votes);
    }
});

// Événement du serveur : Votes révélés
socket.on('votes_revealed', (data) => {
    currentState.is_revealed = true;
    const participants = Object.values(currentState.participants); 
    if (window.updateParticipantsAndVotes) {
        window.updateParticipantsAndVotes(participants, data.votes);
    }
    if (window.displayConsensusResult) { // Ajout de la vérification par sécurité
        window.displayConsensusResult(data.result, data.details); 
    }
    if (window.updateAdminControls) {
        window.updateAdminControls();
    }
});

// Événement du serveur : Nouvelle manche
socket.on('new_round', (data) => {
    currentState.current_story_index = data.index;
    currentState.votes = {};
    currentState.is_revealed = false;
    if (window.resetInterfaceForNewRound && window.updateCurrentStory && window.updateBacklogList) {
        window.resetInterfaceForNewRound();
        window.updateCurrentStory(currentState);
        window.updateBacklogList(currentState.backlog, currentState.current_story_index);
    }
    if (data.use_timer && window.startTimer) {
        window.startTimer(data.duration);
    }
});

// Événement du serveur : Vote relancé
socket.on('vote_restarted', (data) => {
    if (window.resetInterfaceForNewRound) {
        window.resetInterfaceForNewRound();
    }
    const participants = Object.values(currentState.participants); 
    if (window.updateParticipantsAndVotes) {
        window.updateParticipantsAndVotes(participants, {}); 
    }
    if (data.use_timer && window.startTimer) {
        window.startTimer(data.duration);
    }
});

// Mise à jour du fichier Json du backlog 
socket.on('backlog_updated', (data) => {
    const jsonString = JSON.stringify(data.backlog_data, null, 2);
    const blob = new Blob([jsonString], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    
    a.href = url;
    a.download = `backlog_${ROOM_ID}_estimations.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
});

// Événement d'erreur
socket.on('error', function(data) {
    alert('Erreur: ' + data.msg);
});
