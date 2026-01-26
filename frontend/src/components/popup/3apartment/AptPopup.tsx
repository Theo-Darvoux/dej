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
  const [suggestions, setSuggestions] = useState<any[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  if (!open) return null

  const handleSearchAddress = async (query: string) => {
    setAdresse(query)
    setError(null)

    if (query.length < 3) {
      setSuggestions([])
      return
    }

    setLoading(true)
    try {
      // API BAN - Filtered by citycode 91228 (Evry-Courcouronnes)
      const response = await fetch(`https://api-adresse.data.gouv.fr/search/?q=${encodeURIComponent(query)}&citycode=91228&limit=5`)
      const data = await response.json()
      setSuggestions(data.features || [])
    } catch (err) {
      console.error('Error fetching addresses:', err)
    } finally {
      setLoading(false)
    }
  }

  const selectSuggestion = (suggestion: any) => {
    const label = suggestion.properties.label
    setAdresse(label)
    setSuggestions([])
  }

  const handleContinue = () => {
    if (!habiteResidence) {
      if (!adresse) {
        setError("L'adresse est requise.")
        return
      }
      // Simple check to ensure it's in Evry (even if they didn't pick from suggestion)
      const lowercaseAddr = adresse.toLowerCase()
      if (!lowercaseAddr.includes('evry') && !lowercaseAddr.includes('courcouronnes') && !lowercaseAddr.includes('91000') && !lowercaseAddr.includes('91080')) {
        setError("Désolé, nous ne livrons qu'à Évry-Courcouronnes.")
        return
      }
    } else {
      if (!numeroChambre || numeroChambre.length !== 4) {
        setError("Le numéro de chambre doit comporter 4 chiffres.")
        return
      }
    }

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
                onChange={() => {
                  setHabiteResidence(true)
                  setError(null)
                }}
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
                onChange={() => {
                  setHabiteResidence(false)
                  setError(null)
                }}
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
                onChange={(e) => {
                  setNumeroChambre(e.target.value)
                  if (error) setError(null)
                }}
                style={{ textAlign: 'center', fontSize: '1.2rem', letterSpacing: '4px' }}
              />
            </>
          ) : (
            <div style={{ position: 'relative' }}>
              <label className="popup__label" htmlFor="apt-address">
                Adresse à Évry-Courcouronnes
              </label>
              <input
                id="apt-address"
                className="popup__input"
                type="text"
                placeholder="Ex: 1 Rue Charles Fourier..."
                value={adresse}
                onChange={(e) => handleSearchAddress(e.target.value)}
                autoComplete="off"
              />
              {loading && (
                <div style={{ position: 'absolute', right: '12px', top: '50px' }}>
                  <small>Chargement...</small>
                </div>
              )}
              {suggestions.length > 0 && (
                <div className="address-suggestions">
                  {suggestions.map((s, i) => (
                    <div
                      key={i}
                      className="suggestion-item"
                      onClick={() => selectSuggestion(s)}
                    >
                      {s.properties.label}
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {error && <div className="popup__error">{error}</div>}

          <button className="popup__cta" onClick={handleContinue}>
            Continuer
          </button>
        </div>
      </div>
    </div>
  )
}

export default AptPopup
