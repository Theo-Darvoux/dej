import { useEffect, useState } from 'react'
import './RecapPage.css'

type OrderData = {
    menu: string | null
    boisson: string | null
    bonus: string | null
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
                    <span className="recap-loading__spinner">🍟</span>
                    <p>Chargement de ta commande...</p>
                </div>
            </div>
        )
    }

    if (error || !userData?.order) {
        return (
            <div className="recap-page">
                <div className="recap-error">
                    <span className="recap-error__icon">😕</span>
                    <h2>Aucune commande trouvée</h2>
                    <p>{error || "Tu n'as pas encore de commande"}</p>
                    <button className="recap-btn" onClick={onBackToHome}>
                        Retour à l'accueil
                    </button>
                </div>
            </div>
        )
    }

    const { order } = userData

    return (
        <div className="recap-page">
            <div className="recap-card">
                <header className="recap-header">
                    <div className="recap-header__logo">🍟</div>
                    <h1>Mc'INT</h1>
                    <p className="recap-header__subtitle">Récapitulatif de ta commande</p>
                </header>

                <div className="recap-divider" />

                <section className="recap-section">
                    <h3 className="recap-section__title">👤 Informations</h3>
                    <div className="recap-info">
                        <div className="recap-info__row">
                            <span className="recap-info__label">Nom</span>
                            <span className="recap-info__value">{userData.prenom} {userData.nom}</span>
                        </div>
                        <div className="recap-info__row">
                            <span className="recap-info__label">Email</span>
                            <span className="recap-info__value">{userData.email}</span>
                        </div>
                        <div className="recap-info__row">
                            <span className="recap-info__label">Téléphone</span>
                            <span className="recap-info__value">{order.phone || 'Non renseigné'}</span>
                        </div>
                        <div className="recap-info__row">
                            <span className="recap-info__label">Adresse</span>
                            <span className="recap-info__value">{order.adresse || 'Non renseignée'}</span>
                        </div>
                    </div>
                </section>

                <div className="recap-divider" />

                <section className="recap-section">
                    <h3 className="recap-section__title">🕐 Retrait</h3>
                    <div className="recap-time">
                        <span className="recap-time__value">{order.heure_reservation || '--:--'}</span>
                    </div>
                </section>

                <div className="recap-divider" />

                <section className="recap-section">
                    <h3 className="recap-section__title">🍔 Ta commande</h3>
                    <div className="recap-items">
                        {order.menu && (
                            <div className="recap-item">
                                <span className="recap-item__name">{order.menu}</span>
                                <span className="recap-item__badge">Menu</span>
                            </div>
                        )}
                        {order.boisson && (
                            <div className="recap-item">
                                <span className="recap-item__name">{order.boisson}</span>
                                <span className="recap-item__badge">Boisson</span>
                            </div>
                        )}
                        {order.bonus && (
                            <div className="recap-item">
                                <span className="recap-item__name">{order.bonus}</span>
                                <span className="recap-item__badge">Bonus</span>
                            </div>
                        )}
                    </div>
                </section>

                <div className="recap-divider" />

                <section className="recap-total">
                    <span className="recap-total__label">Total payé</span>
                    <span className="recap-total__value">{order.total_amount?.toFixed(2).replace('.', ',')} €</span>
                </section>

                <div className="recap-status">
                    <span className="recap-status__icon">✅</span>
                    <span className="recap-status__text">Paiement confirmé</span>
                </div>

                <button className="recap-btn recap-btn--primary" onClick={onBackToHome}>
                    Retour à l'accueil
                </button>
            </div>
        </div>
    )
}

export default RecapPage
