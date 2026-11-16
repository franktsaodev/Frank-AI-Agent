import { useRef, useState } from 'react'

interface CopyResponseButtonProps {
    content: string
}

interface CopyFeedback {
    content: string
    message: string
}

export function CopyResponseButton({ content }: CopyResponseButtonProps) {
    const [isCopying, setIsCopying] = useState(false)
    const [feedback, setFeedback] = useState<CopyFeedback | null>(null)
    const copyingRef = useRef(false)

    async function handleCopy(): Promise<void> {
        if (copyingRef.current) {
            return
        }

        copyingRef.current = true
        setIsCopying(true)
        setFeedback(null)

        try {
            await navigator.clipboard.writeText(content)

            setFeedback({
                content,
                message: 'Copied.',
            })
        } catch {
            setFeedback({
                content,
                message: 'Unable to copy. Please select and copy the response.',
            })
        } finally {
            copyingRef.current = false
            setIsCopying(false)
        }
    }

    return (
        <div className="response-actions">
            <button
                type="button"
                onClick={handleCopy}
                disabled={isCopying}
                aria-label="Copy response"
            >
                {isCopying ? 'Copying…' : 'Copy'}
            </button>

            <span role="status" aria-atomic="true">
                {feedback?.content === content ? feedback.message : ''}
            </span>
        </div>
    )
}
