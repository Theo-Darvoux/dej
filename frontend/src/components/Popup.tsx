import './Popup.css'

type PopupProps = {
  open: boolean
  onClose: () => void
}

const Popup = ({ open, onClose }: PopupProps) => {
  if (!open) return null

  return (
    <div className="popup-overlay">
      <div className="popup-panel">
        <button className="popup__close" aria-label="Fermer" onClick={onClose}>
          ×
        </button>
        <div className="popup__body">
          <p className="eyebrow">Connexion</p>
          <h2>Connecte-toi à Mc'INT</h2>
          <p className="popup__subtitle">Reçois ton mc-code par email pour finaliser ta commande.</p>
          <label className="popup__label" htmlFor="popup-email">
            Email
          </label>
          <input id="popup-email" className="popup__input" type="email" placeholder="prenom.nom@telecom-sudparis.eu" />
          <button className="popup__cta">Recevoir mon Hypno code</button>
        </div>
      </div>
    </div>
  )
}

export default Popup
