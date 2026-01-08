const API_BASE = '/api';

export async function getPlayers() {
  const res = await fetch(`${API_BASE}/player-characters/`);
  if (!res.ok) throw new Error('Failed to fetch players');
  return res.json();
}

export async function getPlayer(id) {
  const res = await fetch(`${API_BASE}/player-characters/${id}`);
  if (!res.ok) throw new Error('Failed to fetch player');
  return res.json();
}

export async function createPlayer(data) {
  const res = await fetch(`${API_BASE}/player-characters/`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data)
  });
  if (!res.ok) throw new Error('Failed to create player');
  return res.json();
}

export async function startSession(playerId) {
  const res = await fetch(`${API_BASE}/game/start-session`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ player_id: playerId })
  });
  if (!res.ok) throw new Error('Failed to start session');
  return res.json();
}

export async function sendMessage(playerId, sessionId, message) {
  const res = await fetch(`${API_BASE}/game/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      player_id: playerId,
      session_id: sessionId,
      message
    })
  });
  if (!res.ok) throw new Error('Failed to send message');
  return res.json();
}

export async function getChatHistory(sessionId) {
  const res = await fetch(`${API_BASE}/game/history/${sessionId}`);
  if (!res.ok) throw new Error('Failed to fetch history');
  return res.json();
}

export async function getLocations() {
  const res = await fetch(`${API_BASE}/locations/`);
  if (!res.ok) throw new Error('Failed to fetch locations');
  return res.json();
}

export async function getRaces() {
  const res = await fetch(`${API_BASE}/races/`);
  if (!res.ok) throw new Error('Failed to fetch races');
  return res.json();
}

export async function autocompleteAction(playerId, sessionId, userInput = '') {
  const res = await fetch(`${API_BASE}/game/autocomplete`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      player_id: playerId,
      session_id: sessionId,
      user_input: userInput
    })
  });
  if (!res.ok) throw new Error('Failed to autocomplete');
  return res.json();
}

export async function getPlayerInventory(playerId) {
  const res = await fetch(`${API_BASE}/item-instances/owner/PC/${playerId}`);
  if (!res.ok) throw new Error('Failed to fetch inventory');
  return res.json();
}

export async function getItemTemplate(templateId) {
  const res = await fetch(`${API_BASE}/item-templates/${templateId}`);
  if (!res.ok) throw new Error('Failed to fetch item template');
  return res.json();
}

export async function rollDice(playerId, useLuck = false) {
  const res = await fetch(`${API_BASE}/game/roll-dice`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      player_id: playerId,
      use_luck: useLuck
    })
  });
  if (!res.ok) {
    const error = await res.json();
    throw new Error(error.detail || 'Failed to roll dice');
  }
  return res.json();
}
