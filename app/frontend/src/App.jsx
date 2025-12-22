import { Routes, Route } from 'react-router-dom'
import PlayerList from './views/PlayerList'
import CreatePlayer from './views/CreatePlayer'
import Chat from './views/Chat'

function App() {
  return (
    <div className="container">
      <Routes>
        <Route path="/" element={<PlayerList />} />
        <Route path="/create" element={<CreatePlayer />} />
        <Route path="/chat/:playerId" element={<Chat />} />
      </Routes>
    </div>
  )
}

export default App
