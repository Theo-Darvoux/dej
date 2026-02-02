import { useState, useEffect } from 'react'
import './LandingPage.css'

type LandingPageProps = {
    onStart: () => void
    onViewRecap: () => void
}

const LandingPage = ({ onStart, onViewRecap }: LandingPageProps) => {
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
            } catch {
                // User not logged in or network error - show default view
            } finally {
                setIsLoading(false)
            }
        }
        checkUserStatus()
    }, [])

    return (
        <div className="landing">
            {/* CTA Button */}
            <div className="landing__cta">
                {isLoading ? (
                    <button className="landing__btn" disabled>
                        Chargement...
                    </button>
                ) : hasCompletedOrder ? (
                    <button className="landing__btn landing__btn--order" onClick={onViewRecap}>
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
                    <a href="tel:+33661737785">
                        <strong>Solène CHAMPION</strong><br />06 61 73 77 85
                    </a>
                    <a href="tel:+33762357719">
                        <strong>Théo DARVOUX</strong><br />07 62 35 77 19
                    </a>
                </div>
            </div>
        </div>
    )
}

export default LandingPage
