import { useState } from 'react';

function App() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleDownloadPDF = async () => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await fetch('/api/print/get_printPDF', {
        method: 'GET',
        credentials: 'include', // Important pour envoyer les cookies
      });

      if (!response.ok) {
        if (response.status === 403) {
          throw new Error('Accès non autorisé. Vous devez être administrateur.');
        }
        throw new Error('Erreur lors de la génération du PDF');
      }

      // Récupérer le PDF en blob
      const blob = await response.blob();
      
      // Créer une URL pour le blob
      const url = window.URL.createObjectURL(blob);
      
      // Ouvrir dans une nouvelle page
      window.open(url, '_blank');
      
      // Libérer la mémoire après un délai
      setTimeout(() => window.URL.revokeObjectURL(url), 100);
      
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Une erreur est survenue');
      console.error('Erreur:', err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <section className="page">
      <div className="left">
        <h1>Impression de documents</h1>
        <button onClick={handleDownloadPDF} disabled={loading}>
          {loading ? 'Génération en cours...' : 'Télécharger mon document'}
        </button>
        {error && <p style={{ color: 'red', marginTop: '10px' }}>{error}</p>}
      </div>
      <div className="right">
        <img src="/image_print.png" alt="Logo"></img>
      </div>
    </section>
  );
}

export default App;
