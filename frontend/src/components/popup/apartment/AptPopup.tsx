import { useState } from 'react'
import './AptPopup.css'

type AptPopupProps = {
  open: boolean
  onClose: () => void
  onContinue: () => void
  step: number
  total: number
}

const AptPopup = ({ open, onClose, onContinue, step, total }: AptPopupProps) => {
  const [showMore, setShowMore] = useState(false)
  if (!open) return null
  return (
    <div className="popup-overlay">
      <div className="popup-panel">
        <button className="popup__close" aria-label="Fermer" onClick={onClose}>×</button>
        <div className="popup__progress"><div className="popup__progress-fill" style={{ width: `${Math.round((step / total) * 100)}%` }} /></div>
        <div className="popup__body">
          <p className="eyebrow">Appartement</p>
          <h2>Code appartement (4 chiffres)</h2>
          <p className="popup__subtitle">Aide-nous à trouver le bon étage/porte.</p>
          <label className="popup__label" htmlFor="apt-code">Code appartement</label>
          <input id="apt-code" className="popup__input" inputMode="numeric" pattern="[0-9]{4}" maxLength={4} placeholder="0000" />
          {showMore ? (
            <div className="popup__more-fields">
              <label className="popup__label" htmlFor="apt-address">Adresse</label>
              <input id="apt-address" className="popup__input" type="text" placeholder="Immeuble, étage, porte..." />
            </div>
          ) : null}
          <button className="popup__cta" onClick={onContinue}>Continuer</button>
          <button className="popup__hint" onClick={() => setShowMore((v) => !v)}>
            {showMore ? 'Moins d’options d’adresse' : 'Plus d’options d’adresse'}
          </button>
        </div>
      </div>
    </div>
  )
}

export default AptPopup
