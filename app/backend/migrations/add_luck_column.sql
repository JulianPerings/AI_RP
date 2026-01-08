-- Migration: Add luck column to player_character table
-- Run this if you have an existing database

ALTER TABLE player_character ADD COLUMN IF NOT EXISTS luck INTEGER DEFAULT 3;
