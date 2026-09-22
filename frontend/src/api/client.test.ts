import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import {
    ApiError,
    createSession,
    deleteSession,
    getHealth,
    getSessionHistory,
    sendChatMessage,
    streamChatMessage,
} from './client'

import type { ChatStreamEvent } from './types'

const fetchMock = vi.fn<typeof fetch>()

function createJsonResponse(payload: unknown, status = 200): Response {
    return new Response(JSON.stringify(payload), {
        status,
        headers: {
            'Content-Type': 'application/json',
        },
    })
}

function createSseResponse(body: string, status = 200): Response {
    return new Response(body, {
        status,
        headers: {
            'Content-Type': 'text/event-stream',
        },
    })
}

async function collectChatEvents(
    events: AsyncIterable<ChatStreamEvent>,
): Promise<ChatStreamEvent[]> {
    const collectedEvents: ChatStreamEvent[] = []

    for await (const event of events) {
        collectedEvents.push(event)
    }

    return collectedEvents
}

describe('API client', () => {
    beforeEach(() => {
        fetchMock.mockReset()
        vi.stubGlobal('fetch', fetchMock)
    })

    afterEach(() => {
        vi.unstubAllGlobals()
        vi.unstubAllEnvs()
    })

    it('should retrieve API health information', async () => {
        fetchMock.mockResolvedValue(
            createJsonResponse({
                status: 'ok',
                service: 'Frank AI Agent',
                version: '1.4.0',
            }),
        )

        const result = await getHealth()

        expect(result).toEqual({
            status: 'ok',
            service: 'Frank AI Agent',
            version: '1.4.0',
        })

        expect(fetchMock).toHaveBeenCalledWith(
            'http://localhost:8000/health',
            expect.objectContaining({
                headers: {
                    Accept: 'application/json',
                },
            }),
        )
    })

    it('should create a session using POST', async () => {
        fetchMock.mockResolvedValue(
            createJsonResponse(
                {
                    session_id: 'session-123',
                },
                201,
            ),
        )

        const result = await createSession()

        expect(result.session_id).toBe('session-123')

        expect(fetchMock).toHaveBeenCalledWith(
            'http://localhost:8000/api/v1/sessions',
            expect.objectContaining({
                method: 'POST',
            }),
        )
    })

    it('should encode the session ID when retrieving history', async () => {
        fetchMock.mockResolvedValue(
            createJsonResponse({
                session_id: 'session/id',
                messages: [],
            }),
        )

        await getSessionHistory('session/id')

        expect(fetchMock).toHaveBeenCalledWith(
            'http://localhost:8000/api/v1/sessions/session%2Fid/history',
            expect.any(Object),
        )
    })

    it('should send a chat message as JSON', async () => {
        fetchMock.mockResolvedValue(
            createJsonResponse({
                response: 'Hello from the agent.',
            }),
        )

        const result = await sendChatMessage('session-123', 'Hello')

        expect(result.response).toBe('Hello from the agent.')

        expect(fetchMock).toHaveBeenCalledWith(
            'http://localhost:8000/api/v1/sessions/session-123/chat',
            expect.objectContaining({
                method: 'POST',
                headers: {
                    Accept: 'application/json',
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    message: 'Hello',
                }),
            }),
        )
    })

    it('should stream chat events using POST', async () => {
        fetchMock.mockResolvedValue(
            createSseResponse(
                'event: content_delta\n' +
                    'data: {"content":"Hello"}\n\n' +
                    'event: completed\n' +
                    'data: {"response":"Hello"}\n\n',
            ),
        )

        const events = await collectChatEvents(
            streamChatMessage('session/id', 'Hello'),
        )

        expect(events).toEqual([
            {
                type: 'content_delta',
                content: 'Hello',
            },
            {
                type: 'completed',
                response: 'Hello',
            },
        ])

        expect(fetchMock).toHaveBeenCalledWith(
            'http://localhost:8000/api/v1/sessions/session%2Fid/chat/stream',
            expect.objectContaining({
                method: 'POST',
                headers: {
                    Accept: 'text/event-stream',
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    message: 'Hello',
                }),
            }),
        )
    })

    it('should throw ApiError when starting the stream fails', async () => {
        fetchMock.mockResolvedValue(
            createJsonResponse(
                {
                    error: 'session_not_found',
                    message: 'Session not found.',
                },
                404,
            ),
        )

        await expect(
            collectChatEvents(streamChatMessage('missing-session', 'Hello')),
        ).rejects.toEqual(
            expect.objectContaining({
                name: 'ApiError',
                status: 404,
                message: 'Session not found.',
            }),
        )
    })

    it('should reject a response that is not an SSE stream', async () => {
        fetchMock.mockResolvedValue(
            createJsonResponse({
                response: 'Unexpected JSON response',
            }),
        )

        await expect(
            collectChatEvents(streamChatMessage('session-123', 'Hello')),
        ).rejects.toThrow('API returned an invalid chat stream response.')
    })

    it('should reject an SSE response without a body', async () => {
        fetchMock.mockResolvedValue(
            new Response(null, {
                status: 200,
                headers: {
                    'Content-Type': 'text/event-stream',
                },
            }),
        )

        await expect(
            collectChatEvents(streamChatMessage('session-123', 'Hello')),
        ).rejects.toThrow('API returned an empty chat stream response.')
    })

    it('should delete a session using DELETE', async () => {
        fetchMock.mockResolvedValue(
            createJsonResponse({
                deleted: true,
            }),
        )

        const result = await deleteSession('session-123')

        expect(result.deleted).toBe(true)

        expect(fetchMock).toHaveBeenCalledWith(
            'http://localhost:8000/api/v1/sessions/session-123',
            expect.objectContaining({
                method: 'DELETE',
            }),
        )
    })

    it('should throw ApiError using the API error message', async () => {
        fetchMock.mockResolvedValue(
            createJsonResponse(
                {
                    error: 'session_not_found',
                    message: 'Session was not found.',
                },
                404,
            ),
        )

        try {
            await getSessionHistory('missing-session')
            throw new Error('Expected getSessionHistory to reject')
        } catch (error: unknown) {
            expect(error).toBeInstanceOf(ApiError)
            expect(error).toEqual(
                expect.objectContaining({
                    name: 'ApiError',
                    status: 404,
                    message: 'Session was not found.',
                }),
            )
        }
    })

    it('should use same-origin paths when the API base URL is empty', async () => {
        vi.stubEnv('VITE_API_BASE_URL', '')
        vi.resetModules()

        const { getHealth: getSameOriginHealth } = await import('./client')

        fetchMock.mockResolvedValue(
            createJsonResponse({
                status: 'ok',
                service: 'Frank AI Agent',
                version: '1.4.0',
            }),
        )

        await getSameOriginHealth()

        expect(fetchMock).toHaveBeenCalledWith(
            '/health',
            expect.objectContaining({
                headers: {
                    Accept: 'application/json',
                },
            }),
        )
    })
})
