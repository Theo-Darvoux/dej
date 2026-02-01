import { useState, useEffect, useCallback } from 'react'
import { useMenu, type MenuItem } from '../../context/MenuContext'
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

const OrderPage = () => {
    useMenu() // Initialize menu context

    // Wizard State
    const [step, setStep] = useState<Step>('SELECTION')
    const [selectedMenu, setSelectedMenu] = useState<MenuItem | null>(null)
    const [cartItems, setCartItems] = useState<MenuItem[]>([])
    const [extraItems, setExtraItems] = useState<MenuItem[]>([])
    const [deliveryInfo, setDeliveryInfo] = useState<DeliveryInfo | null>(null)
    const [userEmail, setUserEmail] = useState('')
    const [userInfo, setUserInfo] = useState<UserInfo>({ phone: '' })

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
                setStep(event.state.step)
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
        setCartItems(prev => [...prev, ...supplements])
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
        
        // Check if user already has a valid access token
        try {
            const response = await fetch('/api/users/me', {
                credentials: 'include'
            })
            
            if (response.ok) {
                const userData = await response.json()
                // User is already authenticated, skip verification
                setUserEmail(userData.email)
                navigateToStep('CHECKOUT')
                return
            }
        } catch (error) {
            // Token invalid or expired, proceed to verification
            console.log('No valid token, proceeding to verification')
        }
        
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
        // HelloAsso redirects to /payment/success, this is just a fallback
        window.location.href = '/payment/success'
    }

    // Back handlers (called by UI back buttons)
    const handleBack = useCallback(() => {
        // Use browser history to go back (triggers popstate)
        window.history.back()
    }, [])

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
                <div className="order-header__logo">🍟</div>
            </header>

            <main className="order-wizard-content">
                {step === 'SELECTION' && (
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


