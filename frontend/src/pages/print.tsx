import { useState, useEffect } from 'react';

interface OrderCombo {
  menu: string | null;
  boisson: string | null;
  bonus: string | null;
  quantity: number;
}

interface SummaryData {
  start_time: string;
  end_time: string;
  combos: OrderCombo[];
  total_orders: number;
}

function PrintPage() {
  const [loading, setLoading] = useState(false);
  const [summaryLoading, setSummaryLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [startTime, setStartTime] = useState('07:00');
  const [endTime, setEndTime] = useState('19:00');
  const [summary, setSummary] = useState<SummaryData | null>(null);

  const hours = Array.from({ length: 14 }, (_, i) => {
    const h = (i + 7).toString().padStart(2, '0');
    return `${h}:00`;
  });

  const fetchSummary = async () => {
    setSummaryLoading(true);
    try {
      const response = await fetch(`/api/print/summary?start_time=${startTime}&end_time=${endTime}`, {
        credentials: 'include',
      });
      if (!response.ok) throw new Error('Erreur lors de la récupération du résumé');
      const data = await response.json();
      setSummary(data);
    } catch (err) {
      console.error(err);
    } finally {
      setSummaryLoading(false);
    }
  };

  useEffect(() => {
    fetchSummary();
  }, [startTime, endTime]);

  const handleDownloadPDF = async () => {
    setLoading(true);
    setError(null);

    try {
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
      console.error('Erreur:', err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <section className="page print-admin">
      <div className="left">
        <h1>Administration des Impressions</h1>

        <div className="filters" style={{ marginBottom: '20px', display: 'flex', gap: '10px', alignItems: 'center' }}>
          <div>
            <label>De : </label>
            <select value={startTime} onChange={(e) => setStartTime(e.target.value)}>
              {hours.map(h => <option key={h} value={h}>{h}</option>)}
            </select>
          </div>
          <div>
            <label>À : </label>
            <select value={endTime} onChange={(e) => setEndTime(e.target.value)}>
              {hours.map(h => <option key={h} value={h}>{h}</option>)}
            </select>
          </div>
          <button onClick={fetchSummary} disabled={summaryLoading} style={{ padding: '5px 10px' }}>
            Actualiser
          </button>
        </div>

        {summary && (
          <div className="summary-table" style={{ marginTop: '20px', width: '100%' }}>
            <h3>Résumé ({summary.total_orders} commandes)</h3>
            <table style={{ width: '100%', borderCollapse: 'collapse', marginTop: '10px' }}>
              <thead>
                <tr style={{ textAlign: 'left', borderBottom: '2px solid #ddd' }}>
                  <th style={{ padding: '8px' }}>Menu</th>
                  <th style={{ padding: '8px' }}>Boisson</th>
                  <th style={{ padding: '8px' }}>Bonus</th>
                  <th style={{ padding: '8px' }}>Quantité</th>
                </tr>
              </thead>
              <tbody>
                {summary.combos.map((combo, idx) => (
                  <tr key={idx} style={{ borderBottom: '1px solid #eee' }}>
                    <td style={{ padding: '8px' }}>{combo.menu || '-'}</td>
                    <td style={{ padding: '8px' }}>{combo.boisson || '-'}</td>
                    <td style={{ padding: '8px' }}>{combo.bonus || '-'}</td>
                    <td style={{ padding: '8px', fontWeight: 'bold' }}>x {combo.quantity}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        <button
          onClick={handleDownloadPDF}
          disabled={loading}
          style={{ marginTop: '30px', padding: '10px 20px', backgroundColor: '#e63946', color: 'white', border: 'none', borderRadius: '5px', cursor: 'pointer' }}
        >
          {loading ? 'Génération du PDF...' : 'Télécharger les tickets (PDF)'}
        </button>

        {error && <p style={{ color: 'red', marginTop: '10px' }}>{error}</p>}
      </div>
      <div className="right">
        <img src="/image_print.png" alt="Print preview" style={{ maxWidth: '100%', borderRadius: '10px' }} />
      </div>

      <style>{`
        .print-admin select {
          padding: 8px;
          border-radius: 5px;
          border: 1px solid #ccc;
          background: white;
        }
        .summary-table th {
          background-color: #f8f9fa;
        }
        .summary-table tr:hover {
          background-color: #f1f1f1;
        }
      `}</style>
    </section>
  );
}

export default PrintPage;
