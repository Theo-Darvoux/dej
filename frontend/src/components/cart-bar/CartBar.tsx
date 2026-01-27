import { useState } from 'react'
import './CartBar.css'

type CartItem = {
    id?: number
    title: string
    price: string
}

type CartBarProps = {
    itemCount: number
    total: string
    items: CartItem[]
    onCheckout: () => void
    onRemoveItem: (index: number) => void
}

const CartBar = ({ itemCount, total, items, onCheckout, onRemoveItem }: CartBarProps) => {
    const [isOpen, setIsOpen] = useState(false)
    const isEmpty = itemCount === 0

    return (
        <>
            {/* Overlay */}
            {isOpen && (
                <div className="cart-drawer__overlay" onClick={() => setIsOpen(false)} />
            )}

            {/* Drawer */}
            <div className={`cart-drawer ${isOpen ? 'cart-drawer--open' : ''}`}>
                <div className="cart-drawer__header">
                    <h3>🛒 Mon panier</h3>
                    <button className="cart-drawer__close" onClick={() => setIsOpen(false)}>×</button>
                </div>

                <div className="cart-drawer__content">
                    {items.length === 0 ? (
                        <div className="cart-drawer__empty">
                            <p>🛒</p>
                            <p>Ton panier est vide</p>
                        </div>
                    ) : (
                        items.map((item, idx) => (
                            <div key={`${item.id}-${idx}`} className="cart-drawer__item">
                                <div className="cart-drawer__item-info">
                                    <span className="cart-drawer__item-title">{item.title}</span>
                                    <span className="cart-drawer__item-price">{item.price}</span>
                                </div>
                                <button
                                    className="cart-drawer__item-remove"
                                    onClick={() => onRemoveItem(idx)}
                                >
                                    −
                                </button>
                            </div>
                        ))
                    )}
                </div>

                <div className="cart-drawer__footer">
                    <div className="cart-drawer__total">
                        <span>Total</span>
                        <span>{total}</span>
                    </div>
                    <button
                        className="cart-drawer__btn"
                        onClick={() => {
                            setIsOpen(false)
                            onCheckout()
                        }}
                        disabled={isEmpty}
                    >
                        Commander
                    </button>
                </div>
            </div>

            {/* Bottom Bar */}
            <div className={`cart-bar ${isEmpty ? 'cart-bar--hidden' : ''}`}>
                <div className="cart-bar__info" onClick={() => setIsOpen(true)}>
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
        </>
    )
}

export default CartBar
