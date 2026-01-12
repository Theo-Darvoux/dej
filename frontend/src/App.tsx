import { useMemo, useState, useEffect } from 'react'
import './App.css'
import Sidebar from './components/sidebar/Sidebar'
import Borne from './components/borne/Borne'
import MenuCard from './components/menucard/MenuCard'
import RequestPopup from './components/popup/1request/RequestPopup'
import CodePopup from './components/popup/2code/CodePopup'
import AptPopup from './components/popup/3apartment/AptPopup'
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
  item_type?: string
}

type CartItem = {
  id?: number
  title: string
  price: string
}

type ReservationData = {
  date_reservation: string
  heure_reservation: string
  habite_residence: boolean
  numero_chambre?: string
  numero_immeuble?: string
  adresse?: string
  phone: string
  menu_id?: number
  boisson_id?: number
  bonus_id?: number
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
  const [apiStatus, setApiStatus] = useState<string>('Vérification...')
  const [currentEmail, setCurrentEmail] = useState('')
  
  // États pour stocker les données de réservation
  const [reservationData, setReservationData] = useState<Partial<ReservationData>>({})
  const [menuId, setMenuId] = useState<number | undefined>(undefined)
  const [boissonId, setBoissonId] = useState<number | undefined>(undefined)
  const [bonusId, setBonusId] = useState<number | undefined>(undefined)

  // Test connexion API
  useEffect(() => {
    const testApi = async () => {
      try {
        const response = await fetch('/api/menu/categories')
        if (response.ok) {
          setApiStatus('✅ API OK')
        } else {
          setApiStatus(`❌ API Erreur ${response.status}`)
        }
      } catch (error) {
        setApiStatus('❌ API Indisponible')
        console.error('API Error:', error)
      }
    }
    testApi()
  }, [])

  // Fetch categories au chargement
  useEffect(() => {
    const fetchCategories = async () => {
      try {
        const response = await fetch('/api/menu/categories')
        if (!response.ok) {
          const text = await response.text()
          throw new Error(`HTTP ${response.status}: ${text}`)
        }
        const data = await response.json()
        console.log('Categories reçues:', data)
        let list: Category[] = Array.isArray(data)
          ? data
          : Array.isArray((data as any)?.categories)
          ? (data as any).categories
          : []

        // Si vide, utilise des données de test
        if (list.length === 0) {
          console.log('⚠️ Aucune catégorie du backend, utilisation des données de test')
          list = [
            { id: '1', title: 'Burgers' },
            { id: '2', title: 'Pizzas' },
            { id: '3', title: 'Desserts' },
          ]
        }

        console.log('Categories après parse:', list)
        setCategories(list)
        if (list.length > 0) {
          setSelectedCategoryId(list[0].id)
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
        const categoryIdNum = Number(selectedCategoryId)
        const url = isNaN(categoryIdNum)
          ? `/api/menu/items`
          : `/api/menu/items?category_id=${categoryIdNum}`

        console.log('Fetching items from:', url)
        const response = await fetch(url)
        if (!response.ok) {
          const text = await response.text()
          throw new Error(`HTTP ${response.status}: ${text}`)
        }
        const data = await response.json()
        console.log('Items reçus:', data)
        let items: MenuItem[] = Array.isArray(data)
          ? data
          : Array.isArray((data as any)?.items)
          ? (data as any).items
          : []

        // Si vide, utilise des données de test
        if (items.length === 0) {
          console.log('⚠️ Aucun item du backend, utilisation des données de test')
          items = [
            { id: 1, title: 'Burger Classique', subtitle: 'Boeuf haché', price: '12,50 €' },
            { id: 2, title: 'Burger Déluxe', subtitle: 'Double boeuf', price: '15,00 €' },
            { id: 3, title: 'Burger Végétal', subtitle: 'Patty végétale', price: '11,00 €' },
          ]
        }

        console.log('Items après parse:', items)
        setMenuByCategory((prev) => ({
          ...prev,
          [selectedCategoryId]: items,
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
    
    // Stocker les IDs selon le type
    if (item.item_type === 'menu' && item.id) setMenuId(item.id)
    if (item.item_type === 'boisson' && item.id) setBoissonId(item.id)
    if (item.item_type === 'bonus' && item.id) setBonusId(item.id)
  }

  const handleRemoveFromCart = (index: number) => {
    setCartItems((prev) => prev.filter((_, idx) => idx !== index))
  }


   return (
    <div className="page">
      <div style={{ position: 'absolute', top: '10px', left: '10px', fontSize: '12px', color: '#333', zIndex: 1000, background: '#fff', padding: '5px 10px', border: '1px solid #ccc' }}>
        <div>{apiStatus}</div>
        <div>Categories: {categories.length}</div>
        <div>Items: {currentMenus.length}</div>
      </div>
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
                  onAdd={() => {
                    handleAddToCart(item)
                  }}
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
            onRequestCode={(email) => {
              console.log('Email reçu:', email)
              setCurrentEmail(email)
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
            email={currentEmail}
          />
          <AptPopup
            open={isAptOpen}
            onClose={() => setIsAptOpen(false)}
            onContinue={(aptData) => {
              // Stocker les données d'appartement
              setReservationData((prev) => ({
                ...prev,
                habite_residence: aptData.habite_residence,
                numero_chambre: aptData.numero_chambre,
                numero_immeuble: aptData.numero_immeuble,
                adresse: aptData.adresse,
              }))
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
              setCurrentEmail('')
              setReservationData({})
              setMenuId(undefined)
              setBoissonId(undefined)
              setBonusId(undefined)
            }}
            onReservationDataChange={(data) => {
              // Stocker les données de réservation (date, heure, phone)
              setReservationData((prev) => ({ ...prev, ...data }))
            }}
            reservationData={{
              ...reservationData,
              menu_id: menuId,
              boisson_id: boissonId,
              bonus_id: bonusId,
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
