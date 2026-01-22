import './CategorySlider.css'

type Category = {
    id: string
    title: string
    icon?: string  // Emoji or image URL
}

type CategorySliderProps = {
    categories: Category[]
    selectedId: string
    onSelect: (id: string) => void
}

// Default icons for categories if not provided
const getCategoryIcon = (title: string): string => {
    const icons: Record<string, string> = {
        'burgers': '🍔',
        'menus': '🍟',
        'boissons': '🥤',
        'desserts': '🍦',
        'salades': '🥗',
        'wraps': '🌯',
        'petit-dejeuner': '🥞',
        'happy meal': '🎁',
        'mccafe': '☕',
    }

    const key = title.toLowerCase()
    for (const [k, v] of Object.entries(icons)) {
        if (key.includes(k)) return v
    }
    return '🍽️'
}

const CategorySlider = ({ categories, selectedId, onSelect }: CategorySliderProps) => {
    return (
        <nav className="category-slider">
            <div className="category-slider__container">
                {categories.map((category) => {
                    const isActive = category.id === selectedId
                    const icon = category.icon || getCategoryIcon(category.title)

                    return (
                        <button
                            key={category.id}
                            className={`category-slider__item ${isActive ? 'is-active' : ''}`}
                            onClick={() => onSelect(category.id)}
                        >
                            <div className="category-slider__icon">
                                {icon.startsWith('http') ? (
                                    <img src={icon} alt={category.title} />
                                ) : (
                                    icon
                                )}
                            </div>
                            <span className="category-slider__label">{category.title}</span>
                        </button>
                    )
                })}
            </div>
        </nav>
    )
}

export default CategorySlider
