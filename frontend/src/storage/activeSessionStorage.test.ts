import {
    beforeEach,
    describe,
    expect,
    it,
    vi,
} from 'vitest'

import {
    clearStoredSessionId,
    getStoredSessionId,
    storeSessionId,
} from './activeSessionStorage'

const ACTIVE_SESSION_ID_KEY = 'frank-ai-agent.active-session-id'

describe('activeSessionStorage', () => {
    beforeEach(() => {
        window.localStorage.clear()
    })

    it('should return null when no session is stored', () => {
        expect(getStoredSessionId()).toBeNull()
    })

    it('should store and retrieve the active session ID', () => {
        storeSessionId('session-123')

        expect(getStoredSessionId()).toBe('session-123')
    })

    it('should return null when the stored session ID is blank', () => {
        window.localStorage.setItem(
            ACTIVE_SESSION_ID_KEY,
            '   ',
        )

        expect(getStoredSessionId()).toBeNull()
    })

    it('should remove the stored session ID', () => {
        storeSessionId('session-123')

        clearStoredSessionId()

        expect(getStoredSessionId()).toBeNull()
    })

    it('should tolerate unavailable browser storage', () => {
        vi.spyOn(
            Storage.prototype,
            'getItem',
        ).mockImplementation(() => {
            throw new DOMException('Storage unavailable')
        })

        expect(getStoredSessionId()).toBeNull()
    })
})