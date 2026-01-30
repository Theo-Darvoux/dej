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
        responsable1: { name: string; phone: string }
        responsable2: { name: string; phone: string }
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

    // Format time slot for display (e.g., "12h00 - 13h00")
    const formatTimeSlot = (time: string | null) => {
        if (!time) return '--:-- - --:--'
        const [hours, minutes] = time.split(':').map(Number)
        const endHour = hours + 1
        return `${hours}h${minutes.toString().padStart(2, '0')} - ${endHour}h${minutes.toString().padStart(2, '0')}`
    }

    // Get badge info based on payment status
    const getStatusInfo = (status: string) => {
        switch (status) {
            case 'completed':
                return { text: 'Payé', className: 'status--success' }
            case 'pending':
                return { text: 'En attente', className: 'status--pending' }
            case 'failed':
                return { text: 'Échoué', className: 'status--error' }
            default:
                return { text: status, className: '' }
        }
    }

    // Get category badge info
    const getCategoryInfo = (category: string) => {
        const lower = category.toLowerCase()
        if (lower.includes('menu') || lower.includes('boulanger') || lower.includes('gourmand') || lower.includes('veget')) {
            return { badge: 'Menu', className: 'status-item__badge--menu', iconClass: 'status-item__icon--menu' }
        }
        if (lower.includes('boisson') || lower.includes('drink')) {
            return { badge: 'Boisson', className: 'status-item__badge--drink', iconClass: 'status-item__icon--drink' }
        }
        return { badge: 'Extra', className: 'status-item__badge--bonus', iconClass: 'status-item__icon--bonus' }
    }

    if (loading) {
        return (
            <div className="status-page">
                <div className="status-loading">
                    <div className="status-loading__spinner"></div>
                    <p>Chargement de ta commande...</p>
                </div>
            </div>
        )
    }

    if (error || !order) {
        return (
            <div className="status-page">
                <div className="status-error">
                    <div className="status-error__icon">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                            <circle cx="12" cy="12" r="10"/>
                            <path d="M8 15s1.5-2 4-2 4 2 4 2"/>
                            <line x1="9" y1="9" x2="9.01" y2="9"/>
                            <line x1="15" y1="9" x2="15.01" y2="9"/>
                        </svg>
                    </div>
                    <h2>Commande non trouvée</h2>
                    <p>{error || "Cette commande n'existe pas ou le lien est invalide"}</p>
                    <a href="/" className="status-btn status-btn--primary">
                        <span>Retour à l'accueil</span>
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                            <path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/>
                            <polyline points="9 22 9 12 15 12 15 22"/>
                        </svg>
                    </a>
                </div>
            </div>
        )
    }

    const statusInfo = getStatusInfo(order.payment_status)

    return (
        <div className="status-page">
            <div className="status-container">
                {/* Ticket perforé en haut */}
                <div className="status-ticket-edge status-ticket-edge--top"></div>

                <div className="status-card">
                    {/* Header */}
                    <header className="status-header">
                        <div className="status-header__brand">
                            <span className="status-header__logo">M</span>
                            <div className="status-header__text">
                                <h1>Mc'INT</h1>
                                <span className="status-header__tagline">by Hypnos</span>
                            </div>
                        </div>
                        <div className={`status-header__badge ${statusInfo.className}`}>
                            {order.payment_status === 'completed' && (
                                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                                    <polyline points="20 6 9 17 4 12"/>
                                </svg>
                            )}
                            {order.payment_status === 'pending' && (
                                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                                    <circle cx="12" cy="12" r="10"/>
                                    <polyline points="12 6 12 12 16 14"/>
                                </svg>
                            )}
                            {order.payment_status === 'failed' && (
                                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                                    <line x1="18" y1="6" x2="6" y2="18"/>
                                    <line x1="6" y1="6" x2="18" y2="18"/>
                                </svg>
                            )}
                            <span>{statusInfo.text}</span>
                        </div>
                    </header>

                    {/* Customer Name */}
                    <div className="status-customer">
                        <span className="status-customer__label">Commande de</span>
                        <span className="status-customer__name">{order.prenom} {order.nom}</span>
                    </div>

                    {/* Time Section */}
                    <section className="status-time-section">
                        <div className="status-time-label">Créneau de livraison</div>
                        <div className="status-time-display">
                            <span className="status-time-value">{formatTimeSlot(order.heure_reservation)}</span>
                        </div>
                        <div className="status-date">7 février 2026</div>
                    </section>

                    {/* Order Items */}
                    <section className="status-section">
                        <h3 className="status-section__title">
                            <span className="status-section__icon">
                                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                    <path d="M6 2L3 6v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2V6l-3-4z"/>
                                    <line x1="3" y1="6" x2="21" y2="6"/>
                                    <path d="M16 10a4 4 0 0 1-8 0"/>
                                </svg>
                            </span>
                            Ta commande
                        </h3>
                        <div className="status-items">
                            {order.produits.map((p, i) => {
                                const catInfo = getCategoryInfo(p.category)
                                return (
                                    <div key={i} className="status-item">
                                        <div className={`status-item__icon ${catInfo.iconClass}`}>
                                            <svg viewBox="0 0 24 24" fill="currentColor">
                                                <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z"/>
                                            </svg>
                                        </div>
                                        <span className="status-item__name">{p.name}</span>
                                        <span className={`status-item__badge ${catInfo.className}`}>{catInfo.badge}</span>
                                        <span className="status-item__price">{p.price.toFixed(2)} €</span>
                                    </div>
                                )
                            })}
                        </div>
                    </section>

                    {/* Total */}
                    <div className="status-total">
                        <span className="status-total__label">Total payé</span>
                        <span className="status-total__value">{order.total_amount?.toFixed(2).replace('.', ',')} €</span>
                    </div>

                    {/* Separator */}
                    <div className="status-separator">
                        <div className="status-separator__line"></div>
                    </div>

                    {/* Delivery Info */}
                    <section className="status-section status-section--info">
                        <h3 className="status-section__title">
                            <span className="status-section__icon">
                                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                    <path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"/>
                                    <circle cx="12" cy="10" r="3"/>
                                </svg>
                            </span>
                            Livraison
                        </h3>
                        <div className="status-info-grid">
                            <div className="status-info-item">
                                <span className="status-info-item__label">Téléphone</span>
                                <span className="status-info-item__value">{order.phone || 'Non renseigné'}</span>
                            </div>
                            <div className="status-info-item status-info-item--full">
                                <span className="status-info-item__label">Adresse de livraison</span>
                                <span className="status-info-item__value">{order.adresse}</span>
                            </div>
                        </div>
                        {order.special_requests && (
                            <div className="status-notes">
                                <span className="status-notes__label">Notes</span>
                                <span className="status-notes__value">{order.special_requests}</span>
                            </div>
                        )}
                    </section>

                    {/* Payment date if available */}
                    {order.payment_date && (
                        <div className="status-payment-info">
                            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                <rect x="1" y="4" width="22" height="16" rx="2" ry="2"/>
                                <line x1="1" y1="10" x2="23" y2="10"/>
                            </svg>
                            <span>Payé le {new Date(order.payment_date).toLocaleDateString('fr-FR', {
                                day: 'numeric',
                                month: 'long',
                                year: 'numeric',
                                hour: '2-digit',
                                minute: '2-digit'
                            })}</span>
                        </div>
                    )}

                    {/* Separator */}
                    <div className="status-separator">
                        <div className="status-separator__line"></div>
                    </div>

                    {/* Contacts */}
                    <section className="status-section status-section--contacts">
                        <h3 className="status-section__title">
                            <span className="status-section__icon">
                                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                    <path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72 12.84 12.84 0 0 0 .7 2.81 2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45 12.84 12.84 0 0 0 2.81.7A2 2 0 0 1 22 16.92z"/>
                                </svg>
                            </span>
                            Contacts
                        </h3>
                        <p className="status-contacts__intro">En cas de question concernant ta commande :</p>
                        <div className="status-contacts-grid">
                            <a href={`tel:${order.contacts.responsable1.phone}`} className="status-contact-card">
                                <span className="status-contact-card__name">{order.contacts.responsable1.name}</span>
                                <span className="status-contact-card__phone">{order.contacts.responsable1.phone}</span>
                            </a>
                            <a href={`tel:${order.contacts.responsable2.phone}`} className="status-contact-card">
                                <span className="status-contact-card__name">{order.contacts.responsable2.name}</span>
                                <span className="status-contact-card__phone">{order.contacts.responsable2.phone}</span>
                            </a>
                        </div>
                    </section>

                    {/* Action Button */}
                    <a href="/" className="status-btn status-btn--primary">
                        <span>Retour à l'accueil</span>
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                            <path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/>
                            <polyline points="9 22 9 12 15 12 15 22"/>
                        </svg>
                    </a>

                    {/* Footer */}
                    <p className="status-footer">
                        Conserve cette page pour suivre ta commande
                    </p>
                </div>

                {/* Ticket perforé en bas */}
                <div className="status-ticket-edge status-ticket-edge--bottom"></div>
            </div>
        </div>
    )
}

export default OrderStatus
