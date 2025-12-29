import './Sidebar.css'

type Category = {
  id: string
  title: string
}

type SidebarProps = {
  categories: Category[]
  selectedId: string
  onSelect: (id: string) => void
}

const Sidebar = ({ categories, selectedId, onSelect }: SidebarProps) => {
  return (
    <aside className="sidebar">
      <div className="sidebar__logo">🍔</div>
      <nav className="sidebar__nav">
        {categories.map((category) => {
          const isActive = category.id === selectedId
          return (
            <button
              key={category.id}
              className={`sidebar__item ${isActive ? 'is-active' : ''}`}
              onClick={() => onSelect(category.id)}
            >
              <span className="sidebar__dot" aria-hidden />
              <span className="sidebar__label">{category.title}</span>
            </button>
          )
        })}
      </nav>
    </aside>
  )
}

export default Sidebar
