import './CartBar.css'

type CartBarProps = {
    itemCount: number
    total: string
    onCheckout: () => void
}

const CartBar = ({ itemCount, total, onCheckout }: CartBarProps) => {
    const isEmpty = itemCount === 0

    return (
        <div className={`cart-bar ${isEmpty ? 'cart-bar--hidden' : ''}`}>
            <div className="cart-bar__info">
                <div className="cart-bar__icon">
                    🛒
                    {itemCount > 0 && (
                        <span className="cart-bar__badge">{itemCount}</span>
                    )}
                </div>
                <div className="cart-bar__details">
                    <span className="cart-bar__count">
                        {itemCount} article{itemCount !== 1 ? 's' : ''}
                    </span>
                    <span className="cart-bar__total">{total}</span>
                </div>
            </div>

            <button
                className="cart-bar__btn"
                onClick={onCheckout}
                disabled={isEmpty}
            >
                Commander
            </button>
        </div>
    )
}

export default CartBar
