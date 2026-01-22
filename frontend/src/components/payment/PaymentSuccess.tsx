import { useEffect, useState } from 'react'
import './PaymentReturn.css'

type PaymentStatus = 'loading' | 'success' | 'error'

type PaymentSuccessProps = {
    onClose: () => void
}

const PaymentSuccess = ({ onClose }: PaymentSuccessProps) => {
    const [status, setStatus] = useState<PaymentStatus>('loading')
    const [message, setMessage] = useState('')

    useEffect(() => {
        const verifyPayment = async () => {
            const checkoutIntentId = localStorage.getItem('checkout_intent_id')

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
                    // Clear stored data
                    localStorage.removeItem('checkout_intent_id')
                    localStorage.removeItem('pending_reservation_id')
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
                        <button className="payment-return__btn" onClick={onClose}>
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
