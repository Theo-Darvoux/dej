import './MenuCard.css'

type MenuCardProps = {
  title: string
  subtitle: string
  tag?: string
  accent?: string
  price: string
  remaining_quantity?: number
  low_stock_threshold?: number
  onAdd: () => void
}

const MenuCard = ({ title, subtitle, tag, accent, price, remaining_quantity, low_stock_threshold, onAdd }: MenuCardProps) => {
  const isOutOfStock = remaining_quantity === 0;
  const isLowStock = remaining_quantity !== undefined && low_stock_threshold !== undefined && remaining_quantity <= low_stock_threshold && remaining_quantity > 0;

  return (
    <article className={`menu-card ${isOutOfStock ? 'menu-card--disabled' : ''}`} style={{ opacity: isOutOfStock ? 0.6 : 1, filter: isOutOfStock ? 'grayscale(1)' : 'none' }}>
      <div className="menu-card__thumb" aria-hidden>
        <div className="menu-card__glow" style={{ background: accent }} />
        <div className="menu-card__plate">🍟</div>
        {isOutOfStock && <div style={{ position: 'absolute', top: 0, left: 0, right: 0, bottom: 0, background: 'rgba(0,0,0,0.5)', color: 'white', display: 'flex', alignItems: 'center', justifyContent: 'center', fontWeight: 'bold' }}>ÉPUISÉ</div>}
      </div>
      <div className="menu-card__body">
        <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
          {tag ? (
            <span className="menu-card__tag" style={{ color: accent, backgroundColor: `${accent}14` }}>
              {tag}
            </span>
          ) : null}
          {isLowStock && (
            <span className="menu-card__tag" style={{ color: '#d97706', backgroundColor: '#fffbeb', border: '1px solid #d97706' }}>
              Plus que {remaining_quantity} !
            </span>
          )}
        </div>
        <h3>{title}</h3>
        <p>{subtitle}</p>
        <div className="menu-card__footer">
          <span className="menu-card__price">{price}</span>
          <button className="menu-card__add" onClick={onAdd} disabled={isOutOfStock}>
            {isOutOfStock ? 'Épuisé' : 'Ajouter'}
          </button>
        </div>
      </div>
    </article>
  )
}

export default MenuCard
