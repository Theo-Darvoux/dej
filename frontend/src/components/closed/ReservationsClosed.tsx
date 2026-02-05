import { useState, useEffect } from 'react'
import './ReservationsClosed.css'

const ReservationsClosed = () => {
    const [totalOrders, setTotalOrders] = useState<number | null>(null)

    useEffect(() => {
        const fetchStatus = async () => {
            try {
                const response = await fetch('/api/status')
                if (response.ok) {
                    const data = await response.json()
                    setTotalOrders(data.total_orders)
                }
            } catch {
                // Silently fail - count is not critical
            }
        }
        fetchStatus()
    }, [])

    return (
        <div className="closed">
            <div className="closed__content">
                <h1 className="closed__title">Merci pour vos commandes !</h1>
                <p className="closed__subtitle">Les réservations sont désormais fermées.</p>

                {totalOrders !== null && (
                    <div className="closed__stats">
                        <span className="closed__count">{totalOrders}</span>
                        <span className="closed__label">commandes confirmées</span>
                    </div>
                )}

                <p className="closed__message">
                    Rendez-vous le 7 février pour récupérer vos commandes.
                    Vérifiez bien votre créneau horaire dans votre email de confirmation.
                </p>
            </div>

            {/* Contact Info */}
            <div className="closed__contact">
                <p>Pour toute question :</p>
                <div className="closed__contact-people">
                    <a href="tel:+33661737785">
                        <strong>Solène CHAMPION</strong><br />06 61 73 77 85
                    </a>
                    <a href="tel:+33762357719">
                        <strong>Théo DARVOUX</strong><br />07 62 35 77 19
                    </a>
                </div>
            </div>

            {/* Credits */}
            <div className="closed__credits">
                Site créé par Timothé CORMIER & Théo DARVOUX
            </div>
        </div>
    )
}

export default ReservationsClosed
