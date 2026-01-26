import { useState, useEffect } from 'react'
import LandingPage from './components/landing/LandingPage'
import OrderPage from './components/order/OrderPage'
import PaymentSuccess from './components/payment/PaymentSuccess'
import PaymentError from './components/payment/PaymentError'
import OrderTicket from './components/order/OrderTicket'
import PrintPage from './pages/print'
import TerminalPage from './pages/terminal'
import './App.css'

type ViewState = 'landing' | 'order' | 'payment-success' | 'payment-error' | 'admin-print' | 'admin-terminal'

function App() {
  const [view, setView] = useState<ViewState>(() => {
    const path = window.location.pathname
    if (path === '/payment/success') return 'payment-success'
    if (path === '/payment/error') return 'payment-error'
    if (path === '/order') return 'order'
    if (path === '/admin/print' || path === '/print' || path === '/summary') return 'admin-print'
    if (path === '/admin/terminal' || path === '/terminal') return 'admin-terminal'
    return 'landing'
  })
  const [isVerifying, setIsVerifying] = useState(() => window.location.pathname === '/auth/verify')
  const [verifyError, setVerifyError] = useState<string | null>(null)
  const [activeOrder, setActiveOrder] = useState<any>(null)
  const [showTicket, setShowTicket] = useState(false)

  const handleAutoVerify = async (email: string, code: string) => {
    setIsVerifying(true)
    setVerifyError(null)
    try {
      const response = await fetch('/api/auth/verify', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, code }),
      })

      if (!response.ok) {
        const data = await response.json()
        throw new Error(data.detail || 'La vérification a échoué')
      }

      // Success! Move to order page and clean URL
      window.history.pushState({}, '', '/')
      setView('order')
    } catch (err) {
      setVerifyError(err instanceof Error ? err.message : 'Une erreur est survenue')
      setTimeout(() => {
        window.history.pushState({}, '', '/')
        setView('landing')
        setVerifyError(null)
      }, 3000)
    } finally {
      setIsVerifying(false)
    }
  }

  // Check URL path on mount for payment return pages
  useEffect(() => {
    const path = window.location.pathname
    const params = new URLSearchParams(window.location.search)

    if (path === '/auth/verify') {
      const email = params.get('email')
      const code = params.get('code')
      if (email && code) {
        handleAutoVerify(email, code)
      } else {
        setView('landing')
      }
    } else if (path === '/payment/success') {
      setView('payment-success')
    } else if (path === '/payment/error') {
      setView('payment-error')
    } else if (path === '/order') {
      setView('order')
    } else if (path === '/admin/print' || path === '/print' || path === '/summary') {
      setView('admin-print')
    } else if (path === '/admin/terminal' || path === '/terminal') {
      setView('admin-terminal')
    }
  }, [])

  const handleGoHome = () => {
    // Clear URL and go to landing
    window.history.pushState({}, '', '/')
    setView('landing')
    setShowTicket(false)
  }

  const handleViewOrder = (orderData: any) => {
    setActiveOrder(orderData)
    setShowTicket(true)
  }

  return (
    <>
      {isVerifying && (
        <div className="verify-overlay">
          <div className="verify-content">
            <div className="verify-spinner">🍟</div>
            <h2>Vérification de ton accès...</h2>
            {verifyError && <p className="verify-error">{verifyError}</p>}
          </div>
        </div>
      )}

      {view === 'landing' && !isVerifying && (
        <>
          <LandingPage
            onStart={() => {
              window.history.pushState({}, '', '/')
              setView('order')
            }}
            onViewOrder={handleViewOrder}
          />
          {showTicket && activeOrder && (
            <OrderTicket order={activeOrder} onClose={() => setShowTicket(false)} />
          )}
        </>
      )}

      {view === 'order' && !isVerifying && (
        <OrderPage onBackToHome={handleGoHome} />
      )}

      {view === 'payment-success' && !isVerifying && (
        <PaymentSuccess onClose={handleGoHome} />
      )}

      {view === 'payment-error' && !isVerifying && (
        <PaymentError onClose={() => setView('order')} />
      )}

      {view === 'admin-print' && (
        <PrintPage />
      )}

      {view === 'admin-terminal' && (
        <TerminalPage />
      )}
    </>
  )
}

export default App
