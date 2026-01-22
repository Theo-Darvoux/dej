import { useState, useEffect } from 'react'
import LandingPage from './components/landing/LandingPage'
import OrderPage from './components/order/OrderPage'
import PaymentSuccess from './components/payment/PaymentSuccess'
import PaymentError from './components/payment/PaymentError'
import './App.css'

type ViewState = 'landing' | 'order' | 'payment-success' | 'payment-error'

function App() {
  const [view, setView] = useState<ViewState>('landing')

  // Check URL path on mount for payment return pages
  useEffect(() => {
    const path = window.location.pathname

    if (path === '/payment/success') {
      setView('payment-success')
    } else if (path === '/payment/error') {
      setView('payment-error')
    } else if (path === '/order') {
      setView('order')
    }
  }, [])

  const handleGoHome = () => {
    // Clear URL and go to landing
    window.history.pushState({}, '', '/')
    setView('landing')
  }

  return (
    <>
      {view === 'landing' && (
        <LandingPage onStart={() => setView('order')} />
      )}

      {view === 'order' && (
        <OrderPage onBackToHome={handleGoHome} />
      )}

      {view === 'payment-success' && (
        <PaymentSuccess onClose={handleGoHome} />
      )}

      {view === 'payment-error' && (
        <PaymentError onClose={() => setView('order')} />
      )}
    </>
  )
}

export default App
