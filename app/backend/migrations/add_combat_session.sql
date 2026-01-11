-- Migration: Add combat_session table
-- Run this to add combat tracking support

CREATE TABLE IF NOT EXISTS combat_session (
    id SERIAL PRIMARY KEY,
    player_id INTEGER NOT NULL REFERENCES player_character(id),
    status VARCHAR(20) NOT NULL DEFAULT 'active',
    description TEXT,
    team_player JSON DEFAULT '[]',
    team_enemy JSON DEFAULT '[]',
    outcome VARCHAR(50),
    summary TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    ended_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX IF NOT EXISTS idx_combat_session_player_id ON combat_session(player_id);
CREATE INDEX IF NOT EXISTS idx_combat_session_status ON combat_session(status);
