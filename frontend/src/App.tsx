import { useEffect, useRef, useState } from 'react'
import type { FormEvent, KeyboardEvent } from 'react'

import {
  ApiError,
  createSession,
  getHealth,
  sendChatMessage,
} from './api/client'
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
type ChatMessageRole = 'user' | 'assistant'

interface InitializationResult {
  health: HealthResponse
  session: CreateSessionResponse
}

interface ChatMessage {
  id: number
  role: ChatMessageRole
  content: string
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
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [input, setInput] = useState('')
  const [isSending, setIsSending] = useState(false)
  const [chatError, setChatError] = useState<string | null>(null)

  const nextMessageId = useRef(0)
  const messagesEndRef = useRef<HTMLDivElement | null>(null)

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

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({
      behavior: 'smooth',
    })
  }, [messages, isSending])

  function createChatMessage(
    role: ChatMessageRole,
    content: string,
  ): ChatMessage {
    nextMessageId.current += 1

    return {
      id: nextMessageId.current,
      role,
      content,
    }
  }

  async function handleSubmit(
    event: FormEvent<HTMLFormElement>,
  ): Promise<void> {
    event.preventDefault()

    const message = input.trim()

    if (
      !message ||
      sessionId === null ||
      isSending
    ) {
      return
    }

    setMessages((currentMessages) => [
      ...currentMessages,
      createChatMessage('user', message),
    ])
    setInput('')
    setChatError(null)
    setIsSending(true)

    try {
      const response = await sendChatMessage(
        sessionId,
        message,
      )

      setMessages((currentMessages) => [
        ...currentMessages,
        createChatMessage(
          'assistant',
          response.response,
        ),
      ])
    } catch (error: unknown) {
      const message =
        error instanceof ApiError
          ? error.message
          : 'Unable to reach the agent. Please try again.'

      setChatError(message)
    } finally {
      setIsSending(false)
    }
  }

  function handleComposerKeyDown(
    event: KeyboardEvent<HTMLTextAreaElement>,
  ): void {
    if (
      event.key === 'Enter' &&
      !event.shiftKey
    ) {
      event.preventDefault()
      event.currentTarget.form?.requestSubmit()
    }
  }

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

  const canSend =
    sessionId !== null &&
    input.trim().length > 0 &&
    !isSending

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
            <h2 id="conversation-heading">New conversation</h2>
          </div>

          <span className="version-badge">
            {health === null
              ? 'v1.3 in progress'
              : `API ${health.version}`}
          </span>
        </header>

        <section
          className={
            messages.length === 0
              ? 'conversation'
              : 'conversation conversation-active'
          }
          aria-labelledby="conversation-heading"
        >
          {messages.length === 0 ? (
            <div className="welcome">
              <div className="welcome-icon" aria-hidden="true">
                ✦
              </div>

              <p className="welcome-eyebrow">Frank AI Agent</p>
              <h2>What can I help you explore?</h2>

              <p className="welcome-description">
                Chat with a modular AI agent featuring retrieval, memory,
                tool calling, and trusted source attribution.
              </p>

              <div className="capability-grid">
                {capabilities.map((capability) => (
                  <article
                    className="capability-card"
                    key={capability.title}
                  >
                    <h3>{capability.title}</h3>
                    <p>{capability.description}</p>
                  </article>
                ))}
              </div>
            </div>
          ) : (
            <div
              className="chat-thread"
              role="log"
              aria-live="polite"
              aria-busy={isSending}
            >
              {messages.map((message) => (
                <article
                  className={`message-row message-row-${message.role}`}
                  key={message.id}
                >
                  <div className="message-avatar" aria-hidden="true">
                    {message.role === 'user' ? 'You' : 'F'}
                  </div>

                  <div className="message-body">
                    <p className="message-author">
                      {message.role === 'user'
                        ? 'You'
                        : 'Frank AI Agent'}
                    </p>

                    <div className="message-content">
                      {message.content}
                    </div>
                  </div>
                </article>
              ))}

              {isSending && (
                <article className="message-row message-row-assistant">
                  <div className="message-avatar" aria-hidden="true">
                    F
                  </div>

                  <div className="message-body">
                    <p className="message-author">
                      Frank AI Agent
                    </p>

                    <div
                      className="message-content typing-indicator"
                      aria-label="Agent is thinking"
                    >
                      <span />
                      <span />
                      <span />
                    </div>
                  </div>
                </article>
              )}

              <div ref={messagesEndRef} />
            </div>
          )}
        </section>

        <footer className="composer">
          <form
            className="composer-control"
            onSubmit={handleSubmit}
          >
            <textarea
              aria-label="Chat message"
              value={input}
              onChange={(event) => {
                setInput(event.target.value)
              }}
              onKeyDown={handleComposerKeyDown}
              disabled={
                sessionId === null ||
                connectionState !== 'online' ||
                isSending
              }
              maxLength={10_000}
              placeholder={
                sessionId === null
                  ? 'Waiting for an agent session…'
                  : 'Message Frank AI Agent…'
              }
              rows={1}
            />

            <button
              type="submit"
              disabled={!canSend}
            >
              {isSending ? 'Thinking…' : 'Send'}
            </button>
          </form>

          <p
            className={chatError === null ? undefined : 'composer-error'}
            role={chatError === null ? undefined : 'alert'}
          >
            {chatError ??
              'Press Enter to send · Shift+Enter for a new line'}
          </p>
        </footer>
      </main>
    </div>
  )
}

export default App