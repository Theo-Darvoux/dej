import { useState } from 'react'
import '../popup-shared.css'

type RequestPopupProps = {
  open: boolean
  onClose: () => void
  onRequestCode: (email: string) => void
  step: number
  total: number
}

const RequestPopup = ({ open, onClose, onRequestCode, step, total }: RequestPopupProps) => {
  const [email, setEmail] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState('')

  const handleRequestCode = async () => {
    if (!email.trim()) {
      setError('Veuillez entrer un email valide')
      return
    }

    setIsLoading(true)
    setError('')

    try {
      const response = await fetch('/api/auth/request-code', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email }),
      })

      if (!response.ok) {
        const data = await response.json()
        throw new Error(data.detail || 'Erreur lors de la demande du code')
      }

      onRequestCode(email)
      setEmail('')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Une erreur est survenue')
    } finally {
      setIsLoading(false)
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
          <p className="eyebrow">Étape {step} sur {total}</p>
          <h2>Connecte-toi à Mc-INT 🍔</h2>
          <p className="popup__subtitle">
            Reçois ton code de vérification par email pour finaliser ta commande.
          </p>

          <label className="popup__label" htmlFor="popup-email">Adresse email</label>
          <input
            id="popup-email"
            className="popup__input"
            type="email"
            placeholder="ton.email@example.com"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            disabled={isLoading}
          />

          {error && <p className="popup__error">{error}</p>}

          <button
            className="popup__cta"
            onClick={handleRequestCode}
            disabled={isLoading}
          >
            {isLoading ? 'Envoi en cours...' : 'Recevoir mon code'}
          </button>
        </div>
      </div>
    </div>
  )
}

export default RequestPopup
