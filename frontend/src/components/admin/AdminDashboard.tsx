import { useState, useEffect } from 'react'
import './AdminDashboard.css'

interface OrderItem {
    id: string
    name: string
    price: number | string
    item_type: string
}

interface MenuItem {
    id: string
    title: string
    price: string
    item_type: string
}

interface Order {
    id: number
    email: string
    prenom: string
    nom: string
    phone: string
    payment_status: string
    status: string
    total_amount: number
    heure_reservation: string
    menu_item?: OrderItem
    boisson_item?: OrderItem
    extras_items?: OrderItem[]
    created_at: string
    special_requests?: string | null
}

interface StatsData {
    total_orders: number
    menu_distribution: { name: string; count: number }[]
    drink_distribution: { name: string; count: number }[]
    extras_distribution: { name: string; count: number }[]
    time_slot_distribution: { slot: string; count: number }[]
    order_hour_distribution: { hour: number; count: number }[]
    total_extras: number
    total_revenue: number
}

interface AdminDashboardProps {
    onGoHome: () => void
}

// Simple SVG Pie Chart component
const PieChart = ({ data, title }: { data: { name: string; count: number }[]; title: string }) => {
    if (!data || data.length === 0) {
        return (
            <div className="stats-chart">
                <h3>{title}</h3>
                <p className="stats-empty">Aucune donnée</p>
            </div>
        )
    }

    const total = data.reduce((sum, item) => sum + item.count, 0)
    const colors = ['#DA291C', '#FFC72C', '#4caf50', '#2196f3', '#9c27b0', '#ff9800', '#00bcd4', '#e91e63']

    let currentAngle = 0
    const slices = data.map((item, index) => {
        const percentage = item.count / total
        const angle = percentage * 360
        const startAngle = currentAngle
        const endAngle = currentAngle + angle
        currentAngle = endAngle

        const startRad = (startAngle - 90) * (Math.PI / 180)
        const endRad = (endAngle - 90) * (Math.PI / 180)

        const x1 = 50 + 40 * Math.cos(startRad)
        const y1 = 50 + 40 * Math.sin(startRad)
        const x2 = 50 + 40 * Math.cos(endRad)
        const y2 = 50 + 40 * Math.sin(endRad)

        const largeArc = angle > 180 ? 1 : 0

        const pathD = angle >= 359.99
            ? `M 50 10 A 40 40 0 1 1 49.99 10 Z`
            : `M 50 50 L ${x1} ${y1} A 40 40 0 ${largeArc} 1 ${x2} ${y2} Z`

        return {
            path: pathD,
            color: colors[index % colors.length],
            name: item.name,
            count: item.count,
            percentage: (percentage * 100).toFixed(1)
        }
    })

    return (
        <div className="stats-chart">
            <h3>{title}</h3>
            <div className="stats-chart__content">
                <svg viewBox="0 0 100 100" className="pie-svg">
                    {slices.map((slice, index) => (
                        <path
                            key={index}
                            d={slice.path}
                            fill={slice.color}
                            stroke="#1a1a1a"
                            strokeWidth="0.5"
                        />
                    ))}
                </svg>
                <div className="pie-legend">
                    {slices.map((slice, index) => (
                        <div key={index} className="pie-legend__item">
                            <span className="pie-legend__color" style={{ backgroundColor: slice.color }}></span>
                            <span className="pie-legend__name">{slice.name}</span>
                            <span className="pie-legend__count">{slice.count} ({slice.percentage}%)</span>
                        </div>
                    ))}
                </div>
            </div>
        </div>
    )
}

// Bar Chart component for time-based data
const BarChart = ({ data, title, xKey, yKey }: { data: { [key: string]: string | number }[]; title: string; xKey: string; yKey: string }) => {
    if (!data || data.length === 0) {
        return (
            <div className="stats-chart">
                <h3>{title}</h3>
                <p className="stats-empty">Aucune donnée</p>
            </div>
        )
    }

    const maxValue = Math.max(...data.map(item => item[yKey] as number))

    return (
        <div className="stats-chart stats-chart--bar">
            <h3>{title}</h3>
            <div className="bar-chart">
                {data.map((item, index) => {
                    const height = maxValue > 0 ? ((item[yKey] as number) / maxValue) * 100 : 0
                    return (
                        <div key={index} className="bar-chart__item">
                            <div className="bar-chart__bar-container">
                                <div
                                    className="bar-chart__bar"
                                    style={{ height: `${height}%` }}
                                >
                                    <span className="bar-chart__value">{item[yKey]}</span>
                                </div>
                            </div>
                            <span className="bar-chart__label">{item[xKey]}</span>
                        </div>
                    )
                })}
            </div>
        </div>
    )
}

const AdminDashboard = ({ onGoHome }: AdminDashboardProps) => {
    const [orders, setOrders] = useState<Order[]>([])
    const [loading, setLoading] = useState(true)
    const [filterStatus, setFilterStatus] = useState('')
    const [error, setError] = useState<string | null>(null)
    const [editingOrder, setEditingOrder] = useState<Order | null>(null)
    const [menuItems, setMenuItems] = useState<MenuItem[]>([])
    const [printingPdf, setPrintingPdf] = useState(false)
    const [activeTab, setActiveTab] = useState<'orders' | 'stats'>('orders')
    const [statsData, setStatsData] = useState<StatsData | null>(null)
    const [statsLoading, setStatsLoading] = useState(false)

    const fetchOrders = async () => {
        setLoading(true)
        try {
            const url = filterStatus
                ? `/api/admin/orders?payment_status=${filterStatus}`
                : '/api/admin/orders'
            const response = await fetch(url, { credentials: 'include' })
            if (!response.ok) {
                if (response.status === 403) throw new Error("Accès refusé - Admin seulement")
                throw new Error("Erreur lors de la récupération des commandes")
            }
            const data = await response.json()
            setOrders(data)
            setError(null)
        } catch (err) {
            setError(err instanceof Error ? err.message : "Une erreur est survenue")
        } finally {
            setLoading(false)
        }
    }

    const fetchMenuItems = async () => {
        try {
            const response = await fetch('/api/menu/items', { credentials: 'include' })
            if (response.ok) {
                const data = await response.json()
                setMenuItems(data)
            }
        } catch {
            // Silently fail - menu items are optional for admin view
        }
    }

    const fetchStats = async () => {
        setStatsLoading(true)
        try {
            const response = await fetch('/api/admin/stats', { credentials: 'include' })
            if (response.ok) {
                const data = await response.json()
                setStatsData(data)
            }
        } catch {
            // Silently fail
        } finally {
            setStatsLoading(false)
        }
    }

    useEffect(() => {
        fetchOrders()
        fetchMenuItems()
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [filterStatus])

    useEffect(() => {
        if (activeTab === 'stats' && !statsData) {
            fetchStats()
        }
    }, [activeTab, statsData])

    const handleDelete = async (id: number) => {
        if (!window.confirm("Es-tu sûr de vouloir supprimer cette commande ?")) return

        try {
            const response = await fetch(`/api/admin/orders/${id}`, {
                method: 'DELETE',
                credentials: 'include'
            })
            if (response.ok) {
                fetchOrders()
            } else {
                const data = await response.json().catch(() => ({}))
                alert(data.detail || "Erreur lors de la suppression")
            }
        } catch {
            alert("Erreur réseau")
        }
    }

    const handleConfirmPayment = async (id: number) => {
        if (!window.confirm("Confirmer le paiement manuel pour cette commande ?")) return

        try {
            const response = await fetch(`/api/admin/orders/${id}/confirm-payment`, {
                method: 'POST',
                credentials: 'include'
            })
            if (response.ok) {
                fetchOrders()
                alert("Paiement confirmé avec succès")
            } else {
                const data = await response.json().catch(() => ({}))
                alert(data.detail || "Erreur lors de la confirmation du paiement")
            }
        } catch {
            alert("Erreur réseau")
        }
    }

    const handleUpdate = async (e: React.FormEvent) => {
        e.preventDefault()
        if (!editingOrder) return

        try {
            const response = await fetch(`/api/admin/orders/${editingOrder.id}`, {
                method: 'PATCH',
                headers: { 'Content-Type': 'application/json' },
                credentials: 'include',
                body: JSON.stringify({
                    prenom: editingOrder.prenom,
                    nom: editingOrder.nom,
                    menu_id: editingOrder.menu_item?.id || null,
                    boisson_id: editingOrder.boisson_item?.id || null,
                    bonus_ids: editingOrder.extras_items?.map(item => item.id) || [],
                    special_requests: editingOrder.special_requests || null
                })
            })

            if (response.ok) {
                setEditingOrder(null)
                fetchOrders()
            } else {
                const data = await response.json().catch(() => ({}))
                alert(data.detail || "Erreur lors de la mise à jour")
            }
        } catch {
            alert("Erreur réseau")
        }
    }

    const formatDate = (dateStr: string) => {
        return new Date(dateStr).toLocaleString('fr-FR', {
            day: '2-digit',
            month: '2-digit',
            hour: '2-digit',
            minute: '2-digit'
        })
    }

    const formatTimeSlot = (time: string | null) => {
        if (!time) return 'N/A'
        const [hours, minutes] = time.split(':').map(Number)
        const endHour = hours + 1
        return `${hours}h${minutes.toString().padStart(2, '0')} - ${endHour}h${minutes.toString().padStart(2, '0')}`
    }

    const handlePrintAllTickets = async () => {
        setPrintingPdf(true)
        try {
            const response = await fetch('/api/print/get_printPDF?start_time=00:00&end_time=23:59', {
                credentials: 'include'
            })
            if (!response.ok) {
                if (response.status === 404) {
                    alert('Aucune commande payée à imprimer')
                    return
                }
                throw new Error('Erreur lors de la génération du PDF')
            }
            const blob = await response.blob()
            const url = window.URL.createObjectURL(blob)
            window.open(url, '_blank')
        } catch (err) {
            alert(err instanceof Error ? err.message : 'Erreur lors de la génération du PDF')
        } finally {
            setPrintingPdf(false)
        }
    }

    // Toggle extra selection
    const toggleExtra = (extraItem: MenuItem) => {
        if (!editingOrder) return

        const currentExtras = editingOrder.extras_items || []
        const isSelected = currentExtras.some(e => e.id === extraItem.id)

        if (isSelected) {
            // Remove extra
            setEditingOrder({
                ...editingOrder,
                extras_items: currentExtras.filter(e => e.id !== extraItem.id)
            })
        } else {
            // Add extra
            setEditingOrder({
                ...editingOrder,
                extras_items: [
                    ...currentExtras,
                    { id: extraItem.id, name: extraItem.title, price: extraItem.price, item_type: extraItem.item_type }
                ]
            })
        }
    }

    // Calculate stats
    const stats = {
        total: orders.length,
        completed: orders.filter(o => o.payment_status === 'completed').length,
        pending: orders.filter(o => o.payment_status === 'pending').length,
        failed: orders.filter(o => o.payment_status === 'failed').length
    }

    // Get available extras from menu items
    const availableExtras = menuItems.filter(m => m.item_type === 'upsell')

    return (
        <div className="admin-dashboard">
            <header className="admin-header">
                <h1>Dashboard Admin</h1>
                <div className="admin-header__actions">
                    <button
                        onClick={handlePrintAllTickets}
                        className="admin-btn admin-btn--dark"
                        disabled={printingPdf}
                    >
                        {printingPdf ? 'Chargement...' : '🖨️ Imprimer tickets'}
                    </button>
                    <button onClick={onGoHome} className="admin-btn admin-btn--primary">
                        🏠 Retour Accueil
                    </button>
                </div>
            </header>

            {/* Tabs */}
            <div className="admin-tabs">
                <button
                    className={`admin-tab ${activeTab === 'orders' ? 'active' : ''}`}
                    onClick={() => setActiveTab('orders')}
                >
                    📋 Commandes
                </button>
                <button
                    className={`admin-tab ${activeTab === 'stats' ? 'active' : ''}`}
                    onClick={() => setActiveTab('stats')}
                >
                    📊 Statistiques
                </button>
            </div>

            {activeTab === 'orders' && (
                <>
                    {/* Stats */}
                    <div className="admin-stats">
                        <div className="admin-stat">
                            <div className="admin-stat__value">{stats.total}</div>
                            <div className="admin-stat__label">Total</div>
                        </div>
                        <div className="admin-stat">
                            <div className="admin-stat__value">{stats.completed}</div>
                            <div className="admin-stat__label">Payées</div>
                        </div>
                        <div className="admin-stat">
                            <div className="admin-stat__value">{stats.pending}</div>
                            <div className="admin-stat__label">En attente</div>
                        </div>
                        <div className="admin-stat">
                            <div className="admin-stat__value">{stats.failed}</div>
                            <div className="admin-stat__label">Échouées</div>
                        </div>
                    </div>

                    <div className="admin-filters">
                <select value={filterStatus} onChange={(e) => setFilterStatus(e.target.value)}>
                    <option value="">Tous les status</option>
                    <option value="pending">En attente (pending)</option>
                    <option value="completed">Payé (completed)</option>
                    <option value="failed">Échoué (failed)</option>
                </select>
                <button onClick={fetchOrders} className="admin-btn admin-btn--secondary">
                    🔄 Rafraîchir
                </button>
            </div>

            {error && <div className="admin-error">{error}</div>}

            <div className="orders-table-container">
                {loading ? (
                    <div className="no-orders">Chargement...</div>
                ) : orders.length === 0 ? (
                    <div className="no-orders">Aucune commande trouvée.</div>
                ) : (
                    <table className="orders-table">
                        <thead>
                            <tr>
                                <th>Client</th>
                                <th>Contact</th>
                                <th>Commande</th>
                                <th>Créneau</th>
                                <th>Total</th>
                                <th>Paiement</th>
                                <th>Date</th>
                                <th>Actions</th>
                            </tr>
                        </thead>
                        <tbody>
                            {orders.map(order => (
                                <tr key={order.id}>
                                    <td>
                                        <strong>{order.prenom} {order.nom}</strong><br />
                                        <small>{order.email}</small>
                                    </td>
                                    <td>{order.phone || 'N/A'}</td>
                                    <td>
                                        <div className="order-items">
                                            {order.menu_item?.name && <div>🍔 {order.menu_item.name}</div>}
                                            {order.boisson_item?.name && <div>🥤 {order.boisson_item.name}</div>}
                                            {order.extras_items?.map((extra, idx) => (
                                                <div key={idx}>🍟 {extra.name}</div>
                                            ))}
                                        </div>
                                    </td>
                                    <td>{formatTimeSlot(order.heure_reservation)}</td>
                                    <td>{order.total_amount.toFixed(2)}€</td>
                                    <td>
                                        <span className={`status-badge status-badge--${order.payment_status}`}>
                                            {order.payment_status}
                                        </span>
                                    </td>
                                    <td><small>{formatDate(order.created_at)}</small></td>
                                    <td>
                                        <button className="btn-icon btn-icon--edit" onClick={() => setEditingOrder({...order})} title="Modifier">
                                            ✏️
                                        </button>
                                        {order.payment_status !== 'completed' && (
                                            <button className="btn-icon btn-icon--confirm" onClick={() => handleConfirmPayment(order.id)} title="Confirmer paiement (espèces)">
                                                ✅
                                            </button>
                                        )}
                                        <button className="btn-icon btn-icon--delete" onClick={() => handleDelete(order.id)} title="Supprimer">
                                            🗑️
                                        </button>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                )}
            </div>
                </>
            )}

            {activeTab === 'stats' && (
                <div className="admin-stats-panel">
                    {statsLoading ? (
                        <div className="no-orders">Chargement des statistiques...</div>
                    ) : !statsData ? (
                        <div className="no-orders">Impossible de charger les statistiques</div>
                    ) : (
                        <>
                            {/* Summary Stats */}
                            <div className="admin-stats">
                                <div className="admin-stat">
                                    <div className="admin-stat__value">{statsData.total_orders}</div>
                                    <div className="admin-stat__label">Commandes payées</div>
                                </div>
                                <div className="admin-stat">
                                    <div className="admin-stat__value">{statsData.total_revenue.toFixed(2)}€</div>
                                    <div className="admin-stat__label">Chiffre d'affaires</div>
                                </div>
                                <div className="admin-stat">
                                    <div className="admin-stat__value">{statsData.total_extras}</div>
                                    <div className="admin-stat__label">Extras vendus</div>
                                </div>
                            </div>

                            <button onClick={fetchStats} className="admin-btn admin-btn--secondary" style={{ marginBottom: '24px' }}>
                                🔄 Rafraîchir les stats
                            </button>

                            {/* Charts Grid */}
                            <div className="stats-grid">
                                <PieChart
                                    data={statsData.menu_distribution}
                                    title="Menus les plus commandés"
                                />
                                <PieChart
                                    data={statsData.drink_distribution}
                                    title="Boissons les plus commandées"
                                />
                                <PieChart
                                    data={statsData.extras_distribution}
                                    title="Extras les plus commandés"
                                />
                                <BarChart
                                    data={statsData.time_slot_distribution}
                                    title="Créneaux de livraison les plus demandés"
                                    xKey="slot"
                                    yKey="count"
                                />
                                <BarChart
                                    data={statsData.order_hour_distribution.map(item => ({
                                        ...item,
                                        hourLabel: `${item.hour}h`
                                    }))}
                                    title="Heures de commande (quand les clients commandent)"
                                    xKey="hourLabel"
                                    yKey="count"
                                />
                            </div>
                        </>
                    )}
                </div>
            )}

            {editingOrder && (
                <div className="admin-modal" onClick={() => setEditingOrder(null)}>
                    <div className="admin-modal__content" onClick={(e) => e.stopPropagation()}>
                        <h2 className="admin-modal__header">Modifier la commande #{editingOrder.id}</h2>
                        <form onSubmit={handleUpdate}>
                            <div className="admin-form-group">
                                <label>Prénom</label>
                                <input
                                    type="text"
                                    value={editingOrder.prenom || ''}
                                    onChange={(e) => setEditingOrder({ ...editingOrder, prenom: e.target.value })}
                                />
                            </div>
                            <div className="admin-form-group">
                                <label>Nom</label>
                                <input
                                    type="text"
                                    value={editingOrder.nom || ''}
                                    onChange={(e) => setEditingOrder({ ...editingOrder, nom: e.target.value })}
                                />
                            </div>
                            <div className="admin-form-group">
                                <label>Menu</label>
                                <select
                                    value={editingOrder.menu_item?.id || ''}
                                    onChange={(e) => {
                                        const item = menuItems.find(m => m.id === e.target.value)
                                        if (item) {
                                            setEditingOrder({
                                                ...editingOrder,
                                                menu_item: { id: item.id, name: item.title, price: item.price, item_type: item.item_type }
                                            })
                                        } else {
                                            setEditingOrder({ ...editingOrder, menu_item: undefined })
                                        }
                                    }}
                                >
                                    <option value="">Aucun</option>
                                    {menuItems.filter(m => m.item_type === 'menu').map(m => (
                                        <option key={m.id} value={m.id}>{m.title}</option>
                                    ))}
                                </select>
                            </div>
                            <div className="admin-form-group">
                                <label>Boisson</label>
                                <select
                                    value={editingOrder.boisson_item?.id || ''}
                                    onChange={(e) => {
                                        const item = menuItems.find(m => m.id === e.target.value)
                                        if (item) {
                                            setEditingOrder({
                                                ...editingOrder,
                                                boisson_item: { id: item.id, name: item.title, price: item.price, item_type: item.item_type }
                                            })
                                        } else {
                                            setEditingOrder({ ...editingOrder, boisson_item: undefined })
                                        }
                                    }}
                                >
                                    <option value="">Aucune</option>
                                    {menuItems.filter(m => m.item_type === 'boisson').map(m => (
                                        <option key={m.id} value={m.id}>{m.title}</option>
                                    ))}
                                </select>
                            </div>
                            <div className="admin-form-group">
                                <label>Extras</label>
                                <div className="admin-extras-list">
                                    {availableExtras.length === 0 ? (
                                        <p className="admin-extras-empty">Aucun extra disponible</p>
                                    ) : (
                                        availableExtras.map(extra => {
                                            const isSelected = editingOrder.extras_items?.some(e => e.id === extra.id) || false
                                            return (
                                                <label key={extra.id} className={`admin-extra-item ${isSelected ? 'selected' : ''}`}>
                                                    <input
                                                        type="checkbox"
                                                        checked={isSelected}
                                                        onChange={() => toggleExtra(extra)}
                                                    />
                                                    <span className="admin-extra-item__name">{extra.title}</span>
                                                    <span className="admin-extra-item__price">{extra.price}</span>
                                                </label>
                                            )
                                        })
                                    )}
                                </div>
                            </div>
                            <div className="admin-form-group">
                                <label>Demandes spéciales / Notes</label>
                                <textarea
                                    rows={4}
                                    value={editingOrder.special_requests || ''}
                                    onChange={(e) => setEditingOrder({ ...editingOrder, special_requests: e.target.value })}
                                    placeholder="Ajoutez des notes ou demandes spéciales..."
                                />
                            </div>
                            <div className="admin-modal__actions">
                                <button type="button" onClick={() => setEditingOrder(null)}>
                                    Annuler
                                </button>
                                <button type="submit">
                                    Enregistrer
                                </button>
                            </div>
                        </form>
                    </div>
                </div>
            )}
        </div>
    )
}

export default AdminDashboard
