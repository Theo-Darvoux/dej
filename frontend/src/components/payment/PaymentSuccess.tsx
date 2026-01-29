import { useEffect, useState } from 'react'
import './PaymentReturn.css'

type PaymentStatus = 'loading' | 'success' | 'error'

type PaymentSuccessProps = {
    onClose: () => void
}

const PaymentSuccess = ({ onClose }: PaymentSuccessProps) => {
    const [status, setStatus] = useState<PaymentStatus>('loading')
    const [message, setMessage] = useState('')
    const [statusToken, setStatusToken] = useState<string | null>(null)

    useEffect(() => {
        const verifyPayment = async () => {
            const params = new URLSearchParams(window.location.search)
            const urlIntentId = params.get('checkoutIntentId')
            const storedIntentId = localStorage.getItem('checkout_intent_id')

            const checkoutIntentId = urlIntentId || storedIntentId

            if (!checkoutIntentId) {
                setStatus('error')
                setMessage('Aucun paiement en attente trouvé')
                return
            }

            try {
                const response = await fetch(`/api/payments/verify/${checkoutIntentId}`)
                const data = await response.json()

                if (data.success) {
                    setStatus('success')
                    setMessage('Ta commande a bien été enregistrée !')
                    setStatusToken(data.status_token)
                    // Clear stored data only if we were the ones who put it there
                    if (storedIntentId === checkoutIntentId) {
                        localStorage.removeItem('checkout_intent_id')
                        localStorage.removeItem('pending_reservation_id')
                    }
                } else {
                    setStatus('error')
                    setMessage(data.message || 'Le paiement n\'a pas pu être vérifié')
                }
            } catch (err) {
                setStatus('error')
                setMessage('Erreur lors de la vérification du paiement')
            }
        }

        verifyPayment()
    }, [])

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
                        <h1>Vérification du paiement...</h1>
                        <p>Merci de patienter quelques instants.</p>
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

                {status === 'error' && (
                    <>
                        <div className="payment-return__icon payment-return__icon--error">❌</div>
                        <h1>Oups !</h1>
                        <p>{message}</p>
                        <button className="payment-return__btn" onClick={onClose}>
                            Réessayer
                        </button>
                    </>
                )}
            </div>
        </div>
    )
}

export default PaymentSuccess

