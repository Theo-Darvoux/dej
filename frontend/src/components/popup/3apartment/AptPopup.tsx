import { useState } from 'react'
import './AptPopup.css'

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
        <div className="popup__progress"><div className="popup__progress-fill" style={{ width: `${Math.round((step / total) * 100)}%` }} /></div>
        <div className="popup__body">
          <p className="eyebrow">Appartement</p>
          <h2>Habites-tu la résidence ?</h2>
          <div style={{ marginBottom: '1rem' }}>
            <label>
              <input 
                type="radio" 
                checked={habiteResidence} 
                onChange={() => setHabiteResidence(true)} 
              />
              {' '}Oui, j'habite la résidence
            </label>
            <br />
            <label>
              <input 
                type="radio" 
                checked={!habiteResidence} 
                onChange={() => setHabiteResidence(false)} 
              />
              {' '}Non, j'habite ailleurs
            </label>
          </div>
          
          {habiteResidence ? (
            <>
              <p className="popup__subtitle">Aide-nous à trouver le bon étage/porte.</p>
              <label className="popup__label" htmlFor="apt-code">Code appartement (4 chiffres)</label>
              <input 
                id="apt-code" 
                className="popup__input" 
                inputMode="numeric" 
                pattern="[0-9]{4}" 
                maxLength={4} 
                placeholder="0000"
                value={numeroChambre}
                onChange={(e) => setNumeroChambre(e.target.value)}
              />
            </>
          ) : (
            <>
              <label className="popup__label" htmlFor="apt-address">Adresse complète</label>
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
          
          <button className="popup__cta" onClick={handleContinue}>Continuer</button>
        </div>
      </div>
    </div>
  )
}

export default AptPopup
