import { useState } from 'react'
import type { MenuItem } from '../../../context/MenuContext'
import type { DeliveryInfo } from './Delivery'

type UserInfo = {
    phone: string
}

type CheckoutProps = {
    onBack: () => void
    cartItems: MenuItem[]
    onPaymentSuccess: () => void
    isInfoStep?: boolean
    deliveryInfo?: DeliveryInfo | null
    userEmail?: string
    userPhone?: string
    initialUserInfo?: UserInfo
    onInfoContinue?: (info: UserInfo) => void
}

const Checkout = ({
    onBack,
    cartItems,
    onPaymentSuccess: _onPaymentSuccess,
    isInfoStep = false,
    deliveryInfo,
    userEmail,
    userPhone,
    initialUserInfo,
    onInfoContinue
}: CheckoutProps) => {
    void _onPaymentSuccess // Payment success handled by redirect
    const [formData, setFormData] = useState({
        phone: initialUserInfo?.phone || '',
    })
    const [specialRequests, setSpecialRequests] = useState('')
    const [isSubmitting, setIsSubmitting] = useState(false)
    const [error, setError] = useState('')

    const total = cartItems.reduce((acc, item) => {
        const price = parseFloat(item.price.replace(',', '.').replace(' €', '') || '0')
        return acc + price
    }, 0).toFixed(2).replace('.', ',') + ' €'

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault()
        setIsSubmitting(true)

        try {
            if (isInfoStep && onInfoContinue) {
                await new Promise(resolve => setTimeout(resolve, 300))
                onInfoContinue({ phone: formData.phone })
            } else {
                // Real HelloAsso payment flow
                await handlePayWithHelloAsso()
            }
        } catch (err) {
            console.error(err)
            setError(err instanceof Error ? err.message : "Erreur lors de la commande")
        } finally {
            setIsSubmitting(false)
        }
    }

    const handlePayWithHelloAsso = async () => {
        setError('')

        // Parse amount to centimes
        const amountCentimes = Math.round(
            parseFloat(total.replace(',', '.').replace(' €', '')) * 100
        )

        // Fetch user info from API
        let payerFirstName = 'Client'
        let payerLastName = "Mc'INT"
        let payerEmail = userEmail || 'client@mcint.fr'

        try {
            const userResponse = await fetch('/api/users/me', {
                credentials: 'include'
            })
            if (userResponse.ok) {
                const userData = await userResponse.json()
                if (userData.prenom) payerFirstName = userData.prenom
                if (userData.nom) payerLastName = userData.nom
                if (userData.email) payerEmail = userData.email
            }
        } catch (e) {
            console.warn('Could not fetch user info, using defaults')
        }

        // Extract items by type from cart
        const menuItem = cartItems.find(item => item.item_type === 'menu')
        const boissonItem = cartItems.find(item => item.item_type === 'boisson')
        const bonusItem = cartItems.find(item => item.item_type === 'upsell')

        // Extract time slot start hour (format: "08:00-09:00" -> "08:00")
        const timeSlotStart = deliveryInfo?.timeSlot?.split('-')[0] || '12:00'

        // Step 1: Create reservation with order details
        const reservationData = {
            date_reservation: '2026-02-07',
            heure_reservation: timeSlotStart,
            habite_residence: deliveryInfo?.locationType === 'maisel',
            numero_chambre: deliveryInfo?.room || null,
            numero_immeuble: deliveryInfo?.building || null,
            adresse: deliveryInfo?.address || null,
            phone: userPhone || null,
            special_requests: specialRequests || null,
            menu: menuItem?.title || null,
            boisson: boissonItem?.title || null,
            bonus: bonusItem?.title || null,
        }

        console.log('[Checkout] Creating reservation:', reservationData)

        const reservationResponse = await fetch('/api/reservations/', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'include',
            body: JSON.stringify(reservationData),
        })

        if (!reservationResponse.ok) {
            const errorData = await reservationResponse.json().catch(() => ({}))
            throw new Error(errorData.detail || 'Erreur lors de la création de la réservation')
        }

        const reservation = await reservationResponse.json()
        console.log('[Checkout] Reservation created:', reservation)

        // Store reservation ID for payment
        localStorage.setItem('pending_reservation_id', reservation.id?.toString() || '')

        // Step 2: Create checkout intent
        const response = await fetch('/api/payments/checkout', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'include',
            body: JSON.stringify({
                amount: amountCentimes,
                item_name: "Commande Mc'INT",
                payer_email: payerEmail,
                payer_first_name: payerFirstName,
                payer_last_name: payerLastName,
                reservation_id: reservation.id,
            }),
        })

        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}))
            throw new Error(errorData.detail || 'Erreur lors de la création du paiement')
        }

        const data = await response.json()

        // Store checkout intent ID for verification on return
        localStorage.setItem('checkout_intent_id', data.checkout_intent_id)

        // Redirect to HelloAsso
        window.location.href = data.redirect_url
    }

    // Info Step: Collect contact details only
    if (isInfoStep) {
        return (
            <div className="checkout-step">
                <button className="checkout-step__back" onClick={onBack}>← Retour</button>
                <h2 className="checkout-step__title">Vos informations</h2>

                <div className="checkout-summary">
                    <h3>Récapitulatif</h3>
                    <ul>
                        {cartItems.map((item, idx) => (
                            <li key={`${item.id}-${idx}`}>
                                <span>{item.title}</span>
                                <span>{item.price}</span>
                            </li>
                        ))}
                    </ul>
                    <div className="checkout-total">
                        <span>Total</span>
                        <span>{total}</span>
                    </div>
                </div>

                <form className="checkout-form" onSubmit={handleSubmit}>
                    <h3>Coordonnées</h3>

                    <div className="form-group">
                        <label>Téléphone</label>
                        <input
                            type="tel"
                            required
                            value={formData.phone}
                            onChange={e => setFormData({ ...formData, phone: e.target.value })}
                            placeholder="06 12 34 56 78"
                        />
                    </div>

                    <button
                        type="submit"
                        className="checkout-submit-btn"
                        disabled={isSubmitting}
                    >
                        {isSubmitting ? 'Validation...' : 'Continuer'}
                    </button>
                </form>
            </div>
        )
    }

    // Payment Step: Show summary with delivery info and payment button
    return (
        <div className="checkout-step">
            <button className="checkout-step__back" onClick={onBack}>← Retour</button>
            <h2 className="checkout-step__title">Paiement</h2>

            <div className="checkout-summary">
                <h3>Récapitulatif de votre commande</h3>
                <ul>
                    {cartItems.map((item, idx) => (
                        <li key={`${item.id}-${idx}`}>
                            <span>{item.title}</span>
                            <span>{item.price}</span>
                        </li>
                    ))}
                </ul>
                <div className="checkout-total">
                    <span>Total</span>
                    <span>{total}</span>
                </div>
            </div>

            {deliveryInfo && (
                <div className="checkout-delivery-summary">
                    <h3>Livraison</h3>
                    <div className="delivery-info-card">
                        {deliveryInfo.locationType === 'maisel' ? (
                            <p>
                                <strong>📍 Résidence Maisel</strong><br />
                                Bâtiment {deliveryInfo.building}, Chambre {deliveryInfo.room}
                            </p>
                        ) : (
                            <p>
                                <strong>📍 Adresse externe</strong><br />
                                {deliveryInfo.address}
                            </p>
                        )}
                        <p>
                            <strong>🕐 Créneau</strong><br />
                            {deliveryInfo.timeSlot}
                        </p>
                        {userEmail && (
                            <p>
                                <strong>📧 Email</strong><br />
                                {userEmail}
                            </p>
                        )}
                    </div>
                </div>
            )}

            {/* Special Requests */}
            <div className="checkout-special-requests">
                <h3>Demandes spéciales</h3>
                <textarea
                    value={specialRequests}
                    onChange={(e) => setSpecialRequests(e.target.value)}
                    placeholder="Allergies, sans sauce, bien cuit... (optionnel)"
                    rows={3}
                    maxLength={500}
                    className="checkout-special-textarea"
                />
                <span className="checkout-special-count">{specialRequests.length}/500</span>
            </div>

            {error && (
                <p style={{ color: '#d32f2f', textAlign: 'center', margin: '12px 0' }}>{error}</p>
            )}

            <button
                className="checkout-submit-btn checkout-pay-btn"
                onClick={handleSubmit}
                disabled={isSubmitting}
            >
                {isSubmitting ? '⏳ Redirection...' : `Payer ${total} avec HelloAsso`}
            </button>
        </div>
    )
}

export default Checkout

