import { useState } from 'react'
import LandingPage from './components/landing/LandingPage'
import OrderPage from './components/order/OrderPage'
import './App.css'

type ViewState = 'landing' | 'order'

function App() {
  const [view, setView] = useState<ViewState>('landing')

  return (
    <>
      {view === 'landing' && (
        <LandingPage onStart={() => setView('order')} />
      )}

      {view === 'order' && (
        <OrderPage onBackToHome={() => setView('landing')} />
      )}
    </>
  )
}

export default App
