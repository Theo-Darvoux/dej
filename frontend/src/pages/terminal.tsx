import { useState, useEffect } from 'react';

interface TerminalOrder {
    id: number;
    prenom: string | null;
    nom: string | null;
    is_maisel: boolean;
    batiment: string | null;
    menu: string | null;
    boisson: string | null;
    bonus: string | null;
}

interface TerminalData {
    orders: TerminalOrder[];
    current_hour: number;
    total: number;
}

function TerminalPage() {
    const [data, setData] = useState<TerminalData | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [selectedHour, setSelectedHour] = useState<number | null>(null);

    const hours = Array.from({ length: 10 }, (_, i) => i + 8); // 8h to 17h

    const fetchOrders = async (autoHour = true, hour?: number) => {
        setLoading(true);
        try {
            const params = new URLSearchParams();
            params.set('auto_hour', String(autoHour));
            if (hour !== undefined) {
                params.set('hour', String(hour));
            }

            const response = await fetch(`/api/terminal/orders?${params}`, {
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
    };

    useEffect(() => {
        fetchOrders();
        // Auto-refresh every 30 seconds
        const interval = setInterval(() => fetchOrders(selectedHour === null, selectedHour ?? undefined), 30000);
        return () => clearInterval(interval);
    }, [selectedHour]);

    const handleHourChange = (hour: number | null) => {
        setSelectedHour(hour);
        if (hour === null) {
            fetchOrders(true);
        } else {
            fetchOrders(false, hour);
        }
    };

    return (
        <div className="terminal-page">
            <header className="terminal-header">
                <h1>🍔 Terminal Cuisine</h1>
                <div className="terminal-controls">
                    <button
                        className={selectedHour === null ? 'active' : ''}
                        onClick={() => handleHourChange(null)}
                    >
                        Auto ({data?.current_hour ?? '--'}h)
                    </button>
                    {hours.map(h => (
                        <button
                            key={h}
                            className={selectedHour === h ? 'active' : ''}
                            onClick={() => handleHourChange(h)}
                        >
                            {h}h
                        </button>
                    ))}
                </div>
                <div className="terminal-stats">
                    <span className="total">{data?.total ?? 0} commandes</span>
                    <button className="refresh-btn" onClick={() => fetchOrders(selectedHour === null, selectedHour ?? undefined)}>
                        🔄 Actualiser
                    </button>
                </div>
            </header>

            {error && <div className="terminal-error">{error}</div>}
            {loading && <div className="terminal-loading">Chargement...</div>}

            <div className="terminal-grid">
                {data?.orders.map(order => (
                    <div
                        key={order.id}
                        className={`terminal-card ${order.is_maisel ? 'maisel' : 'evry'}`}
                    >
                        <div className="card-header">
                            <span className="location-badge">
                                {order.is_maisel ? `🏠 ${order.batiment || 'Maisel'}` : '📍 Evry'}
                            </span>
                        </div>
                        <div className="card-name">
                            <strong>{order.prenom} {order.nom}</strong>
                        </div>
                        <div className="card-items">
                            {order.menu && <div className="item">🍔 {order.menu}</div>}
                            {order.boisson && <div className="item">🥤 {order.boisson}</div>}
                            {order.bonus && <div className="item">🎁 {order.bonus}</div>}
                        </div>
                    </div>
                ))}

                {data?.orders.length === 0 && !loading && (
                    <div className="terminal-empty">
                        Aucune commande pour ce créneau
                    </div>
                )}
            </div>

            <style>{`
        .terminal-page {
          background: #1a1a2e;
          min-height: 100vh;
          padding: 16px;
          font-family: 'Segoe UI', system-ui, sans-serif;
        }

        .terminal-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          flex-wrap: wrap;
          gap: 16px;
          margin-bottom: 24px;
          padding: 16px;
          background: #16213e;
          border-radius: 12px;
        }

        .terminal-header h1 {
          color: #fff;
          margin: 0;
          font-size: 24px;
        }

        .terminal-controls {
          display: flex;
          gap: 8px;
          flex-wrap: wrap;
        }

        .terminal-controls button {
          padding: 8px 16px;
          border: none;
          border-radius: 8px;
          background: #2d3a5c;
          color: #fff;
          cursor: pointer;
          font-size: 14px;
          transition: all 0.2s;
        }

        .terminal-controls button:hover {
          background: #3d4a6c;
        }

        .terminal-controls button.active {
          background: #e63946;
        }

        .terminal-stats {
          display: flex;
          align-items: center;
          gap: 16px;
        }

        .terminal-stats .total {
          color: #fff;
          font-size: 18px;
          font-weight: 600;
        }

        .refresh-btn {
          padding: 8px 16px;
          border: none;
          border-radius: 8px;
          background: #4ade80;
          color: #000;
          cursor: pointer;
          font-weight: 600;
        }

        .terminal-error {
          background: #e63946;
          color: white;
          padding: 16px;
          border-radius: 8px;
          margin-bottom: 16px;
        }

        .terminal-loading {
          color: #fff;
          text-align: center;
          padding: 32px;
          font-size: 18px;
        }

        .terminal-grid {
          display: grid;
          grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
          gap: 16px;
        }

        .terminal-card {
          border-radius: 12px;
          padding: 16px;
          color: #fff;
          transition: transform 0.2s;
        }

        .terminal-card:hover {
          transform: translateY(-4px);
        }

        .terminal-card.maisel {
          background: linear-gradient(135deg, #1e88e5, #1565c0);
          border-left: 6px solid #4fc3f7;
        }

        .terminal-card.evry {
          background: linear-gradient(135deg, #f57c00, #e65100);
          border-left: 6px solid #ffb74d;
        }

        .card-header {
          margin-bottom: 12px;
        }

        .location-badge {
          background: rgba(255, 255, 255, 0.2);
          padding: 4px 10px;
          border-radius: 12px;
          font-size: 12px;
          font-weight: 600;
        }

        .card-name {
          font-size: 20px;
          margin-bottom: 12px;
        }

        .card-items {
          display: flex;
          flex-direction: column;
          gap: 6px;
        }

        .card-items .item {
          font-size: 14px;
          padding: 4px 8px;
          background: rgba(255, 255, 255, 0.1);
          border-radius: 6px;
        }

        .terminal-empty {
          grid-column: 1 / -1;
          text-align: center;
          color: #8892b0;
          padding: 48px;
          font-size: 18px;
        }

        @media (max-width: 768px) {
          .terminal-header {
            flex-direction: column;
            align-items: stretch;
          }

          .terminal-controls {
            justify-content: center;
          }

          .terminal-stats {
            justify-content: center;
          }
        }
      `}</style>
        </div>
    );
}

export default TerminalPage;
