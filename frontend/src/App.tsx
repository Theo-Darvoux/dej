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
    { title: 'Menu Golden Ligue 1 McDonald’s', subtitle: 'Petit dej', tag: 'Signature', accent: '#f59e0b' },
    { title: 'Menu Duo Golden Ligue 1 McDonald’s', subtitle: 'Petit dej', tag: 'Duo', accent: '#6366f1' },
  ],
  moment: [
    { title: 'Menu Golden Ligue 1 McDonald’s', subtitle: 'Petit dej', tag: 'En vedette', accent: '#0ea5e9' },
    { title: 'Menu Happy Doggy', subtitle: 'Petit dej', tag: 'Nouveau', accent: '#22c55e' },
  ],
  absinthe: [
    { title: 'Spcecial Absinthe', subtitle: 'Biere', tag: 'Edition limitée', accent: '#16a34a' },
    { title: 'Absinthe Twist', subtitle: 'Biere', tag: 'Mix', accent: '#10b981' },
  ],
  poulet: [
    { title: 'scpecial poulet', subtitle: 'Poulet', tag: 'Croustillant', accent: '#ef4444' },
    { title: 'Poulet Grillé', subtitle: 'Poulet', tag: 'Grill', accent: '#f97316' },
  ],
}

const cartItems: CartItem[] = [
  { title: 'Menu Golden Ligue 1', price: '12,90 €' },
  { title: 'Menu Duo Golden', price: '19,50 €' },
  { title: 'Spcecial Absinthe', price: '6,00 €' },
]

function App() {
  const [selectedCategoryId, setSelectedCategoryId] = useState<string>(categories[0].id)

  const currentCategory = useMemo(
    () => categories.find((c) => c.id === selectedCategoryId) ?? categories[0],
    [selectedCategoryId],
  )

  const currentMenus = menuByCategory[currentCategory.id] ?? []

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
                />
              ))}
            </div>
          </main>
        </div>
      </Borne>
    </div>
  )
}

export default App
