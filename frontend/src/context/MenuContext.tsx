import { createContext, useContext, useEffect, useState, type ReactNode } from 'react'

export type Category = {
    id: string
    title: string
}

export type MenuItem = {
    id: string
    category_id: string
    title: string
    subtitle: string
    items?: string[] 
    allergens?: Record<string, string[]>
    tag?: string
    accent?: string
    price: string
    image?: string
    item_type?: string
}

type MenuContextType = {
    categories: Category[]
    menuByCategory: Record<string, MenuItem[]>
    allItems: MenuItem[]
    isLoading: boolean
    error: string | null
    refreshMenu: () => void
}

const MenuContext = createContext<MenuContextType | undefined>(undefined)

export const MenuProvider = ({ children }: { children: ReactNode }) => {
    const [categories, setCategories] = useState<Category[]>([])
    const [menuByCategory, setMenuByCategory] = useState<Record<string, MenuItem[]>>({})
    const [allItems, setAllItems] = useState<MenuItem[]>([])
    const [isLoading, setIsLoading] = useState(true)
    const [error, setError] = useState<string | null>(null)

    const sleep = (ms: number) => new Promise(res => setTimeout(res, ms))

    const fetchMenuData = async () => {
        setIsLoading(true)
        setError(null)
        let success = false
        let attempt = 0
        while (!success) {
            try {
                // Fetch categories and items in parallel
                const [categoriesRes, itemsRes] = await Promise.all([
                    fetch('/api/menu/categories'),
                    fetch('/api/menu/items')
                ])

                if (!categoriesRes.ok) throw new Error('Failed to fetch categories')
                if (!itemsRes.ok) throw new Error('Failed to fetch menu items')

                const categoriesData = await categoriesRes.json()
                const itemsData = await itemsRes.json()

                // Normalize categories
                const categoriesList: Category[] = Array.isArray(categoriesData)
                    ? categoriesData
                    : (categoriesData as any)?.categories || []

                setCategories(categoriesList)

                // Normalize items
                const itemsList: MenuItem[] = Array.isArray(itemsData)
                    ? itemsData
                    : (itemsData as any)?.items || []

                setAllItems(itemsList)

                // Group items by category_id
                const grouped: Record<string, MenuItem[]> = {}

                // Initialize empty arrays for all categories to avoid undefined checks
                categoriesList.forEach(cat => {
                    grouped[cat.id] = []
                })

                itemsList.forEach(item => {
                    const catId = String(item.category_id)
                    if (!grouped[catId]) {
                        grouped[catId] = []
                    }
                    grouped[catId].push(item)
                })

                setMenuByCategory(grouped)
                success = true
            } catch (err) {
                setError(err instanceof Error ? err.message : 'Une erreur est survenue lors du chargement du menu')
                attempt++
                // Exponential backoff: max 5s
                await sleep(Math.min(500 * Math.pow(2, attempt), 5000))
            } finally {
                setIsLoading(!success)
            }
        }
    }

    useEffect(() => {
        fetchMenuData()
    }, [])

    return (
        <MenuContext.Provider value={{
            categories,
            menuByCategory,
            allItems,
            isLoading,
            error,
            refreshMenu: fetchMenuData
        }}>
            {children}
        </MenuContext.Provider>
    )
}

export const useMenu = () => {
    const context = useContext(MenuContext)
    if (context === undefined) {
        throw new Error('useMenu must be used within a MenuProvider')
    }
    return context
}
