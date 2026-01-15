import { useState } from 'react'
import '../popup-shared.css'

type ReservationData = {
  date_reservation?: string
  heure_reservation?: string
  habite_residence?: boolean
  numero_chambre?: string
  numero_immeuble?: string
  adresse?: string
  phone?: string
  menu_id?: number
  boisson_id?: number
  bonus_id?: number
}

type InfoPopupProps = {
  open: boolean
  onClose: () => void
  step: number
  total: number
  amount: string
  onPaymentSuccess: () => void
  onReservationDataChange: (data: Partial<ReservationData>) => void
  reservationData?: Partial<ReservationData>
}

const InfoPopup = ({
  open,
  onClose,
  step,
  total,
  amount,
  onReservationDataChange,
  reservationData
}: InfoPopupProps) => {
  const [phone, setPhone] = useState('')
  const [dateReservation, setDateReservation] = useState('')
  const [heureReservation, setHeureReservation] = useState('')
  const [showPayment, setShowPayment] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const handleNext = async () => {
    if (!phone.trim()) {
      setError('Numéro de téléphone requis')
      return
    }
    if (!dateReservation) {
      setError('Date de réservation requise')
      return
    }
    if (!heureReservation) {
      setError('Heure de réservation requise')
      return
    }

    setError('')

    onReservationDataChange({
      phone,
      date_reservation: dateReservation,
      heure_reservation: heureReservation,
    })

    try {
      const completeData = {
        ...reservationData,
        phone,
        date_reservation: dateReservation,
        heure_reservation: heureReservation,
      }
      const reservationResponse = await fetch('/api/reservations/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify(completeData),
      })
      if (!reservationResponse.ok) {
        const errorData = await reservationResponse.json().catch(() => ({}))
        throw new Error(errorData.detail || 'Erreur lors de l\'enregistrement de la réservation')
      }

      const reservation = await reservationResponse.json()
      // Store reservation ID for payment
      localStorage.setItem('pending_reservation_id', reservation.id?.toString() || '')

      setShowPayment(true)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erreur de réservation.')
    }
  }

  const handlePayWithHelloAsso = async () => {
    setLoading(true)
    setError('')

    try {
      // Parse amount to centimes
      const amountCentimes = Math.round(
        parseFloat(amount.replace(',', '.').replace(' €', '')) * 100
      )

      // Get user info from reservationData or use defaults
      const payerFirstName = 'Client'
      const payerLastName = 'Mc-INT'
      const payerEmail = localStorage.getItem('user_email') || 'client@mcint.fr'

      // Create checkout intent
      const response = await fetch('/api/payments/checkout', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({
          amount: amountCentimes,
          item_name: 'Commande Mc-INT',
          payer_email: payerEmail,
          payer_first_name: payerFirstName,
          payer_last_name: payerLastName,
          reservation_id: parseInt(localStorage.getItem('pending_reservation_id') || '0'),
        }),
      })

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}))
        throw new Error(errorData.detail || 'Erreur lors de la création du paiement')
      }

      const data = await response.json()

      // Store checkout intent ID for verification on return
      localStorage.setItem('checkout_intent_id', data.checkout_intent_id)

      // Redirect to HelloAsso
      window.location.href = data.redirect_url

    } catch (err) {
      setLoading(false)
      setError(err instanceof Error ? err.message : 'Erreur de paiement.')
    }
  }

  if (!open) return null

  return (
    <div className="popup-overlay">
      <div className="popup-panel">
        <button className="popup__close" aria-label="Fermer" onClick={onClose}>
          ×
        </button>
        <div className="popup__progress">
          <div className="popup__progress-fill" style={{ width: `${Math.round((step / total) * 100)}%` }} />
        </div>
        <div className="popup__body">
          {!showPayment ? (
            <>
              <p className="eyebrow">Étape {step} sur {total}</p>
              <h2>Détails de livraison 📦</h2>
              <p className="popup__subtitle">
                Choisis quand tu veux recevoir ta commande.
              </p>

              <label className="popup__label" htmlFor="info-date">Date de livraison</label>
              <input
                id="info-date"
                className="popup__input"
                type="date"
                min="2026-02-07"
                max="2026-02-07"
                value={dateReservation}
                onChange={(e) => setDateReservation(e.target.value)}
              />

              <label className="popup__label" htmlFor="info-time">Heure de livraison</label>
              <input
                id="info-time"
                className="popup__input"
                type="time"
                min="07:00"
                max="18:00"
                step={3600}
                value={heureReservation}
                onChange={(e) => setHeureReservation(e.target.value)}
              />

              <label className="popup__label" htmlFor="info-phone">Numéro de téléphone</label>
              <input
                id="info-phone"
                className="popup__input"
                type="tel"
                placeholder="06 12 34 56 78"
                value={phone}
                onChange={(e) => setPhone(e.target.value)}
              />

              {error && <p className="popup__error">{error}</p>}

              <button className="popup__cta" onClick={handleNext}>
                Continuer vers le paiement
              </button>
            </>
          ) : (
            <>
              <p className="eyebrow">Paiement sécurisé</p>
              <h2>Finalise ta commande 💳</h2>
              <p className="popup__subtitle">
                Montant total : <strong style={{ color: '#264027', fontSize: '1.2rem' }}>{amount}</strong>
              </p>

              <div style={{
                background: '#f5f5f5',
                padding: '20px',
                borderRadius: '12px',
                marginTop: '16px',
                textAlign: 'center'
              }}>
                <p style={{ margin: '0 0 16px 0', color: '#666' }}>
                  Tu vas être redirigé vers HelloAsso pour effectuer ton paiement en toute sécurité.
                </p>
                <img
                  src="https://www.helloasso.com/assets/img/logos/logo-helloasso.svg"
                  alt="HelloAsso"
                  style={{ height: '40px', marginBottom: '8px' }}
                  onError={(e) => {
                    e.currentTarget.style.display = 'none'
                  }}
                />
                <p style={{ fontSize: '0.8rem', color: '#999', margin: 0 }}>
                  100% gratuit pour les associations
                </p>
              </div>

              {error && <p className="popup__error">{error}</p>}

              <button
                className="popup__cta"
                onClick={handlePayWithHelloAsso}
                disabled={loading}
                style={{
                  background: loading ? '#ccc' : '#264027',
                  color: '#fff'
                }}
              >
                {loading ? '⏳ Redirection...' : `Payer ${amount} avec HelloAsso`}
              </button>

              <p style={{
                textAlign: 'center',
                fontSize: '0.8rem',
                color: '#757575',
                marginTop: '16px'
              }}>
                🔒 Paiement sécurisé par HelloAsso
              </p>
            </>
          )}
        </div>
      </div>
    </div>
  )
}

export default InfoPopup
