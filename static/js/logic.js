/*
@file logic.js
@brief Logique front-end pour la salle de Planning Poker
@description
Ce fichier gère :
- Les contrôles et affichages spécifiques à l'admin
- La création et le comportement des cartes de vote
- La mise à jour en temps réel des participants, votes et backlog
- Le timer et la gestion des rounds
- L'affichage des résultats de consensus
*/

let countdownInterval;
let currentState = {};
let isAdmin = false;

// --- A. GESTION DE L'ADMIN ET DES CONTRÔLES ---
/** Met à jour la visibilité des contrôles admin. */

const updateAdminControls = () => {
    document.querySelectorAll('.admin-control').forEach(el => {
        el.style.display = isAdmin ? 'block' : 'none';
    });
    document.getElementById('timer-input-group').style.display = 
        document.getElementById('use-timer-checkbox').checked ? 'block' : 'none';
};

// Écouteur pour afficher/cacher le champ de durée du timer
document.getElementById('use-timer-checkbox').addEventListener('change', updateAdminControls);

// AFFICHAGE DES CARTES ET SYNCHRONISATION

const cardValues = ["0", "1", "2", "3", "5", "8", "13", "20", "40", "100", "?", "☕️"];
const deckElement = document.getElementById('card-deck');

// Générations des boutons de vote avec vos images SVG spécifiques
const setupCardDeck = () => {
    deckElement.innerHTML = ''; 
    cardValues.forEach(value => {
        const button = document.createElement('button');
        button.className = 'card-btn svg-card';
        button.setAttribute('data-value', value);
        let fileName;

        if (value === '?') {
            fileName = 'cartes_interro';
        } else if (value === '☕️') {
            fileName = 'cartes_cafe';
        } else {
            fileName = `cartes_${value}`;
        }

        const img = document.createElement('img');
        img.src = `/static/cartes/${fileName}.svg`;
        img.alt = `Carte ${value}`;
        img.className = "svg-img-content";

        button.appendChild(img);
        
        button.addEventListener('click', function() {
            const voteValue = this.getAttribute('data-value');
            if (socket) {
                socket.emit('submit_vote', { room_id: ROOM_ID, username: USERNAME, vote: voteValue });
            }
            document.querySelectorAll('.card-btn').forEach(btn => btn.classList.remove('selected'));
            this.classList.add('selected');
        });
        deckElement.appendChild(button);
    });
};

// Mettre à jour la liste des participants et leur état de vote
const updateParticipantsAndVotes = (participants, votes) => {
    const listElement = document.getElementById('participants-list');
    const votesElement = document.getElementById('other-votes'); 
    listElement.innerHTML = '';
    votesElement.innerHTML = ''; 

    let votedCount = 0;
    
    participants.forEach(username => {
        const hasVoted = Object.keys(votes).includes(username);
        if (hasVoted) votedCount++; 

        // Mise à jour de la liste des pseudos 
        const li = document.createElement('li');
        li.textContent = username;
        li.style.fontWeight = hasVoted ? 'bold' : 'normal';
        li.innerHTML += hasVoted ? ' ✅' : '';
        listElement.appendChild(li);

        // Mise à jour de l'affichage des cartes 
        // On n'affiche pas la carte de l'utilisateur local dans #other-votes 
        if (currentState.is_revealed || hasVoted) {
            const card = document.createElement('div');
            card.className = 'participant-card';
            card.setAttribute('data-username', username);

            if (currentState.is_revealed) {
                card.classList.add('revealed');
                const voteValue = hasVoted ? votes[username] : 'N/A';
                
                if (hasVoted) {
                    let fileName;
                    if (voteValue === '?') fileName = 'carte_interro';
                    else if (voteValue === '☕️') fileName = 'cartes_cafe';
                    else fileName = `cartes_${voteValue}`;

                    card.innerHTML = `<img src="/static/cartes/${fileName}.svg" class="svg-img-content">`;
                } else {
                    card.textContent = 'N/A';
                }
            }else if (hasVoted) {
                // Affiche le dos de carte
                card.classList.add('voted'); 
                card.textContent = '';
                
            } else {
                // Afficher un placeholder
                card.classList.add('pending'); 
                card.textContent = '...'; 
            }
            votesElement.appendChild(card);
        }
    });

    // Ensuite, on met à jour le DOM après l'itération
    document.getElementById('participant-count').textContent = participants.length;
    
    // Révélation automatique si sans timer et tous ont voté (Admin seulement)
    if (isAdmin && window.currentState.is_started && !window.currentState.use_timer && !window.currentState.is_revealed && votedCount === participants.length && participants.length > 0) {
        socket.emit('reveal_votes', { room_id: ROOM_ID });
    }
    
    // Mettre à jour les boutons admin (Révéler / Suivant)
    if (isAdmin) {
        document.getElementById('reveal-votes-btn').disabled = (votedCount === 0 || window.currentState.is_revealed);
        document.getElementById('next-task-btn').disabled = !currentState.is_revealed;
        document.getElementById('restart-vote-btn').disabled = !currentState.is_revealed;
    }
};


// Réinitialise l'interface pour un nouveau vote. 
const resetInterfaceForNewRound = () => {
    document.querySelectorAll('.card-btn').forEach(btn => btn.classList.remove('selected'));
    document.getElementById('time-remaining').textContent = 'Prêt';
    document.getElementById('other-votes').innerHTML = '';
    
    // Réinitialise l'état des boutons admin au début d'un round
    if (isAdmin) {
        document.getElementById('reveal-votes-btn').disabled = true;
        document.getElementById('next-task-btn').disabled = true;
        document.getElementById('restart-vote-btn').disabled = true;
    }
};

// Met à jour la liste des tâches du backlog. 
const updateBacklogList = (backlog, currentIndex) => {
    const listElement = document.getElementById('backlog-list');
    listElement.innerHTML = '';
    document.getElementById('total-tasks').textContent = backlog.length;

    backlog.forEach((task, index) => {
        const li = document.createElement('li');
        li.textContent = `${index + 1}. ${task.name}`;
        if (index === currentIndex) {
            li.classList.add('current');
        }
        
        listElement.appendChild(li);
    });
};

// Met à jour les détails de la tâche en cours.
const updateCurrentStory = (state) => {
    const currentTask = state.backlog[state.current_story_index];
    if (currentTask) {
        document.getElementById('story-name').textContent = currentTask.name;
        document.getElementById('story-description').textContent = currentTask.description;
        document.getElementById('current-index').textContent = state.current_story_index + 1;
    }
};


const timerDisplay = document.getElementById('time-remaining');

// Lance le décompte du timer. 
const startTimer = (duration) => {
    clearInterval(countdownInterval); 
    let time = duration;
    
    const tick = () => {
        const minutes = String(Math.floor(time / 60)).padStart(2, '0');
        const seconds = String(time % 60).padStart(2, '0');
        timerDisplay.textContent = `${minutes}:${seconds}`;

        if (time <= 0) {
            clearInterval(countdownInterval);
            // La révélation automatique se fait côté serveur.
            if (isAdmin) {
                socket.emit('reveal_votes', { room_id: ROOM_ID });
            }
            timerDisplay.textContent = 'TERMINÉ !';
        } else {
            time--;
        }
    };
    
    tick();
    countdownInterval = setInterval(tick, 1000);
};


// Crée une nouvelle section dans l'interface pour afficher ce résultat.
const displayConsensusResult = (result, details) => {
    let resultContainer = document.getElementById('consensus-result');
    if (!resultContainer) {
        resultContainer = document.createElement('div');
        resultContainer.id = 'consensus-result';
        document.getElementById('story-details').appendChild(resultContainer);
    }
    
    resultContainer.innerHTML = `
        <h3>Résultat Final : <span style="color: #4CAF50;">${result}</span></h3>
        <p style="font-size: 0.9em; color: #555;">Règle appliquée : ${details}</p>
    `;
};


window.currentState = currentState;
window.isAdmin = isAdmin;
window.updateAdminControls = updateAdminControls;
window.updateParticipantsAndVotes = updateParticipantsAndVotes;
window.updateBacklogList = updateBacklogList; 
window.updateCurrentStory = updateCurrentStory; 
window.resetInterfaceForNewRound = resetInterfaceForNewRound; 
window.startTimer = startTimer;
window.displayConsensusResult = displayConsensusResult;
window.setupCardDeck = setupCardDeck;

