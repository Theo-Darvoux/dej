import { useState, useEffect, useCallback } from 'react'
import { useMenu, type MenuItem } from '../../context/MenuContext'
import { safeJSONParse, safeGetItem } from '../../utils/storage'
import MenuSelection from './steps/MenuSelection'
import MenuDetail from './steps/MenuDetail'
import Supplements from './steps/Supplements'
import Delivery, { type DeliveryInfo } from './steps/Delivery'
import EmailVerification from './steps/EmailVerification'
import Checkout from './steps/Checkout'
import './OrderPage.css'

type Step = 'SELECTION' | 'DETAIL' | 'SUPPLEMENTS' | 'INFO' | 'DELIVERY' | 'VERIFICATION' | 'CHECKOUT'

export type UserInfo = {
    phone: string
}

// localStorage keys for state persistence
const STORAGE_KEYS = {
    CART: 'mcint_cart',
    EXTRAS: 'mcint_extras',
    SELECTED_MENU: 'mcint_selected_menu',
    USER_EMAIL: 'mcint_user_email',
    USER_INFO: 'mcint_user_info',
    DELIVERY_INFO: 'mcint_delivery_info',
    STEP: 'mcint_step'
}

const OrderPage = () => {
    useMenu() // Initialize menu context

    // Loading and error states
    const [isCheckingAuth, setIsCheckingAuth] = useState(false)
    const [authError, setAuthError] = useState<string | null>(null)

    // Wizard State - initialize from localStorage with safe parsing
    const [selectedMenu, setSelectedMenu] = useState<MenuItem | null>(() => {
        return safeJSONParse<MenuItem | null>(STORAGE_KEYS.SELECTED_MENU, null)
    })
    const [step, setStep] = useState<Step>(() => {
        const saved = safeGetItem(STORAGE_KEYS.STEP)
        const savedStep = (saved as Step) || 'SELECTION'

        // Validate step consistency: if no menu selected, can't be past SELECTION
        const hasSelectedMenu = safeJSONParse<MenuItem | null>(STORAGE_KEYS.SELECTED_MENU, null)
        if (!hasSelectedMenu && savedStep !== 'SELECTION') {
            return 'SELECTION'
        }

        return savedStep
    })
    const [cartItems, setCartItems] = useState<MenuItem[]>(() => {
        return safeJSONParse<MenuItem[]>(STORAGE_KEYS.CART, [])
    })
    const [extraItems, setExtraItems] = useState<MenuItem[]>(() => {
        return safeJSONParse<MenuItem[]>(STORAGE_KEYS.EXTRAS, [])
    })
    const [deliveryInfo, setDeliveryInfo] = useState<DeliveryInfo | null>(() => {
        return safeJSONParse<DeliveryInfo | null>(STORAGE_KEYS.DELIVERY_INFO, null)
    })
    const [userEmail, setUserEmail] = useState(() => {
        return safeGetItem(STORAGE_KEYS.USER_EMAIL, '')
    })
    const [userInfo, setUserInfo] = useState<UserInfo>(() => {
        return safeJSONParse<UserInfo>(STORAGE_KEYS.USER_INFO, { phone: '' })
    })

    // Persist state to localStorage on change
    useEffect(() => {
        localStorage.setItem(STORAGE_KEYS.STEP, step)
    }, [step])

    useEffect(() => {
        if (selectedMenu) {
            localStorage.setItem(STORAGE_KEYS.SELECTED_MENU, JSON.stringify(selectedMenu))
        } else {
            localStorage.removeItem(STORAGE_KEYS.SELECTED_MENU)
        }
    }, [selectedMenu])

    useEffect(() => {
        localStorage.setItem(STORAGE_KEYS.CART, JSON.stringify(cartItems))
    }, [cartItems])

    useEffect(() => {
        localStorage.setItem(STORAGE_KEYS.EXTRAS, JSON.stringify(extraItems))
    }, [extraItems])

    useEffect(() => {
        if (deliveryInfo) {
            localStorage.setItem(STORAGE_KEYS.DELIVERY_INFO, JSON.stringify(deliveryInfo))
        } else {
            localStorage.removeItem(STORAGE_KEYS.DELIVERY_INFO)
        }
    }, [deliveryInfo])

    useEffect(() => {
        if (userEmail) {
            localStorage.setItem(STORAGE_KEYS.USER_EMAIL, userEmail)
        } else {
            localStorage.removeItem(STORAGE_KEYS.USER_EMAIL)
        }
    }, [userEmail])

    useEffect(() => {
        localStorage.setItem(STORAGE_KEYS.USER_INFO, JSON.stringify(userInfo))
    }, [userInfo])

    // Clear all order state from localStorage (called on successful order)
    const clearOrderState = useCallback(() => {
        Object.values(STORAGE_KEYS).forEach(key => localStorage.removeItem(key))
        localStorage.removeItem('pending_reservation_id')
        localStorage.removeItem('checkout_intent_id')
    }, [])

    // Navigate to step with history push
    const navigateToStep = useCallback((newStep: Step) => {
        window.history.pushState({ step: newStep, view: 'order' }, '', '/order')
        setStep(newStep)
    }, [])

    // Handle browser back/forward button
    useEffect(() => {
        const handlePopState = (event: PopStateEvent) => {
            // Check if this is an order step navigation
            if (event.state?.view === 'order' && event.state?.step) {
                const targetStep = event.state.step as Step

                // Validate step consistency: reset to SELECTION if menu is lost
                if (targetStep !== 'SELECTION' && !localStorage.getItem(STORAGE_KEYS.SELECTED_MENU)) {
                    setStep('SELECTION')
                    setSelectedMenu(null)
                    window.history.replaceState({ step: 'SELECTION', view: 'order' }, '', '/order')
                    return
                }

                setStep(targetStep)
            }
            // If navigating away from order view, App.tsx handles it via its own popstate listener
        }

        window.addEventListener('popstate', handlePopState)
        return () => window.removeEventListener('popstate', handlePopState)
    }, [])

    // Push initial state on mount (so back from SELECTION works)
    useEffect(() => {
        // Replace current state with order view + SELECTION step
        window.history.replaceState({ step: 'SELECTION', view: 'order' }, '', '/order')
    }, [])

    // Step 1: Menu Selected
    const handleMenuSelect = (menu: MenuItem) => {
        setSelectedMenu(menu)
        navigateToStep('DETAIL')
    }

    // Step 2: Confirm Menu -> Go to Supplements
    const handleMenuConfirm = () => {
        if (selectedMenu) {
            setCartItems([selectedMenu])
            navigateToStep('SUPPLEMENTS')
        }
    }

    // Step 3: Add Supplements -> Go to Info
    const handleSupplementsContinue = (supplements: MenuItem[]) => {
        setExtraItems(supplements)
        // Remove old supplements (upsells) from cart before adding new ones to prevent duplication
        const withoutSupplements = cartItems.filter(item => item.item_type !== 'upsell')
        setCartItems([...withoutSupplements, ...supplements])
        navigateToStep('INFO')
    }

    // Step 4: Info confirmed -> Go to Delivery (save user info)
    const handleInfoContinue = (info: UserInfo) => {
        setUserInfo(info)
        navigateToStep('DELIVERY')
    }

    // Step 5: Delivery confirmed -> Go to Verification or Checkout (if already logged in)
    const handleDeliveryContinue = async (info: DeliveryInfo) => {
        setDeliveryInfo(info)
        setAuthError(null)
        setIsCheckingAuth(true)

        // Check if user already has a valid access token
        try {
            const response = await fetch('/api/users/me', {
                credentials: 'include'
            })

            if (response.ok) {
                const userData = await response.json()
                // User is already authenticated, skip verification
                setUserEmail(userData.email)
                setIsCheckingAuth(false)
                navigateToStep('CHECKOUT')
                return
            } else if (response.status === 401) {
                // Token invalid or expired, proceed to verification
                console.log('Token expired, proceeding to verification')
            } else {
                // Unexpected error
                const errorData = await response.json().catch(() => ({}))
                setAuthError(errorData.detail || 'Erreur de vérification du compte')
            }
        } catch (error) {
            // Network error
            console.log('Network error checking auth:', error)
            setAuthError('Erreur de connexion au serveur. Veuillez réessayer.')
        }

        setIsCheckingAuth(false)
        // No valid token, go to verification
        navigateToStep('VERIFICATION')
    }

    // Step 6: Email verified -> Go to Checkout
    const handleVerificationComplete = (isCotisant: boolean, email: string) => {
        if (isCotisant) {
            setUserEmail(email)
            navigateToStep('CHECKOUT')
        }
        // Non-cotisants are blocked in the verification component
    }

    // Step 7: Payment Success (legacy - now handled by /payment/success route)
    const handlePaymentSuccess = () => {
        // Clear order state on successful payment
        clearOrderState()
        // HelloAsso redirects to /payment/success, this is just a fallback
        window.location.href = '/payment/success'
    }

    // Back handlers (called by UI back buttons)
    const handleBack = useCallback(() => {
        // Use browser history to go back (triggers popstate)
        window.history.back()
    }, [])

    // Reset order state for error recovery
    const handleResetOrder = useCallback(() => {
        if (confirm('Voulez-vous recommencer votre commande ?')) {
            clearOrderState()
            setSelectedMenu(null)
            setCartItems([])
            setExtraItems([])
            setDeliveryInfo(null)
            setUserInfo({ phone: '' })
            setStep('SELECTION')
            window.history.replaceState({ step: 'SELECTION', view: 'order' }, '', '/order')
        }
    }, [clearOrderState])

    const getStepTitle = () => {
        switch (step) {
            case 'SELECTION': return 'Nos Menus'
            case 'DETAIL': return 'Détails du menu'
            case 'SUPPLEMENTS': return 'Suppléments'
            case 'INFO': return 'Vos informations'
            case 'DELIVERY': return 'Livraison'
            case 'VERIFICATION': return 'Vérification'
            case 'CHECKOUT': return 'Paiement'
        }
    }

    return (
        <div className="order-page-wizard">
            <header className="order-header">
                <button className="order-header__back" onClick={handleBack} aria-label="Retour">
                    ←
                </button>
                <div className="order-header__title">
                    <h1>Mc'INT</h1>
                    <p>{getStepTitle()}</p>
                </div>
                <button
                    className="order-header__reset"
                    onClick={handleResetOrder}
                    aria-label="Recommencer la commande"
                    title="Recommencer la commande"
                >
                    ↻
                </button>
            </header>

            <main className="order-wizard-content">
                {/* Auth checking loading state */}
                {isCheckingAuth && (
                    <div className="order-loading">
                        <div className="order-loading__spinner"></div>
                        <p>Vérification de votre session...</p>
                    </div>
                )}

                {/* Auth error display */}
                {authError && (
                    <div className="order-error">
                        <p>{authError}</p>
                        <button onClick={() => setAuthError(null)}>Fermer</button>
                    </div>
                )}

                {step === 'SELECTION' && !isCheckingAuth && (
                    <MenuSelection onSelect={handleMenuSelect} />
                )}

                {step === 'DETAIL' && selectedMenu && (
                    <MenuDetail
                        menu={selectedMenu}
                        onBack={handleBack}
                        onConfirm={handleMenuConfirm}
                    />
                )}

                {step === 'SUPPLEMENTS' && (
                    <Supplements
                        initialSelectedItems={extraItems}
                        onBack={handleBack}
                        onContinue={handleSupplementsContinue}
                    />
                )}

                {step === 'INFO' && (
                    <Checkout
                        onBack={handleBack}
                        cartItems={cartItems}
                        onPaymentSuccess={() => { }}
                        isInfoStep={true}
                        initialUserInfo={userInfo}
                        onInfoContinue={handleInfoContinue}
                    />
                )}

                {step === 'DELIVERY' && (
                    <Delivery
                        onBack={handleBack}
                        onContinue={handleDeliveryContinue}
                        initialDeliveryInfo={deliveryInfo}
                    />
                )}

                {step === 'VERIFICATION' && (
                    <EmailVerification
                        onBack={handleBack}
                        onVerified={handleVerificationComplete}
                        initialEmail={userEmail}
                    />
                )}

                {step === 'CHECKOUT' && (
                    <Checkout
                        onBack={handleBack}
                        cartItems={cartItems}
                        onPaymentSuccess={handlePaymentSuccess}
                        isInfoStep={false}
                        deliveryInfo={deliveryInfo}
                        userEmail={userEmail}
                        userPhone={userInfo.phone}
                    />
                )}
            </main>
        </div>
    )
}

export default OrderPage


