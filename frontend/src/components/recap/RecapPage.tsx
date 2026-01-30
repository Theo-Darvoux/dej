import { useEffect, useState } from 'react'
import './RecapPage.css'

type OrderData = {
    menu: string | null
    boisson: string | null
    extras: string[]
    total_amount: number
    heure_reservation: string | null
    adresse: string | null
    phone: string | null
}

type UserData = {
    prenom: string | null
    nom: string | null
    email: string
    order: OrderData | null
}

type RecapPageProps = {
    onBackToHome: () => void
}

const RecapPage = ({ onBackToHome }: RecapPageProps) => {
    const [userData, setUserData] = useState<UserData | null>(null)
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState<string | null>(null)

    useEffect(() => {
        const fetchUserData = async () => {
            try {
                const response = await fetch('/api/users/me', {
                    credentials: 'include'
                })
                if (!response.ok) {
                    throw new Error('Non connecté')
                }
                const data = await response.json()
                setUserData(data)
            } catch (err) {
                setError(err instanceof Error ? err.message : 'Erreur')
            } finally {
                setLoading(false)
            }
        }
        fetchUserData()
    }, [])

    if (loading) {
        return (
            <div className="recap-page">
                <div className="recap-loading">
                    <div className="recap-loading__spinner"></div>
                    <p>Chargement de ta commande...</p>
                </div>
            </div>
        )
    }

    if (error || !userData?.order) {
        return (
            <div className="recap-page">
                <div className="recap-error">
                    <div className="recap-error__icon">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                            <circle cx="12" cy="12" r="10"/>
                            <path d="M8 15s1.5-2 4-2 4 2 4 2"/>
                            <line x1="9" y1="9" x2="9.01" y2="9"/>
                            <line x1="15" y1="9" x2="15.01" y2="9"/>
                        </svg>
                    </div>
                    <h2>Aucune commande trouvée</h2>
                    <p>{error || "Tu n'as pas encore passé de commande"}</p>
                    <button className="recap-btn recap-btn--primary" onClick={onBackToHome}>
                        Retour à l'accueil
                    </button>
                </div>
            </div>
        )
    }

    const { order } = userData

    // Format time for display
    const formatTime = (time: string | null) => {
        if (!time) return '--:--'
        return time.replace(':', 'h')
    }

    return (
        <div className="recap-page">
            <div className="recap-container">
                {/* Ticket perforé en haut */}
                <div className="recap-ticket-edge recap-ticket-edge--top"></div>

                <div className="recap-card">
                    {/* Header */}
                    <header className="recap-header">
                        <div className="recap-header__brand">
                            <span className="recap-header__logo">M</span>
                            <div className="recap-header__text">
                                <h1>Mc'INT</h1>
                                <span className="recap-header__tagline">by Hypnos</span>
                            </div>
                        </div>
                        <div className="recap-header__badge">
                            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                                <polyline points="20 6 9 17 4 12"/>
                            </svg>
                            <span>Confirmé</span>
                        </div>
                    </header>

                    {/* Time Section - Big and prominent */}
                    <section className="recap-time-section">
                        <div className="recap-time-label">Créneau de livraison</div>
                        <div className="recap-time-display">
                            <span className="recap-time-value">{formatTime(order.heure_reservation)}</span>
                        </div>
                        <div className="recap-date">7 février 2026</div>
                    </section>

                    {/* Order Items */}
                    <section className="recap-section">
                        <h3 className="recap-section__title">
                            <span className="recap-section__icon">
                                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                    <path d="M6 2L3 6v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2V6l-3-4z"/>
                                    <line x1="3" y1="6" x2="21" y2="6"/>
                                    <path d="M16 10a4 4 0 0 1-8 0"/>
                                </svg>
                            </span>
                            Ta commande
                        </h3>
                        <div className="recap-items">
                            {order.menu && (
                                <div className="recap-item">
                                    <div className="recap-item__icon recap-item__icon--menu">
                                        <svg viewBox="0 0 24 24" fill="currentColor">
                                            <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z"/>
                                        </svg>
                                    </div>
                                    <span className="recap-item__name">{order.menu}</span>
                                    <span className="recap-item__badge recap-item__badge--menu">Menu</span>
                                </div>
                            )}
                            {order.boisson && (
                                <div className="recap-item">
                                    <div className="recap-item__icon recap-item__icon--drink">
                                        <svg viewBox="0 0 24 24" fill="currentColor">
                                            <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z"/>
                                        </svg>
                                    </div>
                                    <span className="recap-item__name">{order.boisson}</span>
                                    <span className="recap-item__badge recap-item__badge--drink">Boisson</span>
                                </div>
                            )}
                            {order.extras?.map((extra, index) => (
                                <div key={index} className="recap-item">
                                    <div className="recap-item__icon recap-item__icon--bonus">
                                        <svg viewBox="0 0 24 24" fill="currentColor">
                                            <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z"/>
                                        </svg>
                                    </div>
                                    <span className="recap-item__name">{extra}</span>
                                    <span className="recap-item__badge recap-item__badge--bonus">Extra</span>
                                </div>
                            ))}
                        </div>
                    </section>

                    {/* Total */}
                    <div className="recap-total">
                        <span className="recap-total__label">Total payé</span>
                        <span className="recap-total__value">{order.total_amount?.toFixed(2).replace('.', ',')} €</span>
                    </div>

                    {/* Separator */}
                    <div className="recap-separator">
                        <div className="recap-separator__line"></div>
                    </div>

                    {/* User Info */}
                    <section className="recap-section recap-section--info">
                        <h3 className="recap-section__title">
                            <span className="recap-section__icon">
                                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                    <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/>
                                    <circle cx="12" cy="7" r="4"/>
                                </svg>
                            </span>
                            Informations
                        </h3>
                        <div className="recap-info-grid">
                            <div className="recap-info-item">
                                <span className="recap-info-item__label">Nom</span>
                                <span className="recap-info-item__value">{userData.prenom} {userData.nom}</span>
                            </div>
                            <div className="recap-info-item">
                                <span className="recap-info-item__label">Email</span>
                                <span className="recap-info-item__value recap-info-item__value--small">{userData.email}</span>
                            </div>
                            <div className="recap-info-item">
                                <span className="recap-info-item__label">Téléphone</span>
                                <span className="recap-info-item__value">{order.phone || 'Non renseigné'}</span>
                            </div>
                            <div className="recap-info-item recap-info-item--full">
                                <span className="recap-info-item__label">Adresse de livraison</span>
                                <span className="recap-info-item__value">{order.adresse || 'Non renseignée'}</span>
                            </div>
                        </div>
                    </section>

                    {/* Action Button */}
                    <button className="recap-btn recap-btn--primary" onClick={onBackToHome}>
                        <span>Retour à l'accueil</span>
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                            <path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/>
                            <polyline points="9 22 9 12 15 12 15 22"/>
                        </svg>
                    </button>
                </div>

                {/* Ticket perforé en bas */}
                <div className="recap-ticket-edge recap-ticket-edge--bottom"></div>
            </div>
        </div>
    )
}

export default RecapPage
