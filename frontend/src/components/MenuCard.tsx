import './MenuCard.css'

type MenuCardProps = {
  title: string
  subtitle: string
  tag?: string
  accent?: string
}

const MenuCard = ({ title, subtitle, tag, accent }: MenuCardProps) => {
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
      </div>
    </article>
  )
}

export default MenuCard
