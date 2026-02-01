import { useState, useEffect, useCallback } from 'react'
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

function getViewFromPath(path: string): ViewState {
  if (path === '/payment/success') return 'payment-success'
  if (path === '/payment/error') return 'payment-error'
  if (path === '/order') return 'order'
  if (path.startsWith('/order/status/')) return 'order-status'
  if (path === '/recap') return 'recap'
  if (path === '/admin') return 'admin'
  if (path === '/admin/print') return 'admin-print'
  if (path === '/terminal') return 'admin-terminal'
  return 'landing'
}

function App() {
  const [view, setView] = useState<ViewState>(() => getViewFromPath(window.location.pathname))

  // Initialize history state on mount (for proper back navigation)
  useEffect(() => {
    const initialView = getViewFromPath(window.location.pathname)
    // Only replace if no state exists (initial page load)
    if (!window.history.state?.view) {
      window.history.replaceState({ view: initialView }, '', window.location.pathname)
    }
  }, [])

  // Handle browser back/forward navigation
  useEffect(() => {
    const handlePopState = (event: PopStateEvent) => {
      // If state has view info, use it; otherwise derive from URL
      if (event.state?.view) {
        setView(event.state.view)
      } else {
        setView(getViewFromPath(window.location.pathname))
      }
    }

    window.addEventListener('popstate', handlePopState)
    return () => window.removeEventListener('popstate', handlePopState)
  }, [])

  // Navigation helper that pushes state with view info
  const navigateTo = useCallback((newView: ViewState, path: string) => {
    window.history.pushState({ view: newView }, '', path)
    setView(newView)
  }, [])

  const handleGoHome = useCallback(() => {
    navigateTo('landing', '/')
  }, [navigateTo])

  const handleViewRecap = useCallback(() => {
    navigateTo('recap', '/recap')
  }, [navigateTo])

  const handleStartOrder = useCallback(() => {
    navigateTo('order', '/order')
  }, [navigateTo])

  return (
    <MenuProvider>
      {view === 'landing' && (
        <LandingPage
          onStart={handleStartOrder}
          onViewRecap={handleViewRecap}
        />
      )}

      {view === 'order' && (
        <OrderPage />
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
