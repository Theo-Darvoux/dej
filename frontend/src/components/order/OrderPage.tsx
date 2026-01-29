import { useState } from 'react'
import { useMenu, type MenuItem } from '../../context/MenuContext'
import MenuSelection from './steps/MenuSelection'
import MenuDetail from './steps/MenuDetail'
import Supplements from './steps/Supplements'
import Delivery, { type DeliveryInfo } from './steps/Delivery'
import EmailVerification from './steps/EmailVerification'
import Checkout from './steps/Checkout'
import './OrderPage.css'

type OrderPageProps = {
    onBackToHome: () => void
}

type Step = 'SELECTION' | 'DETAIL' | 'SUPPLEMENTS' | 'INFO' | 'DELIVERY' | 'VERIFICATION' | 'CHECKOUT'

export type UserInfo = {
    phone: string
}

const OrderPage = ({ onBackToHome }: OrderPageProps) => {
    useMenu() // Initialize menu context

    // Wizard State
    const [step, setStep] = useState<Step>('SELECTION')
    const [selectedMenu, setSelectedMenu] = useState<MenuItem | null>(null)
    const [cartItems, setCartItems] = useState<MenuItem[]>([])
    const [extraItems, setExtraItems] = useState<MenuItem[]>([])
    const [deliveryInfo, setDeliveryInfo] = useState<DeliveryInfo | null>(null)
    const [userEmail, setUserEmail] = useState('')
    const [userInfo, setUserInfo] = useState<UserInfo>({ phone: '' })

    // Step 1: Menu Selected
    const handleMenuSelect = (menu: MenuItem) => {
        setSelectedMenu(menu)
        setStep('DETAIL')
    }

    // Step 2: Confirm Menu -> Go to Supplements
    const handleMenuConfirm = () => {
        if (selectedMenu) {
            setCartItems([selectedMenu])
            setStep('SUPPLEMENTS')
        }
    }

    // Step 3: Add Supplements -> Go to Info
    const handleSupplementsContinue = (supplements: MenuItem[]) => {
        setExtraItems(supplements)
        setCartItems(prev => [...prev, ...supplements])
        setStep('INFO')
    }

    // Step 4: Info confirmed -> Go to Delivery (save user info)
    const handleInfoContinue = (info: UserInfo) => {
        setUserInfo(info)
        setStep('DELIVERY')
    }

    // Step 5: Delivery confirmed -> Go to Verification
    const handleDeliveryContinue = (info: DeliveryInfo) => {
        setDeliveryInfo(info)
        setStep('VERIFICATION')
    }

    // Step 6: Email verified -> Go to Checkout
    const handleVerificationComplete = (isCotisant: boolean, email: string) => {
        if (isCotisant) {
            setUserEmail(email)
            setStep('CHECKOUT')
        }
        // Non-cotisants are blocked in the verification component
    }

    // Step 7: Payment Success (legacy - now handled by /payment/success route)
    const handlePaymentSuccess = () => {
        // HelloAsso redirects to /payment/success, this is just a fallback
        window.location.href = '/payment/success'
    }

    // Back handlers
    const handleBack = () => {
        switch (step) {
            case 'SELECTION':
                onBackToHome()
                break
            case 'DETAIL':
                setStep('SELECTION')
                setSelectedMenu(null)
                break
            case 'SUPPLEMENTS':
                setCartItems([])
                setExtraItems([])
                setStep('DETAIL')
                break
            case 'INFO':
                if (selectedMenu) setCartItems([selectedMenu])
                setStep('SUPPLEMENTS')
                break
            case 'DELIVERY':
                setStep('INFO')
                break
            case 'VERIFICATION':
                setStep('DELIVERY')
                break
            case 'CHECKOUT':
                setStep('VERIFICATION')
                break
        }
    }

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


