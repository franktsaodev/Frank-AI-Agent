import { useEffect, useState } from 'react'

import { createSession, getHealth } from './api/client'
import type {
  CreateSessionResponse,
  HealthResponse,
} from './api/types'
import './App.css'

const capabilities = [
  {
    title: 'Knowledge retrieval',
    description: 'Ask questions about indexed project documentation.',
  },
  {
    title: 'Trusted citations',
    description: 'Receive answers backed by validated document sources.',
  },
  {
    title: 'Agent tools',
    description: 'Interact with tools through the agent execution flow.',
  },
] as const

type ConnectionState = 'checking' | 'online' | 'offline'

interface InitializationResult {
  health: HealthResponse
  session: CreateSessionResponse
}

let initializationPromise: Promise<InitializationResult> | null = null

function initializeApplication(): Promise<InitializationResult> {
  if (initializationPromise === null) {
    initializationPromise = getHealth()
      .then(async (health) => {
        const session = await createSession()

        return {
          health,
          session,
        }
      })
      .catch((error: unknown) => {
        initializationPromise = null

        throw error
      })
  }

  return initializationPromise
}

function App() {
  const [connectionState, setConnectionState] =
    useState<ConnectionState>('checking')
  const [health, setHealth] = useState<HealthResponse | null>(null)
  const [sessionId, setSessionId] = useState<string | null>(null)

  useEffect(() => {
    let active = true

    void initializeApplication()
      .then((result) => {
        if (!active) {
          return
        }

        setHealth(result.health)
        setSessionId(result.session.session_id)
        setConnectionState('online')
      })
      .catch(() => {
        if (active) {
          setConnectionState('offline')
        }
      })

    return () => {
      active = false
    }
  }, [])

  const connectionTitle = {
    checking: 'Initializing agent',
    online: 'Agent ready',
    offline: 'API unavailable',
  }[connectionState]

  const connectionDescription =
    connectionState === 'online' && health !== null
      ? `${health.service} ${health.version}`
      : connectionState === 'offline'
        ? 'Start the FastAPI service'
        : 'Creating an isolated session'

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-mark" aria-hidden="true">
            F
          </div>

          <div>
            <p className="brand-eyebrow">AI Agent</p>
            <h1>Frank</h1>
          </div>
        </div>

        <div className="sidebar-section">
          <p className="sidebar-label">Workspace</p>

          <div className="navigation-item navigation-item-active">
            <span className="navigation-icon" aria-hidden="true">
              ◇
            </span>
            New conversation
          </div>

          {sessionId !== null && (
            <div className="session-card">
              <p>Active session</p>
              <code title={sessionId}>{sessionId}</code>
            </div>
          )}
        </div>

        <div className="sidebar-footer" aria-live="polite">
          <span
            className={`status-dot status-dot-${connectionState}`}
            aria-hidden="true"
          />

          <div>
            <strong>{connectionTitle}</strong>
            <span>{connectionDescription}</span>
          </div>
        </div>
      </aside>

      <main className="workspace">
        <header className="workspace-header">
          <div>
            <p className="workspace-eyebrow">Agent Playground</p>
            <h2>New conversation</h2>
          </div>

          <span className="version-badge">
            {health === null ? 'v1.3 in progress' : `API ${health.version}`}
          </span>
        </header>

        <section className="conversation" aria-labelledby="welcome-heading">
          <div className="welcome">
            <div className="welcome-icon" aria-hidden="true">
              ✦
            </div>

            <p className="welcome-eyebrow">Frank AI Agent</p>
            <h2 id="welcome-heading">What can I help you explore?</h2>

            <p className="welcome-description">
              Chat with a modular AI agent featuring retrieval, memory,
              tool calling, and trusted source attribution.
            </p>

            <div className="capability-grid">
              {capabilities.map((capability) => (
                <article className="capability-card" key={capability.title}>
                  <h3>{capability.title}</h3>
                  <p>{capability.description}</p>
                </article>
              ))}
            </div>
          </div>
        </section>

        <footer className="composer">
          <div className="composer-control">
            <textarea
              aria-label="Chat message"
              disabled
              placeholder={
                sessionId === null
                  ? 'Waiting for an agent session…'
                  : 'Session ready — chat integration comes next…'
              }
              rows={1}
            />

            <button type="button" disabled>
              Send
            </button>
          </div>

          <p>
            {sessionId === null
              ? 'Connecting to the Frank AI Agent API'
              : 'Session initialized · Chat endpoint integration comes next'}
          </p>
        </footer>
      </main>
    </div>
  )
}

export default App