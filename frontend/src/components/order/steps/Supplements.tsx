import { useState } from 'react'
import { useMenu, type MenuItem } from '../../../context/MenuContext'

type SupplementsProps = {
    initialSelectedItems?: MenuItem[]
    onBack: () => void
    onContinue: (selectedItems: MenuItem[]) => void
}

const Supplements = ({ initialSelectedItems = [], onBack, onContinue }: SupplementsProps) => {
    const { menuByCategory, categories } = useMenu()
    const [selectedSupplements, setSelectedSupplements] = useState<MenuItem[]>(initialSelectedItems)
    const [modalInfo, setModalInfo] = useState<{ show: boolean, message: string }>({ show: false, message: '' })
    const [pendingItem, setPendingItem] = useState<MenuItem | null>(null)

    // Find Drinks and Extras categories (case-insensitive matching)
    const drinkCategory = categories.find(c =>
        c.title.toLowerCase() === 'boissons' || c.title.toLowerCase() === 'boisson'
    )
    const extraCategory = categories.find(c =>
        c.title.toLowerCase() === 'extra' ||
        c.title.toLowerCase() === 'extras' ||
        c.title.toLowerCase() === 'option' ||
        c.title.toLowerCase() === 'options'
    )

    const drinks = drinkCategory ? (menuByCategory[drinkCategory.id] || []) : []
    const extras = extraCategory ? (menuByCategory[extraCategory.id] || []) : []

    // Check if item is a drink (not an extra like Chouffe)
    const isDrink = (item: MenuItem) => {
        return drinks.some(d => d.id === item.id)
    }

    // Get currently selected drink
    const selectedDrink = selectedSupplements.find(item => isDrink(item))

    const toggleItem = (item: MenuItem) => {
        const isSelected = selectedSupplements.some(i => i.id === item.id)

        if (isSelected) {
            setSelectedSupplements(prev => prev.filter(i => i.id !== item.id))
            return
        }

        // Adding - check conditions
        const name = item.title.toLowerCase()
        let conditionMsg = ""

        if (name.includes('chouffe')) {
            conditionMsg = "Condition requise : Être un ancien membre du club Absinthe.\n\nCette condition sera vérifiée par notre staff lors de la préparation."
        } else if (name.includes('poulet')) {
            conditionMsg = "Condition requise : Être un 3A+.\n\nCette condition sera vérifiée par notre staff lors de la préparation."
        }

        if (conditionMsg) {
            setPendingItem(item)
            setModalInfo({ show: true, message: conditionMsg })
        } else {
            if (isDrink(item)) {
                setSelectedSupplements(prev => {
                    const withoutDrinks = prev.filter(i => !isDrink(i))
                    return [...withoutDrinks, item]
                })
            } else {
                setSelectedSupplements(prev => [...prev, item])
            }
        }
    }

    const confirmModal = () => {
        if (pendingItem) {
            setSelectedSupplements(prev => [...prev, pendingItem])
        }
        closeModal()
    }

    const closeModal = () => {
        setModalInfo({ show: false, message: '' })
        setPendingItem(null)
    }

    return (
        <div className="supplements-step">
            <button className="supplements-step__back" onClick={onBack}>← Retour</button>
            <h2 className="supplements-step__title">Un petit supplément ?</h2>

            <div className="supplements-section">
                <h3 className="supplements-section__title">
                    <span className="supplements-section__icon">🥤</span>
                    Choisissez votre boisson gratuite
                    <span className="supplements-section__hint">(1 seule)</span>
                </h3>
                <div className="drinks-grid">
                    {/* No drink option */}
                    <div
                        className={`drink-card drink-card--none ${!selectedDrink ? 'selected' : ''}`}
                        onClick={() => setSelectedSupplements(prev => prev.filter(i => !isDrink(i)))}
                    >
                        <div className="drink-card__icon">🚫</div>
                        <span className="drink-card__name">Aucune</span>
                        <div className="drink-card__radio">
                            {!selectedDrink && <span className="drink-card__radio-dot"></span>}
                        </div>
                    </div>
                    {drinks.map(item => (
                        <div
                            key={item.id}
                            className={`drink-card ${selectedDrink?.id === item.id ? 'selected' : ''}`}
                            onClick={() => toggleItem(item)}
                        >
                            <div className="drink-card__icon">🥤</div>
                            <span className="drink-card__name">{item.title}</span>
                            {item.subtitle && <span className="drink-card__size">{item.subtitle}</span>}
                            <div className="drink-card__radio">
                                {selectedDrink?.id === item.id && <span className="drink-card__radio-dot"></span>}
                            </div>
                        </div>
                    ))}
                </div>
            </div>

            <div className="supplements-section">
                <h3>Extras</h3>
                <div className="supplements-grid">
                    {extras.map(item => {
                        const name = item.title.toLowerCase()
                        let bannerImg = null
                        if (name.includes('chouffe')) bannerImg = '/images/BiereAbsinthe.webp'
                        if (name.includes('poulet')) bannerImg = '/images/PouletRoti.webp'

                        if (bannerImg) {
                            return (
                                <div
                                    key={item.id}
                                    className={`supplement-banner-card ${selectedSupplements.some(i => i.id === item.id) ? 'selected' : ''}`}
                                    onClick={() => toggleItem(item)}
                                >
                                    <img src={bannerImg} alt={item.title} className="supplement-banner-img" />
                                    <div className="supplement-banner-info">
                                        <span className="supplement-banner-title">{item.title}</span>
                                        <span className="supplement-banner-price">
                                            {(item.price.includes('0.00') || item.price.includes('0,00')) ? '0€' : item.price}
                                        </span>
                                    </div>
                                    {selectedSupplements.some(i => i.id === item.id) && <div className="supplement-banner-check">✓</div>}
                                </div>
                            )
                        }

                        return (
                            <div
                                key={item.id}
                                className={`supplement-card ${selectedSupplements.some(i => i.id === item.id) ? 'selected' : ''}`}
                                onClick={() => toggleItem(item)}
                            >
                                <span className="supplement-card__name">{item.title}</span>
                                <span className="supplement-card__price">{item.price}</span>
                            </div>
                        )
                    })}
                    {extras.length === 0 && <p className="empty-msg">Aucun extra disponible.</p>}
                </div>
            </div>

            <button className="supplements-step__continue" onClick={() => onContinue(selectedSupplements)}>
                Continuer
            </button>

            {/* Custom Modal */}
            {modalInfo.show && (
                <div className="modal-overlay" onClick={closeModal}>
                    <div className="modal-content" onClick={e => e.stopPropagation()}>
                        <div className="modal-header">
                            <h3>Condition Spéciale</h3>
                        </div>
                        <div className="modal-body">
                            {modalInfo.message.split('\n').map((line, i) => (
                                <p key={i}>{line}</p>
                            ))}
                        </div>
                        <div className="modal-actions">
                            <button className="modal-btn cancel" onClick={closeModal}>Annuler</button>
                            <button className="modal-btn confirm" onClick={confirmModal}>J'ai compris</button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    )
}

export default Supplements
