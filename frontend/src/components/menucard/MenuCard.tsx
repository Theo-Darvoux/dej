import './MenuCard.css'

type MenuCardProps = {
  title: string
  subtitle: string
  tag?: string
  accent?: string
  price: string
  image?: string
  remaining_quantity?: number
  low_stock_threshold?: number
  onAdd: () => void
}

// Get emoji based on title keywords
const getProductEmoji = (title: string): string => {
  const lower = title.toLowerCase()
  if (lower.includes('burger') || lower.includes('big mac') || lower.includes('mcroyal')) return '🍔'
  if (lower.includes('frite') || lower.includes('potatoes')) return '🍟'
  if (lower.includes('nugget') || lower.includes('mcnugget')) return '🍗'
  if (lower.includes('wrap') || lower.includes('mcwrap')) return '🌯'
  if (lower.includes('salade') || lower.includes('salad')) return '🥗'
  if (lower.includes('glace') || lower.includes('mcflurry') || lower.includes('sundae')) return '🍦'
  if (lower.includes('coca') || lower.includes('fanta') || lower.includes('sprite') || lower.includes('boisson')) return '🥤'
  if (lower.includes('café') || lower.includes('coffee') || lower.includes('cappuccino')) return '☕'
  if (lower.includes('petit') || lower.includes('breakfast') || lower.includes('mcmuffin')) return '🥞'
  if (lower.includes('happy') || lower.includes('meal')) return '🎁'
  if (lower.includes('filet') || lower.includes('fish')) return '🐟'
  if (lower.includes('poulet') || lower.includes('chicken') || lower.includes('mcchicken')) return '🍗'
  return '🍔'
}

const MenuCard = ({
  title,
  subtitle,
  tag,
  price,
  image,
  remaining_quantity,
  low_stock_threshold,
  onAdd
}: MenuCardProps) => {
  const isOutOfStock = remaining_quantity === 0
  const isLowStock = remaining_quantity !== undefined &&
    low_stock_threshold !== undefined &&
    remaining_quantity <= low_stock_threshold &&
    remaining_quantity > 0

  const emoji = getProductEmoji(title)

  return (
    <article className={`menu-card ${isOutOfStock ? 'menu-card--disabled' : ''}`}>
      <div className="menu-card__image">
        {image ? (
          <img src={image} alt={title} />
        ) : (
          <span className="menu-card__image-emoji">{emoji}</span>
        )}

        {tag && (
          <span className="menu-card__badge">{tag}</span>
        )}

        {isLowStock && (
          <span className="menu-card__badge menu-card__badge--warning">
            Plus que {remaining_quantity}!
          </span>
        )}

        {isOutOfStock && (
          <div className="menu-card__out-of-stock">Épuisé</div>
        )}
      </div>

      <div className="menu-card__content">
        <h3 className="menu-card__title">{title}</h3>
        <p className="menu-card__subtitle">{subtitle}</p>

        <div className="menu-card__footer">
          <span className="menu-card__price">{price}</span>
          <button
            className="menu-card__btn"
            onClick={onAdd}
            disabled={isOutOfStock}
          >
            {isOutOfStock ? 'Épuisé' : 'Choisir'}
          </button>
        </div>
      </div>
    </article>
  )
}

export default MenuCard
