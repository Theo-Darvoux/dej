import { useState, useEffect } from 'react'
import './LandingPage.css'

type LandingPageProps = {
    onStart: () => void
    onViewRecap: () => void
}

// Liste des pubs disponibles
const ADS = [
    { id: 'focaccia', name: 'Boulanger\'INT', image: '/ads/pub1_focaccia.webp' },
    { id: 'risotto', name: 'Le Gras c\'est la vie', image: '/ads/pub2_risotto.webp' },
    { id: 'vieux', name: 'Menu Vieux', image: '/ads/pub3_vieux.webp' },
    { id: 'exotint', name: 'Exot\'INT', image: '/ads/pub4_exotint.webp' },
    { id: 'shotgun', name: 'Shotgun', image: '/ads/pub5_shotgun.webp' },
]

const LandingPage = ({ onStart, onViewRecap }: LandingPageProps) => {
    const [currentAd, setCurrentAd] = useState(0)
    const [hasCompletedOrder, setHasCompletedOrder] = useState(false)
    const [isLoading, setIsLoading] = useState(true)

    useEffect(() => {
        const checkUserStatus = async () => {
            try {
                const response = await fetch('/api/users/me', {
                    credentials: 'include'
                })
                if (response.ok) {
                    const data = await response.json()
                    // Afficher "Voir mon recap" seulement si paiement complété
                    if (data.has_active_order && data.payment_status === 'completed') {
                        setHasCompletedOrder(true)
                    }
                }
            } catch (err) {
                console.error('Failed to fetch user status:', err)
            } finally {
                setIsLoading(false)
            }
        }
        checkUserStatus()
    }, [])

    // Auto-rotation toutes les 6 secondes
    useEffect(() => {
        const interval = setInterval(() => {
            setCurrentAd((prev) => (prev + 1) % ADS.length)
        }, 6000)
        return () => clearInterval(interval)
    }, [])

    return (
        <div className="landing" onClick={hasCompletedOrder ? undefined : onStart}>
            {/* Carousel de pubs */}
            <div className="landing__carousel">
                {ADS.map((ad, index) => (
                    <div
                        key={ad.id}
                        className={`landing__slide ${index === currentAd ? 'is-active' : ''}`}
                        style={{ backgroundImage: `url(${ad.image})` }}
                    />
                ))}
            </div>

            {/* Overlay gradient */}
            <div className="landing__overlay" />

            {/* Indicateurs de slide */}
            <div className="landing__dots">
                {ADS.map((ad, index) => (
                    <button
                        key={ad.id}
                        className={`landing__dot ${index === currentAd ? 'is-active' : ''}`}
                        onClick={(e) => {
                            e.stopPropagation()
                            setCurrentAd(index)
                        }}
                    />
                ))}
            </div>

            {/* CTA Button */}
            <div className="landing__cta">
                {isLoading ? (
                    <button className="landing__btn" disabled>
                        Chargement...
                    </button>
                ) : hasCompletedOrder ? (
                    <button className="landing__btn landing__btn--order" onClick={(e) => {
                        e.stopPropagation()
                        onViewRecap()
                    }}>
                        Voir mon récap 🍟
                    </button>
                ) : (
                    <button className="landing__btn" onClick={onStart}>
                        Touchez pour commander
                    </button>
                )}
                <p className="landing__hint">
                    {hasCompletedOrder ? "Tu as déjà une commande confirmée" : "Appuyez sur l'écran pour commencer"}
                </p>
            </div>

            {/* Contact Info */}
            <div className="landing__contact">
                <p>📞 Pour tout changement ou réclamation&nbsp;:</p>
                <div className="landing__contact-people">
                    <a href="tel:+33661737785" onClick={(e) => e.stopPropagation()}>
                        <strong>Solène CHAMPION</strong><br />06 61 73 77 85
                    </a>
                    <a href="tel:+33762357719" onClick={(e) => e.stopPropagation()}>
                        <strong>Théo DARVOUX</strong><br />07 62 35 77 19
                    </a>
                </div>
            </div>
        </div>
    )
}

export default LandingPage
