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
    getHealth,
    getSessionHistory,
} from '../api/client'
import {
    clearStoredSessionId,
    getStoredSessionId,
    storeSessionId,
} from '../storage/activeSessionStorage'
import {
    initializeApplication,
    resetApplicationInitialization,
} from './applicationInitializer'

vi.mock('../api/client', async (importOriginal) => {
    const actual =
        await importOriginal<typeof import('../api/client')>()

    return {
        ...actual,
        createSession: vi.fn(),
        getHealth: vi.fn(),
        getSessionHistory: vi.fn(),
    }
})

vi.mock('../storage/activeSessionStorage', () => ({
    clearStoredSessionId: vi.fn(),
    getStoredSessionId: vi.fn(),
    storeSessionId: vi.fn(),
}))

const getHealthMock = vi.mocked(getHealth)
const createSessionMock = vi.mocked(createSession)
const getSessionHistoryMock = vi.mocked(getSessionHistory)
const getStoredSessionIdMock = vi.mocked(getStoredSessionId)
const storeSessionIdMock = vi.mocked(storeSessionId)
const clearStoredSessionIdMock = vi.mocked(clearStoredSessionId)

const healthResponse = {
    status: 'ok' as const,
    service: 'Frank AI Agent',
    version: '1.3.0',
}

describe('application initializer', () => {
    beforeEach(() => {
        resetApplicationInitialization()
        vi.clearAllMocks()

        getHealthMock.mockResolvedValue(healthResponse)
        getStoredSessionIdMock.mockReturnValue(null)
        createSessionMock.mockResolvedValue({
            session_id: 'new-session',
        })
    })

    it('should create and store a session when none is stored', async () => {
        const result = await initializeApplication()

        expect(result).toEqual({
            health: healthResponse,
            sessionId: 'new-session',
            history: [],
        })

        expect(createSessionMock).toHaveBeenCalledOnce()
        expect(storeSessionIdMock).toHaveBeenCalledWith(
            'new-session',
        )
        expect(getSessionHistoryMock).not.toHaveBeenCalled()
    })

    it('should restore a stored session and its history', async () => {
        getStoredSessionIdMock.mockReturnValue(
            'stored-session',
        )
        getSessionHistoryMock.mockResolvedValue({
            session_id: 'stored-session',
            messages: [
                {
                    role: 'user',
                    content: 'Hello',
                },
                {
                    role: 'assistant',
                    content: 'Hi!',
                },
            ],
        })

        const result = await initializeApplication()

        expect(result).toEqual({
            health: healthResponse,
            sessionId: 'stored-session',
            history: [
                {
                    role: 'user',
                    content: 'Hello',
                },
                {
                    role: 'assistant',
                    content: 'Hi!',
                },
            ],
        })

        expect(getSessionHistoryMock).toHaveBeenCalledWith(
            'stored-session',
        )
        expect(createSessionMock).not.toHaveBeenCalled()
        expect(storeSessionIdMock).not.toHaveBeenCalled()
    })

    it('should replace an expired stored session', async () => {
        getStoredSessionIdMock.mockReturnValue(
            'expired-session',
        )
        getSessionHistoryMock.mockRejectedValue(
            new ApiError(
                404,
                'Session not found',
            ),
        )

        const result = await initializeApplication()

        expect(clearStoredSessionIdMock).toHaveBeenCalledOnce()
        expect(createSessionMock).toHaveBeenCalledOnce()
        expect(storeSessionIdMock).toHaveBeenCalledWith(
            'new-session',
        )
        expect(result.sessionId).toBe('new-session')
        expect(result.history).toEqual([])
    })

    it('should propagate non-404 history errors', async () => {
        getStoredSessionIdMock.mockReturnValue(
            'stored-session',
        )
        getSessionHistoryMock.mockRejectedValue(
            new ApiError(
                500,
                'Internal server error',
            ),
        )

        await expect(
            initializeApplication(),
        ).rejects.toMatchObject({
            status: 500,
            message: 'Internal server error',
        })

        expect(clearStoredSessionIdMock).not.toHaveBeenCalled()
        expect(createSessionMock).not.toHaveBeenCalled()
        expect(storeSessionIdMock).not.toHaveBeenCalled()
    })

    it('should share one promise between simultaneous calls', async () => {
        const firstPromise = initializeApplication()
        const secondPromise = initializeApplication()

        expect(firstPromise).toBe(secondPromise)

        await firstPromise

        expect(getHealthMock).toHaveBeenCalledOnce()
        expect(createSessionMock).toHaveBeenCalledOnce()
    })

    it('should retry after initialization fails', async () => {
        getHealthMock
            .mockRejectedValueOnce(
                new Error('API unavailable'),
            )
            .mockResolvedValueOnce(healthResponse)

        await expect(
            initializeApplication(),
        ).rejects.toThrow('API unavailable')

        const result = await initializeApplication()

        expect(result.sessionId).toBe('new-session')
        expect(getHealthMock).toHaveBeenCalledTimes(2)
        expect(createSessionMock).toHaveBeenCalledOnce()
    })

    it('should initialize again after an explicit reset', async () => {
        createSessionMock
            .mockResolvedValueOnce({
                session_id: 'session-1',
            })
            .mockResolvedValueOnce({
                session_id: 'session-2',
            })

        const firstResult = await initializeApplication()

        resetApplicationInitialization()

        const secondResult = await initializeApplication()

        expect(firstResult.sessionId).toBe('session-1')
        expect(secondResult.sessionId).toBe('session-2')
        expect(getHealthMock).toHaveBeenCalledTimes(2)
        expect(createSessionMock).toHaveBeenCalledTimes(2)
    })
})