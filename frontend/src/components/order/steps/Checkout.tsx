import { useState } from 'react'
import { fetchWithAuth } from '../../../utils/api'
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
    const [phoneError, setPhoneError] = useState('')

    // Validate phone number (French + international formats)
    const validatePhone = (phone: string): boolean => {
        const cleaned = phone.replace(/[\s.\-()]/g, '')

        const frenchMobile = /^0[67]\d{8}$/
        const frenchLandline = /^0[1-59]\d{8}$/
        const frenchIntl = /^\+33[1-9]\d{8}$/
        const frenchIntl2 = /^0033[1-9]\d{8}$/
        const international = /^\+[1-9]\d{7,14}$/
        const generic = /^[0-9]\d{7,14}$/

        return frenchMobile.test(cleaned) ||
               frenchLandline.test(cleaned) ||
               frenchIntl.test(cleaned) ||
               frenchIntl2.test(cleaned) ||
               international.test(cleaned) ||
               generic.test(cleaned)
    }

    const handlePhoneChange = (value: string) => {
        setFormData({ ...formData, phone: value })

        // Clear error while typing
        if (phoneError) {
            setPhoneError('')
        }
    }

    const handlePhoneBlur = () => {
        if (formData.phone && !validatePhone(formData.phone)) {
            setPhoneError('Numéro de téléphone invalide (ex: 06 12 34 56 78 ou +32 123 456 789)')
        }
    }

    const total = cartItems.reduce((acc, item) => {
        const price = parseFloat(item.price.replace(',', '.').replace(' €', '') || '0')
        return acc + price
    }, 0).toFixed(2).replace('.', ',') + ' €'

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault()

        // Validate phone before submitting (required field)
        if (isInfoStep) {
            if (!formData.phone) {
                setPhoneError('Le numéro de téléphone est requis')
                return
            }
            if (!validatePhone(formData.phone)) {
                setPhoneError('Numéro de téléphone invalide (ex: 06 12 34 56 78 ou +32 123 456 789)')
                return
            }
        }

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
            setError(err instanceof Error ? err.message : "Erreur lors de la commande")
        } finally {
            setIsSubmitting(false)
        }
    }

    const handlePayWithHelloAsso = async () => {
        setError('')
        let payerFirstName = ''
        let payerLastName = ''
        let payerEmail = userEmail || ''

        try {
            const userResponse = await fetchWithAuth('/api/users/me')
            if (userResponse.ok) {
                const userData = await userResponse.json()
                if (userData.prenom) payerFirstName = userData.prenom
                if (userData.nom) payerLastName = userData.nom
                if (userData.email) payerEmail = userData.email
            }
        } catch {
            // Fallback: extract from email if user data fetch fails
        }

        // Fallback: If prenom/nom not available from user data, extract from email
        if ((!payerFirstName || !payerLastName) && payerEmail) {
            try {
                const localPart = payerEmail.split('@')[0]
                const parts = localPart.replace(/_/g, '.').replace(/-/g, '.').split('.').filter(p => p)
                if (parts.length >= 2) {
                    if (!payerFirstName) {
                        payerFirstName = parts[0].charAt(0).toUpperCase() + parts[0].slice(1).toLowerCase()
                    }
                    if (!payerLastName) {
                        payerLastName = parts[1].charAt(0).toUpperCase() + parts[1].slice(1).toLowerCase()
                    }
                }
            } catch {
                // If extraction fails, throw error
            }
        }

        // Final validation before sending to backend
        if (!payerFirstName || payerFirstName.length < 2) {
            throw new Error('Prénom invalide. Veuillez vous reconnecter.')
        }
        if (!payerLastName || payerLastName.length < 2) {
            throw new Error('Nom invalide. Veuillez vous reconnecter.')
        }

        const menuItem = cartItems.find(item => item.item_type === 'menu')
        const boissonItem = cartItems.find(item => item.item_type === 'boisson')
        const extraItems = cartItems.filter(item => item.item_type === 'upsell')
        const timeSlotStart = deliveryInfo?.timeSlot?.split('-')[0] || '12:00'

        const reservationData = {
            heure_reservation: timeSlotStart,
            habite_residence: deliveryInfo?.locationType === 'maisel',
            numero_chambre: deliveryInfo?.room || null,
            adresse: deliveryInfo?.address || null,
            phone: userPhone || null,
            special_requests: specialRequests || null,
            menu: menuItem?.title || null,
            boisson: boissonItem?.title || null,
            extras: extraItems.map(item => item.title),
        }

        const reservationResponse = await fetchWithAuth('/api/reservations/', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(reservationData),
        })

        if (!reservationResponse.ok) {
            const errorData = await reservationResponse.json().catch(() => ({}))
            throw new Error(errorData.detail || 'Erreur lors de la création de la réservation')
        }

        const reservation = await reservationResponse.json()

        localStorage.setItem('pending_reservation_id', reservation.id?.toString() || '')

        const response = await fetchWithAuth('/api/payments/checkout', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                payer_email: payerEmail,
                payer_first_name: payerFirstName,
                payer_last_name: payerLastName,
                reservation_id: reservation.id
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
                            onChange={e => handlePhoneChange(e.target.value)}
                            onBlur={handlePhoneBlur}
                            placeholder="06 12 34 56 78"
                            className={phoneError ? 'input-error' : ''}
                            autoComplete="tel"
                        />
                        {phoneError && <span className="form-error">{phoneError}</span>}
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
                                <strong>Maisel</strong><br />
                                Bâtiment U{deliveryInfo.room?.[0]}, Chambre {deliveryInfo.room}
                            </p>
                        ) : (
                            <p>
                                <strong>Adresse externe</strong><br />
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
                    placeholder="Allergies, livreur, livrer à un local / GS... (optionnel)"
                    rows={3}
                    maxLength={500}
                    className="checkout-special-textarea"
                />
                <span className={`checkout-special-count ${specialRequests.length >= 480 ? 'checkout-special-count--warning' : ''}`}>
                    {specialRequests.length}/500
                    {specialRequests.length >= 480 && ' - Limite bientôt atteinte'}
                </span>
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

