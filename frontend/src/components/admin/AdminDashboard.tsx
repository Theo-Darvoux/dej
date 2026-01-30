import { useState, useEffect } from 'react'
import './AdminDashboard.css'

interface OrderItem {
    id: number
    name: string
    price: number
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
}

interface AdminDashboardProps {
    onGoHome: () => void
}

const AdminDashboard = ({ onGoHome }: AdminDashboardProps) => {
    const [orders, setOrders] = useState<Order[]>([])
    const [loading, setLoading] = useState(true)
    const [filterStatus, setFilterStatus] = useState('')
    const [error, setError] = useState<string | null>(null)
    const [editingOrder, setEditingOrder] = useState<Order | null>(null)
    const [menuItems, setMenuItems] = useState<OrderItem[]>([])
    const [printingPdf, setPrintingPdf] = useState(false)

    const fetchOrders = async () => {
        setLoading(true)
        try {
            const url = filterStatus
                ? `/api/admin/orders?payment_status=${filterStatus}`
                : '/api/admin/orders'
            const response = await fetch(url)
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
            const response = await fetch('/api/menu/items')
            if (response.ok) {
                const data = await response.json()
                setMenuItems(data)
            }
        } catch (err) {
            console.error("Failed to fetch menu items", err)
        }
    }

    useEffect(() => {
        fetchOrders()
        fetchMenuItems()
    }, [filterStatus])

    const handleDelete = async (id: number) => {
        if (!window.confirm("Es-tu sûr de vouloir supprimer cette commande ?")) return

        try {
            const response = await fetch(`/api/admin/orders/${id}`, { method: 'DELETE' })
            if (response.ok) {
                fetchOrders()
            } else {
                alert("Erreur lors de la suppression")
            }
        } catch (err) {
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
                body: JSON.stringify({
                    prenom: editingOrder.prenom,
                    nom: editingOrder.nom,
                    payment_status: editingOrder.payment_status,
                    status: editingOrder.status,
                    menu_id: editingOrder.menu_item?.id,
                    boisson_id: editingOrder.boisson_item?.id,
                    bonus_ids: editingOrder.extras_items?.map(e => e.id) || []
                })
            })

            if (response.ok) {
                setEditingOrder(null)
                fetchOrders()
            } else {
                alert("Erreur lors de la mise à jour")
            }
        } catch (err) {
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

    const handlePrintAllTickets = async () => {
        setPrintingPdf(true)
        try {
            const response = await fetch('/api/print/get_printPDF?start_time=00:00&end_time=23:59')
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

    return (
        <div className="admin-dashboard">
            <header className="admin-header">
                <h1>Dashboard Admin</h1>
                <div style={{ display: 'flex', gap: '0.5rem' }}>
                    <button
                        onClick={handlePrintAllTickets}
                        className="payment-return__btn"
                        style={{ width: 'auto', padding: '0.5rem 1rem', background: '#333', color: '#fff' }}
                        disabled={printingPdf}
                    >
                        {printingPdf ? 'Chargement...' : 'Imprimer tickets'}
                    </button>
                    <button onClick={onGoHome} className="payment-return__btn" style={{ width: 'auto', padding: '0.5rem 1rem' }}>
                        Retour Accueil
                    </button>
                </div>
            </header>

            <div className="admin-filters">
                <select value={filterStatus} onChange={(e) => setFilterStatus(e.target.value)}>
                    <option value="">Tous les status</option>
                    <option value="pending">En attente (pending)</option>
                    <option value="completed">Payé (completed)</option>
                    <option value="failed">Échoué (failed)</option>
                </select>
                <button onClick={fetchOrders} className="payment-return__btn" style={{ width: 'auto', padding: '0.5rem 1rem', background: '#eee', color: '#333' }}>
                    🔄 Rafraîchir
                </button>
            </div>

            {error && <div className="verify-error" style={{ marginBottom: '1rem' }}>{error}</div>}

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
                                <th>Heure</th>
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
                                        <small>
                                            {order.menu_item?.name && <div>🍔 {order.menu_item.name}</div>}
                                            {order.boisson_item?.name && <div>🥤 {order.boisson_item.name}</div>}
                                            {order.extras_items?.map((extra, idx) => (
                                                <div key={idx}>🍟 {extra.name}</div>
                                            ))}
                                        </small>
                                    </td>
                                    <td>{order.heure_reservation || 'N/A'}</td>
                                    <td>{order.total_amount.toFixed(2)}€</td>
                                    <td>
                                        <span className={`status-badge status-badge--${order.payment_status}`}>
                                            {order.payment_status}
                                        </span>
                                    </td>
                                    <td><small>{formatDate(order.created_at)}</small></td>
                                    <td>
                                        <button className="btn-icon btn-icon--edit" onClick={() => setEditingOrder(order)} title="Modifier">
                                            ✏️
                                        </button>
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

            {editingOrder && (
                <div className="admin-modal">
                    <div className="admin-modal__content">
                        <h2 className="admin-modal__header">Modifier la commande #{editingOrder.id}</h2>
                        <form onSubmit={handleUpdate}>
                            <div className="admin-form-group">
                                <label>Prénom</label>
                                <input
                                    type="text"
                                    value={editingOrder.prenom}
                                    onChange={(e) => setEditingOrder({ ...editingOrder, prenom: e.target.value })}
                                />
                            </div>
                            <div className="admin-form-group">
                                <label>Nom</label>
                                <input
                                    type="text"
                                    value={editingOrder.nom}
                                    onChange={(e) => setEditingOrder({ ...editingOrder, nom: e.target.value })}
                                />
                            </div>
                            <div className="admin-form-group">
                                <label>Status Paiement</label>
                                <select
                                    value={editingOrder.payment_status}
                                    onChange={(e) => setEditingOrder({ ...editingOrder, payment_status: e.target.value })}
                                >
                                    <option value="pending">En attente (pending)</option>
                                    <option value="completed">Payé (completed)</option>
                                    <option value="failed">Échoué (failed)</option>
                                </select>
                            </div>
                            <div className="admin-form-group">
                                <label>Menu</label>
                                <select
                                    value={editingOrder.menu_item?.id || ''}
                                    onChange={(e) => {
                                        const item = menuItems.find(m => m.id === parseInt(e.target.value))
                                        setEditingOrder({ ...editingOrder, menu_item: item })
                                    }}
                                >
                                    <option value="">Aucun</option>
                                    {menuItems.filter(m => m.item_type === 'menu').map(m => (
                                        <option key={m.id} value={m.id}>{m.name}</option>
                                    ))}
                                </select>
                            </div>
                            <div className="admin-modal__actions">
                                <button type="button" className="payment-return__btn payment-return__btn--secondary" onClick={() => setEditingOrder(null)}>
                                    Annuler
                                </button>
                                <button type="submit" className="payment-return__btn payment-return__btn--primary">
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
