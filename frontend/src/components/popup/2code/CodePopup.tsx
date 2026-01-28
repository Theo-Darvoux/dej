import { useState } from 'react'
import '../popup-shared.css'

type CodePopupProps = {
  open: boolean
  onClose: () => void
  onContinue: (authenticated: boolean) => void
  step: number
  total: number
  email: string
}

const CodePopup = ({ open, onClose, onContinue, step, total, email }: CodePopupProps) => {
  const [code, setCode] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState('')

  const handleVerifyCode = async () => {
    if (!code.trim()) {
      setError('Veuillez entrer le code')
      return
    }

    setIsLoading(true)
    setError('')

    try {
      const response = await fetch('/api/auth/verify', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, code }),
      })

      if (!response.ok) {
        const data = await response.json()
        throw new Error(data.detail || 'Code invalide')
      }

      onContinue(true)
      setCode('')
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
          <h2>Saisis ton code 🔐</h2>
          <p className="popup__subtitle">
            Entre le code (6 lettres et chiffres) reçu sur <strong>{email}</strong> pour continuer.
          </p>

          <label className="popup__label" htmlFor="popup-code">Code de vérification</label>
          <input
            id="popup-code"
            className="popup__input"
            type="text"
            placeholder="code"
            value={code}
            onChange={(e) => setCode(e.target.value)}
            disabled={isLoading}
            maxLength={6}
            style={{ textAlign: 'center', fontSize: '1.5rem', letterSpacing: '8px', textTransform: 'none' }}
          />

          {error && <p className="popup__error">{error}</p>}

          <a
            className="popup__link"
            href="https://cerbere.imt.fr/"
            target="_blank"
            rel="noopener noreferrer"
          >
            📧 Ouvrir ma boîte mail (Zimbra)
          </a>

          <button
            className="popup__cta"
            onClick={handleVerifyCode}
            disabled={isLoading}
          >
            {isLoading ? 'Vérification...' : 'Valider le code'}
          </button>
        </div>
      </div>
    </div>
  )
}

export default CodePopup
