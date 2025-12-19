# tests/test_app.py
import pytest
from unittest.mock import patch, MagicMock
from app import calculate_consensus, rooms, app

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
# Tests SocketIO (avec contexte Flask)
# -----------------------------

@patch('app.emit')
def test_submit_vote_socketio(mock_emit):
    room_id = 'ROOM2'
    rooms[room_id] = {
        'participants': {'SID456': 'bob'},
        'admin_name': 'admin',
        'admin_sid': 'ADMIN123',
        'backlog': [{'name': 'Tâche 1', 'description': 'desc', 'votes': {}}],
        'votes': {},
        'is_started': True,
        'is_revealed': False
    }

    mock_request = MagicMock()
    mock_request.sid = 'SID456'

    with app.test_request_context():
        with patch('app.request', mock_request):
            from app import on_submit_vote
            data = {'username': 'bob', 'room_id': room_id, 'vote': '5'}
            on_submit_vote(data)
            assert rooms[room_id]['votes']['bob'] == '5'
            mock_emit.assert_called()

# Test pour la fonction request_backlog_download
@patch('app.emit')
def test_request_backlog_download_socketio(mock_emit):
    room_id = 'ROOM3'
    rooms[room_id] = {
        'participants': {},
        'admin_name': 'admin',
        'admin_sid': 'ADMIN123',
        'backlog': [{'name': 'Story 1', 'description': 'desc'}],
        'votes': {},
        'is_started': True
    }

    mock_request = MagicMock()
    mock_request.sid = 'ADMIN123'

    with app.test_request_context():
        with patch('app.request', mock_request):
            from app import on_request_backlog_download
            data = {'room_id': room_id}
            on_request_backlog_download(data)
            mock_emit.assert_called_with(
                'backlog_updated',
                {'backlog_data': rooms[room_id]['backlog']},
                room='ADMIN123'
            )

