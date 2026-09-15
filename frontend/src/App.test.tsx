import {
    render,
    screen,
} from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import {
    beforeEach,
    describe,
    expect,
    it,
    vi,
} from 'vitest'

import {
    ApiError,
    createSession,
    deleteSession,
    sendChatMessage,
} from './api/client'
import App from './App'
import {
    initializeApplication,
    resetApplicationInitialization,
} from './session/applicationInitializer'
import {
    storeSessionId,
} from './storage/activeSessionStorage'

vi.mock('./api/client', async (importOriginal) => {
    const actual =
        await importOriginal<typeof import('./api/client')>()

    return {
        ...actual,
        createSession: vi.fn(),
        deleteSession: vi.fn(),
        sendChatMessage: vi.fn(),
    }
})

vi.mock('./session/applicationInitializer', () => ({
    initializeApplication: vi.fn(),
    resetApplicationInitialization: vi.fn(),
}))

vi.mock('./storage/activeSessionStorage', () => ({
    storeSessionId: vi.fn(),
}))

const initializeApplicationMock =
    vi.mocked(initializeApplication)
const resetApplicationInitializationMock =
    vi.mocked(resetApplicationInitialization)

const createSessionMock = vi.mocked(createSession)
const deleteSessionMock = vi.mocked(deleteSession)
const sendChatMessageMock = vi.mocked(sendChatMessage)
const storeSessionIdMock = vi.mocked(storeSessionId)

const healthResponse = {
    status: 'ok' as const,
    service: 'Frank AI Agent',
    version: '1.2.0',
}

function createPendingPromise<T>(): Promise<T> {
    return new Promise(() => undefined)
}

describe('App', () => {
    beforeEach(() => {
        vi.clearAllMocks()

        initializeApplicationMock.mockResolvedValue({
            health: healthResponse,
            sessionId: 'session-123',
            history: [],
        })
    })

    it('should show the initializing state while initialization is pending', () => {
        initializeApplicationMock.mockReturnValue(
            createPendingPromise(),
        )

        render(<App />)

        expect(
            screen.getByText('Initializing agent'),
        ).toBeInTheDocument()

        expect(
            screen.getByRole(
                'textbox',
                {
                    name: 'Chat message',
                },
            ),
        ).toBeDisabled()

        expect(
            screen.getByRole(
                'button',
                {
                    name: 'New conversation',
                },
            ),
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

        expect(
            await screen.findByText('Agent ready'),
        ).toBeInTheDocument()

        expect(
            screen.getByTitle('stored-session'),
        ).toHaveTextContent('stored-session')

        expect(
            screen.getByText('How do sessions expire?'),
        ).toBeInTheDocument()

        expect(
            screen.getByText('Sessions use sliding expiration.'),
        ).toBeInTheDocument()

        expect(
            screen.queryByText('Ignored tool output'),
        ).not.toBeInTheDocument()

        expect(
            screen.getByRole(
                'textbox',
                {
                    name: 'Chat message',
                },
            ),
        ).toBeEnabled()
    })

    it('should retry initialization after the API becomes available', async () => {
        const user = userEvent.setup()

        initializeApplicationMock
            .mockRejectedValueOnce(
                new Error('API unavailable'),
            )
            .mockResolvedValueOnce({
                health: healthResponse,
                sessionId: 'recovered-session',
                history: [],
            })

        render(<App />)

        expect(
            await screen.findByText('API unavailable'),
        ).toBeInTheDocument()

        await user.click(
            screen.getByRole(
                'button',
                {
                    name: 'Retry connection',
                },
            ),
        )

        expect(
            await screen.findByText('Agent ready'),
        ).toBeInTheDocument()

        expect(
            screen.getByTitle('recovered-session'),
        ).toHaveTextContent('recovered-session')

        expect(
            resetApplicationInitializationMock,
        ).toHaveBeenCalledOnce()

        expect(
            initializeApplicationMock,
        ).toHaveBeenCalledTimes(2)
    })

    it('should send a message and display the agent response', async () => {
        const user = userEvent.setup()

        sendChatMessageMock.mockResolvedValue({
            response: 'Sessions use sliding expiration.',
        })

        render(<App />)

        await screen.findByText('Agent ready')

        const messageInput = screen.getByRole(
            'textbox',
            {
                name: 'Chat message',
            },
        )

        await user.type(
            messageInput,
            'How do sessions expire?',
        )

        await user.click(
            screen.getByRole(
                'button',
                {
                    name: 'Send',
                },
            ),
        )

        expect(sendChatMessageMock).toHaveBeenCalledWith(
            'session-123',
            'How do sessions expire?',
        )

        expect(
            screen.getByText('How do sessions expire?'),
        ).toBeInTheDocument()

        expect(
            await screen.findByText(
                'Sessions use sliding expiration.',
            ),
        ).toBeInTheDocument()

        expect(messageInput).toHaveValue('')
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

        expect(
            await screen.findByText('Previous question'),
        ).toBeInTheDocument()

        await user.click(
            screen.getByRole(
                'button',
                {
                    name: 'New conversation',
                },
            ),
        )

        expect(
            await screen.findByTitle('new-session'),
        ).toHaveTextContent('new-session')

        expect(
            screen.queryByText('Previous question'),
        ).not.toBeInTheDocument()

        expect(storeSessionIdMock).toHaveBeenCalledWith(
            'new-session',
        )

        expect(deleteSessionMock).toHaveBeenCalledWith(
            'old-session',
        )
    })

    it('should show an error when sending a message fails', async () => {
        const user = userEvent.setup()

        sendChatMessageMock.mockRejectedValue(
            new ApiError(
                503,
                'Agent service is unavailable.',
            ),
        )

        render(<App />)

        await screen.findByText('Agent ready')

        const messageInput = screen.getByRole(
            'textbox',
            {
                name: 'Chat message',
            },
        )

        await user.type(
            messageInput,
            'Hello',
        )

        await user.click(
            screen.getByRole(
                'button',
                {
                    name: 'Send',
                },
            ),
        )

        expect(
            await screen.findByText(
                'Agent service is unavailable.',
            ),
        ).toBeInTheDocument()

        expect(
            screen.getByText('Hello'),
        ).toBeInTheDocument()

        expect(messageInput).toBeEnabled()
    })

    it('should keep the active session when creating a new one fails', async () => {
        const user = userEvent.setup()

        createSessionMock.mockRejectedValue(
            new ApiError(
                500,
                'Unable to create the session.',
            ),
        )

        render(<App />)

        expect(
            await screen.findByTitle('session-123'),
        ).toHaveTextContent('session-123')

        await user.click(
            screen.getByRole(
                'button',
                {
                    name: 'New conversation',
                },
            ),
        )

        expect(
            await screen.findByText(
                'Unable to create the session.',
            ),
        ).toBeInTheDocument()

        expect(
            screen.getByTitle('session-123'),
        ).toHaveTextContent('session-123')

        expect(storeSessionIdMock).not.toHaveBeenCalled()
        expect(deleteSessionMock).not.toHaveBeenCalled()
    })
})
