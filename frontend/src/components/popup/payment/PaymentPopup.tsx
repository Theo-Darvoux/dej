import { useState } from 'react'
import './PaymentPopup.css'

type PaymentPopupProps = {
  open: boolean
  onClose: () => void
  onPaymentSuccess: () => void
  step: number
  total: number
  amount: string
}

const PaymentPopup = ({ open, onClose, onPaymentSuccess, step, total, amount }: PaymentPopupProps) => {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const handlePayment = async () => {
    setLoading(true)
    setError('')
    
    try {
      // Call Stripe Mock API for dev
      const response = await fetch('http://stripe-mock:12111/v1/payment_intents', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: new URLSearchParams({
          amount: (parseFloat(amount.replace(',', '.').replace(' €', '')) * 100).toString(),
          currency: 'eur',
          'payment_method_types[]': 'card',
        }),
      })

      if (response.ok) {
        setTimeout(() => {
          setLoading(false)
          onPaymentSuccess()
        }, 1000)
      } else {
        throw new Error('Payment failed')
      }
    } catch (err) {
      setLoading(false)
      setError('Erreur de paiement. Réessaye.')
    }
  }

  if (!open) return null

  return (
    <div className="popup-overlay">
      <div className="popup-panel">
        <button className="popup__close" aria-label="Fermer" onClick={onClose}>×</button>
        <div className="popup__progress">
          <div className="popup__progress-fill" style={{ width: `${Math.round((step / total) * 100)}%` }} />
        </div>
        <div className="popup__body">
          <p className="eyebrow">Paiement</p>
          <h2>Finalise ta commande</h2>
          <p className="popup__subtitle">Montant total : <strong>{amount}</strong></p>

          <div className="payment__card">
            <label className="popup__label" htmlFor="card-number">Numéro de carte</label>
            <input
              id="card-number"
              className="popup__input"
              type="text"
              placeholder="4242 4242 4242 4242"
              maxLength={19}
            />

            <div className="payment__row">
              <div>
                <label className="popup__label" htmlFor="card-expiry">Expiration</label>
                <input
                  id="card-expiry"
                  className="popup__input"
                  type="text"
                  placeholder="MM/YY"
                  maxLength={5}
                />
              </div>
              <div>
                <label className="popup__label" htmlFor="card-cvc">CVC</label>
                <input
                  id="card-cvc"
                  className="popup__input"
                  type="text"
                  placeholder="123"
                  maxLength={3}
                />
              </div>
            </div>
          </div>

          {error && <p className="payment__error">{error}</p>}

          <button className="popup__cta" onClick={handlePayment} disabled={loading}>
            {loading ? 'Traitement...' : `Payer ${amount}`}
          </button>

          <p className="payment__notice">Mode développement : Stripe Mock actif</p>
        </div>
      </div>
    </div>
  )
}

export default PaymentPopup
