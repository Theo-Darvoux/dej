import { useState } from 'react'
import '../popup-shared.css'

type ApartmentData = {
  habite_residence: boolean
  numero_chambre?: string
  numero_immeuble?: string
  adresse?: string
}

type AptPopupProps = {
  open: boolean
  onClose: () => void
  onContinue: (data: ApartmentData) => void
  step: number
  total: number
}

const AptPopup = ({ open, onClose, onContinue, step, total }: AptPopupProps) => {
  const [habiteResidence, setHabiteResidence] = useState(true)
  const [numeroChambre, setNumeroChambre] = useState('')
  const [adresse, setAdresse] = useState('')

  if (!open) return null

  const handleContinue = () => {
    const data: ApartmentData = {
      habite_residence: habiteResidence,
      numero_chambre: habiteResidence ? numeroChambre : undefined,
      adresse: habiteResidence ? undefined : adresse,
    }
    onContinue(data)
  }

  return (
    <div className="popup-overlay">
      <div className="popup-panel">
        <button className="popup__close" aria-label="Fermer" onClick={onClose}>×</button>
        <div className="popup__progress">
          <div className="popup__progress-fill" style={{ width: `${Math.round((step / total) * 100)}%` }} />
        </div>
        <div className="popup__body">
          <p className="eyebrow">Étape {step} sur {total}</p>
          <h2>Où habites-tu ? 🏠</h2>
          <p className="popup__subtitle">
            Aide-nous à te livrer ta commande au bon endroit.
          </p>

          <div className="popup__radio-group">
            <label className="popup__radio-label">
              <input
                type="radio"
                checked={habiteResidence}
                onChange={() => setHabiteResidence(true)}
              />
              <div>
                <strong>J'habite la résidence</strong>
                <br />
                <small style={{ color: '#757575' }}>Livraison directe à ta chambre</small>
              </div>
            </label>

            <label className="popup__radio-label">
              <input
                type="radio"
                checked={!habiteResidence}
                onChange={() => setHabiteResidence(false)}
              />
              <div>
                <strong>J'habite ailleurs</strong>
                <br />
                <small style={{ color: '#757575' }}>Indique ton adresse complète</small>
              </div>
            </label>
          </div>

          {habiteResidence ? (
            <>
              <label className="popup__label" htmlFor="apt-code">
                Numéro de chambre (4 chiffres)
              </label>
              <input
                id="apt-code"
                className="popup__input"
                inputMode="numeric"
                pattern="[0-9]{4}"
                maxLength={4}
                placeholder="Ex: 1234"
                value={numeroChambre}
                onChange={(e) => setNumeroChambre(e.target.value)}
                style={{ textAlign: 'center', fontSize: '1.2rem', letterSpacing: '4px' }}
              />
            </>
          ) : (
            <>
              <label className="popup__label" htmlFor="apt-address">
                Adresse complète
              </label>
              <input
                id="apt-address"
                className="popup__input"
                type="text"
                placeholder="Rue, ville, code postal..."
                value={adresse}
                onChange={(e) => setAdresse(e.target.value)}
              />
            </>
          )}

          <button className="popup__cta" onClick={handleContinue}>
            Continuer
          </button>
        </div>
      </div>
    </div>
  )
}

export default AptPopup
