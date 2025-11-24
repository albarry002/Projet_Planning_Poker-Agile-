const API_URL = "https://curly-space-fortnight-976qj97g4ppjcxwr7-5001.app.github.dev/api";

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

async function setMode() {
    const session_id = document.getElementById("mode_session_id").value;
    const mode = document.getElementById("mode_select").value; // "strict", "moyenne", "mediane"

    const res = await fetch(`${API_URL}/session/set_mode`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ session_id, mode })
    });

    const data = await res.json();
    document.getElementById("mode_result").innerText = JSON.stringify(data, null, 2);
}

async function vote() {
    const session_id = document.getElementById("vote_session_id").value;
    const player = document.getElementById("player_name").value;
    const value = parseFloat(document.getElementById("vote_value").value);


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
