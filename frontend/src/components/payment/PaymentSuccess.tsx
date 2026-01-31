import { useEffect, useState, useRef } from 'react'
import './PaymentReturn.css'

type PaymentStatus = 'loading' | 'polling' | 'success' | 'timeout' | 'error'

type PaymentSuccessProps = {
    onClose: () => void
}

const POLL_INTERVAL_MS = 2500
const MAX_POLL_DURATION_MS = 90000
const MAX_POLLS = Math.floor(MAX_POLL_DURATION_MS / POLL_INTERVAL_MS) // 36 polls

const PaymentSuccess = ({ onClose }: PaymentSuccessProps) => {
    const [status, setStatus] = useState<PaymentStatus>('loading')
    const [message, setMessage] = useState('')
    const [statusToken, setStatusToken] = useState<string | null>(null)
    const [pollCount, setPollCount] = useState(0)
    const pollIntervalRef = useRef<number | null>(null)
    const startTimeRef = useRef<number>(Date.now())

    useEffect(() => {
        const params = new URLSearchParams(window.location.search)
        const urlIntentId = params.get('checkoutIntentId')
        const storedIntentId = localStorage.getItem('checkout_intent_id')

        const checkoutIntentId = urlIntentId || storedIntentId

        if (!checkoutIntentId) {
            setStatus('error')
            setMessage('Aucun paiement en attente trouvé')
            return
        }

        // Start polling
        startPolling(checkoutIntentId, storedIntentId)

        // Cleanup on unmount
        return () => {
            if (pollIntervalRef.current) {
                clearInterval(pollIntervalRef.current)
            }
        }
    }, [])

    const startPolling = (checkoutIntentId: string, storedIntentId: string | null) => {
        setStatus('polling')
        startTimeRef.current = Date.now()

        const poll = async () => {
            const currentPollCount = Math.floor((Date.now() - startTimeRef.current) / POLL_INTERVAL_MS)
            setPollCount(currentPollCount + 1)

            try {
                const response = await fetch(`/api/payments/status/${checkoutIntentId}`)

                if (!response.ok) {
                    if (response.status === 404) {
                        clearPolling()
                        setStatus('error')
                        setMessage('Commande introuvable. Vérifie ton email ou contacte le support.')
                        return
                    }
                    throw new Error(`HTTP ${response.status}`)
                }

                const data = await response.json()

                if (data.payment_status === 'completed') {
                    clearPolling()
                    setStatus('success')
                    setMessage('Ta commande a bien été enregistrée !')
                    setStatusToken(data.status_token)

                    // Clear stored data only if we were the ones who put it there
                    if (storedIntentId === checkoutIntentId) {
                        localStorage.removeItem('checkout_intent_id')
                        localStorage.removeItem('pending_reservation_id')
                    }
                } else if (data.payment_status === 'failed') {
                    clearPolling()
                    setStatus('error')
                    setMessage('Le paiement a échoué. Réessaye ou contacte le support.')
                } else if (currentPollCount >= MAX_POLLS - 1) {
                    // Timeout reached
                    clearPolling()
                    setStatus('timeout')
                    setMessage('La confirmation prend plus de temps que prévu...')
                }
            } catch {
                // Don't fail immediately on network errors, keep polling unless timeout
                if (currentPollCount >= MAX_POLLS - 1) {
                    clearPolling()
                    setStatus('timeout')
                    setMessage('Impossible de vérifier le statut. Vérifie ta connexion.')
                }
            }
        }

        // Initial poll
        poll()

        // Set up interval for subsequent polls
        pollIntervalRef.current = window.setInterval(poll, POLL_INTERVAL_MS)
    }

    const clearPolling = () => {
        if (pollIntervalRef.current) {
            clearInterval(pollIntervalRef.current)
            pollIntervalRef.current = null
        }
    }

    const handleRefresh = () => {
        window.location.reload()
    }

    const handleViewOrder = () => {
        if (statusToken) {
            window.location.href = `/order/status/${statusToken}`
        } else {
            onClose()
        }
    }

    return (
        <div className="payment-return">
            <div className="payment-return__card">
                {status === 'loading' && (
                    <>
                        <div className="payment-return__icon payment-return__icon--loading">⏳</div>
                        <h1>Initialisation...</h1>
                        <p>Préparation de la vérification du paiement.</p>
                    </>
                )}

                {status === 'polling' && (
                    <>
                        <div className="payment-return__icon payment-return__icon--loading">⏳</div>
                        <h1>Vérification du paiement...</h1>
                        <p>Attente de la confirmation de HelloAsso.</p>
                        <p className="payment-return__details">
                            Tentative {pollCount} / {MAX_POLLS}
                        </p>
                        <p className="payment-return__hint">
                            Cela prend généralement moins de 10 secondes.
                        </p>
                    </>
                )}

                {status === 'success' && (
                    <>
                        <div className="payment-return__icon payment-return__icon--success">✅</div>
                        <h1>Paiement réussi !</h1>
                        <p>{message}</p>
                        <p className="payment-return__details">
                            Tu recevras un email de confirmation avec les détails de ta commande.
                        </p>
                        <button className="payment-return__btn payment-return__btn--primary" onClick={handleViewOrder}>
                            📊 Voir ma commande
                        </button>
                        <button className="payment-return__btn payment-return__btn--secondary" onClick={onClose}>
                            Retour à l'accueil
                        </button>
                    </>
                )}

                {status === 'timeout' && (
                    <>
                        <div className="payment-return__icon payment-return__icon--warning">⏱️</div>
                        <h1>Confirmation en cours...</h1>
                        <p>{message}</p>
                        <p className="payment-return__details">
                            Ton paiement a probablement été reçu, mais la confirmation prend du temps.
                        </p>
                        <p className="payment-return__hint">
                            Vérifie ton email pour la confirmation, ou actualise cette page dans quelques instants.
                        </p>
                        <button className="payment-return__btn payment-return__btn--primary" onClick={handleRefresh}>
                            🔄 Actualiser
                        </button>
                        <button className="payment-return__btn payment-return__btn--secondary" onClick={onClose}>
                            Retour à l'accueil
                        </button>
                    </>
                )}

                {status === 'error' && (
                    <>
                        <div className="payment-return__icon payment-return__icon--error">❌</div>
                        <h1>Oups !</h1>
                        <p>{message}</p>
                        <p className="payment-return__hint">
                            Si ton paiement a été débité, vérifie ton email ou contacte le support.
                        </p>
                        <button className="payment-return__btn payment-return__btn--primary" onClick={handleRefresh}>
                            🔄 Réessayer
                        </button>
                        <button className="payment-return__btn payment-return__btn--secondary" onClick={onClose}>
                            Retour à l'accueil
                        </button>
                    </>
                )}
            </div>
        </div>
    )
}

export default PaymentSuccess
