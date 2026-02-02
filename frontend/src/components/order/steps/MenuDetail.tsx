import type { MenuItem } from '../../../context/MenuContext'

type MenuDetailProps = {
    menu: MenuItem
    onBack: () => void
    onConfirm: () => void
}

const MenuDetail = ({ menu, onBack, onConfirm }: MenuDetailProps) => {
    // Extract items from menu for display
    const menuItems = menu.items || []

    return (
        <div className="menu-detail">
            {/* Back Button */}
            <button className="menu-detail__back" onClick={onBack}>
                <span className="menu-detail__back-icon">←</span>
                <span>Retour aux menus</span>
            </button>

            <div className="menu-detail__card">
                {/* Hero Section */}
                <div className="menu-detail__hero">
                    <div className="menu-detail__hero-bg"></div>
                    <div className="menu-detail__hero-content">
                        {/* Dynamic menu hero image */}
                        {menu.id === 'menu_boulanger' && (
                            <img src="/images/focaccia.webp" alt="Focaccia" className="menu-detail__emoji" />
                        )}
                        {menu.id === 'menu_gourmand' && (
                            <img src="/images/sandwich.webp" alt="Sandwich" className="menu-detail__emoji" />
                        )}
                        {menu.id === 'menu_veget' && (
                            <img src="/images/risotto.webp" alt="Risotto" className="menu-detail__emoji" />
                        )}
                        <div className="menu-detail__badge">Menu Signature</div>
                    </div>
                    {/* Floating decorations - Menu Boulanger */}
                    {menu.id === 'menu_boulanger' && (
                        <>
                            <div className="menu-detail__float menu-detail__float--1">
                                <img src="/images/tiramisu.webp" alt="Focaccia" />
                            </div>
                            <div className="menu-detail__float menu-detail__float--2">
                                <img src="/images/tiramisu.webp" alt="Tiramisu" />
                            </div>
                            <div className="menu-detail__float menu-detail__float--3">
                                <img src="/images/focaccia.webp" alt="Focaccia" />
                            </div>
                        </>
                    )}
                    {/* Floating decorations - Menu Gourmand */}
                    {menu.id === 'menu_gourmand' && (
                        <>
                            <div className="menu-detail__float menu-detail__float--1">
                                <img src="/images/sandwich.webp" alt="Sandwich" />
                            </div>
                            <div className="menu-detail__float menu-detail__float--2">
                                <img src="/images/citron_tartelette.webp" alt="Tartelette" />
                            </div>
                            <div className="menu-detail__float menu-detail__float--3">
                                <img src="/images/chouquettes.webp" alt="Chouquettes" />
                            </div>
                        </>
                    )}
                    {/* Floating decorations - Menu Végétarien */}
                    {menu.id === 'menu_veget' && (
                        <>
                            <div className="menu-detail__float menu-detail__float--1">
                                <img src="/images/risotto.webp" alt="Risotto" />
                            </div>
                            <div className="menu-detail__float menu-detail__float--2">
                                <img src="/images/donut.webp" alt="Donut" />
                            </div>
                            <div className="menu-detail__float menu-detail__float--3">
                                <img src="/images/donut.webp" alt="Risotto" />
                            </div>
                        </>
                    )}
                </div>

                {/* Content Section */}
                <div className="menu-detail__body">
                    <div className="menu-detail__header">
                        <h2 className="menu-detail__title">{menu.title}</h2>
                        <div className="menu-detail__price-tag">
                            <span className="menu-detail__price-label">Prix</span>
                            <span className="menu-detail__price">{menu.price}</span>
                        </div>
                    </div>

                    {menu.subtitle && (
                        <p className="menu-detail__subtitle">{menu.subtitle}</p>
                    )}

                    {/* Menu Contents */}
                    <div className="menu-detail__contents">
                        <h3 className="menu-detail__contents-title">
                            <span className="menu-detail__contents-icon">→</span>
                            Ce menu contient
                        </h3>
                        <ul className="menu-detail__list">
                            {menuItems.map((item: string, idx: number) => (
                                <li key={idx} className="menu-detail__list-item">
                                    <span className="menu-detail__list-check">✓</span>
                                    <span>{item}</span>
                                </li>
                            ))}
                        </ul>
                    </div>

                    {/* Allergens Section */}
                    {menu.allergens && Object.keys(menu.allergens).length > 0 && (
                        <div className="menu-detail__allergens">
                            <h3 className="menu-detail__allergens-title">
                                <span className="menu-detail__allergens-icon">⚠️</span>
                                Allergènes
                            </h3>
                            <ul className="menu-detail__allergens-list">
                                {Object.entries(menu.allergens).map(([itemName, allergenList], idx) => (
                                    <li key={idx} className="menu-detail__allergens-item">
                                        <strong>{itemName} :</strong>{' '}
                                        {allergenList.join(', ')}
                                    </li>
                                ))}
                            </ul>
                        </div>
                    )}

                    {/* CTA Section */}
                    <div className="menu-detail__cta">
                        <button className="menu-detail__confirm-btn" onClick={onConfirm}>
                            <span className="menu-detail__confirm-text">Je choisis ce menu</span>
                            <span className="menu-detail__confirm-icon">→</span>
                        </button>
                        <p className="menu-detail__hint">Personnalisez ensuite avec vos extras préférés</p>
                    </div>
                </div>
            </div>
        </div>
    )
}

export default MenuDetail

