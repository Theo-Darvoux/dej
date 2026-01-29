import { useMenu, type MenuItem } from '../../../context/MenuContext'

type MenuSelectionProps = {
    onSelect: (menu: MenuItem) => void
}

const MenuSelection = ({ onSelect }: MenuSelectionProps) => {
    const { allItems, isLoading } = useMenu()

    if (isLoading) {
        return <div className="menu-selection-loading">Chargement des menus...</div>
    }

    // Filter to get all menus
    const featuredItems = allItems.filter(item =>
        item.item_type === 'menu'
    )

    return (
        <div className="menu-selection">
            <h2 className="menu-selection__title">Nos Menus Phares</h2>
            <div className="menu-selection__grid">
                {featuredItems.map(item => (
                    <div
                        key={item.id}
                        className="menu-card-large"
                        onClick={() => onSelect(item)}
                    >
                        <div className="menu-card-large__image">
                            {/* Placeholder or actual image */}
                            <span className="menu-card-large__emoji">🍔</span>
                        </div>
                        <div className="menu-card-large__content">
                            <h3 className="menu-card-large__title">{item.title.replace(/^Menu\s+/i, '')}</h3>
                            <ul className="menu-card-large__list">
                                {(item.items || []).map((element: string, idx: number) => (
                                    <li key={idx} className="menu-card-large__list-item">
                                        {element}
                                    </li>
                                ))}
                            </ul>
                            <div className="menu-card-large__footer">
                                <span className="menu-card-large__price">{item.price}</span>
                                <span className="menu-card-large__cta">Choisir →</span>
                            </div>
                        </div>
                    </div>
                ))}
            </div>

            {/* BDE Warning Notice */}
            <div className="menu-selection__notice">
                <span className="menu-selection__notice-icon">🎓</span>
                <p>Les commandes sont <strong>réservées aux cotisants BDE</strong>. Votre statut sera vérifié lors de la validation.</p>
            </div>

            {featuredItems.length === 0 && (
                <p>Aucun menu disponible pour le moment.</p>
            )}
        </div>
    )
}

export default MenuSelection

