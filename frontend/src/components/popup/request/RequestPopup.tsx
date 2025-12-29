import './RequestPopup.css'

type RequestPopupProps = {
  open: boolean
  onClose: () => void
  onRequestCode: () => void
  step: number
  total: number
}

const RequestPopup = ({ open, onClose, onRequestCode, step, total }: RequestPopupProps) => {
  if (!open) return null
  return (
    <div className="popup-overlay">
      <div className="popup-panel">
        <button className="popup__close" aria-label="Fermer" onClick={onClose}>
          ×
        </button>
        <div className="popup__progress"><div className="popup__progress-fill" style={{ width: `${Math.round((step / total) * 100)}%` }} /></div>
        <div className="popup__body">
          <p className="eyebrow">Connexion</p>
          <h2>Connecte-toi à mc-INT</h2>
          <p className="popup__subtitle">Reçois ton mc-code par email pour finaliser ta commande.</p>
          <label className="popup__label" htmlFor="popup-email">Email</label>
          <input id="popup-email" className="popup__input" type="email" placeholder="ton.email@example.com" />
          <a className="popup__link" href="https://z.imt.fr/" target="_blank" rel="noopener noreferrer">Ouvrir z.imt.fr</a>
          <button className="popup__cta" onClick={onRequestCode}>Recevoir mon mc-code</button>
        </div>
      </div>
    </div>
  )
}

export default RequestPopup
