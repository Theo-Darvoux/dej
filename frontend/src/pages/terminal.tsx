import { useState, useEffect, useCallback } from 'react';
import './terminal.css';

interface TerminalOrder {
    id: number;
    prenom: string | null;
    nom: string | null;
    is_maisel: boolean;
    batiment: string | null;
    chambre: number | null;
    menu: string | null;
    boisson: string | null;
    extras: string[];
    heure: string;
    special_request?: string | null;
}

interface TerminalData {
    orders: TerminalOrder[];
    current_hour: number;
    total: number;
}

type OrderUrgency = 'overdue' | 'urgent' | 'upcoming';

function TerminalPage() {
    const [data, setData] = useState<TerminalData | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [currentTime, setCurrentTime] = useState(new Date());

    const fetchOrders = useCallback(async () => {
        setLoading(true);
        try {
            const response = await fetch('/api/terminal/orders?all_orders=true', {
                credentials: 'include',
            });

            if (!response.ok) {
                if (response.status === 403) {
                    throw new Error('Accès non autorisé. Vous devez être administrateur.');
                }
                throw new Error('Erreur lors de la récupération des commandes');
            }

            const result = await response.json();
            setData(result);
            setError(null);
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Une erreur est survenue');
        } finally {
            setLoading(false);
        }
    }, []);

    // Fetch orders and set up auto-refresh
    useEffect(() => {
        fetchOrders();
        const interval = setInterval(fetchOrders, 30000); // Refresh every 30s
        return () => clearInterval(interval);
    }, [fetchOrders]);

    // Update current time every second
    useEffect(() => {
        const interval = setInterval(() => setCurrentTime(new Date()), 1000);
        return () => clearInterval(interval);
    }, []);

    // Mark order as completed
    const handleCompleteOrder = useCallback(async (orderId: number) => {
        try {
            // Remove from display immediately for better UX
            setData(prevData => {
                if (!prevData) return prevData;
                return {
                    ...prevData,
                    orders: prevData.orders.filter(order => order.id !== orderId),
                    total: prevData.total - 1
                };
            });

            /* REAL API CALL (uncomment when ready):
            const response = await fetch(`/api/terminal/orders/${orderId}/complete`, {
                method: 'POST',
                credentials: 'include',
            });

            if (!response.ok) {
                throw new Error('Erreur lors de la validation de la commande');
            }
            */
        } catch (err) {
            console.error('Error completing order:', err);
            // Optionally refresh data on error
            fetchOrders();
        }
    }, [fetchOrders]);

    // Determine urgency based on current time
    const getOrderUrgency = useCallback((orderHeure: string): OrderUrgency => {
        const [orderHour] = orderHeure.split(':').map(Number);
        const currentHour = currentTime.getHours();
        const currentMinute = currentTime.getMinutes();

        // If order hour is before current hour -> overdue (RED)
        if (orderHour < currentHour) {
            return 'overdue';
        }

        // If order is for next hour and current minute > 50 -> urgent (ORANGE)
        if (orderHour === currentHour + 1 && currentMinute >= 50) {
            return 'urgent';
        }

        // If order is for current hour -> urgent (ORANGE)
        if (orderHour === currentHour) {
            return 'urgent';
        }

        // Otherwise -> upcoming (GREEN)
        return 'upcoming';
    }, [currentTime]);

    // Sort orders by urgency (overdue first, then urgent, then upcoming)
    const sortedOrders = data?.orders
        .map(order => ({ ...order, urgency: getOrderUrgency(order.heure) }))
        .sort((a, b) => {
            const urgencyOrder: Record<OrderUrgency, number> = { overdue: 0, urgent: 1, upcoming: 2 };
            if (urgencyOrder[a.urgency] !== urgencyOrder[b.urgency]) {
                return urgencyOrder[a.urgency] - urgencyOrder[b.urgency];
            }
            // Same urgency, sort by hour
            return a.heure.localeCompare(b.heure);
        })
        .slice(0, 24) ?? []; // Max 24 orders (3 columns x 8 rows)

    const formatTime = (date: Date) => {
        return date.toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit', second: '2-digit' });
    };

    const getUrgencyColor = (urgency: OrderUrgency) => {
        switch (urgency) {
            case 'overdue': return '#e63946';  // Red
            case 'urgent': return '#f4a261';   // Orange
            case 'upcoming': return '#2a9d8f'; // Green
        }
    };

    const getUrgencyLabel = (urgency: OrderUrgency) => {
        switch (urgency) {
            case 'overdue': return 'EN RETARD';
            case 'urgent': return 'MAINTENANT';
            case 'upcoming': return 'À VENIR';
        }
    };

    return (
        <div className="terminal-page">
            <header className="terminal-header">
                <div className="terminal-header-left">
                    <h1>🍔 Terminal Cuisine</h1>
                    <span className="terminal-current-time">{formatTime(currentTime)}</span>
                </div>
                <div className="terminal-header-right">
                    <div className="terminal-legend">
                        <span className="terminal-legend-item overdue">🔴 En retard</span>
                        <span className="terminal-legend-item urgent">🟠 Maintenant</span>
                        <span className="terminal-legend-item upcoming">🟢 À venir</span>
                    </div>
                    <div className="stats">
                        <span className="total">{data?.total ?? 0} commandes</span>
                        <button className="terminal-refresh-btn" onClick={fetchOrders}>
                            🔄 Actualiser
                        </button>
                    </div>
                </div>
            </header>

            {error && <div className="terminal-error">{error}</div>}
            {loading && !data && <div className="terminal-loading">Chargement...</div>}

            <div className="terminal-grid">
                {sortedOrders.map(order => (
                    <div
                        key={order.id}
                        className="terminal-card"
                        style={{ borderLeftColor: getUrgencyColor(order.urgency) }}
                        onClick={() => handleCompleteOrder(order.id)}
                    >
                        <div className="terminal-card-header">
                            <span 
                                className="terminal-urgency-badge"
                                style={{ backgroundColor: getUrgencyColor(order.urgency) }}
                            >
                                {order.heure} - {getUrgencyLabel(order.urgency)}
                            </span>
                        </div>
                        <div className="terminal-card-name">
                            <strong>{order.prenom} {order.nom}</strong>
                        </div>
                        <div className="terminal-card-items">
                            {order.menu && <div className="item menu">🍔 {order.menu}</div>}
                            {order.boisson && <div className="item boisson">🥤 {order.boisson}</div>}
                            {order.extras?.map((extra, idx) => (
                                <div key={idx} className="item extra">🎁 {extra}</div>
                            ))}
                        </div>
                        {order.special_request && (
                            <div className="terminal-special-request">
                                ⚠️ DEMANDE SPÉCIALE
                            </div>
                        )}
                    </div>
                ))}

                {sortedOrders.length === 0 && !loading && (
                    <div className="terminal-empty">
                        Aucune commande à préparer
                    </div>
                )}
            </div>
        </div>
    );
}

export default TerminalPage;
