# AI RPG Frontend

React-based frontend for the AI Game Master RPG.

## Views

### 1. Player List (`/`)
- Displays all existing player characters
- Shows stats: level, health, gold, XP
- Click any player to go to their chat session
- Link to create new character

### 2. Create Character (`/create`)
- Form to create new player character
- Fields: name, class, race, starting location, backstory
- Backstory tip: mention items and NPCs for auto-setup
- Auto-creates first session on submission
- Redirects to chat with `?new=true` to trigger intro

### 3. Chat (`/chat/:playerId`)
- Real-time chat with the AI Game Master
- Shows tool calls made by the LLM
- **Autocomplete button (✨)**: 
  - Empty input → suggests contextual action based on situation
  - With input → polishes rough idea into narrative prose
  - Uses player context, location, NPCs for smart suggestions
- **Dice Roll button (🎲)**:
  - Type action first, then click to roll d20
  - Animated throw animation
  - Shows result with critical/fumble indicators
  - Input locks after rolling - send or reroll
  - **Reroll with Luck (🍀)**: Spend luck points to reroll
  - Roll result appended to message for GM to interpret
- **Inventory button (🎒)**:
  - Opens modal showing all player items
  - Shows equipped status, quantities, descriptions
- **Loading indicator** while GM responds:
  - Input disabled during response
  - Animated quill + rotating flavor text
  - Prevents sending multiple messages
- Auto-scrolls to latest message

## Tech Stack

- **React 18** - UI framework
- **React Router 6** - Client-side routing
- **Vite** - Build tool & dev server
- **CSS** - Custom styling (fantasy theme)

## Development

```bash
# Install dependencies
npm install

# Run dev server
npm run dev

# Build for production
npm run build
```

## Docker

Runs via docker-compose:
```bash
docker-compose up
```

Frontend available at: http://localhost:5173

## API Proxy

Vite proxies `/api/*` requests to the backend:
- `/api/player-characters/` → `http://backend:8000/player-characters/`
- `/api/game/chat` → `http://backend:8000/game/chat`

## File Structure

```
src/
├── api/
│   └── index.js       # API client functions
├── views/
│   ├── PlayerList.jsx # Character selection
│   ├── CreatePlayer.jsx # Character creation form
│   └── Chat.jsx       # Game chat interface
├── App.jsx            # Router setup
├── main.jsx           # Entry point
└── index.css          # Global styles
```

## Features

- **Fantasy theme** with custom fonts (Cinzel, Crimson Text)
- **Responsive design** for desktop and mobile
- **Loading states** with playful messages
- **Tool call visibility** shows what the GM is doing
- **Session persistence** via player's current_session_id
