-- Migration: Add story_messages column to player_character table
-- Run this if you have an existing database

ALTER TABLE player_character ADD COLUMN IF NOT EXISTS story_messages JSON DEFAULT '[]';

-- Note: This replaces the old chat_session and chat_message tables
-- You can optionally drop them after migrating any existing data:
-- DROP TABLE IF EXISTS chat_message;
-- DROP TABLE IF EXISTS chat_session;
