import { act, render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import {
    ApiError,
    ChatStreamError,
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

    it('should show the initialization request ID and clear it after retrying', async () => {
        const user = userEvent.setup()
        const requestId = '83100577-b10b-4953-89fe-b7c29cbcfd36'

        initializeApplicationMock
            .mockRejectedValueOnce(
                new ApiError(503, 'Session storage is unavailable.', requestId),
            )
            .mockResolvedValueOnce({
                health: healthResponse,
                sessionId: 'recovered-session',
                history: [],
            })

        render(<App />)

        expect(await screen.findByText('API unavailable')).toBeInTheDocument()

        const requestIdInput = await screen.findByRole('textbox', {
            name: 'Request ID',
        })

        expect(requestIdInput).toHaveValue(requestId)
        expect(requestIdInput).toHaveAttribute('readonly')

        await user.click(
            screen.getByRole('button', {
                name: 'Retry connection',
            }),
        )

        expect(await screen.findByText('Agent ready')).toBeInTheDocument()
        expect(screen.getByTitle('recovered-session')).toHaveTextContent(
            'recovered-session',
        )
        expect(
            screen.queryByRole('textbox', {
                name: 'Request ID',
            }),
        ).not.toBeInTheDocument()
    })

    it.each([
        {
            scenario: 'an API error with a request ID',
            error: new ApiError(
                503,
                'Private retry failure detail',
                'retry-request-id',
            ),
            requestId: 'retry-request-id',
        },
        {
            scenario: 'an API error without a request ID',
            error: new ApiError(503, 'Private retry failure detail'),
            requestId: null,
        },
        {
            scenario: 'a network error',
            error: new Error('Private retry failure detail'),
            requestId: null,
        },
    ])(
        'should update initialization diagnostics after retrying fails with $scenario',
        async ({ error, requestId }) => {
            const user = userEvent.setup()
            let rejectRetry!: (reason: Error) => void

            const retryPromise = new Promise<never>((_, reject) => {
                rejectRetry = reject
            })

            initializeApplicationMock
                .mockRejectedValueOnce(
                    new ApiError(
                        503,
                        'Initial failure detail',
                        'initial-request-id',
                    ),
                )
                .mockReturnValueOnce(retryPromise)

            render(<App />)

            expect(
                await screen.findByRole('textbox', { name: 'Request ID' }),
            ).toHaveValue('initial-request-id')

            await user.click(
                screen.getByRole('button', { name: 'Retry connection' }),
            )

            expect(screen.getByText('Initializing agent')).toBeInTheDocument()
            expect(screen.queryByRole('alert')).not.toBeInTheDocument()
            expect(
                screen.queryByRole('textbox', { name: 'Request ID' }),
            ).not.toBeInTheDocument()

            await act(async () => {
                rejectRetry(error)
            })

            expect(
                await screen.findByText('API unavailable'),
            ).toBeInTheDocument()
            expect(screen.getByRole('alert')).toHaveTextContent(
                'Unable to initialize the agent. Please retry.',
            )
            expect(
                screen.queryByText('Private retry failure detail'),
            ).not.toBeInTheDocument()

            if (requestId === null) {
                expect(
                    screen.queryByRole('textbox', { name: 'Request ID' }),
                ).not.toBeInTheDocument()
            } else {
                expect(
                    screen.getByRole('textbox', { name: 'Request ID' }),
                ).toHaveValue(requestId)
            }

            expect(
                screen.getByRole('textbox', { name: 'Chat message' }),
            ).toBeDisabled()
            expect(
                screen.getByRole('button', { name: 'Retry connection' }),
            ).toBeEnabled()
            expect(initializeApplicationMock).toHaveBeenCalledTimes(2)
        },
    )

    it('should stop an active response and restore the draft without a chat error', async () => {
        const user = userEvent.setup()
        let finishStream!: () => void

        const streamGate = new Promise<void>((resolve) => {
            finishStream = resolve
        })

        streamChatMessageMock.mockImplementation(
            async function* (
                _sessionId,
                _message,
                signal,
            ): AsyncGenerator<ChatStreamEvent> {
                signal?.addEventListener('abort', finishStream, {
                    once: true,
                })

                try {
                    yield {
                        type: 'content_delta',
                        content: 'Unpersisted partial response',
                    }

                    await streamGate

                    throw new ChatStreamError(
                        'Unable to read the chat stream.',
                        'stopped-stream-request-id',
                    )
                } finally {
                    signal?.removeEventListener('abort', finishStream)
                }
            },
        )

        render(<App />)

        try {
            await screen.findByText('Agent ready')

            const messageInput = screen.getByRole('textbox', {
                name: 'Chat message',
            })

            await user.type(messageInput, 'Question to stop')
            await user.click(
                screen.getByRole('button', {
                    name: 'Send',
                }),
            )

            expect(
                await screen.findByText('Unpersisted partial response'),
            ).toBeInTheDocument()
            expect(messageInput).toBeDisabled()

            await user.click(
                await screen.findByRole('button', {
                    name: 'Stop response',
                }),
            )

            expect(streamChatMessageMock.mock.calls[0]?.[2]?.aborted).toBe(true)

            await waitFor(() => {
                expect(messageInput).toBeEnabled()
            })

            expect(getSessionHistoryMock).toHaveBeenCalledTimes(1)
            expect(getSessionHistoryMock).toHaveBeenCalledWith('session-123')
            expect(messageInput).toHaveValue('Question to stop')

            expect(
                screen.queryByText('Unpersisted partial response'),
            ).not.toBeInTheDocument()
            expect(
                screen.queryByLabelText('Agent is thinking'),
            ).not.toBeInTheDocument()
            expect(
                screen.queryByRole('button', {
                    name: 'Stop response',
                }),
            ).not.toBeInTheDocument()

            expect(screen.queryByRole('alert')).not.toBeInTheDocument()
            expect(
                screen.queryByRole('textbox', {
                    name: 'Request ID',
                }),
            ).not.toBeInTheDocument()

            expect(
                screen.getByRole('button', {
                    name: 'Send',
                }),
            ).toBeEnabled()

            expect(streamChatMessageMock).toHaveBeenCalledTimes(1)
        } finally {
            await act(async () => {
                finishStream()
            })
        }
    })

    it.each(['read failure', 'late completion', 'clean end'])(
        'should stop before first content and wait for history recovery (%s)',
        async (termination) => {
            const user = userEvent.setup()

            let finishStream!: () => void
            const streamGate = new Promise<void>((resolve) => {
                finishStream = resolve
            })

            let finishHistory!: () => void
            const historyGate = new Promise<void>((resolve) => {
                finishHistory = resolve
            })

            getSessionHistoryMock.mockImplementationOnce(async () => {
                await historyGate

                return {
                    session_id: 'session-123',
                    messages: [],
                }
            })

            streamChatMessageMock.mockImplementationOnce(
                async function* (
                    _sessionId,
                    _message,
                    signal,
                ): AsyncGenerator<ChatStreamEvent> {
                    signal?.addEventListener('abort', finishStream, {
                        once: true,
                    })

                    try {
                        await streamGate

                        if (termination === 'read failure') {
                            throw new ChatStreamError(
                                'Unable to read the chat stream.',
                                'cancelled-request-id',
                            )
                        }

                        if (termination === 'late completion') {
                            yield {
                                type: 'content_delta',
                                content: 'Late partial content',
                            }
                            yield {
                                type: 'completed',
                                response: 'Late completed response',
                            }
                        }
                    } finally {
                        signal?.removeEventListener('abort', finishStream)
                    }
                },
            )

            render(<App />)

            try {
                await screen.findByText('Agent ready')

                const messageInput = screen.getByRole('textbox', {
                    name: 'Chat message',
                })

                await user.type(messageInput, 'Stop before first content')
                await user.click(screen.getByRole('button', { name: 'Send' }))

                await user.click(
                    await screen.findByRole('button', {
                        name: 'Stop response',
                    }),
                )

                await waitFor(() => {
                    expect(getSessionHistoryMock).toHaveBeenCalledTimes(1)
                })

                expect(streamChatMessageMock.mock.calls[0]?.[2]?.aborted).toBe(
                    true,
                )
                expect(getSessionHistoryMock).toHaveBeenCalledWith(
                    'session-123',
                )

                expect(messageInput).toBeDisabled()
                expect(messageInput).toHaveValue('Stop before first content')
                expect(
                    screen.getByRole('button', {
                        name: 'Restoring conversation…',
                    }),
                ).toBeDisabled()
                expect(
                    screen.getByRole('button', {
                        name: /New conversation/,
                    }),
                ).toBeDisabled()
                expect(
                    screen.queryByLabelText('Agent is thinking'),
                ).not.toBeInTheDocument()

                // 即使直接觸發表單提交，恢復完成前也不能重送。
                const form = messageInput.closest('form')

                if (form === null) {
                    throw new Error('Chat composer form was not found.')
                }

                await act(async () => {
                    form.requestSubmit()
                })

                expect(streamChatMessageMock).toHaveBeenCalledTimes(1)
                expect(
                    screen.queryByText('Late partial content'),
                ).not.toBeInTheDocument()
                expect(
                    screen.queryByText('Late completed response'),
                ).not.toBeInTheDocument()
                expect(screen.queryByRole('alert')).not.toBeInTheDocument()

                await act(async () => {
                    finishHistory()
                })

                await waitFor(() => {
                    expect(messageInput).toBeEnabled()
                })

                expect(messageInput).toHaveValue('Stop before first content')
                expect(
                    screen.getByRole('button', { name: 'Send' }),
                ).toBeEnabled()
                expect(screen.queryByRole('alert')).not.toBeInTheDocument()
                expect(
                    screen.queryByRole('textbox', { name: 'Request ID' }),
                ).not.toBeInTheDocument()
                expect(
                    screen.queryByText('Late completed response'),
                ).not.toBeInTheDocument()
            } finally {
                await act(async () => {
                    finishStream()
                    finishHistory()
                })
            }
        },
    )

    it.each(['history-recovery-request-id', null])(
        'should show recovery diagnostics when stopped history cannot be loaded (%s)',
        async (requestId) => {
            const user = userEvent.setup()

            let finishStream!: () => void
            const streamGate = new Promise<void>((resolve) => {
                finishStream = resolve
            })

            getSessionHistoryMock.mockRejectedValueOnce(
                new ApiError(500, 'History unavailable', requestId),
            )

            streamChatMessageMock.mockImplementationOnce(
                async function* (
                    _sessionId,
                    _message,
                    signal,
                ): AsyncGenerator<ChatStreamEvent> {
                    signal?.addEventListener('abort', finishStream, {
                        once: true,
                    })

                    try {
                        yield {
                            type: 'content_delta',
                            content: 'Discard this partial response',
                        }

                        await streamGate

                        throw new ChatStreamError(
                            'Unable to read the chat stream.',
                            'cancelled-stream-request-id',
                        )
                    } finally {
                        signal?.removeEventListener('abort', finishStream)
                    }
                },
            )

            render(<App />)

            try {
                await screen.findByText('Agent ready')

                const messageInput = screen.getByRole('textbox', {
                    name: 'Chat message',
                })

                await user.type(messageInput, 'Preserve this draft')
                await user.click(screen.getByRole('button', { name: 'Send' }))

                await screen.findByText('Discard this partial response')

                await user.click(
                    screen.getByRole('button', { name: 'Stop response' }),
                )

                expect(await screen.findByRole('alert')).toHaveTextContent(
                    'Unable to load the latest conversation. Please reload before retrying.',
                )

                await waitFor(() => {
                    expect(messageInput).toBeEnabled()
                })

                expect(messageInput).toHaveValue('Preserve this draft')
                expect(
                    screen.queryByText('Discard this partial response'),
                ).not.toBeInTheDocument()

                if (requestId === null) {
                    expect(
                        screen.queryByRole('textbox', { name: 'Request ID' }),
                    ).not.toBeInTheDocument()
                } else {
                    expect(
                        screen.getByRole('textbox', { name: 'Request ID' }),
                    ).toHaveValue(requestId)
                }

                expect(getSessionHistoryMock).toHaveBeenCalledWith(
                    'session-123',
                )
                expect(streamChatMessageMock).toHaveBeenCalledTimes(1)
            } finally {
                await act(async () => {
                    finishStream()
                })
            }
        },
    )

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

        expect(streamChatMessageMock).toHaveBeenCalledWith(
            'session-123',
            'How do sessions expire?',
            expect.any(AbortSignal),
        )

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
            expect.any(AbortSignal),
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

    it.each(['83100577-b10b-4953-89fe-b7c29cbcfd36', null])(
        'should show the available request ID after a stream read failure (%s)',
        async (requestId) => {
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

            async function* failDuringChat(): AsyncGenerator<ChatStreamEvent> {
                yield {
                    type: 'content_delta',
                    content: 'Uncommitted response',
                }

                throw new ChatStreamError(
                    'Private connection failure detail',
                    requestId,
                )
            }

            streamChatMessageMock.mockReturnValue(failDuringChat())

            render(<App />)
            await screen.findByText('Agent ready')

            const messageInput = screen.getByRole('textbox', {
                name: 'Chat message',
            })

            await user.type(messageInput, 'Hello')
            await user.click(screen.getByRole('button', { name: 'Send' }))

            expect(
                await screen.findByText('Previously saved reply'),
            ).toBeInTheDocument()

            expect(screen.getByRole('alert')).toHaveTextContent(
                'Unable to reach the agent. Please try again.',
            )
            expect(
                screen.queryByText('Private connection failure detail'),
            ).not.toBeInTheDocument()
            expect(
                screen.queryByText('Uncommitted response'),
            ).not.toBeInTheDocument()
            expect(messageInput).toHaveValue('Hello')

            if (requestId === null) {
                expect(
                    screen.queryByRole('textbox', { name: 'Request ID' }),
                ).not.toBeInTheDocument()
            } else {
                expect(
                    screen.getByRole('textbox', { name: 'Request ID' }),
                ).toHaveValue(requestId)
            }

            expect(getSessionHistoryMock).toHaveBeenCalledWith('session-123')
            expect(streamChatMessageMock).toHaveBeenCalledOnce()
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
