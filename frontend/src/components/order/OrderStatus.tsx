import { useEffect, useState } from 'react'
import './OrderStatus.css'

// Extract token from URL path: /order/status/:token
const getTokenFromPath = (): string | null => {
    const path = window.location.pathname
    const match = path.match(/^\/order\/status\/(.+)$/)
    return match ? match[1] : null
}

type OrderStatusData = {
    prenom: string
    nom: string
    status: string
    payment_status: string
    date_reservation: string
    heure_reservation: string | null
    adresse: string
    phone: string | null
    special_requests: string | null
    produits: Array<{
        name: string
        price: number
        category: string
    }>
    total_amount: number
    payment_date: string | null
    contacts: {
        responsable1: { name: string; email: string }
        responsable2: { name: string; email: string }
    }
}

const OrderStatus = () => {
    const [token] = useState(() => getTokenFromPath())
    const [order, setOrder] = useState<OrderStatusData | null>(null)
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState<string | null>(null)

    useEffect(() => {
        const fetchOrderStatus = async () => {
            try {
                const response = await fetch(`/api/users/order/status/${token}`)

                if (!response.ok) {
                    if (response.status === 404) {
                        throw new Error('Commande non trouvée')
                    }
                    throw new Error('Erreur lors du chargement')
                }

                const data = await response.json()
                setOrder(data)
            } catch (err) {
                setError(err instanceof Error ? err.message : 'Erreur inconnue')
            } finally {
                setLoading(false)
            }
        }

        if (token) {
            fetchOrderStatus()
        }
    }, [token])

    if (loading) {
        return (
            <div className="order-status-page">
                <div className="order-status-container">
                    <div className="loading-spinner"></div>
                    <p>Chargement de votre commande...</p>
                </div>
            </div>
        )
    }

    if (error || !order) {
        return (
            <div className="order-status-page">
                <div className="order-status-container error">
                    <h1>❌ Erreur</h1>
                    <p>{error || 'Commande non trouvée'}</p>
                    <a href="/" className="back-home-btn">Retour à l'accueil</a>
                </div>
            </div>
        )
    }

    const getStatusBadge = (status: string) => {
        switch (status) {
            case 'completed':
                return <span className="status-badge success">✅ Payé</span>
            case 'pending':
                return <span className="status-badge pending">⏳ En attente</span>
            case 'failed':
                return <span className="status-badge error">❌ Échoué</span>
            default:
                return <span className="status-badge">{status}</span>
        }
    }

    return (
        <div className="order-status-page">
            <div className="order-status-container">
                {/* Header */}
                <div className="order-header">
                    <h1>🍔 Mc'INT</h1>
                    <h2>Suivi de commande</h2>
                </div>

                {/* Status Banner */}
                <div className={`status-banner ${order.payment_status}`}>
                    {getStatusBadge(order.payment_status)}
                    <div className="customer-name">
                        {order.prenom} {order.nom}
                    </div>
                </div>

                {/* Order Summary */}
                <section className="order-section">
                    <h3>📋 Récapitulatif de commande</h3>
                    <div className="products-list">
                        {order.produits.map((p, i) => (
                            <div key={i} className="product-item">
                                <span className="product-category">{p.category}</span>
                                <span className="product-name">{p.name}</span>
                                <span className="product-price">{p.price.toFixed(2)} €</span>
                            </div>
                        ))}
                        <div className="product-item total">
                            <span></span>
                            <span>Total</span>
                            <span className="product-price">{order.total_amount.toFixed(2)} €</span>
                        </div>
                    </div>
                </section>

                {/* Delivery Info */}
                <section className="order-section delivery">
                    <h3>📍 Informations de livraison</h3>
                    <div className="info-grid">
                        <div className="info-item">
                            <strong>Date</strong>
                            <span>7 février 2026</span>
                        </div>
                        <div className="info-item">
                            <strong>Heure</strong>
                            <span>{order.heure_reservation || 'Non renseigné'}</span>
                        </div>
                        <div className="info-item">
                            <strong>Adresse</strong>
                            <span>{order.adresse}</span>
                        </div>
                        <div className="info-item">
                            <strong>Téléphone</strong>
                            <span>{order.phone || 'Non renseigné'}</span>
                        </div>
                    </div>
                    {order.special_requests && (
                        <div className="special-requests">
                            <strong>Notes :</strong> {order.special_requests}
                        </div>
                    )}
                </section>

                {/* Payment Info */}
                {order.payment_date && (
                    <section className="order-section payment">
                        <h3>💳 Paiement</h3>
                        <p>Payé le {new Date(order.payment_date).toLocaleDateString('fr-FR', {
                            day: 'numeric',
                            month: 'long',
                            year: 'numeric',
                            hour: '2-digit',
                            minute: '2-digit'
                        })}</p>
                    </section>
                )}

                {/* Contacts */}
                <section className="order-section contacts">
                    <h3>📞 Contacts des responsables</h3>
                    <p>En cas de question concernant votre commande :</p>
                    <div className="contacts-grid">
                        <div className="contact-card">
                            <strong>{order.contacts.responsable1.name}</strong>
                            <a href={`mailto:${order.contacts.responsable1.email}`}>
                                {order.contacts.responsable1.email}
                            </a>
                        </div>
                        <div className="contact-card">
                            <strong>{order.contacts.responsable2.name}</strong>
                            <a href={`mailto:${order.contacts.responsable2.email}`}>
                                {order.contacts.responsable2.email}
                            </a>
                        </div>
                    </div>
                </section>

                {/* Footer */}
                <div className="order-footer">
                    <p>Conservez cette page pour suivre votre commande.</p>
                    <a href="/" className="back-home-btn">Retour à l'accueil</a>
                </div>
            </div>
        </div>
    )
}

export default OrderStatus
