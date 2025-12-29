import { useState } from 'react'
import './InfoPopup.css'

type InfoPopupProps = {
  open: boolean
  onClose: () => void
  step: number
  total: number
  amount: string
  onPaymentSuccess: () => void
}

const InfoPopup = ({ open, onClose, step, total, amount, onPaymentSuccess }: InfoPopupProps) => {
  const [phone, setPhone] = useState('')
  const [cardNumber, setCardNumber] = useState('')
  const [expiry, setExpiry] = useState('')
  const [cvc, setCvc] = useState('')
  const [showPayment, setShowPayment] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const handleNext = () => {
    if (!phone.trim()) {
      setError('Numéro de téléphone requis')
      return
    }
    setError('')
    setShowPayment(true)
  }

  const handlePayment = async () => {
    setLoading(true)
    setError('')
    
    try {
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
        <button className="popup__close" aria-label="Fermer" onClick={onClose}>
          ×
        </button>
        <div className="popup__progress"><div className="popup__progress-fill" style={{ width: `${Math.round((step / total) * 100)}%` }} /></div>
        <div className="popup__body">
          {!showPayment ? (
            <>
              <p className="eyebrow">Informations</p>
              <h2>Numéro de téléphone</h2>
              <p className="popup__subtitle"><strong>ON EN A BESOIN POUR LES CONTACTER LORS DE LA LIVRAISON</strong></p>
              <label className="popup__label" htmlFor="info-phone">Téléphone</label>
              <input 
                id="info-phone" 
                className="popup__input" 
                type="tel" 
                placeholder="06 12 34 56 78"
                value={phone}
                onChange={(e) => setPhone(e.target.value)}
              />
              {error && <p className="payment__error">{error}</p>}
              <button className="popup__cta" onClick={handleNext}>Continuer</button>
            </>
          ) : (
            <>
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
                  value={cardNumber}
                  onChange={(e) => setCardNumber(e.target.value)}
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
                      value={expiry}
                      onChange={(e) => setExpiry(e.target.value)}
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
                      value={cvc}
                      onChange={(e) => setCvc(e.target.value)}
                    />
                  </div>
                </div>
              </div>

              {error && <p className="payment__error">{error}</p>}

              <button className="popup__cta" onClick={handlePayment} disabled={loading}>
                {loading ? 'Traitement...' : `Payer ${amount}`}
              </button>

              <p className="payment__notice">Mode développement : Stripe Mock actif</p>
            </>
          )}
        </div>
      </div>
    </div>
  )
}

export default InfoPopup
