import { useEffect, useLayoutEffect, useRef, useState } from 'react'
import type { KeyboardEvent, SubmitEvent } from 'react'

import {
    ApiError,
    ChatStreamError,
    createSession,
    deleteSession,
    getSessionHistory,
    streamChatMessage,
} from './api/client'
import type { HealthResponse, HistoryMessageResponse } from './api/types'
import { MessageContent } from './components/MessageContent'
import {
    initializeApplication,
    resetApplicationInitialization,
} from './session/applicationInitializer'
import { storeSessionId } from './storage/activeSessionStorage'

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
type ChatStreamState =
    'idle' | 'streaming' | 'stopping' | 'recovering' | 'finishing'
type ChatMessageRole = 'user' | 'assistant'

interface ChatMessage {
    id: number
    role: ChatMessageRole
    content: string
}

interface ChatErrorDetails {
    message: string
    requestId: string | null
}

function createRestoredMessages(
    history: HistoryMessageResponse[],
): ChatMessage[] {
    const restoredMessages: ChatMessage[] = []

    for (const historyMessage of history) {
        if (
            (historyMessage.role !== 'user' &&
                historyMessage.role !== 'assistant') ||
            historyMessage.content === null
        ) {
            continue
        }

        restoredMessages.push({
            id: restoredMessages.length + 1,
            role: historyMessage.role,
            content: historyMessage.content,
        })
    }

    return restoredMessages
}

function App() {
    const [connectionState, setConnectionState] =
        useState<ConnectionState>('checking')
    const [health, setHealth] = useState<HealthResponse | null>(null)
    const [sessionId, setSessionId] = useState<string | null>(null)
    const [messages, setMessages] = useState<ChatMessage[]>([])
    const [input, setInput] = useState('')
    const [chatStreamState, setChatStreamState] =
        useState<ChatStreamState>('idle')
    const isSending = chatStreamState !== 'idle'
    const [isCreatingSession, setIsCreatingSession] = useState(false)
    const [chatErrorDetails, setChatErrorDetails] =
        useState<ChatErrorDetails | null>(null)

    const chatError = chatErrorDetails?.message ?? null

    const nextMessageId = useRef(0)
    const messagesEndRef = useRef<HTMLDivElement | null>(null)
    const composerRef = useRef<HTMLTextAreaElement | null>(null)
    const sendingRef = useRef(false)
    const mountedRef = useRef(false)
    const streamAbortControllerRef = useRef<AbortController | null>(null)

    function setChatError(
        message: string | null,
        requestId: string | null = null,
    ): void {
        setChatErrorDetails(
            message === null
                ? null
                : {
                      message,
                      requestId,
                  },
        )
    }

    useEffect(() => {
        let active = true
        mountedRef.current = true

        void initializeApplication()
            .then((result) => {
                if (!active) {
                    return
                }

                const restoredMessages = createRestoredMessages(result.history)

                nextMessageId.current = restoredMessages.length

                setHealth(result.health)
                setSessionId(result.sessionId)
                setMessages(restoredMessages)
                setChatError(null)
                setConnectionState('online')
            })
            .catch((error: unknown) => {
                if (!active) {
                    return
                }

                setChatError(
                    'Unable to initialize the agent. Please retry.',
                    error instanceof ApiError ? error.requestId : null,
                )
                setConnectionState('offline')
            })

        return () => {
            active = false
            mountedRef.current = false
            const controller = streamAbortControllerRef.current
            streamAbortControllerRef.current = null
            controller?.abort()
        }
    }, [])

    useEffect(() => {
        messagesEndRef.current?.scrollIntoView({
            behavior: 'smooth',
        })
    }, [messages, isSending])

    useLayoutEffect(() => {
        const textarea = composerRef.current

        if (textarea === null) {
            return
        }

        function resizeComposer(): void {
            if (textarea === null) {
                return
            }

            // 先解除舊高度，才能在內容減少時縮回。
            textarea.style.overflowY = 'hidden'
            textarea.style.height = 'auto'

            const contentHeight = textarea.scrollHeight

            textarea.style.height = `${Math.min(
                180,
                Math.max(44, contentHeight),
            )}px`
            textarea.style.overflowY = contentHeight > 180 ? 'auto' : 'hidden'
        }

        resizeComposer()
        window.addEventListener('resize', resizeComposer)

        return () => {
            window.removeEventListener('resize', resizeComposer)
        }
    }, [input])

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

    async function handleRetryConnection(): Promise<void> {
        if (connectionState === 'checking') {
            return
        }

        setConnectionState('checking')
        setChatError(null)

        try {
            resetApplicationInitialization()

            const result = await initializeApplication()
            const restoredMessages = createRestoredMessages(result.history)

            nextMessageId.current = restoredMessages.length

            setHealth(result.health)
            setSessionId(result.sessionId)
            setMessages(restoredMessages)
            setConnectionState('online')
        } catch (error: unknown) {
            setHealth(null)
            setSessionId(null)
            setChatError(
                'Unable to initialize the agent. Please retry.',
                error instanceof ApiError ? error.requestId : null,
            )
            setConnectionState('offline')
        }
    }

    async function handleNewConversation(): Promise<void> {
        if (sessionId === null || isSending || isCreatingSession) {
            return
        }

        const previousSessionId = sessionId

        setIsCreatingSession(true)
        setChatError(null)

        try {
            const newSession = await createSession()

            storeSessionId(newSession.session_id)
            setSessionId(newSession.session_id)
            setMessages([])
            setInput('')
            nextMessageId.current = 0

            void deleteSession(previousSessionId).catch(() => undefined)
        } catch (error: unknown) {
            const message =
                error instanceof ApiError
                    ? error.message
                    : 'Unable to create a new session. Please try again.'

            setChatError(
                message,
                error instanceof ApiError ? error.requestId : null,
            )
        } finally {
            setIsCreatingSession(false)
        }
    }

    function handleStopResponse(): void {
        const controller = streamAbortControllerRef.current

        if (controller === null || controller.signal.aborted) {
            return
        }

        setChatStreamState('stopping')
        controller.abort()
    }

    async function handleSubmit(
        event: SubmitEvent<HTMLFormElement>,
    ): Promise<void> {
        event.preventDefault()

        const message = input.trim()

        if (
            !message ||
            sessionId === null ||
            isSending ||
            isCreatingSession ||
            sendingRef.current
        ) {
            return
        }

        sendingRef.current = true
        const abortController = new AbortController()
        streamAbortControllerRef.current = abortController

        const activeSessionId = sessionId

        const userMessage = createChatMessage('user', message)

        setMessages((currentMessages) => [...currentMessages, userMessage])
        setInput('')
        setChatError(null)
        setChatStreamState('streaming')

        let assistantMessageId: number | null = null
        let streamCompleted = false
        let streamFailed = false

        function discardProvisionalMessages(): void {
            setMessages((currentMessages) =>
                currentMessages.filter(
                    (currentMessage) =>
                        currentMessage.id !== userMessage.id &&
                        currentMessage.id !== assistantMessageId,
                ),
            )
            setInput(message)
        }

        async function replaceExpiredSession(): Promise<void> {
            try {
                const replacementSession = await createSession()

                if (!mountedRef.current) {
                    return
                }

                storeSessionId(replacementSession.session_id)
                setSessionId(replacementSession.session_id)
                setMessages([])
                nextMessageId.current = 0
                setChatError(
                    'Session expired. A new conversation is ready. Please send your message again.',
                )
            } catch (replacementError: unknown) {
                if (!mountedRef.current) {
                    return
                }

                setChatError(
                    replacementError instanceof ApiError
                        ? replacementError.message
                        : 'Unable to create a new session. Please try again.',
                    replacementError instanceof ApiError
                        ? replacementError.requestId
                        : null,
                )
            }
        }

        async function restoreAfterFailedStream(): Promise<void> {
            streamAbortControllerRef.current = null
            setChatStreamState('recovering')
            discardProvisionalMessages()

            try {
                const sessionHistory = await getSessionHistory(activeSessionId)

                if (!mountedRef.current) {
                    return
                }
                const restoredMessages = createRestoredMessages(
                    sessionHistory.messages,
                )

                nextMessageId.current = restoredMessages.length
                setMessages(restoredMessages)
            } catch (historyError: unknown) {
                if (!mountedRef.current) {
                    return
                }

                if (
                    historyError instanceof ApiError &&
                    historyError.status === 404
                ) {
                    await replaceExpiredSession()
                    return
                }

                setChatError(
                    'Unable to load the latest conversation. Please reload before retrying.',
                    historyError instanceof ApiError
                        ? historyError.requestId
                        : null,
                )
            }
        }

        try {
            for await (const event of streamChatMessage(
                activeSessionId,
                message,
                abortController.signal,
            )) {
                if (abortController.signal.aborted || !mountedRef.current) {
                    throw new DOMException('Response stopped.', 'AbortError')
                }

                if (event.type === 'content_delta') {
                    if (assistantMessageId === null) {
                        const assistantMessage = createChatMessage(
                            'assistant',
                            event.content,
                        )

                        assistantMessageId = assistantMessage.id

                        setMessages((currentMessages) => [
                            ...currentMessages,
                            assistantMessage,
                        ])
                    } else {
                        const messageId = assistantMessageId

                        setMessages((currentMessages) =>
                            currentMessages.map((currentMessage) =>
                                currentMessage.id === messageId
                                    ? {
                                          ...currentMessage,
                                          content:
                                              currentMessage.content +
                                              event.content,
                                      }
                                    : currentMessage,
                            ),
                        )
                    }

                    continue
                }

                if (event.type === 'completed') {
                    streamCompleted = true
                    streamAbortControllerRef.current = null
                    setChatStreamState('finishing')

                    if (assistantMessageId === null) {
                        const assistantMessage = createChatMessage(
                            'assistant',
                            event.response,
                        )

                        assistantMessageId = assistantMessage.id

                        setMessages((currentMessages) => [
                            ...currentMessages,
                            assistantMessage,
                        ])
                    } else {
                        const messageId = assistantMessageId

                        setMessages((currentMessages) =>
                            currentMessages.map((currentMessage) =>
                                currentMessage.id === messageId
                                    ? {
                                          ...currentMessage,
                                          content: event.response,
                                      }
                                    : currentMessage,
                            ),
                        )
                    }

                    break
                }

                streamFailed = true
                setChatError(event.message, event.requestId ?? null)
                await restoreAfterFailedStream()
                break
            }

            if (abortController.signal.aborted && !streamCompleted) {
                throw new DOMException('Response stopped.', 'AbortError')
            }

            if (!streamCompleted && !streamFailed) {
                throw new Error('Chat stream ended before completion.')
            }
        } catch (error: unknown) {
            if (!mountedRef.current) {
                return
            }

            streamAbortControllerRef.current = null
            setChatStreamState('recovering')

            if (abortController.signal.aborted) {
                setChatError(null)
                await restoreAfterFailedStream()
                return
            }

            if (error instanceof ApiError && error.status === 404) {
                discardProvisionalMessages()
                await replaceExpiredSession()
                return
            }

            const errorMessage =
                error instanceof ApiError
                    ? error.message
                    : 'Unable to reach the agent. Please try again.'

            setChatError(
                errorMessage,
                error instanceof ApiError || error instanceof ChatStreamError
                    ? error.requestId
                    : null,
            )

            await restoreAfterFailedStream()
        } finally {
            if (streamAbortControllerRef.current === abortController) {
                streamAbortControllerRef.current = null
            }
            sendingRef.current = false

            if (mountedRef.current) {
                setChatStreamState('idle')
            }
        }
    }

    function handleComposerKeyDown(
        event: KeyboardEvent<HTMLTextAreaElement>,
    ): void {
        if (event.nativeEvent.isComposing) {
            return
        }

        if (event.key === 'Enter' && !event.shiftKey) {
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

    const sendButtonLabel = {
        idle: 'Send',
        streaming: 'Stop response',
        stopping: 'Stopping…',
        recovering: 'Restoring conversation…',
        finishing: 'Finishing…',
    }[chatStreamState]

    const canSend =
        sessionId !== null &&
        input.trim().length > 0 &&
        !isSending &&
        !isCreatingSession

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

                    <button
                        type="button"
                        className="navigation-item navigation-item-active"
                        onClick={handleNewConversation}
                        disabled={
                            sessionId === null || isSending || isCreatingSession
                        }
                    >
                        <span className="navigation-icon" aria-hidden="true">
                            ◇
                        </span>

                        {isCreatingSession
                            ? 'Creating conversation…'
                            : 'New conversation'}
                    </button>

                    {sessionId !== null && (
                        <div className="session-card">
                            <p>Active session</p>
                            <code title={sessionId}>{sessionId}</code>
                        </div>
                    )}
                </div>

                <div
                    className={`sidebar-footer sidebar-footer-${connectionState}`}
                    aria-live="polite"
                >
                    <span
                        className={`status-dot status-dot-${connectionState}`}
                        aria-hidden="true"
                    />

                    <div>
                        <strong>{connectionTitle}</strong>
                        <span>{connectionDescription}</span>

                        {connectionState === 'offline' && (
                            <button
                                type="button"
                                className="retry-connection-button"
                                onClick={() => {
                                    void handleRetryConnection()
                                }}
                            >
                                Retry connection
                            </button>
                        )}
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
                            ? 'API version pending'
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
                                Chat with a modular AI agent featuring
                                retrieval, memory, tool calling, and trusted
                                source attribution.
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
                                    <div
                                        className="message-avatar"
                                        aria-hidden="true"
                                    >
                                        {message.role === 'user' ? 'You' : 'F'}
                                    </div>

                                    <div className="message-body">
                                        <p className="message-author">
                                            {message.role === 'user'
                                                ? 'You'
                                                : 'Frank AI Agent'}
                                        </p>

                                        <div className="message-content">
                                            <MessageContent
                                                content={message.content}
                                            />
                                        </div>
                                    </div>
                                </article>
                            ))}

                            {chatStreamState === 'streaming' && (
                                <article className="message-row message-row-assistant">
                                    <div
                                        className="message-avatar"
                                        aria-hidden="true"
                                    >
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
                    <form className="composer-control" onSubmit={handleSubmit}>
                        <textarea
                            ref={composerRef}
                            aria-label="Chat message"
                            value={input}
                            onChange={(event) => {
                                setInput(event.target.value)
                            }}
                            onKeyDown={handleComposerKeyDown}
                            disabled={
                                sessionId === null ||
                                connectionState !== 'online' ||
                                isSending ||
                                isCreatingSession
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
                            type={isSending ? 'button' : 'submit'}
                            disabled={
                                isSending
                                    ? chatStreamState !== 'streaming'
                                    : !canSend
                            }
                            onClick={isSending ? handleStopResponse : undefined}
                        >
                            {sendButtonLabel}
                        </button>
                    </form>

                    <p
                        className={
                            chatError === null ? undefined : 'composer-error'
                        }
                        role={chatError === null ? undefined : 'alert'}
                    >
                        {chatError ??
                            'Press Enter to send · Shift+Enter for a new line'}
                    </p>

                    {chatErrorDetails?.requestId && (
                        <label className="request-id">
                            <span>Request ID</span>
                            <input
                                type="text"
                                value={chatErrorDetails.requestId}
                                readOnly
                                onFocus={(event) => {
                                    event.currentTarget.select()
                                }}
                            />
                        </label>
                    )}
                </footer>
            </main>
        </div>
    )
}

export default App
