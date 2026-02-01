import { useState, useEffect } from 'react';
import './print.css';

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
    </div>
  );
}

export default PrintPage;
