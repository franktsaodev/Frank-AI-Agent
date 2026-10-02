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

    it.each(['83100577-b10b-4953-89fe-b7c29cbcfd36', null])(
        'should preserve the response request ID when reading the stream fails (%s)',
        async (requestId) => {
            const headers = new Headers({
                'Content-Type': 'text/event-stream',
            })

            if (requestId !== null) {
                headers.set('X-Request-ID', requestId)
            }

            let readCount = 0

            const body = new ReadableStream<Uint8Array>(
                {
                    pull(controller) {
                        readCount += 1

                        if (readCount === 1) {
                            controller.enqueue(
                                new TextEncoder().encode(
                                    'event: content_delta\n' +
                                        'data: {"content":"Partial reply"}\n\n',
                                ),
                            )
                            return
                        }

                        controller.error(
                            new Error('Private connection failure detail'),
                        )
                    },
                },
                {
                    highWaterMark: 0,
                },
            )

            const fetchSpy = vi
                .spyOn(globalThis, 'fetch')
                .mockResolvedValueOnce(new Response(body, { headers }))

            try {
                const stream = streamChatMessage('session-123', 'Hello')

                expect(await stream.next()).toEqual({
                    done: false,
                    value: {
                        type: 'content_delta',
                        content: 'Partial reply',
                    },
                })

                await expect(stream.next()).rejects.toMatchObject({
                    name: 'ChatStreamError',
                    message: 'Unable to read the chat stream.',
                    requestId,
                })
            } finally {
                fetchSpy.mockRestore()
            }
        },
    )

    it.each([
        {
            scenario: 'invalid JSON',
            body: 'event: content_delta\ndata: {"content":\n\n',
            message: 'Unable to read the chat stream.',
        },
        {
            scenario: 'invalid event payload',
            body: 'event: content_delta\ndata: {"content":123}\n\n',
            message: 'Unable to read the chat stream.',
        },
        {
            scenario: 'missing terminal event',
            body: 'event: content_delta\ndata: {"content":"Partial reply"}\n\n',
            message: 'Chat stream ended before completion.',
        },
    ])(
        'should preserve the response request ID for $scenario',
        async ({ body, message }) => {
            const requestId = '83100577-b10b-4953-89fe-b7c29cbcfd36'

            const fetchSpy = vi
                .spyOn(globalThis, 'fetch')
                .mockResolvedValueOnce(
                    new Response(body, {
                        headers: {
                            'Content-Type': 'text/event-stream',
                            'X-Request-ID': requestId,
                        },
                    }),
                )

            try {
                await expect(
                    collectChatEvents(
                        streamChatMessage('session-123', 'Hello'),
                    ),
                ).rejects.toMatchObject({
                    name: 'ChatStreamError',
                    message,
                    requestId,
                })
            } finally {
                fetchSpy.mockRestore()
            }
        },
    )

    it.each([
        {
            terminal: 'completed',
            block: 'event: completed\ndata: {"response":"Done"}\n\n',
            expected: {
                type: 'completed',
                response: 'Done',
            },
        },
        {
            terminal: 'error',
            block:
                'event: error\n' +
                'data: {"error":"session_conflict","message":"Please retry."}\n\n',
            expected: {
                type: 'error',
                error: 'session_conflict',
                message: 'Please retry.',
                requestId: '83100577-b10b-4953-89fe-b7c29cbcfd36',
            },
        },
    ])(
        'should stop parsing after the $terminal event',
        async ({ block, expected }) => {
            const fetchSpy = vi
                .spyOn(globalThis, 'fetch')
                .mockResolvedValueOnce(
                    new Response(
                        block + 'event: content_delta\ndata: invalid-json\n\n',
                        {
                            headers: {
                                'Content-Type': 'text/event-stream',
                                'X-Request-ID':
                                    '83100577-b10b-4953-89fe-b7c29cbcfd36',
                            },
                        },
                    ),
                )

            try {
                const events = await collectChatEvents(
                    streamChatMessage('session-123', 'Hello'),
                )

                expect(events).toEqual([expected])
            } finally {
                fetchSpy.mockRestore()
            }
        },
    )

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

    it('should preserve the request ID when an API request fails', async () => {
        const requestId = '83100577-b10b-4953-89fe-b7c29cbcfd36'

        const fetchSpy = vi.spyOn(globalThis, 'fetch').mockResolvedValueOnce(
            new Response(
                JSON.stringify({
                    error: 'session_storage_unavailable',
                    message: 'Session storage is unavailable.',
                }),
                {
                    status: 503,
                    headers: {
                        'Content-Type': 'application/json',
                        'X-Request-ID': requestId,
                    },
                },
            ),
        )

        try {
            await expect(
                sendChatMessage('session-123', 'Hello'),
            ).rejects.toMatchObject({
                name: 'ApiError',
                status: 503,
                message: 'Session storage is unavailable.',
                requestId,
            })
        } finally {
            fetchSpy.mockRestore()
        }
    })

    it.each(['83100577-b10b-4953-89fe-b7c29cbcfd36', null])(
        'should attach the response request ID to a stream error (%s)',
        async (requestId) => {
            const headers = new Headers({
                'Content-Type': 'text/event-stream',
            })

            if (requestId !== null) {
                headers.set('X-Request-ID', requestId)
            }

            const fetchSpy = vi
                .spyOn(globalThis, 'fetch')
                .mockResolvedValueOnce(
                    new Response(
                        'event: content_delta\n' +
                            'data: {"content":"Partial reply"}\n\n' +
                            'event: error\n' +
                            'data: {"error":"session_conflict",' +
                            '"message":"Please retry.",' +
                            '"requestId":"payload-id"}\n\n',
                        {
                            status: 200,
                            headers,
                        },
                    ),
                )

            try {
                const events = await collectChatEvents(
                    streamChatMessage('session-123', 'Hello'),
                )

                expect(events).toEqual([
                    {
                        type: 'content_delta',
                        content: 'Partial reply',
                    },
                    {
                        type: 'error',
                        error: 'session_conflict',
                        message: 'Please retry.',
                        requestId,
                    },
                ])
            } finally {
                fetchSpy.mockRestore()
            }
        },
    )

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
