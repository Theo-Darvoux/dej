import { useState } from 'react'
import './CodePopup.css'

type CodePopupProps = {
  open: boolean
  onClose: () => void
  onContinue: () => void
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

      onContinue()
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
        <div className="popup__progress"><div className="popup__progress-fill" style={{ width: `${Math.round((step / total) * 100)}%` }} /></div>
        <div className="popup__body">
          <p className="eyebrow">Vérification</p>
          <h2>Saisis ton mc-code</h2>
          <p className="popup__subtitle">Entre le code reçu par email pour continuer.</p>
          <label className="popup__label" htmlFor="popup-code">Code</label>
          <input 
            id="popup-code" 
            className="popup__input" 
            type="text" 
            placeholder="xxxx"
            value={code}
            onChange={(e) => setCode(e.target.value)}
            disabled={isLoading}
          />
          {error && <p style={{ color: '#ef4444', fontSize: '14px', marginTop: '8px' }}>{error}</p>}
          <a className="popup__link" href="https://z.imt.fr/" target="_blank" rel="noopener noreferrer">Ouvrir z.imt.fr</a>
          <button 
            className="popup__cta" 
            onClick={handleVerifyCode}
            disabled={isLoading}
          >
            {isLoading ? 'Vérification...' : 'Continuer'}
          </button>
        </div>
      </div>
    </div>
  )
}

export default CodePopup
