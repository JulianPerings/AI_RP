import { useState, useEffect, useRef } from 'react'
import { Link, useParams, useSearchParams } from 'react-router-dom'
import { getPlayer, startSession, sendMessage, getStory, autocompleteAction, getPlayerInventory, getItemTemplate, rollDice, getCombatState, textToSpeech } from '../api'
import CombatHud from '../components/CombatHud'

const LOADING_MESSAGES = [
  "The Game Master is weaving your tale...",
  "Rolling the dice of fate...",
  "Consulting ancient scrolls...",
  "The quill scratches across parchment...",
  "Destiny unfolds before you...",
  "The threads of fate intertwine...",
  "Magic flows through the realm...",
  "Your story takes shape..."
]

function Chat() {
  const { playerId } = useParams()
  const [searchParams] = useSearchParams()
  const isNewCharacter = searchParams.get('new') === 'true'

  function getLlmSettings() {
    return {
      provider: localStorage.getItem('llm_provider') || null,
      model: localStorage.getItem('llm_model') || null,
      thinking: localStorage.getItem('llm_thinking') === 'true' ? true : null,
    }
  }
  
  const [player, setPlayer] = useState(null)
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(true)
  const [sending, setSending] = useState(false)
  const [autocompleting, setAutocompleting] = useState(false)
  const [loadingMessage, setLoadingMessage] = useState(LOADING_MESSAGES[0])
  const [error, setError] = useState(null)
  const [showInventory, setShowInventory] = useState(false)
  const [inventory, setInventory] = useState([])
  const [loadingInventory, setLoadingInventory] = useState(false)

  // Combat HUD state
  const [combatState, setCombatState] = useState(null)
  
  // Dice rolling state
  const [diceRoll, setDiceRoll] = useState(null)  // Current roll result
  const [isRolling, setIsRolling] = useState(false)  // Animation state
  const [diceAnimating, setDiceAnimating] = useState(false)  // Throw animation
  
  // TTS state — streaming chunked WAV playback
  const [ttsPlaying, setTtsPlaying] = useState(false)
  const ttsAudioRef = useRef(null)
  const ttsControlRef = useRef(null)  // { stopped, queue, playing, audio }

  const messagesEndRef = useRef(null)
  const loadingIntervalRef = useRef(null)
  const initializedRef = useRef(false)

  useEffect(() => {
    // Prevent double initialization from React StrictMode
    if (initializedRef.current) return
    initializedRef.current = true
    
    initializeChat()
    return () => {
      if (loadingIntervalRef.current) {
        clearInterval(loadingIntervalRef.current)
      }
    }
  }, [playerId])

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  useEffect(() => {
    if (sending || loading) {
      let idx = 0
      loadingIntervalRef.current = setInterval(() => {
        idx = (idx + 1) % LOADING_MESSAGES.length
        setLoadingMessage(LOADING_MESSAGES[idx])
      }, 3000)
    } else {
      if (loadingIntervalRef.current) {
        clearInterval(loadingIntervalRef.current)
      }
    }
    return () => {
      if (loadingIntervalRef.current) {
        clearInterval(loadingIntervalRef.current)
      }
    }
  }, [sending, loading])

  function scrollToBottom() {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  function isTtsEnabled() {
    return localStorage.getItem('tts_enabled') === 'true'
  }

  async function playTts(text, pid) {
    if (!isTtsEnabled() || !text) return

    // Stop any previous playback
    stopTts()

    const ctrl = { stopped: false, queue: [], playing: false, audio: null }
    ttsControlRef.current = ctrl
    setTtsPlaying(true)

    // Sequential queue player — starts as soon as the first chunk arrives
    function playNext() {
      if (ctrl.stopped || ctrl.queue.length === 0) {
        ctrl.playing = false
        // If stream finished and queue drained, we're done
        if (ctrl.streamDone && ctrl.queue.length === 0 && !ctrl.stopped) {
          setTtsPlaying(false)
          ttsControlRef.current = null
        }
        return
      }
      ctrl.playing = true
      const blob = ctrl.queue.shift()
      const url = URL.createObjectURL(blob)
      const audio = new Audio(url)
      ctrl.audio = audio
      ttsAudioRef.current = audio
      const onFinish = () => {
        URL.revokeObjectURL(url)
        ctrl.audio = null
        playNext()
      }
      audio.onended = onFinish
      audio.onerror = onFinish
      audio.play().catch(onFinish)
    }

    try {
      const response = await textToSpeech(text, pid || playerId)
      if (ctrl.stopped) return

      const reader = response.body.getReader()
      let buffer = new Uint8Array(0)

      while (!ctrl.stopped) {
        const { done, value } = await reader.read()
        if (done) break

        // Append new data to buffer
        const merged = new Uint8Array(buffer.length + value.length)
        merged.set(buffer)
        merged.set(value, buffer.length)
        buffer = merged

        // Parse length-prefixed WAV chunks: [4-byte BE uint32 length][WAV bytes]
        while (buffer.length >= 4) {
          const view = new DataView(buffer.buffer, buffer.byteOffset, buffer.byteLength)
          const chunkLen = view.getUint32(0, false)
          if (buffer.length < 4 + chunkLen) break

          const wavData = buffer.slice(4, 4 + chunkLen)
          buffer = buffer.slice(4 + chunkLen)

          ctrl.queue.push(new Blob([wavData], { type: 'audio/wav' }))
          if (!ctrl.playing) playNext()
        }
      }

      ctrl.streamDone = true
      // If nothing is playing and queue is empty, mark done
      if (!ctrl.playing && ctrl.queue.length === 0) {
        setTtsPlaying(false)
        ttsControlRef.current = null
      }
    } catch (err) {
      console.error('TTS streaming failed:', err)
      setTtsPlaying(false)
      ttsControlRef.current = null
    }
  }

  function stopTts() {
    const ctrl = ttsControlRef.current
    if (ctrl) {
      ctrl.stopped = true
      ctrl.queue = []
      if (ctrl.audio) {
        ctrl.audio.pause()
        if (ctrl.audio.src) URL.revokeObjectURL(ctrl.audio.src)
      }
    }
    if (ttsAudioRef.current) {
      ttsAudioRef.current.pause()
      ttsAudioRef.current = null
    }
    ttsControlRef.current = null
    setTtsPlaying(false)
  }

  function formatStoryMessages(story) {
    if (!story?.messages) return []
    return story.messages.map(msg => ({
      role: msg.role === 'player' ? 'player' : 'gm',
      content: msg.content,
      tags: msg.tags || [],
      toolCalls: []
    }))
  }

  function attachToolCallsToLatestGm(messagesList, toolCalls) {
    if (!messagesList?.length) return messagesList
    for (let i = messagesList.length - 1; i >= 0; i--) {
      if (messagesList[i]?.role === 'gm') {
        messagesList[i] = { ...messagesList[i], toolCalls: toolCalls || [] }
        return messagesList
      }
    }
    return messagesList
  }

  async function initializeChat() {
    try {
      setLoading(true)

      const playerData = await getPlayer(playerId)
      setPlayer(playerData)

      // Load combat state for HUD
      try {
        const cs = await getCombatState(parseInt(playerId))
        setCombatState(cs)
      } catch {
        setCombatState(null)
      }

      // Try to load existing story
      const story = await getStory(parseInt(playerId))
      
      if (isNewCharacter || !story.messages || story.messages.length === 0) {
        // New character or no story - start a fresh session
        const { provider, model, thinking } = getLlmSettings()
        const session = await startSession(parseInt(playerId), provider, model, thinking)
        setMessages([{
          role: 'gm',
          content: session.intro,
          toolCalls: session.tool_calls || []
        }])
        // Auto-play TTS for session intro
        playTts(session.intro, playerId)
      } else {
        // Existing story - load messages
        const formatted = formatStoryMessages(story)
        setMessages(formatted)
      }
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  async function refreshCombat() {
    try {
      const cs = await getCombatState(parseInt(playerId))
      setCombatState(cs)
      return cs
    } catch {
      setCombatState(null)
      return null
    }
  }

  async function handleAutocomplete() {
    if (sending || autocompleting || !player) return
    
    setAutocompleting(true)
    try {
      const { provider, model, thinking } = getLlmSettings()
      const result = await autocompleteAction(
        parseInt(playerId),
        input.trim(),
        provider, model, thinking
      )
      console.log('Autocomplete result:', result)
      if (result && result.suggestion) {
        setInput(result.suggestion)
      }
    } catch (err) {
      console.error('Autocomplete failed:', err)
    } finally {
      setAutocompleting(false)
    }
  }

  async function handleOpenInventory() {
    setShowInventory(true)
    setLoadingInventory(true)
    try {
      const items = await getPlayerInventory(parseInt(playerId))
      // Fetch template info for each item
      const itemsWithTemplates = await Promise.all(
        items.map(async (item) => {
          try {
            const template = await getItemTemplate(item.template_id)
            return { ...item, template }
          } catch {
            return { ...item, template: null }
          }
        })
      )
      setInventory(itemsWithTemplates)
    } catch (err) {
      console.error('Failed to load inventory:', err)
      setInventory([])
    } finally {
      setLoadingInventory(false)
    }
  }

  async function handleRollDice(useLuck = false) {
    if (isRolling || sending) return
    
    setIsRolling(true)
    setDiceAnimating(true)
    
    try {
      const result = await rollDice(parseInt(playerId), useLuck)
      
      // Wait for throw animation
      await new Promise(resolve => setTimeout(resolve, 600))
      setDiceAnimating(false)
      
      // Update dice roll and player luck
      setDiceRoll(result)
      setPlayer(prev => ({ ...prev, luck: result.luck_remaining }))
      
    } catch (err) {
      console.error('Dice roll failed:', err)
      setDiceAnimating(false)
    } finally {
      setIsRolling(false)
    }
  }

  async function handleSend(e) {
    e.preventDefault()
    if (!input.trim() || sending || !player) return

    // Build message with optional dice roll
    let userMessage = input.trim()
    if (diceRoll) {
      const rollInfo = diceRoll.is_critical ? ' [CRITICAL SUCCESS - Natural 20!]' :
                       diceRoll.is_fumble ? ' [CRITICAL FAIL - Natural 1!]' :
                       ` [Rolled: ${diceRoll.roll}]`
      userMessage = userMessage + rollInfo
    }
    
    // Build tags for the message BEFORE clearing diceRoll
    const tags = diceRoll ? [`dice:${diceRoll.roll}`, diceRoll.is_critical ? 'critical' : diceRoll.is_fumble ? 'fumble' : null].filter(Boolean) : null
    
    setInput('')
    setDiceRoll(null)  // Clear dice after sending
    setSending(true)

    // Add player message immediately
    setMessages(prev => [...prev, { role: 'player', content: userMessage, tags: tags || [] }])

    try {
      const { provider, model, thinking } = getLlmSettings()
      const response = await sendMessage(
        parseInt(playerId),
        userMessage,
        tags,
        provider, model, thinking
      )

      const gmToolCalls = response.tool_calls || []
      const endedCombatThisTurn = gmToolCalls.some(tc => tc?.tool === 'end_combat')

      // If combat ended this turn, the backend does not persist this final GM response.
      // Avoid showing it briefly in the UI; we'll sync from story (which contains the summary).
      if (!endedCombatThisTurn) {
        setMessages(prev => [...prev, {
          role: 'gm',
          content: response.response,
          toolCalls: gmToolCalls
        }])
      }
      
      // Auto-play TTS for GM response
      playTts(response.response, playerId)

      // Refresh player stats (health, gold may have changed)
      const updatedPlayer = await getPlayer(playerId)
      setPlayer(updatedPlayer)

      // Refresh combat HUD (combat may have started/ended or HP changed)
      const wasInCombat = !!combatState?.in_combat
      const cs = await refreshCombat()

      // Always sync messages from story after GM responds so server-side compression/tag edits
      // (e.g. end_combat compression, retro-tagging) are reflected without manual reload.
      const story = await getStory(parseInt(playerId))
      const formatted = attachToolCallsToLatestGm(formatStoryMessages(story), gmToolCalls)
      setMessages(formatted)
    } catch (err) {
      setError(err.message)
      // Remove the player message on error
      setMessages(prev => prev.slice(0, -1))
    } finally {
      setSending(false)
    }
  }

  if (loading) {
    return (
      <div>
        <Link to="/" className="nav-back">← Back to Characters</Link>
        <div className="loading-container" style={{ minHeight: '60vh' }}>
          <div className="loading-quill">🪶</div>
          <div className="loading-spinner"></div>
          <p className="loading-text">{loadingMessage}</p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div>
        <Link to="/" className="nav-back">← Back to Characters</Link>
        <div className="card" style={{ borderColor: 'var(--accent)', textAlign: 'center' }}>
          <h3 style={{ color: 'var(--accent)' }}>Something went wrong</h3>
          <p>{error}</p>
          <button className="btn btn-secondary" onClick={() => window.location.reload()} style={{ marginTop: '1rem' }}>
            Try Again
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="chat-container">
      <div className="chat-header">
        <div className="chat-header-left">
          <Link to="/" className="nav-back">← Exit</Link>
        </div>
        
        <div className="chat-header-center">
          <span className="player-name">{player?.name}</span>
          <div className="player-info">
            <span className="class-name">{player?.character_class || 'Adventurer'}</span>
            <span>•</span>
            <span>Level {player?.level}</span>
          </div>
          <div className="stat-display xp">
            <span>XP</span>
            <div style={{ 
              width: '60px', 
              height: '6px', 
              background: 'rgba(255,255,255,0.15)', 
              borderRadius: '3px',
              overflow: 'hidden'
            }}>
              <div style={{ 
                width: `${player?.experience || 0}%`, 
                height: '100%', 
                background: 'linear-gradient(90deg, #60a5fa, #a78bfa)',
                borderRadius: '3px'
              }} />
            </div>
            <span style={{ fontSize: '0.8rem' }}>{player?.experience || 0}/100</span>
          </div>
        </div>

        <div className="chat-header-right">
          <div className="stat-display health">
            <span>❤️</span>
            <span>{player?.health}/{player?.max_health}</span>
          </div>
          <div className="stat-display gold">
            <span>💰</span>
            <span>{player?.gold}</span>
          </div>
          <div className="stat-display luck">
            <span>🍀</span>
            <span>{player?.luck ?? 3}</span>
          </div>
        </div>
      </div>

      <CombatHud combatState={combatState} />

      <div className="chat-messages">
        {messages.map((msg, idx) => (
          <div key={idx} className={`message message-${msg.role === 'gm' ? 'gm' : 'player'}`}>
            <div className="message-label">
              {msg.role === 'gm' ? (
                <>
                  📖 Game Master
                  {isTtsEnabled() && (
                    <button
                      type="button"
                      className="btn-tts-play"
                      onClick={(e) => { e.stopPropagation(); playTts(msg.content, playerId) }}
                      title="Play narration"
                    >
                      {ttsPlaying ? '⏹' : '🔊'}
                    </button>
                  )}
                </>
              ) : '⚔️ You'}
            </div>
            <div className="message-content">{msg.content}</div>
            {msg.toolCalls && msg.toolCalls.length > 0 && (
              <div className="tool-calls">
                {msg.toolCalls.map((tc, i) => (
                  <span key={i} className="tool-call">
                    🔧 {tc.tool}
                  </span>
                ))}
              </div>
            )}
          </div>
        ))}
        
        {sending && (
          <div className="message message-gm">
            <div className="message-label">📖 Game Master</div>
            <div className="loading-container" style={{ padding: '1rem 0' }}>
              <div className="loading-quill">🪶</div>
              <p className="loading-text">{loadingMessage}</p>
            </div>
          </div>
        )}
        
        <div ref={messagesEndRef} />
      </div>

      <div className="chat-bottom-row">
        <button 
          type="button"
          className="btn btn-inventory"
          onClick={handleOpenInventory}
          title="Open Inventory"
        >
          🎒 Inventory
        </button>

        <form onSubmit={handleSend} className="chat-input-area">
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault()
                if (input.trim() && !sending) handleSend(e)
              }
            }}
            placeholder={sending ? "The Game Master is responding..." : "What do you do? (Shift+Enter for new line)"}
            disabled={sending || autocompleting || diceRoll}
            autoFocus
            rows={2}
          />
          <button 
            type="button"
            className="btn btn-secondary"
            onClick={handleAutocomplete}
            disabled={sending || autocompleting || diceRoll}
            title="Generate or polish your action"
          >
            {autocompleting ? '...' : '✨'}
          </button>
          
          {/* Dice Roll Button */}
          <button 
            type="button"
            className={`btn btn-dice ${!input.trim() ? 'disabled' : ''} ${diceRoll ? 'has-roll' : ''} ${diceAnimating ? 'throwing' : ''} ${diceRoll?.is_critical ? 'critical' : ''} ${diceRoll?.is_fumble ? 'fumble' : ''}`}
            onClick={() => diceRoll ? (player?.luck > 0 ? handleRollDice(true) : null) : handleRollDice(false)}
            disabled={!input.trim() || isRolling || sending || (diceRoll && player?.luck <= 0)}
          >
            <span className={`dice-icon ${diceAnimating ? 'animate-throw' : ''}`}>
              {isRolling && !diceRoll ? '🎲' : diceRoll ? diceRoll.roll : '🎲'}
            </span>
          </button>
          
          <button 
            type="submit" 
            className="btn btn-primary"
            disabled={sending || !input.trim()}
          >
            {sending ? '...' : 'Send'}
          </button>
        </form>
      </div>

      {/* Inventory Modal */}
      {showInventory && (
        <div className="modal-overlay" onClick={() => setShowInventory(false)}>
          <div className="modal-content inventory-modal" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h2>🎒 Inventory</h2>
              <div className="inventory-legend">
                <span className="legend-item"><span className="legend-dot equipped"></span> Equipped</span>
              </div>
              <button className="modal-close" onClick={() => setShowInventory(false)}>×</button>
            </div>
            <div className="modal-body">
              {loadingInventory ? (
                <div className="loading-container">
                  <div className="loading-spinner" />
                  <p>Loading inventory...</p>
                </div>
              ) : inventory.length === 0 ? (
                <p className="empty-inventory">Your inventory is empty.</p>
              ) : (
                <div className="inventory-grid">
                  {inventory.map((item, idx) => (
                    <div key={idx} className={`inventory-item ${item.is_equipped ? 'equipped' : ''}`}>
                      <div className="item-icon">
                        {item.template?.category === 'weapon' ? '⚔️' :
                         item.template?.category === 'armor' ? '🛡️' :
                         item.template?.category === 'consumable' ? '🧪' :
                         item.template?.category === 'quest' ? '📜' : '📦'}
                      </div>
                      <div className="item-details">
                        <span className="item-name">{item.custom_name || item.template?.name || 'Unknown Item'}</span>
                        {item.quantity > 1 && <span className="item-quantity">x{item.quantity}</span>}
                        {item.is_equipped && <span className="item-equipped">EQUIPPED</span>}
                      </div>
                      {item.template?.description && (
                        <p className="item-description">{item.template.description}</p>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default Chat
