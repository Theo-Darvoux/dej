import { useMemo, useState } from 'react'
import './App.css'
import Sidebar from './components/Sidebar'
import Borne from './components/Borne'
import MenuCard from './components/MenuCard'

type Category = {
  id: string
  title: string
}

type MenuItem = {
  title: string
  subtitle: string
  tag?: string
  accent?: string
  price: string
}

type CartItem = {
  title: string
  price: string
}

const categories: Category[] = [
  { id: 'offres', title: 'Les offres' },
  { id: 'moment', title: 'En ce moment' },
  { id: 'absinthe', title: 'Spcecial Absinthe' },
  { id: 'poulet', title: 'scpecial poulet' },
]

const menuByCategory: Record<string, MenuItem[]> = {
  offres: [
    { title: 'Menu Golden Ligue 1 McDonald’s', subtitle: 'Petit dej', tag: 'Signature', accent: '#f59e0b', price: '12,90 €' },
    { title: 'Menu Duo Golden Ligue 1 McDonald’s', subtitle: 'Petit dej', tag: 'Duo', accent: '#6366f1', price: '19,50 €' },
  ],
  moment: [
    { title: 'Menu Golden Ligue 1 McDonald’s', subtitle: 'Petit dej', tag: 'En vedette', accent: '#0ea5e9', price: '12,90 €' },
    { title: 'Menu Happy Doggy', subtitle: 'Petit dej', tag: 'Nouveau', accent: '#22c55e', price: '9,40 €' },
  ],
  absinthe: [
    { title: 'Spcecial Absinthe', subtitle: 'Biere', tag: 'Edition limitée', accent: '#16a34a', price: '6,00 €' },
    { title: 'Absinthe Twist', subtitle: 'Biere', tag: 'Mix', accent: '#10b981', price: '6,50 €' },
  ],
  poulet: [
    { title: 'scpecial poulet', subtitle: 'Poulet', tag: 'Croustillant', accent: '#ef4444', price: '10,90 €' },
    { title: 'Poulet Grillé', subtitle: 'Poulet', tag: 'Grill', accent: '#f97316', price: '9,90 €' },
  ],
}

function App() {
  const [selectedCategoryId, setSelectedCategoryId] = useState<string>(categories[0].id)
  const [cartItems, setCartItems] = useState<CartItem[]>([])

  const currentCategory = useMemo(
    () => categories.find((c) => c.id === selectedCategoryId) ?? categories[0],
    [selectedCategoryId],
  )

  const currentMenus = menuByCategory[currentCategory.id] ?? []

  const handleAddToCart = (item: MenuItem) => {
    setCartItems((prev) => [...prev, { title: item.title, price: item.price }])
  }

  const handleRemoveFromCart = (index: number) => {
    setCartItems((prev) => prev.filter((_, idx) => idx !== index))
  }

  return (
    <div className="page">
      <Borne>
        <div className="screen-layout">
          <Sidebar categories={categories} selectedId={currentCategory.id} onSelect={setSelectedCategoryId} />

          <main className="screen-content">
            <header className="content__header">
              <p className="eyebrow">Mes offres</p>
              <h1 className="title">{currentCategory.title}</h1>
            </header>

            <div className="menu-grid">
              {currentMenus.map((item) => (
                <MenuCard
                  key={item.title}
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
                    <div key={`${item.title}-${idx}`} className="cart__row">
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
                <button className="cart__cta">Commander</button>
              </div>
            </div>
          </main>
        </div>
      </Borne>
    </div>
  )
}

export default App
