import { useMemo, useState, useEffect } from 'react'
import CategorySlider from '../category-slider/CategorySlider'
import MenuCard from '../menucard/MenuCard'
import CartBar from '../cart-bar/CartBar'
import RequestPopup from '../popup/1request/RequestPopup'
import CodePopup from '../popup/2code/CodePopup'
import AptPopup from '../popup/3apartment/AptPopup'
import InfoPopup from '../popup/info/InfoPopup'
import './OrderPage.css'

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
    image?: string
    item_type?: string
    remaining_quantity?: number
    low_stock_threshold?: number
}

type CartItem = {
    id?: number
    title: string
    price: string
    item_type?: string
    category_id?: string
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

type OrderPageProps = {
    onBackToHome: () => void
}

// Groupes de catégories mutuellement exclusives
// On ne peut prendre qu'UN SEUL item parmi toutes les catégories d'un groupe
// Pour ajouter une catégorie au groupe menu, ajouter son nom ici (ex: "VIEUX")
const EXCLUSIVE_CATEGORY_GROUPS: string[][] = [
    ["BOULANGER'INT", "LE GRAS C'EST LA VIE", "EXOT'INT"], // Menus principaux
    // Ajouter d'autres groupes ici si nécessaire
]

const OrderPage = ({ onBackToHome }: OrderPageProps) => {
    const [categories, setCategories] = useState<Category[]>([])
    const [menuByCategory, setMenuByCategory] = useState<Record<string, MenuItem[]>>({})
    const [selectedCategoryId, setSelectedCategoryId] = useState<string>('')
    const [cartItems, setCartItems] = useState<CartItem[]>([])
    const [isRequestOpen, setIsRequestOpen] = useState(false)
    const [isCodeOpen, setIsCodeOpen] = useState(false)
    const [isAptOpen, setIsAptOpen] = useState(false)
    const [isInfoOpen, setIsInfoOpen] = useState(false)
    const [currentEmail, setCurrentEmail] = useState('')
    const [hasToken, setHasToken] = useState(false)
    const [toast, setToast] = useState<{ message: string; visible: boolean }>({ message: '', visible: false })

    const [reservationData, setReservationData] = useState<Partial<ReservationData>>({})
    const [menuId, setMenuId] = useState<number | undefined>(undefined)
    const [boissonId, setBoissonId] = useState<number | undefined>(undefined)
    const [bonusId, setBonusId] = useState<number | undefined>(undefined)

    // Toast helper
    const showToast = (message: string) => {
        setToast({ message, visible: true })
        setTimeout(() => setToast({ message: '', visible: false }), 3000)
    }

    // Check for token on mount
    useEffect(() => {
        const checkToken = () => {
            const hasAccessToken = document.cookie.includes('access_token=')
            setHasToken(hasAccessToken)
        }
        checkToken()
    }, [])

    // Fetch categories
    useEffect(() => {
        const fetchCategories = async () => {
            try {
                const response = await fetch('/api/menu/categories')
                if (!response.ok) throw new Error(`HTTP ${response.status}`)
                const data = await response.json()
                let list: Category[] = Array.isArray(data)
                    ? data
                    : Array.isArray((data as any)?.categories)
                        ? (data as any).categories
                        : []

                setCategories(list)
                if (list.length > 0) {
                    setSelectedCategoryId(list[0].id)
                }
            } catch (error) {
                console.error('Erreur catégories:', error)
            }
        }
        fetchCategories()
    }, [])

    // Fetch items when category changes
    useEffect(() => {
        if (!selectedCategoryId) return

        const fetchMenuItems = async () => {
            try {
                const categoryIdNum = Number(selectedCategoryId)
                const url = isNaN(categoryIdNum)
                    ? `/api/menu/items`
                    : `/api/menu/items?category_id=${categoryIdNum}`

                const response = await fetch(url)
                if (!response.ok) throw new Error(`HTTP ${response.status}`)
                const data = await response.json()
                let items: MenuItem[] = Array.isArray(data)
                    ? data
                    : Array.isArray((data as any)?.items)
                        ? (data as any).items
                        : []

                setMenuByCategory((prev) => ({
                    ...prev,
                    [selectedCategoryId]: items,
                }))
            } catch (error) {
                console.error('Erreur items:', error)
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
        const itemType = item.item_type || 'menu'
        const categoryId = selectedCategoryId
        const categoryName = currentCategory?.title || ''

        // Vérifier si la catégorie appartient à un groupe exclusif
        const exclusiveGroup = EXCLUSIVE_CATEGORY_GROUPS.find(group =>
            group.includes(categoryName)
        )

        if (exclusiveGroup) {
            // Vérifier si on a déjà un item d'une catégorie du même groupe
            const existingFromGroup = cartItems.find(ci => {
                const ciCategoryName = categories.find(c => c.id === ci.category_id)?.title || ''
                return exclusiveGroup.includes(ciCategoryName)
            })

            if (existingFromGroup) {
                showToast(`Vous avez déjà un menu - un seul choix parmi les formules`)
                return
            }
        } else {
            // Catégorie normale: vérifier si on a déjà un item de la même catégorie
            const hasSameCategory = cartItems.some(ci => ci.category_id === categoryId)

            if (hasSameCategory) {
                showToast(`Vous avez déjà un article de ${categoryName}`)
                return
            }
        }

        setCartItems((prev) => {
            return [...prev, {
                id: item.id,
                title: item.title,
                price: item.price,
                item_type: itemType,
                category_id: categoryId
            }]
        })

        if (item.item_type === 'menu' && item.id) setMenuId(item.id)
        if (item.item_type === 'boisson' && item.id) setBoissonId(item.id)
        if (item.item_type === 'upsell' && item.id) setBonusId(item.id)
    }

    const handleRemoveFromCart = (index: number) => {
        const removedItem = cartItems[index]
        setCartItems((prev) => prev.filter((_, idx) => idx !== index))

        // Réinitialiser l'ID correspondant
        if (removedItem?.item_type === 'menu') setMenuId(undefined)
        if (removedItem?.item_type === 'boisson') setBoissonId(undefined)
        if (removedItem?.item_type === 'upsell') setBonusId(undefined)
    }

    const handleCheckout = () => {
        setIsRequestOpen(true)
    }

    const handleLogout = async () => {
        try {
            await fetch('/api/auth/logout', { method: 'POST' })
            onBackToHome()
        } catch (error) {
            console.error('Logout failed:', error)
            onBackToHome() // Fallback
        }
    }

    return (
        <div className="order-page">
            {/* Toast Notification */}
            {toast.visible && (
                <div className="order-toast">
                    <span className="order-toast__icon">⚠️</span>
                    <span className="order-toast__message">{toast.message}</span>
                </div>
            )}

            {/* Header */}
            <header className="order-header">
                <button className="order-header__back" onClick={onBackToHome} aria-label="Retour">
                    ←
                </button>
                <div className="order-header__title">
                    <h1>Mc-INT</h1>
                    <p>Commande à emporter</p>
                </div>
                <div className="order-header__logo">🍟</div>
                {hasToken && (
                    <button className="order-header__logout" onClick={handleLogout} aria-label="Déconnexion">
                        Déconnexion
                    </button>
                )}
            </header>

            {/* Main Layout */}
            <div className="order-layout">
                {/* Category Slider (horizontal on mobile, vertical on desktop) */}
                <CategorySlider
                    categories={categories}
                    selectedId={selectedCategoryId}
                    onSelect={setSelectedCategoryId}
                />

                {/* Content */}
                <main className="order-content">
                    {/* Section Header */}
                    <div className="order-section">
                        <p className="order-section__eyebrow">Nos produits</p>
                        <h2 className="order-section__title">
                            {currentCategory?.title || 'Chargement...'}
                        </h2>
                    </div>

                    {/* Menu Grid */}
                    <div className="order-grid">
                        <div className="order-grid__container">
                            {currentMenus.length === 0 ? (
                                <div style={{ gridColumn: '1 / -1', textAlign: 'center', padding: '40px 20px', color: '#757575' }}>
                                    <p style={{ fontSize: '48px', marginBottom: '16px' }}>🍔</p>
                                    <p style={{ fontWeight: '600' }}>Chargement des produits...</p>
                                    <p style={{ fontSize: '0.85rem' }}>Catégorie: {currentCategory?.title || 'Aucune'}</p>
                                </div>
                            ) : (
                                currentMenus.map((item, idx) => (
                                    <MenuCard
                                        key={`${item.id}-${idx}`}
                                        title={item.title}
                                        subtitle={item.subtitle}
                                        tag={item.tag}
                                        price={item.price}
                                        image={item.image}
                                        remaining_quantity={item.remaining_quantity}
                                        low_stock_threshold={item.low_stock_threshold}
                                        onAdd={() => handleAddToCart(item)}
                                    />
                                ))
                            )}
                        </div>
                    </div>
                </main>

                {/* Desktop Cart Sidebar */}
                <aside className="order-cart">
                    <div className="order-cart__header">
                        <span>Mon panier</span>
                        <span>{cartItems.length} article{cartItems.length !== 1 ? 's' : ''}</span>
                    </div>

                    <div className="order-cart__list">
                        {cartItems.length === 0 ? (
                            <div className="order-cart__empty">
                                <p>🛒</p>
                                <p>Votre panier est vide</p>
                            </div>
                        ) : (
                            cartItems.map((item, idx) => (
                                <div key={`${item.id}-${idx}`} className="order-cart__item">
                                    <div className="order-cart__item-info">
                                        <div className="order-cart__item-title">{item.title}</div>
                                        <div className="order-cart__item-price">{item.price}</div>
                                    </div>
                                    <button
                                        className="order-cart__item-remove"
                                        onClick={() => handleRemoveFromCart(idx)}
                                        aria-label={`Retirer ${item.title}`}
                                    >
                                        −
                                    </button>
                                </div>
                            ))
                        )}
                    </div>

                    <div className="order-cart__footer">
                        <div className="order-cart__total">
                            <span>Total</span>
                            <span>{totalAmount}</span>
                        </div>
                        <button
                            className="order-cart__btn"
                            onClick={handleCheckout}
                            disabled={cartItems.length === 0}
                        >
                            Commander
                        </button>
                    </div>
                </aside>
            </div>

            {/* Mobile Cart Bar */}
            <CartBar
                itemCount={cartItems.length}
                total={totalAmount}
                onCheckout={handleCheckout}
            />

            {/* Checkout Popups */}
            <RequestPopup
                open={isRequestOpen}
                onClose={() => setIsRequestOpen(false)}
                onRequestCode={(email) => {
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
                    onBackToHome()
                }}
                onReservationDataChange={(data) => {
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
    )
}

export default OrderPage
