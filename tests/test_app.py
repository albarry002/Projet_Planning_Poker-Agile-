# tests/test_app.py
import pytest
from unittest.mock import patch, MagicMock
from app import app, calculate_consensus, rooms
from flask import session

# --- FIXTURE FLASK TEST CLIENT ---
@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        with client.session_transaction() as sess:
            sess['username'] = 'test_user'
        yield client

# -------------------
# TESTS CALCUL CONSENSUS
# -------------------
def test_calculate_consensus_strict_consensus():
    votes = {'alice': '3', 'bob': '3'}
    result, details = calculate_consensus(votes, 'strict')
    assert result == '3'
    assert "Consensus atteint" in details

def test_calculate_consensus_strict_no_consensus():
    votes = {'alice': '3', 'bob': '5'}
    result, details = calculate_consensus(votes, 'strict')
    assert result == 'NO CONSENSUS'
    assert "Divergence" in details

def test_calculate_consensus_average():
    votes = {'alice': '3', 'bob': '5'}
    result, details = calculate_consensus(votes, 'average')
    assert result == 4.0
    assert "Moyenne simple" in details

def test_calculate_consensus_median_even():
    votes = {'alice': '1', 'bob': '3'}
    result, details = calculate_consensus(votes, 'median')
    assert result == '2.0'
    assert "Médiane" in details

def test_calculate_consensus_empty():
    votes = {'alice': '?', 'bob': '☕️'}
    result, details = calculate_consensus(votes, 'average')
    assert "N/A" in result

# -------------------
# TESTS ROUTES FLASK
# -------------------
def test_home_route(client):
    rv = client.get('/')
    page_content = rv.get_data(as_text=True)
    assert "Créer" in page_content or "Rejoindre" in page_content

def test_create_room(client):
    data = {
        'username': 'admin',
        'session_name': 'Session Test',
        'session_type': 'strict'
    }
    rv = client.post('/create_room', data=data)
    assert rv.status_code == 302  # Redirection vers /room/<room_id>

def test_join_existing_room(client):
    room_id = 'TEST123'
    rooms[room_id] = {
        'participants': {},
        'admin_name': 'admin',
        'backlog': [],
        'votes': {},
        'is_started': False
    }
    data = {'username': 'bob', 'room_id': room_id}
    rv = client.post('/join_room', data=data)
    assert rv.status_code == 302

# -------------------
# TESTS SOCKET.IO
# -------------------
@patch('app.emit')
def test_join_socketio(mock_emit):
    room_id = 'ROOM1'
    rooms[room_id] = {'participants': {}, 'admin_name': 'admin', 'admin_sid': None, 'backlog': [], 'votes': {}, 'is_started': False}
    
    mock_request = MagicMock()
    mock_request.sid = 'SID123'
    
    with patch('app.request', mock_request):
        from app import on_join
        data = {'username': 'admin', 'room_id': room_id}
        on_join(data)
    
    assert rooms[room_id]['admin_sid'] == 'SID123'
    assert rooms[room_id]['participants']['SID123'] == 'admin'
    assert mock_emit.called

@patch('app.emit')
def test_submit_vote(mock_emit):
    room_id = 'ROOMVOTE'
    rooms[room_id] = {'participants': {'SID1': 'alice'}, 'admin_name': 'admin', 'admin_sid': 'SIDADMIN',
                      'backlog': [{'name':'task1'}], 'votes': {}, 'is_started': True, 'is_revealed': False}
    
    mock_request = MagicMock()
    mock_request.sid = 'SID1'
    
    with patch('app.request', mock_request):
        from app import on_submit_vote
        data = {'username': 'alice', 'room_id': room_id, 'vote': '5'}
        on_submit_vote(data)
    
    assert rooms[room_id]['votes']['alice'] == '5'
    assert mock_emit.called

@patch('app.emit')
def test_reveal_votes(mock_emit):
    room_id = 'ROOMREVEAL'
    rooms[room_id] = {'participants': {'SID1': 'alice'}, 'admin_name': 'admin', 'admin_sid': 'SIDADMIN',
                      'backlog':[{'name':'task1'}], 'votes': {'alice': '3'}, 'is_started': True, 'is_revealed': False, 'session_type':'strict', 'current_story_index':0}
    
    mock_request = MagicMock()
    mock_request.sid = 'SIDADMIN'
    
    with patch('app.request', mock_request):
        from app import on_reveal_votes
        data = {'room_id': room_id}
        on_reveal_votes(data)
    
    assert rooms[room_id]['is_revealed'] is True
    assert 'final_vote' in rooms[room_id]['backlog'][0]
    assert mock_emit.called

