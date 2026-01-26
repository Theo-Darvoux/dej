import { useState, useEffect } from 'react'
import './LandingPage.css'

type LandingPageProps = {
    onStart: () => void
    onViewOrder: (orderData: any) => void
}

// Liste des pubs disponibles
const ADS = [
    { id: 'focaccia', name: 'Boulanger\'INT', image: '/ads/pub1_focaccia.webp' },
    { id: 'risotto', name: 'Le Gras c\'est la vie', image: '/ads/pub2_risotto.webp' },
    { id: 'vieux', name: 'Menu Vieux', image: '/ads/pub3_vieux.webp' },
    { id: 'exotint', name: 'Exot\'INT', image: '/ads/pub4_exotint.webp' },
    { id: 'shotgun', name: 'Shotgun', image: '/ads/pub5_shotgun.webp' },
]

const LandingPage = ({ onStart, onViewOrder }: LandingPageProps) => {
    const [currentAd, setCurrentAd] = useState(0)
    const [userOrder, setUserOrder] = useState<any>(null)

    useEffect(() => {
        const checkUserStatus = async () => {
            try {
                const response = await fetch('/api/users/me')
                if (response.ok) {
                    const data = await response.json()
                    if (data.has_active_order) {
                        setUserOrder(data.order)
                    }
                }
            } catch (err) {
                console.error('Failed to fetch user status:', err)
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
        <div className="landing" onClick={userOrder ? undefined : onStart}>
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
                {userOrder ? (
                    <button className="landing__btn landing__btn--order" onClick={(e) => {
                        e.stopPropagation()
                        onViewOrder(userOrder)
                    }}>
                        Voir ma commande 🍟
                    </button>
                ) : (
                    <button className="landing__btn" onClick={onStart}>
                        Touchez pour commander
                    </button>
                )}
                <p className="landing__hint">
                    {userOrder ? "Tu as déjà une commande en cours" : "Appuyez sur l'écran pour commencer"}
                </p>
            </div>
        </div>
    )
}

export default LandingPage
