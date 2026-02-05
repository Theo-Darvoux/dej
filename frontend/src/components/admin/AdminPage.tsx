import { useState, useEffect } from 'react'
import { fetchWithAuth } from '../../utils/api'
import AdminDashboard from './AdminDashboard'
import AdminLogin from './AdminLogin'
import './AdminPage.css'

type AuthState = 'loading' | 'not_logged_in' | 'not_admin' | 'admin'

interface AdminPageProps {
    onGoHome: () => void
}

const AdminPage = ({ onGoHome }: AdminPageProps) => {
    const [authState, setAuthState] = useState<AuthState>('loading')

    const checkAdminStatus = async () => {
        setAuthState('loading')
        try {
            const response = await fetchWithAuth('/api/admin/orders?limit=1')

            if (response.ok) {
                setAuthState('admin')
            } else if (response.status === 401) {
                // Token refresh also failed, need to log in
                setAuthState('not_logged_in')
            } else if (response.status === 403) {
                setAuthState('not_admin')
            } else {
                setAuthState('not_logged_in')
            }
        } catch {
            setAuthState('not_logged_in')
        }
    }

    useEffect(() => {
        // Check admin status on mount - intentional state initialization
        // eslint-disable-next-line react-hooks/set-state-in-effect
        checkAdminStatus()
    }, [])

    const handleLoginSuccess = () => {
        checkAdminStatus()
    }

    const handleLogout = async () => {
        try {
            await fetchWithAuth('/api/auth/logout', { method: 'POST' })
        } catch {
            // Ignore errors
        }
        setAuthState('not_logged_in')
    }

    if (authState === 'loading') {
        return (
            <div className="admin-page admin-page--loading">
                <div className="admin-loading">
                    <div className="admin-loading__spinner">🍟</div>
                    <p>Vérification des accès...</p>
                </div>
            </div>
        )
    }

    if (authState === 'not_logged_in') {
        return (
            <div className="admin-page">
                <AdminLogin onLoginSuccess={handleLoginSuccess} />
                <button className="admin-page__home-btn" onClick={onGoHome}>
                    Retour à l'accueil
                </button>
            </div>
        )
    }

    if (authState === 'not_admin') {
        return (
            <div className="admin-page">
                <div className="admin-access-denied">
                    <div className="admin-access-denied__card">
                        <span className="admin-access-denied__icon">🚫</span>
                        <h2>Accès refusé</h2>
                        <p>
                            Vous êtes connecté mais vous n'avez pas les droits administrateur.
                        </p>
                        <p className="admin-access-denied__hint">
                            Contactez un administrateur si vous pensez que c'est une erreur.
                        </p>
                        <div className="admin-access-denied__actions">
                            <button className="admin-access-denied__btn" onClick={onGoHome}>
                                Retour à l'accueil
                            </button>
                            <button className="admin-access-denied__btn admin-access-denied__btn--secondary" onClick={handleLogout}>
                                Se déconnecter
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        )
    }

    return <AdminDashboard onGoHome={onGoHome} />
}

export default AdminPage
