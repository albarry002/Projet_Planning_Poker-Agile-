# tests/test_app.py
import pytest
from app import calculate_consensus, rooms, app
from unittest.mock import patch, MagicMock

# -------------------------
# Tests unitaires calculate_consensus
# -------------------------

def test_calculate_consensus_strict_consensus():
    votes = {'alice': '3', 'bob': '3'}
    result, details = calculate_consensus(votes, 'strict')
    assert float(result) == 3  # conversion en float pour éviter '3.0' vs '3'
    assert "Consensus atteint" in details

def test_calculate_consensus_strict_no_consensus():
    votes = {'alice': '3', 'bob': '5'}
    result, details = calculate_consensus(votes, 'strict')
    assert result == "NO CONSENSUS"

def test_calculate_consensus_average():
    votes = {'alice': '3', 'bob': '5'}
    result, details = calculate_consensus(votes, 'average')
    assert float(result) == 4.0
    assert "Moyenne" in details

def test_calculate_consensus_median_odd():
    votes = {'alice': '3', 'bob': '5', 'carol': '8'}
    result, details = calculate_consensus(votes, 'median')
    assert float(result) == 5
    assert "Médiane" in details

def test_calculate_consensus_median_even():
    votes = {'alice': '3', 'bob': '5', 'carol': '8', 'dan': '13'}
    result, details = calculate_consensus(votes, 'median')
    assert float(result) == 6.5
    assert "Médiane" in details

def test_calculate_consensus_no_numeric():
    votes = {'alice': '?', 'bob': '☕️'}
    result, details = calculate_consensus(votes, 'average')
    assert "N/A" in result

# -------------------------
# Tests Flask-SocketIO (fonction on_join)
# -------------------------

@patch('app.emit')  # on empêche l'envoi réel des événements
def test_join_socketio(mock_emit):
    room_id = 'ROOM1'
    rooms[room_id] = {
        'participants': {}, 
        'admin_name': 'admin', 
        'admin_sid': None, 
        'backlog': [], 
        'votes': {}, 
        'is_started': False
    }

    # Simuler request.sid
    mock_request = MagicMock()
    mock_request.sid = 'SID123'

    with app.app_context():  # Contexte Flask nécessaire
        with patch('app.request', mock_request):
            from app import on_join
            data = {'username': 'admin', 'room_id': room_id}
            on_join(data)
            assert 'SID123' in rooms[room_id]['participants']
            assert rooms[room_id]['admin_sid'] == 'SID123'
            mock_emit.assert_called()  # vérifier qu'un emit a été appelé

# -------------------------
# Test submit_vote
# -------------------------
@patch('app.emit')
def test_submit_vote(mock_emit):
    room_id = 'ROOM2'
    rooms[room_id] = {
        'participants': {'SID1': 'alice'}, 
        'admin_name': 'admin',
        'admin_sid': 'SIDADMIN',
        'backlog': [{'name': 'Tâche1', 'votes': {}}],
        'votes': {},
        'is_started': True,
        'is_revealed': False
    }

    mock_request = MagicMock()
    mock_request.sid = 'SID1'

    with app.app_context():
        with patch('app.request', mock_request):
            from app import on_submit_vote
            data = {'room_id': room_id, 'username': 'alice', 'vote': '5'}
            on_submit_vote(data)
            assert rooms[room_id]['votes']['alice'] == '5'
            mock_emit.assert_called()

# -------------------------
# Test reveal_votes
# -------------------------
@patch('app.emit')
def test_reveal_votes(mock_emit):
    room_id = 'ROOM3'
    rooms[room_id] = {
        'participants': {'SIDADMIN': 'admin'}, 
        'admin_name': 'admin',
        'admin_sid': 'SIDADMIN',
        'backlog': [{'name': 'Tâche1', 'votes': {}}],
        'votes': {'admin': '3'},
        'is_started': True,
        'is_revealed': False,
        'session_type': 'strict',
        'current_story_index': 0
    }

    mock_request = MagicMock()
    mock_request.sid = 'SIDADMIN'

    with app.app_context():
        with patch('app.request', mock_request):
            from app import on_reveal_votes
            data = {'room_id': room_id}
            on_reveal_votes(data)
            assert rooms[room_id]['is_revealed'] is True
            assert 'final_vote' in rooms[room_id]['backlog'][0]
            mock_emit.assert_called()
