# Projet_Planning_Poker-Agile-

Une application web interactive de **Planning Poker** permettant aux équipes Agile d'estimer leurs tâches (User Stories) de manière collaborative, synchronisée et ludique.

Ce projet a été réalisé dans le cadre du cours de Développement Web Avancé. Il utilise **Python (Flask)** pour le backend et **Socket.IO** pour la communication en temps réel bidirectionnelle.

## Fonctionnalités Principales

* **Temps Réel (WebSockets) :** Les votes, la révélation des cartes et les changements de tâches sont instantanés pour tous les participants sans rechargement de page.
* **Gestion de Session :** Création et jointure de salles via un ID unique.
* **Backlog JSON :** Importation d'une liste de tâches via fichier JSON et export des résultats finaux.
* **Interface Moderne :** Thème sombre (Dark Mode), cartes animées en SVG, design responsive.
* **Outils Admin :** Timer configurable, contrôles de flux (Révéler, Relancer, Suivant).

## Modes de Jeu (Règles de Consensus)

L'application gère trois modes de calcul pour valider les estimations :

1.  **Strict (Unanimité) :**
    * *Principe :* Pour qu'une estimation soit validée, **tous** les participants doivent avoir voté pour la même valeur.
    * *Comportement :* En cas de divergence (ex: un 3 et un 5), le système affiche "NO CONSENSUS". L'administrateur doit relancer le vote après débat.

2.  **Moyenne (Average) :**
    * *Principe :* Calcule la moyenne arithmétique des votes numériques.
    * *Comportement :* Le résultat est arrondi à une décimale (ex: 12.5) et validé immédiatement.

3.  **Médiane (Median) :**
    * *Principe :* Sélectionne la valeur centrale de tous les votes triés.
    * *Comportement :* Idéal pour ignorer les valeurs aberrantes et valider le vote de la majorité.

*(Note : Les cartes spéciales comme "Café" ☕️ ou "?" sont exclues des calculs mathématiques).*

## Installation et Lancement

Le code doit tourner directement sur la machine de l'évaluateur. Suivez ces commandes exactes :

### 1. Cloner le projet
```bash
git clone [https://github.com/VOTRE_PSEUDO/NOM_DU_PROJET.git](https://github.com/VOTRE_PSEUDO/NOM_DU_PROJET.git)
cd NOM_DU_PROJET
```

### 2. Installation des dépendances
```bash
pip install -r requirements.txt
```

### 3. Démarrer le server
```bash
python app.py
```

### 4. Accéder à l'application
ouvrrez votre navigateur web et accédez à l'addresse : `http://127.0.0.1:5000`

## Guide d'Utilisation

### Pour l'Administrateur (Scrum Master)

1. **Création :** Sur la page d'accueil, remplissez le formulaire "Créer une Session". Choisissez le mode (Strict/Moyenne/Médiane) et chargez le fichier backlog.json.

2. **Invitation** : Partagez l'ID de la Session (affiché en haut de la salle) avec les membres de l'équipe.

3. **Gestion :**
    - Attendez que tout le monde ait voté (les cartes des joueurs s'affichent face cachée).
    - Cliquez sur "Révéler" pour afficher les résultats et le consensus.
    - Cliquez sur "Tâche Suivante" pour passer à l'item suivant du backlog.

4. **Export :** À la fin, cliquez sur "Télécharger les Estimations" pour récupérer le JSON mis à jour.

### Pour les Participants

1. Sur la page d'accueil, cliquez sur le lien "Rejoindre une session".

2. Entrez votre Pseudo et l'ID de la session.

3. Une fois dans la salle, cliquez sur une carte de votre deck pour voter.

## 📂 Structure du Projet
```
📁 PROJET/
├── 📄 app.py              # Point d'entrée serveur (Flask + SocketIO)
├── 📄 requirements.txt    # Liste des dépendances Python
├── 📁 static/
│   ├── 📁 css/
│   │   ├── 📄 style.css   # Styles de la page d'accueil
│   │   └── 📄 room.css    # Styles de la salle de jeu
│   ├── 📁 js/
│   │   ├── 📄 main.js     # Gestion des événements SocketIO (Client)
│   │   └── 📄 logic.js    # Logique d'interface (DOM, Timer, Deck)
│   └── 📁 cartes/         # Images SVG des cartes (0, 1, 2, ?, café...)
└── 📁 templates/
    ├── 📄 home.html       # Page d'accueil (Login/Création)
    └── 📄 room.html       # Salle de jeu principale
```

