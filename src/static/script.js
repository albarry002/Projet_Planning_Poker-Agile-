const API_URL = "http://127.0.0.1:5001/api";

async function createSession() {
    const name = document.getElementById("session_name").value;
    const players = document.getElementById("players").value.split(",");
    const rule = document.getElementById("rule").value;

    const res = await fetch(`${API_URL}/session/create`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ session_name: name, players, rule })
    });

    const data = await res.json();
    document.getElementById("create_result").innerText = JSON.stringify(data, null, 2);
}

async function vote() {
    const session_id = document.getElementById("vote_session_id").value;
    const player = document.getElementById("player_name").value;
    const value = document.getElementById("vote_value").value;

    const res = await fetch(`${API_URL}/vote`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ session_id, player, value })
    });

    const data = await res.json();
    document.getElementById("vote_result").innerText = JSON.stringify(data, null, 2);
}

async function reveal() {
    const session_id = document.getElementById("reveal_session_id").value;

    const res = await fetch(`${API_URL}/votes/reveal?session_id=${session_id}`);
    const data = await res.json();
    document.getElementById("reveal_result").innerText = JSON.stringify(data, null, 2);
}
