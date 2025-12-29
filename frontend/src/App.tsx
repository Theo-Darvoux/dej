import { useMemo, useState, useEffect } from 'react'
import './App.css'
import Sidebar from './components/sidebar/Sidebar'
import Borne from './components/borne/Borne'
import MenuCard from './components/menucard/MenuCard'
import RequestPopup from './components/popup/request/RequestPopup'
import CodePopup from './components/popup/code/CodePopup'
import AptPopup from './components/popup/apartment/AptPopup'
import InfoPopup from './components/popup/info/InfoPopup'

type Category = {
  id: string
  title: string
}

type MenuItem = {
  id?: number
  title: string
  subtitle: string
  tag?: string
  accent?: string
  price: string
}

type CartItem = {
  id?: number
  title: string
  price: string
}

function App() {
  const [categories, setCategories] = useState<Category[]>([])
  const [menuByCategory, setMenuByCategory] = useState<Record<string, MenuItem[]>>({})
  const [selectedCategoryId, setSelectedCategoryId] = useState<string>('')
  const [cartItems, setCartItems] = useState<CartItem[]>([])
  const [isRequestOpen, setIsRequestOpen] = useState(false)
  const [isCodeOpen, setIsCodeOpen] = useState(false)
  const [isAptOpen, setIsAptOpen] = useState(false)
  const [isInfoOpen, setIsInfoOpen] = useState(false)

  // Fetch categories au chargement
  useEffect(() => {
    const fetchCategories = async () => {
      try {
        const response = await fetch('/api/menu/categories')
        const data = await response.json()
        setCategories(data)
        if (data.length > 0) {
          setSelectedCategoryId(data[0].id)
        }
      } catch (error) {
        console.error('Erreur lors du chargement des catégories:', error)
      }
    }
    fetchCategories()
  }, [])

  // Fetch items quand la catégorie change
  useEffect(() => {
    if (!selectedCategoryId) return

    const fetchMenuItems = async () => {
      try {
        const response = await fetch(`/api/menu/items?category_id=${selectedCategoryId}`)
        const data = await response.json()
        setMenuByCategory((prev) => ({
          ...prev,
          [selectedCategoryId]: data,
        }))
      } catch (error) {
        console.error('Erreur lors du chargement des items:', error)
      }
    }
    fetchMenuItems()
  }, [selectedCategoryId])

  const currentCategory = useMemo(
    () => categories.find((c) => c.id === selectedCategoryId) ?? categories[0],
    [categories, selectedCategoryId],
  )

  const currentMenus = menuByCategory[selectedCategoryId] ?? []

  const totalAmount = useMemo(() => {
    const sum = cartItems.reduce((acc, item) => {
      const price = parseFloat(item.price.replace(',', '.').replace(' €', ''))
      return acc + price
    }, 0)
    return sum.toFixed(2).replace('.', ',') + ' €'
  }, [cartItems])

  const handleAddToCart = (item: MenuItem) => {
    setCartItems((prev) => {
      if (prev.length >= 3) return prev
      return [...prev, { id: item.id, title: item.title, price: item.price }]
    })
  }

  const handleRemoveFromCart = (index: number) => {
    setCartItems((prev) => prev.filter((_, idx) => idx !== index))
  }

  return (
    <div className="page">
      <Borne>
        <div className="screen-layout">
          <Sidebar categories={categories} selectedId={currentCategory?.id || ''} onSelect={setSelectedCategoryId} />

          <main className="screen-content">
            <header className="content__header">
              <p className="eyebrow">Mes offres</p>
              <h1 className="title">{currentCategory?.title || 'Chargement...'}</h1>
            </header>

            <div className="menu-grid">
              {currentMenus.map((item, idx) => (
                <MenuCard
                  key={`${item.id}-${idx}`}
                  title={item.title}
                  subtitle={item.subtitle}
                  tag={item.tag}
                  accent={item.accent}
                  price={item.price}
                  onAdd={() => handleAddToCart(item)}
                />
              ))}
            </div>

            <div className="cart">
              <div className="cart__header">
                <span>Panier</span>
                <span>{cartItems.length} articles</span>
              </div>
              <div className="cart__list">
                {cartItems.length === 0 ? (
                  <div className="cart__empty">Aucun article dans le panier</div>
                ) : (
                  cartItems.map((item, idx) => (
                    <div key={`${item.id}-${idx}`} className="cart__row">
                      <span className="cart__title">{item.title}</span>
                      <div className="cart__actions">
                        <span className="cart__price">{item.price}</span>
                        <button
                          className="cart__remove"
                          aria-label={`Retirer ${item.title}`}
                          onClick={() => handleRemoveFromCart(idx)}
                        >
                          –
                        </button>
                      </div>
                    </div>
                  ))
                )}
              </div>
              <div className="cart__footer">
                <button
                  className="cart__cta"
                  onClick={() => setIsRequestOpen(true)}
                  disabled={cartItems.length === 0}
                >
                  Commander
                </button>
              </div>
            </div>
          </main>
          <RequestPopup
            open={isRequestOpen}
            onClose={() => setIsRequestOpen(false)}
            onRequestCode={() => {
              setIsRequestOpen(false)
              setIsCodeOpen(true)
            }}
            step={1}
            total={4}
          />
          <CodePopup
            open={isCodeOpen}
            onClose={() => setIsCodeOpen(false)}
            onContinue={() => {
              setIsCodeOpen(false)
              setIsAptOpen(true)
            }}
            step={2}
            total={4}
          />
          <AptPopup
            open={isAptOpen}
            onClose={() => setIsAptOpen(false)}
            onContinue={() => {
              setIsAptOpen(false)
              setIsInfoOpen(true)
            }}
            step={3}
            total={4}
          />
          <InfoPopup
            open={isInfoOpen}
            onClose={() => setIsInfoOpen(false)}
            onPaymentSuccess={() => {
              setIsInfoOpen(false)
              alert('Paiement réussi ! Commande confirmée.')
              setCartItems([])
            }}
            step={4}
            total={4}
            amount={totalAmount}
          />
        </div>
      </Borne>
    </div>
  )
}

export default App
