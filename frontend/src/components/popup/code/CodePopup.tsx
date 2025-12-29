import './CodePopup.css'

type CodePopupProps = {
  open: boolean
  onClose: () => void
  onContinue: () => void
  step: number
  total: number
}

const CodePopup = ({ open, onClose, onContinue, step, total }: CodePopupProps) => {
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
          <input id="popup-code" className="popup__input" type="text" placeholder="1234-5678" />
          <button className="popup__cta" onClick={onContinue}>Continuer</button>
        </div>
      </div>
    </div>
  )
}

export default CodePopup
