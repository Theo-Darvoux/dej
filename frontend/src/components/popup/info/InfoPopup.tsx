import { useState, useEffect } from 'react'
import '../popup-shared.css'

type TimeSlot = {
  slot: string
  start: string
  available: boolean
}

type ReservationData = {
  date_reservation?: string
  heure_reservation?: string
  habite_residence?: boolean
  numero_chambre?: string
  numero_immeuble?: string
  adresse?: string
  phone?: string
  menu_id?: string
  boisson_id?: string
  bonus_ids?: string[]
}

type InfoPopupProps = {
  open: boolean
  onClose: () => void
  onBack: () => void
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
  onBack,
  step,
  total,
  amount,
  onReservationDataChange,
  reservationData
}: InfoPopupProps) => {
  const [phone, setPhone] = useState('')
  const dateReservation = '2026-02-07' // Date fixe - ne peut pas être modifiée
  const [heureReservation, setHeureReservation] = useState('')
  const [showPayment, setShowPayment] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [timeSlots, setTimeSlots] = useState<TimeSlot[]>([])
  const [loadingSlots, setLoadingSlots] = useState(true)

  // Charger les créneaux disponibles quand le popup s'ouvre
  useEffect(() => {
    if (!open) return

    const fetchAvailability = async () => {
      setLoadingSlots(true)
      try {
        const params = new URLSearchParams()
        if (reservationData?.menu_id) params.append('menu_id', reservationData.menu_id.toString())
        if (reservationData?.boisson_id) params.append('boisson_id', reservationData.boisson_id.toString())
        // Envoyer les bonus_ids comme liste séparée par des virgules
        if (reservationData?.bonus_ids && reservationData.bonus_ids.length > 0) {
          params.append('bonus_ids', reservationData.bonus_ids.join(','))
        }

        const response = await fetch(`/api/reservations/availability?${params.toString()}`, {
          credentials: 'include'
        })

        if (response.ok) {
          const data = await response.json()
          setTimeSlots(data.slots || [])
        } else {
          console.error('Erreur chargement disponibilités')
          // Fallback: tous les créneaux disponibles
          setTimeSlots([
            { slot: "07:00 - 08:00", start: "07:00", available: false },
            { slot: "08:00 - 09:00", start: "08:00", available: false },
            { slot: "09:00 - 10:00", start: "09:00", available: false },
            { slot: "10:00 - 11:00", start: "10:00", available: false },
            { slot: "11:00 - 12:00", start: "11:00", available: false },
            { slot: "12:00 - 13:00", start: "12:00", available: false },
            { slot: "13:00 - 14:00", start: "13:00", available: false },
            { slot: "14:00 - 15:00", start: "14:00", available: false },
            { slot: "15:00 - 16:00", start: "15:00", available: false },
            { slot: "16:00 - 17:00", start: "16:00", available: false },
            { slot: "17:00 - 18:00", start: "17:00", available: false },
            { slot: "18:00 - 19:00", start: "18:00", available: false },
            { slot: "19:00 - 20:00", start: "19:00", available: false },
          ])
        }
      } catch (err) {
        console.error('Erreur fetch availability:', err)
      } finally {
        setLoadingSlots(false)
      }
    }

    fetchAvailability()
  }, [open, reservationData?.menu_id, reservationData?.boisson_id, reservationData?.bonus_ids])

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

      // Fetch user info from API
      let payerFirstName = 'Client'
      let payerLastName = "Mc'INT"
      let payerEmail = 'client@mcint.fr'

      try {
        const userResponse = await fetch('/api/users/me', {
          credentials: 'include'
        })
        if (userResponse.ok) {
          const userData = await userResponse.json()
          if (userData.prenom) payerFirstName = userData.prenom
          if (userData.nom) payerLastName = userData.nom
          if (userData.email) payerEmail = userData.email
        }
      } catch (e) {
        console.warn('Could not fetch user info, using defaults')
      }

      // Create checkout intent
      const response = await fetch('/api/payments/checkout', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({
          amount: amountCentimes,
          item_name: "Commande Mc'INT",
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
              <button className="popup__back" onClick={onBack} aria-label="Retour">
                ← Retour
              </button>
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
                value={dateReservation}
                readOnly
                style={{ cursor: 'not-allowed', backgroundColor: '#f0f0f0' }}
              />

              <label className="popup__label" htmlFor="info-time">Créneau de livraison</label>
              {loadingSlots ? (
                <p style={{ color: '#666', fontSize: '0.9rem' }}>⏳ Chargement des créneaux...</p>
              ) : (
                <select
                  id="info-time"
                  className="popup__input"
                  value={heureReservation}
                  onChange={(e) => setHeureReservation(e.target.value)}
                  style={{ cursor: 'pointer' }}
                >
                  <option value="">-- Sélectionne un créneau --</option>
                  {timeSlots.map((slot) => (
                    <option
                      key={slot.start}
                      value={slot.start}
                      disabled={!slot.available}
                      style={{
                        color: slot.available ? 'inherit' : '#999',
                        backgroundColor: slot.available ? 'inherit' : '#f0f0f0'
                      }}
                    >
                      {slot.slot}{!slot.available ? ' (Complet)' : ''}
                    </option>
                  ))}
                </select>
              )}

              <label className="popup__label" htmlFor="info-phone">Numéro de téléphone</label>
              <input
                id="info-phone"
                className="popup__input"
                type="tel"
                maxLength={13}
                placeholder="07... ou +33..."
                value={phone}
                onChange={(e) => {
                  // N'accepter que les chiffres et + au début
                  const value = e.target.value
                  const filtered = value.replace(/[^\d+]/g, '').replace(/(?!^)\+/g, '')
                  setPhone(filtered)
                }}
              />

              {error && <p className="popup__error">{error}</p>}

              <button className="popup__cta" onClick={handleNext}>
                Continuer vers le paiement
              </button>
            </>
          ) : (
            <>
              <button className="popup__back" onClick={() => setShowPayment(false)} aria-label="Retour">
                ← Retour
              </button>
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
