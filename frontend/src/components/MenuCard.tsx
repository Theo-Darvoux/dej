import './MenuCard.css'

type MenuCardProps = {
  title: string
  subtitle: string
  tag?: string
  accent?: string
  price: string
  onAdd: () => void
}

const MenuCard = ({ title, subtitle, tag, accent, price, onAdd }: MenuCardProps) => {
  return (
    <article className="menu-card">
      <div className="menu-card__thumb" aria-hidden>
        <div className="menu-card__glow" style={{ background: accent }} />
        <div className="menu-card__plate">🍟</div>
      </div>
      <div className="menu-card__body">
        {tag ? (
          <span className="menu-card__tag" style={{ color: accent, backgroundColor: `${accent}14` }}>
            {tag}
          </span>
        ) : null}
        <h3>{title}</h3>
        <p>{subtitle}</p>
        <div className="menu-card__footer">
          <span className="menu-card__price">{price}</span>
          <button className="menu-card__add" onClick={onAdd}>
            Ajouter
          </button>
        </div>
      </div>
    </article>
  )
}

export default MenuCard
