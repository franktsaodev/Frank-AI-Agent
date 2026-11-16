import { act, render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'

import { CopyResponseButton } from './CopyResponseButton'

describe('CopyResponseButton', () => {
    it('should retry a failed copy and keep each response independent', async () => {
        const user = userEvent.setup()
        const firstResponse = 'First response\n[Source: knowledge/first.md]'
        const secondResponse = 'Second response'

        const writeText = vi
            .spyOn(navigator.clipboard, 'writeText')
            .mockRejectedValueOnce(new Error('Permission denied'))
            .mockResolvedValue(undefined)

        try {
            render(
                <>
                    <CopyResponseButton content={firstResponse} />
                    <CopyResponseButton content={secondResponse} />
                </>,
            )

            const buttons = screen.getAllByRole('button', {
                name: 'Copy response',
            })
            const statuses = screen.getAllByRole('status')

            await user.click(buttons[0])

            await waitFor(() => {
                expect(statuses[0]).toHaveTextContent(
                    'Unable to copy. Please select and copy the response.',
                )
            })
            expect(buttons[0]).toBeEnabled()
            expect(statuses[1]).toBeEmptyDOMElement()

            await user.click(buttons[0])

            await waitFor(() => {
                expect(statuses[0]).toHaveTextContent('Copied.')
            })
            expect(statuses[1]).toBeEmptyDOMElement()

            await user.click(buttons[1])

            await waitFor(() => {
                expect(statuses[1]).toHaveTextContent('Copied.')
            })
            expect(statuses[0]).toHaveTextContent('Copied.')

            expect(writeText).toHaveBeenCalledTimes(3)
            expect(writeText).toHaveBeenNthCalledWith(1, firstResponse)
            expect(writeText).toHaveBeenNthCalledWith(2, firstResponse)
            expect(writeText).toHaveBeenNthCalledWith(3, secondResponse)
        } finally {
            writeText.mockRestore()
        }
    })

    it('should prevent duplicate pending copies and hide feedback for older content', async () => {
        const user = userEvent.setup()

        let finishCopy!: () => void
        const pendingCopy = new Promise<void>((resolve) => {
            finishCopy = resolve
        })

        const writeText = vi
            .spyOn(navigator.clipboard, 'writeText')
            .mockReturnValueOnce(pendingCopy)
            .mockResolvedValue(undefined)

        try {
            const { rerender } = render(
                <CopyResponseButton content="Earlier content" />,
            )

            const button = screen.getByRole('button', {
                name: 'Copy response',
            })

            await user.click(button)

            expect(button).toBeDisabled()
            expect(button).toHaveTextContent('Copying')
            expect(screen.getByRole('status')).toBeEmptyDOMElement()

            await user.click(button)

            expect(writeText).toHaveBeenCalledTimes(1)

            rerender(<CopyResponseButton content="Updated content" />)

            await act(async () => {
                finishCopy()
            })

            expect(button).toBeEnabled()
            expect(screen.getByRole('status')).toBeEmptyDOMElement()
            expect(writeText).toHaveBeenNthCalledWith(1, 'Earlier content')

            await user.click(button)

            await waitFor(() => {
                expect(screen.getByRole('status')).toHaveTextContent('Copied.')
            })
            expect(writeText).toHaveBeenCalledTimes(2)
            expect(writeText).toHaveBeenNthCalledWith(2, 'Updated content')
        } finally {
            await act(async () => {
                finishCopy()
            })
            writeText.mockRestore()
        }
    })
})
