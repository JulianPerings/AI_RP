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

export async function startSession(playerId, llmProvider = null, model = null, thinking = null) {
  const res = await fetch(`${API_BASE}/game/start-session`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ player_id: playerId, llm_provider: llmProvider, model, thinking })
  });
  if (!res.ok) throw new Error('Failed to start session');
  return res.json();
}

export async function sendMessage(playerId, message, tags = null, llmProvider = null, model = null, thinking = null) {
  const res = await fetch(`${API_BASE}/game/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      player_id: playerId,
      message,
      tags,
      llm_provider: llmProvider,
      model,
      thinking
    })
  });
  if (!res.ok) throw new Error('Failed to send message');
  return res.json();
}

export async function getStory(playerId, limit = 50) {
  const res = await fetch(`${API_BASE}/game/story/${playerId}?limit=${limit}`);
  if (!res.ok) throw new Error('Failed to fetch story');
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

export async function autocompleteAction(playerId, userInput = '', llmProvider = null, model = null, thinking = null) {
  const res = await fetch(`${API_BASE}/game/autocomplete`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      player_id: playerId,
      user_input: userInput,
      llm_provider: llmProvider,
      model,
      thinking
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

export async function getCombatState(playerId) {
  const res = await fetch(`${API_BASE}/game/combat/${playerId}`);
  if (!res.ok) throw new Error('Failed to fetch combat state');
  return res.json();
}

export async function getAvailableProviders() {
  const res = await fetch(`${API_BASE}/game/providers`);
  if (!res.ok) throw new Error('Failed to fetch providers');
  return res.json();
}

export async function textToSpeech(text, playerId) {
  const body = { text };
  if (playerId) body.player_id = parseInt(playerId);
  const res = await fetch(`${API_BASE}/game/tts`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body)
  });
  if (!res.ok) throw new Error('TTS generation failed');
  return res;  // raw Response — caller reads the chunked-wav stream
}
