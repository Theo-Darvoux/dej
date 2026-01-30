import { useState, useEffect } from 'react';

interface OrderItem {
  id: number;
  prenom: string | null;
  nom: string | null;
  heure_reservation: string;
  menu: string | null;
  boisson: string | null;
  extras: string[];
  payment_status: string;
  is_maisel: boolean;
  adresse: string | null;
}

interface OrdersResponse {
  orders: OrderItem[];
  total: number;
  page: number;
  per_page: number;
  total_pages: number;
}

function PrintPage() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [orders, setOrders] = useState<OrderItem[]>([]);
  const [total, setTotal] = useState(0);
  const [totalPages, setTotalPages] = useState(1);

  // Filters
  const [viewMode, setViewMode] = useState<'all' | 'slot'>('all');
  const [selectedSlot, setSelectedSlot] = useState('08:00');
  const [paymentFilter, setPaymentFilter] = useState<'all' | 'completed' | 'pending'>('all');
  const [perPage, setPerPage] = useState(50);
  const [page, setPage] = useState(1);

  // Time slots 8h-9h to 17h-18h
  const timeSlots = Array.from({ length: 10 }, (_, i) => {
    const start = (i + 8).toString().padStart(2, '0');
    const end = (i + 9).toString().padStart(2, '0');
    return { value: `${start}:00`, label: `${start}h - ${end}h` };
  });

  const fetchOrders = async () => {
    setLoading(true);
    setError(null);

    try {
      const params = new URLSearchParams();

      if (viewMode === 'all') {
        params.set('start_time', '08:00');
        params.set('end_time', '18:00');
      } else {
        const startHour = parseInt(selectedSlot.split(':')[0]);
        const endHour = startHour + 1;
        params.set('start_time', `${startHour.toString().padStart(2, '0')}:00`);
        params.set('end_time', `${endHour.toString().padStart(2, '0')}:00`);
      }

      params.set('payment_status', paymentFilter);
      params.set('page', String(page));
      params.set('per_page', String(perPage));

      const response = await fetch(`/api/print/orders?${params}`, {
        credentials: 'include',
      });

      if (!response.ok) {
        if (response.status === 403) {
          throw new Error('Accès non autorisé. Vous devez être administrateur.');
        }
        throw new Error('Erreur lors de la récupération des commandes');
      }

      const data: OrdersResponse = await response.json();
      setOrders(data.orders);
      setTotal(data.total);
      setTotalPages(data.total_pages);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Une erreur est survenue');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchOrders();
  }, [viewMode, selectedSlot, paymentFilter, perPage, page]);

  const handleDownloadPDF = async () => {
    setLoading(true);
    setError(null);

    try {
      let startTime = '08:00';
      let endTime = '18:00';

      if (viewMode === 'slot') {
        const startHour = parseInt(selectedSlot.split(':')[0]);
        const endHour = startHour + 1;
        startTime = `${startHour.toString().padStart(2, '0')}:00`;
        endTime = `${endHour.toString().padStart(2, '0')}:00`;
      }

      const response = await fetch(`/api/print/get_printPDF?start_time=${startTime}&end_time=${endTime}`, {
        method: 'GET',
        credentials: 'include',
      });

      if (!response.ok) {
        if (response.status === 403) {
          throw new Error('Accès non autorisé. Vous devez être administrateur.');
        }
        if (response.status === 404) {
          throw new Error('Aucune commande trouvée pour ce créneau.');
        }
        throw new Error('Erreur lors de la génération du PDF');
      }

      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      window.open(url, '_blank');
      setTimeout(() => window.URL.revokeObjectURL(url), 100);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Une erreur est survenue');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="print-page">
      <div className="print-sidebar">
        <h1>📄 Administration des Impressions</h1>

        <div className="filter-section">
          <h3>🕐 Créneau horaire</h3>
          <div className="radio-group">
            <label>
              <input
                type="radio"
                checked={viewMode === 'all'}
                onChange={() => { setViewMode('all'); setPage(1); }}
              />
              Toute la journée (8h-18h)
            </label>
            <label>
              <input
                type="radio"
                checked={viewMode === 'slot'}
                onChange={() => { setViewMode('slot'); setPage(1); }}
              />
              Créneau spécifique
            </label>
          </div>

          {viewMode === 'slot' && (
            <select
              value={selectedSlot}
              onChange={(e) => { setSelectedSlot(e.target.value); setPage(1); }}
            >
              {timeSlots.map(slot => (
                <option key={slot.value} value={slot.value}>{slot.label}</option>
              ))}
            </select>
          )}
        </div>

        <div className="filter-section">
          <h3>💳 Statut paiement</h3>
          <select
            value={paymentFilter}
            onChange={(e) => { setPaymentFilter(e.target.value as 'all' | 'completed' | 'pending'); setPage(1); }}
          >
            <option value="all">Tous</option>
            <option value="completed">Payés uniquement</option>
            <option value="pending">En attente uniquement</option>
          </select>
        </div>

        <div className="filter-section">
          <h3>📊 Affichage</h3>
          <select
            value={perPage}
            onChange={(e) => { setPerPage(Number(e.target.value)); setPage(1); }}
          >
            <option value={10}>10 par page</option>
            <option value={50}>50 par page</option>
            <option value={200}>200 par page</option>
          </select>
        </div>

        <div className="stats">
          <span className="total">{total} commandes au total</span>
        </div>

        <button
          className="print-btn"
          onClick={handleDownloadPDF}
          disabled={loading}
        >
          {loading ? '⏳ Génération...' : '🖨️ Imprimer les tickets (PDF)'}
        </button>

        {error && <div className="error-msg">{error}</div>}
      </div>

      <div className="print-content">
        <div className="table-header">
          <h2>Liste des commandes</h2>
          <div className="pagination">
            <button disabled={page <= 1} onClick={() => setPage(p => p - 1)}>◀ Précédent</button>
            <span>Page {page} / {totalPages}</span>
            <button disabled={page >= totalPages} onClick={() => setPage(p => p + 1)}>Suivant ▶</button>
          </div>
        </div>

        {loading && <div className="loading">Chargement...</div>}

        <table>
          <thead>
            <tr>
              <th>#</th>
              <th>Heure</th>
              <th>Nom</th>
              <th>Prénom</th>
              <th>Lieu</th>
              <th>Menu</th>
              <th>Boisson</th>
              <th>Extras</th>
              <th>Paiement</th>
            </tr>
          </thead>
          <tbody>
            {orders.map((order, idx) => (
              <tr key={order.id} className={order.payment_status === 'completed' ? 'paid' : 'pending'}>
                <td>{(page - 1) * perPage + idx + 1}</td>
                <td>{order.heure_reservation}</td>
                <td>{order.nom || '-'}</td>
                <td>{order.prenom || '-'}</td>
                <td className={order.is_maisel ? 'maisel' : 'evry'}>
                  {order.is_maisel ? '🏠 Maisel' : `📍 ${order.adresse || 'Evry'}`}
                </td>
                <td>{order.menu || '-'}</td>
                <td>{order.boisson || '-'}</td>
                <td>{order.extras?.length > 0 ? order.extras.join(', ') : '-'}</td>
                <td>
                  <span className={`badge ${order.payment_status}`}>
                    {order.payment_status === 'completed' ? '✅ Payé' : '⏳ En attente'}
                  </span>
                </td>
              </tr>
            ))}

            {orders.length === 0 && !loading && (
              <tr>
                <td colSpan={9} className="empty">Aucune commande trouvée</td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      <style>{`
        .print-page {
          display: flex;
          min-height: 100vh;
          background: #f5f5f5;
          font-family: 'Segoe UI', system-ui, sans-serif;
        }

        .print-sidebar {
          width: 320px;
          background: #1a1a2e;
          color: white;
          padding: 24px;
          display: flex;
          flex-direction: column;
          gap: 24px;
        }

        .print-sidebar h1 {
          font-size: 20px;
          margin: 0;
        }

        .filter-section {
          display: flex;
          flex-direction: column;
          gap: 12px;
        }

        .filter-section h3 {
          margin: 0;
          font-size: 14px;
          color: #a0a0a0;
        }

        .radio-group {
          display: flex;
          flex-direction: column;
          gap: 8px;
        }

        .radio-group label {
          display: flex;
          align-items: center;
          gap: 8px;
          cursor: pointer;
        }

        .print-sidebar select {
          padding: 10px;
          border-radius: 8px;
          border: none;
          background: #2d3a5c;
          color: white;
          font-size: 14px;
        }

        .stats {
          padding: 16px;
          background: #2d3a5c;
          border-radius: 8px;
          text-align: center;
        }

        .stats .total {
          font-size: 18px;
          font-weight: 600;
        }

        .print-btn {
          padding: 16px;
          border: none;
          border-radius: 8px;
          background: #e63946;
          color: white;
          font-size: 16px;
          font-weight: 600;
          cursor: pointer;
          transition: background 0.2s;
          margin-top: auto;
        }

        .print-btn:hover {
          background: #c1121f;
        }

        .print-btn:disabled {
          background: #666;
          cursor: not-allowed;
        }

        .error-msg {
          background: #e63946;
          padding: 12px;
          border-radius: 8px;
          text-align: center;
        }

        .print-content {
          flex: 1;
          padding: 24px;
          overflow-x: auto;
        }

        .table-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 16px;
        }

        .table-header h2 {
          margin: 0;
          color: #333;
        }

        .pagination {
          display: flex;
          align-items: center;
          gap: 12px;
        }

        .pagination button {
          padding: 8px 16px;
          border: none;
          border-radius: 6px;
          background: #1a1a2e;
          color: white;
          cursor: pointer;
        }

        .pagination button:disabled {
          background: #ccc;
          cursor: not-allowed;
        }

        .loading {
          text-align: center;
          padding: 32px;
          color: #666;
        }

        table {
          width: 100%;
          border-collapse: collapse;
          background: white;
          border-radius: 12px;
          overflow: hidden;
          box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }

        th, td {
          padding: 12px 16px;
          text-align: left;
          border-bottom: 1px solid #eee;
        }

        th {
          background: #1a1a2e;
          color: white;
          font-weight: 600;
          font-size: 13px;
          text-transform: uppercase;
        }

        tr:hover {
          background: #f9f9f9;
        }

        tr.paid {
          background: #e8f5e9;
        }

        tr.pending {
          background: #fff3e0;
        }

        td.maisel {
          color: #1565c0;
          font-weight: 600;
        }

        td.evry {
          color: #e65100;
          font-weight: 600;
        }

        .badge {
          padding: 4px 8px;
          border-radius: 12px;
          font-size: 12px;
          font-weight: 600;
        }

        .badge.completed {
          background: #4caf50;
          color: white;
        }

        .badge.pending {
          background: #ff9800;
          color: white;
        }

        td.empty {
          text-align: center;
          color: #999;
          padding: 48px;
        }

        @media (max-width: 1024px) {
          .print-page {
            flex-direction: column;
          }

          .print-sidebar {
            width: 100%;
          }
        }
      `}</style>
    </div>
  );
}

export default PrintPage;
