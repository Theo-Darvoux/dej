import { useState, useEffect } from 'react'
import { MenuProvider } from './context/MenuContext'
import LandingPage from './components/landing/LandingPage'
import OrderPage from './components/order/OrderPage'
import OrderStatus from './components/order/OrderStatus'
import PaymentSuccess from './components/payment/PaymentSuccess'
import PaymentError from './components/payment/PaymentError'
import RecapPage from './components/recap/RecapPage'
import AdminPage from './components/admin/AdminPage'
import PrintPage from './pages/print'
import TerminalPage from './pages/terminal'
import './App.css'

type ViewState = 'landing' | 'order' | 'order-status' | 'payment-success' | 'payment-error' | 'recap' | 'admin' | 'admin-print' | 'admin-terminal'

function App() {
  const [view, setView] = useState<ViewState>(() => {
    const path = window.location.pathname
    if (path === '/payment/success') return 'payment-success'
    if (path === '/payment/error') return 'payment-error'
    if (path === '/order') return 'order'
    if (path.startsWith('/order/status/')) return 'order-status'
    if (path === '/recap') return 'recap'
    if (path === '/admin') return 'admin'
    return 'landing'
  })

  // Check URL path on mount for payment return pages
  useEffect(() => {
    const path = window.location.pathname

    if (path === '/payment/success') {
      setView('payment-success')
    } else if (path === '/payment/error') {
      setView('payment-error')
    } else if (path === '/order') {
      setView('order')
    } else if (path.startsWith('/order/status/')) {
      setView('order-status')
    } else if (path === '/recap') {
      setView('recap')
    } else if (path === '/admin') {
      setView('admin')
    }
  }, [])

  const handleGoHome = () => {
    // Clear URL and go to landing
    window.history.pushState({}, '', '/')
    setView('landing')
  }

  const handleViewRecap = () => {
    window.history.pushState({}, '', '/recap')
    setView('recap')
  }

  return (
    <MenuProvider>
      {view === 'landing' && (
        <LandingPage
          onStart={() => {
            window.history.pushState({}, '', '/')
            setView('order')
          }}
          onViewRecap={handleViewRecap}
        />
      )}

      {view === 'order' && (
        <OrderPage onBackToHome={handleGoHome} />
      )}

      {view === 'order-status' && (
        <OrderStatus />
      )}

      {view === 'recap' && (
        <RecapPage onBackToHome={handleGoHome} />
      )}

      {view === 'payment-success' && (
        <PaymentSuccess onClose={handleGoHome} />
      )}

      {view === 'payment-error' && (
        <PaymentError onClose={() => setView('order')} />
      )}

      {view === 'admin' && (
        <AdminPage onGoHome={handleGoHome} />
      )}

      {view === 'admin-print' && (
        <PrintPage />
      )}

      {view === 'admin-terminal' && (
        <TerminalPage />
      )}
    </MenuProvider>
  )
}

export default App
