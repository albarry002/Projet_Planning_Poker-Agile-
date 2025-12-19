# tests/test_app.py
import pytest
from unittest.mock import patch
from app import calculate_consensus, rooms, app, socketio

# -----------------------------
# Tests de la fonction calculate_consensus
# -----------------------------

def test_calculate_consensus_strict_consensus():
    votes = {'alice': '3', 'bob': '3'}
    result, details = calculate_consensus(votes, 'strict')
    assert float(result) == 3.0
    assert "Consensus atteint" in details

def test_calculate_consensus_strict_no_consensus():
    votes = {'alice': '3', 'bob': '5'}
    result, details = calculate_consensus(votes, 'strict')
    assert result == "NO CONSENSUS"
    assert "Divergence détectée" in details

def test_calculate_consensus_average():
    votes = {'alice': '3', 'bob': '5'}
    result, details = calculate_consensus(votes, 'average')
    assert float(result) == 4.0
    assert "Moyenne simple" in details

def test_calculate_consensus_median_odd():
    votes = {'alice': '1', 'bob': '3', 'charlie': '5'}
    result, details = calculate_consensus(votes, 'median')
    assert float(result) == 3.0
    assert "Médiane" in details

def test_calculate_consensus_median_even():
    votes = {'alice': '1', 'bob': '3', 'charlie': '5', 'dave': '7'}
    result, details = calculate_consensus(votes, 'median')
    assert float(result) == 4.0  # (3+5)/2
    assert "Médiane" in details

def test_calculate_consensus_non_numeric():
    votes = {'alice': '?', 'bob': '☕️'}
    result, details = calculate_consensus(votes, 'average')
    assert "N/A" in result
    assert "Aucun vote" in details

# -----------------------------
# Tests SocketIO avec test_client
# -----------------------------

def test_join_and_submit_vote():
    room_id = 'ROOM1'
    rooms[room_id] = {
        'participants': {},
        'admin_name': 'admin',
        'admin_sid': None,
        'backlog': [{'name': 'Tâche 1', 'description': 'desc', 'votes': {}}],
        'votes': {},
        'is_started': True,
        'is_revealed': False
    }

    # Créer un client SocketIO pour simuler la connexion
    with app.app_context():
        client = socketio.test_client(app)
        
        # Joindre la salle
        client.emit('join', {'username': 'bob', 'room_id': room_id})
        assert 'bob' in rooms[room_id]['participants'].values()

        # Soumettre un vote
        client.emit('submit_vote', {'username': 'bob', 'room_id': room_id, 'vote': '5'})
        assert rooms[room_id]['votes']['bob'] == '5'

