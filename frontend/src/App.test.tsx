import { act, render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import {
    ApiError,
    createSession,
    deleteSession,
    getSessionHistory,
    streamChatMessage,
} from './api/client'
import App from './App'
import {
    initializeApplication,
    resetApplicationInitialization,
} from './session/applicationInitializer'
import { storeSessionId } from './storage/activeSessionStorage'
import type { ChatStreamEvent } from './api/types'

vi.mock('./api/client', async (importOriginal) => {
    const actual = await importOriginal<typeof import('./api/client')>()

    return {
        ...actual,
        createSession: vi.fn(),
        deleteSession: vi.fn(),
        getSessionHistory: vi.fn(),
        streamChatMessage: vi.fn(),
    }
})

vi.mock('./session/applicationInitializer', () => ({
    initializeApplication: vi.fn(),
    resetApplicationInitialization: vi.fn(),
}))

vi.mock('./storage/activeSessionStorage', () => ({
    storeSessionId: vi.fn(),
}))

const initializeApplicationMock = vi.mocked(initializeApplication)
const resetApplicationInitializationMock = vi.mocked(
    resetApplicationInitialization,
)

const createSessionMock = vi.mocked(createSession)
const deleteSessionMock = vi.mocked(deleteSession)
const getSessionHistoryMock = vi.mocked(getSessionHistory)
const streamChatMessageMock = vi.mocked(streamChatMessage)
const storeSessionIdMock = vi.mocked(storeSessionId)

const healthResponse = {
    status: 'ok' as const,
    service: 'Frank AI Agent',
    version: '1.4.0',
}

function createPendingPromise<T>(): Promise<T> {
    return new Promise(() => undefined)
}

async function* createChatStream(
    events: ChatStreamEvent[],
): AsyncGenerator<ChatStreamEvent> {
    for (const event of events) {
        yield event
    }
}

async function* createFailingChatStream(
    error: Error,
): AsyncGenerator<ChatStreamEvent> {
    yield* []
    throw error
}

describe('App', () => {
    beforeEach(() => {
        vi.clearAllMocks()

        getSessionHistoryMock.mockResolvedValue({
            session_id: 'session-123',
            messages: [],
        })

        initializeApplicationMock.mockResolvedValue({
            health: healthResponse,
            sessionId: 'session-123',
            history: [],
        })
    })

    it('should show the initializing state while initialization is pending', () => {
        initializeApplicationMock.mockReturnValue(createPendingPromise())

        render(<App />)

        expect(screen.getByText('Initializing agent')).toBeInTheDocument()

        expect(
            screen.getByRole('textbox', {
                name: 'Chat message',
            }),
        ).toBeDisabled()

        expect(
            screen.getByRole('button', {
                name: 'New conversation',
            }),
        ).toBeDisabled()
    })

    it('should restore the active session and conversation history', async () => {
        initializeApplicationMock.mockResolvedValue({
            health: healthResponse,
            sessionId: 'stored-session',
            history: [
                {
                    role: 'user',
                    content: 'How do sessions expire?',
                },
                {
                    role: 'assistant',
                    content: 'Sessions use sliding expiration.',
                },
                {
                    role: 'tool',
                    content: 'Ignored tool output',
                },
                {
                    role: 'assistant',
                    content: null,
                },
            ],
        })

        render(<App />)

        expect(await screen.findByText('Agent ready')).toBeInTheDocument()

        expect(screen.getByTitle('stored-session')).toHaveTextContent(
            'stored-session',
        )

        expect(screen.getByText('How do sessions expire?')).toBeInTheDocument()

        expect(
            screen.getByText('Sessions use sliding expiration.'),
        ).toBeInTheDocument()

        expect(
            screen.queryByText('Ignored tool output'),
        ).not.toBeInTheDocument()

        expect(
            screen.getByRole('textbox', {
                name: 'Chat message',
            }),
        ).toBeEnabled()
    })

    it('should retry initialization after the API becomes available', async () => {
        const user = userEvent.setup()

        initializeApplicationMock
            .mockRejectedValueOnce(new Error('API unavailable'))
            .mockResolvedValueOnce({
                health: healthResponse,
                sessionId: 'recovered-session',
                history: [],
            })

        render(<App />)

        expect(await screen.findByText('API unavailable')).toBeInTheDocument()

        await user.click(
            screen.getByRole('button', {
                name: 'Retry connection',
            }),
        )

        expect(await screen.findByText('Agent ready')).toBeInTheDocument()

        expect(screen.getByTitle('recovered-session')).toHaveTextContent(
            'recovered-session',
        )

        expect(resetApplicationInitializationMock).toHaveBeenCalledOnce()

        expect(initializeApplicationMock).toHaveBeenCalledTimes(2)
    })

    it('should stream and display the agent response', async () => {
        const user = userEvent.setup()

        streamChatMessageMock.mockReturnValue(
            createChatStream([
                {
                    type: 'content_delta',
                    content: 'Sessions use ',
                },
                {
                    type: 'content_delta',
                    content: 'sliding expiration.',
                },
                {
                    type: 'completed',
                    response: 'Sessions use sliding expiration.',
                },
            ]),
        )

        render(<App />)

        await screen.findByText('Agent ready')

        const messageInput = screen.getByRole('textbox', {
            name: 'Chat message',
        })

        await user.type(messageInput, 'How do sessions expire?')

        await user.click(
            screen.getByRole('button', {
                name: 'Send',
            }),
        )

        await waitFor(() => {
            expect(streamChatMessageMock).toHaveBeenCalledWith(
                'session-123',
                'How do sessions expire?',
            )
        })

        expect(screen.getByText('How do sessions expire?')).toBeInTheDocument()

        expect(
            await screen.findByText('Sessions use sliding expiration.'),
        ).toBeInTheDocument()

        expect(messageInput).toHaveValue('')
    })

    it('should submit a message only once when the form is submitted twice immediately', async () => {
        const user = userEvent.setup()
        let finishStream!: () => void

        const streamGate = new Promise<void>((resolve) => {
            finishStream = resolve
        })

        streamChatMessageMock.mockImplementation(async function* () {
            await streamGate
            yield {
                type: 'completed',
                response: 'Done',
            }
        })

        render(<App />)
        await screen.findByText('Agent ready')

        const messageInput = screen.getByRole('textbox', {
            name: 'Chat message',
        })
        await user.type(messageInput, 'Hello')

        const form = messageInput.closest('form')
        if (form === null) {
            throw new Error('Chat form was not found.')
        }

        act(() => {
            form.requestSubmit()
            form.requestSubmit()
        })

        const requestCount = streamChatMessageMock.mock.calls.length

        await act(async () => {
            finishStream()
        })

        expect(requestCount).toBe(1)

        await waitFor(() => {
            expect(messageInput).toBeEnabled()
        })

        await user.type(messageInput, 'Next question')
        await user.click(screen.getByRole('button', { name: 'Send' }))

        await waitFor(() => {
            expect(streamChatMessageMock).toHaveBeenCalledTimes(2)
        })
    })

    it('should show an error received from the chat stream', async () => {
        const user = userEvent.setup()

        streamChatMessageMock.mockReturnValue(
            createChatStream([
                {
                    type: 'error',
                    error: 'client_rate_limit',
                    message:
                        'The AI service is temporarily rate limited. ' +
                        'Please try again later.',
                },
            ]),
        )

        render(<App />)

        await screen.findByText('Agent ready')

        const messageInput = screen.getByRole('textbox', {
            name: 'Chat message',
        })

        await user.type(messageInput, 'Hello')

        await user.click(
            screen.getByRole('button', {
                name: 'Send',
            }),
        )

        expect(
            await screen.findByText(
                'The AI service is temporarily rate limited. ' +
                    'Please try again later.',
            ),
        ).toBeInTheDocument()

        expect(streamChatMessageMock).toHaveBeenCalledWith(
            'session-123',
            'Hello',
        )
    })

    it('should restore saved history and draft after a stream error', async () => {
        const user = userEvent.setup()

        getSessionHistoryMock.mockResolvedValue({
            session_id: 'session-123',
            messages: [
                {
                    role: 'assistant',
                    content: 'Previously saved reply',
                },
            ],
        })

        streamChatMessageMock.mockReturnValue(
            createChatStream([
                {
                    type: 'content_delta',
                    content: 'Uncommitted response',
                },
                {
                    type: 'error',
                    error: 'client_timeout',
                    message: 'The AI service took too long to respond.',
                },
            ]),
        )

        render(<App />)
        await screen.findByText('Agent ready')

        const messageInput = screen.getByRole('textbox', {
            name: 'Chat message',
        })

        await user.type(messageInput, 'My question')
        await user.click(screen.getByRole('button', { name: 'Send' }))

        expect(
            await screen.findByText('Previously saved reply'),
        ).toBeInTheDocument()
        expect(screen.getByRole('alert')).toHaveTextContent(
            'The AI service took too long to respond.',
        )
        expect(
            screen.queryByText('Uncommitted response'),
        ).not.toBeInTheDocument()
        expect(messageInput).toHaveValue('My question')
        expect(getSessionHistoryMock).toHaveBeenCalledOnce()
        expect(getSessionHistoryMock).toHaveBeenCalledWith('session-123')
        expect(streamChatMessageMock).toHaveBeenCalledTimes(1)
    })

    it('should discard unpersisted messages and restore input after a stream conflict', async () => {
        const user = userEvent.setup()

        streamChatMessageMock.mockReturnValue(
            createChatStream([
                {
                    type: 'content_delta',
                    content: 'Uncommitted response',
                },
                {
                    type: 'error',
                    error: 'session_conflict',
                    message:
                        'Session was updated by another request. Please retry.',
                },
            ]),
        )

        render(<App />)

        await screen.findByText('Agent ready')

        const messageInput = screen.getByRole('textbox', {
            name: 'Chat message',
        })

        await user.type(messageInput, 'Hello')
        await user.click(screen.getByRole('button', { name: 'Send' }))

        expect(await screen.findByRole('alert')).toHaveTextContent(
            'Session was updated by another request. Please retry.',
        )

        await waitFor(() => {
            expect(
                screen.queryByText('Uncommitted response'),
            ).not.toBeInTheDocument()
            expect(
                screen.queryByText('Hello', {
                    selector: '.message-row-user .message-content',
                }),
            ).not.toBeInTheDocument()
            expect(messageInput).toHaveValue('Hello')
        })

        expect(streamChatMessageMock).toHaveBeenCalledTimes(1)
    })

    it('should load the latest session history after a stream conflict', async () => {
        const user = userEvent.setup()

        getSessionHistoryMock.mockResolvedValue({
            session_id: 'session-123',
            messages: [
                {
                    role: 'user',
                    content: 'Another request',
                },
                {
                    role: 'assistant',
                    content: 'Saved reply',
                },
            ],
        })

        streamChatMessageMock.mockReturnValue(
            createChatStream([
                {
                    type: 'content_delta',
                    content: 'Uncommitted response',
                },
                {
                    type: 'error',
                    error: 'session_conflict',
                    message:
                        'Session was updated by another request. Please retry.',
                },
            ]),
        )

        render(<App />)
        await screen.findByText('Agent ready')

        const messageInput = screen.getByRole('textbox', {
            name: 'Chat message',
        })

        await user.type(messageInput, 'My question')
        await user.click(screen.getByRole('button', { name: 'Send' }))

        expect(await screen.findByText('Saved reply')).toBeInTheDocument()
        expect(screen.getByText('Another request')).toBeInTheDocument()
        expect(
            screen.queryByText('Uncommitted response'),
        ).not.toBeInTheDocument()
        expect(messageInput).toHaveValue('My question')
        expect(getSessionHistoryMock).toHaveBeenCalledOnce()
        expect(getSessionHistoryMock).toHaveBeenCalledWith('session-123')
    })

    it('should load the latest history when starting the stream returns HTTP 409', async () => {
        const user = userEvent.setup()

        getSessionHistoryMock.mockResolvedValue({
            session_id: 'session-123',
            messages: [
                {
                    role: 'assistant',
                    content: 'Saved reply from another request',
                },
            ],
        })

        streamChatMessageMock.mockReturnValue(
            createFailingChatStream(
                new ApiError(
                    409,
                    'Session was updated by another request. Please retry.',
                ),
            ),
        )

        render(<App />)
        await screen.findByText('Agent ready')

        const messageInput = screen.getByRole('textbox', {
            name: 'Chat message',
        })

        await user.type(messageInput, 'My question')
        await user.click(screen.getByRole('button', { name: 'Send' }))

        expect(
            await screen.findByText('Saved reply from another request'),
        ).toBeInTheDocument()

        expect(screen.getByRole('alert')).toHaveTextContent(
            'Session was updated by another request. Please retry.',
        )
        expect(messageInput).toHaveValue('My question')
        expect(
            screen.queryByText('My question', {
                selector: '.message-row-user .message-content',
            }),
        ).not.toBeInTheDocument()
        expect(getSessionHistoryMock).toHaveBeenCalledOnce()
        expect(getSessionHistoryMock).toHaveBeenCalledWith('session-123')
        expect(streamChatMessageMock).toHaveBeenCalledTimes(1)
    })

    it('should preserve the draft and explain when conflict history cannot be loaded', async () => {
        const user = userEvent.setup()

        initializeApplicationMock.mockResolvedValue({
            health: healthResponse,
            sessionId: 'session-123',
            history: [
                {
                    role: 'assistant',
                    content: 'Previous saved reply',
                },
            ],
        })

        getSessionHistoryMock.mockRejectedValue(
            new Error('History unavailable'),
        )

        streamChatMessageMock.mockReturnValue(
            createChatStream([
                {
                    type: 'content_delta',
                    content: 'Uncommitted response',
                },
                {
                    type: 'error',
                    error: 'session_conflict',
                    message:
                        'Session was updated by another request. Please retry.',
                },
            ]),
        )

        render(<App />)
        await screen.findByText('Previous saved reply')

        const messageInput = screen.getByRole('textbox', {
            name: 'Chat message',
        })

        await user.type(messageInput, 'My question')
        await user.click(screen.getByRole('button', { name: 'Send' }))

        expect(
            await screen.findByText(
                'Unable to load the latest conversation. Please reload before retrying.',
            ),
        ).toBeInTheDocument()

        expect(screen.getByText('Previous saved reply')).toBeInTheDocument()
        expect(
            screen.queryByText('Uncommitted response'),
        ).not.toBeInTheDocument()
        expect(messageInput).toHaveValue('My question')
        expect(getSessionHistoryMock).toHaveBeenCalledOnce()
        expect(streamChatMessageMock).toHaveBeenCalledTimes(1)
    })

    it('should replace the session when history returns 404 after a stream conflict', async () => {
        const user = userEvent.setup()

        initializeApplicationMock.mockResolvedValue({
            health: healthResponse,
            sessionId: 'expired-session',
            history: [
                {
                    role: 'assistant',
                    content: 'Previous saved reply',
                },
            ],
        })
        getSessionHistoryMock.mockRejectedValue(
            new ApiError(404, 'Session not found.'),
        )
        createSessionMock.mockResolvedValue({
            session_id: 'replacement-session',
        })
        streamChatMessageMock.mockReturnValue(
            createChatStream([
                {
                    type: 'content_delta',
                    content: 'Uncommitted response',
                },
                {
                    type: 'error',
                    error: 'session_conflict',
                    message:
                        'Session was updated by another request. Please retry.',
                },
            ]),
        )

        render(<App />)
        await screen.findByText('Previous saved reply')

        const messageInput = screen.getByRole('textbox', {
            name: 'Chat message',
        })

        await user.type(messageInput, 'My question')
        await user.click(screen.getByRole('button', { name: 'Send' }))

        expect(
            await screen.findByTitle('replacement-session'),
        ).toHaveTextContent('replacement-session')
        expect(
            screen.queryByText('Previous saved reply'),
        ).not.toBeInTheDocument()
        expect(
            screen.queryByText('Uncommitted response'),
        ).not.toBeInTheDocument()
        expect(messageInput).toHaveValue('My question')
        expect(screen.getByRole('alert')).toHaveTextContent(
            'Session expired. A new conversation is ready. Please send your message again.',
        )
        expect(getSessionHistoryMock).toHaveBeenCalledWith('expired-session')
        expect(storeSessionIdMock).toHaveBeenCalledWith('replacement-session')
        expect(deleteSessionMock).not.toHaveBeenCalled()
        expect(streamChatMessageMock).toHaveBeenCalledTimes(1)
    })

    it('should reconcile history when the stream ends before completion', async () => {
        const user = userEvent.setup()

        getSessionHistoryMock.mockResolvedValue({
            session_id: 'session-123',
            messages: [
                {
                    role: 'assistant',
                    content: 'Earlier saved response',
                },
            ],
        })

        streamChatMessageMock.mockReturnValue(
            createChatStream([
                {
                    type: 'content_delta',
                    content: 'Partial response',
                },
            ]),
        )

        render(<App />)
        await screen.findByText('Agent ready')

        const messageInput = screen.getByRole('textbox', {
            name: 'Chat message',
        })

        await user.type(messageInput, 'Hello')
        await user.click(screen.getByRole('button', { name: 'Send' }))

        expect(
            await screen.findByText('Earlier saved response'),
        ).toBeInTheDocument()
        expect(screen.getByRole('alert')).toHaveTextContent(
            'Unable to reach the agent. Please try again.',
        )
        expect(screen.queryByText('Partial response')).not.toBeInTheDocument()
        expect(messageInput).toHaveValue('Hello')
        expect(getSessionHistoryMock).toHaveBeenCalledOnce()
        expect(getSessionHistoryMock).toHaveBeenCalledWith('session-123')
    })

    it('should replace the active session for a new conversation', async () => {
        const user = userEvent.setup()

        initializeApplicationMock.mockResolvedValue({
            health: healthResponse,
            sessionId: 'old-session',
            history: [
                {
                    role: 'user',
                    content: 'Previous question',
                },
            ],
        })

        createSessionMock.mockResolvedValue({
            session_id: 'new-session',
        })

        deleteSessionMock.mockResolvedValue({
            deleted: true,
        })

        render(<App />)

        expect(await screen.findByText('Previous question')).toBeInTheDocument()

        await user.click(
            screen.getByRole('button', {
                name: 'New conversation',
            }),
        )

        expect(await screen.findByTitle('new-session')).toHaveTextContent(
            'new-session',
        )

        expect(screen.queryByText('Previous question')).not.toBeInTheDocument()

        expect(storeSessionIdMock).toHaveBeenCalledWith('new-session')

        expect(deleteSessionMock).toHaveBeenCalledWith('old-session')
    })

    it('should show an error when sending a message fails', async () => {
        const user = userEvent.setup()

        streamChatMessageMock.mockReturnValue(
            createFailingChatStream(
                new ApiError(503, 'Agent service is unavailable.'),
            ),
        )

        render(<App />)

        await screen.findByText('Agent ready')

        const messageInput = screen.getByRole('textbox', {
            name: 'Chat message',
        })

        await user.type(messageInput, 'Hello')

        await user.click(
            screen.getByRole('button', {
                name: 'Send',
            }),
        )

        expect(
            await screen.findByText('Agent service is unavailable.'),
        ).toBeInTheDocument()

        expect(
            screen.queryByText('Hello', {
                selector: '.message-row-user .message-content',
            }),
        ).not.toBeInTheDocument()

        expect(messageInput).toHaveValue('Hello')
        expect(getSessionHistoryMock).toHaveBeenCalledWith('session-123')
        expect(messageInput).toBeEnabled()
        expect(
            screen.queryByRole('textbox', { name: 'Request ID' }),
        ).not.toBeInTheDocument()
    })

    it.each(['HTTP', 'SSE'])(
        'should show the request ID for a %s chat error',
        async (errorSource) => {
            const user = userEvent.setup()
            const requestId = '83100577-b10b-4953-89fe-b7c29cbcfd36'
            const errorMessage = 'Agent service is unavailable.'

            getSessionHistoryMock.mockResolvedValue({
                session_id: 'session-123',
                messages: [],
            })

            if (errorSource === 'HTTP') {
                streamChatMessageMock.mockReturnValue(
                    createFailingChatStream(
                        new ApiError(503, errorMessage, requestId),
                    ),
                )
            } else {
                streamChatMessageMock.mockReturnValue(
                    createChatStream([
                        {
                            type: 'error',
                            error: 'client_connection_error',
                            message: errorMessage,
                            requestId,
                        },
                    ]),
                )
            }

            render(<App />)
            await screen.findByText('Agent ready')

            const messageInput = screen.getByRole('textbox', {
                name: 'Chat message',
            })

            await user.type(messageInput, 'Hello')
            await user.click(screen.getByRole('button', { name: 'Send' }))

            expect(await screen.findByRole('alert')).toHaveTextContent(
                errorMessage,
            )

            const requestIdInput = await screen.findByRole('textbox', {
                name: 'Request ID',
            })

            expect(requestIdInput).toHaveValue(requestId)
            expect(requestIdInput).toHaveAttribute('readonly')
            expect(messageInput).toHaveValue('Hello')

            streamChatMessageMock.mockReturnValue(
                createChatStream([
                    {
                        type: 'completed',
                        response: 'Retry succeeded',
                    },
                ]),
            )

            await user.click(screen.getByRole('button', { name: 'Send' }))

            expect(
                await screen.findByText('Retry succeeded'),
            ).toBeInTheDocument()
            expect(
                screen.queryByRole('textbox', { name: 'Request ID' }),
            ).not.toBeInTheDocument()
            expect(screen.queryByRole('alert')).not.toBeInTheDocument()
        },
    )

    it.each(['history-request-id', null])(
        'should use the recovery request ID when history loading fails (%s)',
        async (historyRequestId) => {
            const user = userEvent.setup()

            streamChatMessageMock.mockReturnValue(
                createChatStream([
                    {
                        type: 'error',
                        error: 'session_conflict',
                        message: 'Please retry.',
                        requestId: 'chat-request-id',
                    },
                ]),
            )

            getSessionHistoryMock.mockRejectedValue(
                new ApiError(
                    503,
                    'History storage is unavailable.',
                    historyRequestId,
                ),
            )

            render(<App />)
            await screen.findByText('Agent ready')

            const messageInput = screen.getByRole('textbox', {
                name: 'Chat message',
            })

            await user.type(messageInput, 'Hello')
            await user.click(screen.getByRole('button', { name: 'Send' }))

            expect(
                await screen.findByText(
                    'Unable to load the latest conversation. Please reload before retrying.',
                ),
            ).toBeInTheDocument()

            if (historyRequestId === null) {
                expect(
                    screen.queryByRole('textbox', { name: 'Request ID' }),
                ).not.toBeInTheDocument()
            } else {
                expect(
                    screen.getByRole('textbox', { name: 'Request ID' }),
                ).toHaveValue(historyRequestId)
            }

            expect(messageInput).toHaveValue('Hello')
        },
    )

    it('should create a new session and preserve the draft when the active session expires', async () => {
        const user = userEvent.setup()

        initializeApplicationMock.mockResolvedValue({
            health: healthResponse,
            sessionId: 'expired-session',
            history: [{ role: 'assistant', content: 'Previous reply' }],
        })

        streamChatMessageMock.mockReturnValue(
            createFailingChatStream(new ApiError(404, 'Session not found.')),
        )
        getSessionHistoryMock.mockRejectedValue(
            new ApiError(404, 'Session not found.'),
        )
        createSessionMock.mockResolvedValue({
            session_id: 'replacement-session',
        })

        render(<App />)
        await screen.findByText('Previous reply')

        const messageInput = screen.getByRole('textbox', {
            name: 'Chat message',
        })

        await user.type(messageInput, 'My question')
        await user.click(screen.getByRole('button', { name: 'Send' }))

        expect(
            await screen.findByTitle('replacement-session'),
        ).toHaveTextContent('replacement-session')
        expect(screen.queryByText('Previous reply')).not.toBeInTheDocument()
        expect(messageInput).toHaveValue('My question')
        expect(screen.getByRole('alert')).toHaveTextContent(
            'Session expired. A new conversation is ready. Please send your message again.',
        )
        expect(storeSessionIdMock).toHaveBeenCalledWith('replacement-session')
        expect(deleteSessionMock).not.toHaveBeenCalled()
        expect(streamChatMessageMock).toHaveBeenCalledTimes(1)
    })

    it('should preserve the draft when replacing an expired session fails', async () => {
        const user = userEvent.setup()

        initializeApplicationMock.mockResolvedValue({
            health: healthResponse,
            sessionId: 'expired-session',
            history: [{ role: 'assistant', content: 'Previous reply' }],
        })
        streamChatMessageMock.mockReturnValue(
            createFailingChatStream(new ApiError(404, 'Session not found.')),
        )
        createSessionMock.mockRejectedValue(
            new ApiError(503, 'Session storage is temporarily unavailable.'),
        )

        render(<App />)
        await screen.findByText('Previous reply')

        const messageInput = screen.getByRole('textbox', {
            name: 'Chat message',
        })

        await user.type(messageInput, 'My question')
        await user.click(screen.getByRole('button', { name: 'Send' }))

        expect(
            await screen.findByText(
                'Session storage is temporarily unavailable.',
            ),
        ).toBeInTheDocument()
        expect(screen.getByTitle('expired-session')).toBeInTheDocument()
        expect(screen.getByText('Previous reply')).toBeInTheDocument()
        expect(
            screen.queryByText('My question', {
                selector: '.message-row-user .message-content',
            }),
        ).not.toBeInTheDocument()
        expect(messageInput).toHaveValue('My question')
        expect(messageInput).toBeEnabled()
        expect(storeSessionIdMock).not.toHaveBeenCalled()
        expect(deleteSessionMock).not.toHaveBeenCalled()
    })

    it('should keep the active session when creating a new one fails', async () => {
        const user = userEvent.setup()

        createSessionMock.mockRejectedValue(
            new ApiError(500, 'Unable to create the session.'),
        )

        render(<App />)

        expect(await screen.findByTitle('session-123')).toHaveTextContent(
            'session-123',
        )

        await user.click(
            screen.getByRole('button', {
                name: 'New conversation',
            }),
        )

        expect(
            await screen.findByText('Unable to create the session.'),
        ).toBeInTheDocument()

        expect(screen.getByTitle('session-123')).toHaveTextContent(
            'session-123',
        )

        expect(storeSessionIdMock).not.toHaveBeenCalled()
        expect(deleteSessionMock).not.toHaveBeenCalled()
    })
})
