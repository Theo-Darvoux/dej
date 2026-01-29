import { useState } from 'react'

type AdminLoginProps = {
    onLoginSuccess: () => void
}

type LoginState = 'email_entry' | 'code_sent'

const AdminLogin = ({ onLoginSuccess }: AdminLoginProps) => {
    const [state, setState] = useState<LoginState>('email_entry')
    const [email, setEmail] = useState('')
    const [code, setCode] = useState('')
    const [error, setError] = useState('')
    const [isLoading, setIsLoading] = useState(false)

    const isValidEmail = (email: string) => {
        return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)
    }

    const handleRequestCode = async () => {
        if (!isValidEmail(email)) {
            setError('Veuillez entrer une adresse email valide')
            return
        }

        setIsLoading(true)
        setError('')

        try {
            const response = await fetch('/api/auth/request-code', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ email })
            })

            if (!response.ok) {
                const data = await response.json()
                throw new Error(data.detail || 'Erreur lors de l\'envoi du code')
            }

            setState('code_sent')
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Erreur inconnue')
        } finally {
            setIsLoading(false)
        }
    }

    const handleVerifyCode = async () => {
        if (code.length < 6) {
            setError('Le code doit contenir 6 caractères')
            return
        }

        setIsLoading(true)
        setError('')

        try {
            const response = await fetch('/api/auth/verify', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ email, code })
            })

            const contentType = response.headers.get('content-type')
            if (!contentType || !contentType.includes('application/json')) {
                throw new Error('Erreur serveur. Réessayez dans quelques instants.')
            }

            const data = await response.json()

            if (!response.ok) {
                throw new Error(data.detail || 'Code invalide ou expiré')
            }

            onLoginSuccess()
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Erreur de vérification')
        } finally {
            setIsLoading(false)
        }
    }

    const handleCodeChange = (value: string) => {
        const cleaned = value.replace(/[^a-zA-Z0-9]/g, '').slice(0, 6)
        setCode(cleaned)
        if (error) setError('')
    }

    const handleEmailChange = (value: string) => {
        setEmail(value.trim().toLowerCase())
        if (error) setError('')
    }

    return (
        <div className="admin-login">
            <div className="admin-login__card">
                <div className="admin-login__header">
                    <span className="admin-login__icon">🔐</span>
                    <h2>Connexion Admin</h2>
                </div>

                {state === 'email_entry' && (
                    <div className="admin-login__form">
                        <p className="admin-login__info">
                            Entrez votre adresse email pour recevoir un code de connexion.
                        </p>
                        <div className="form-group">
                            <label>Email</label>
                            <input
                                type="email"
                                value={email}
                                onChange={e => handleEmailChange(e.target.value)}
                                placeholder="votre@email.com"
                                className="admin-login__input"
                            />
                        </div>
                        <button
                            className="admin-login__btn admin-login__btn--primary"
                            onClick={handleRequestCode}
                            disabled={isLoading || !email}
                        >
                            {isLoading ? 'Envoi en cours...' : 'Envoyer le code'}
                        </button>
                        {error && <div className="admin-login__error">{error}</div>}
                    </div>
                )}

                {state === 'code_sent' && (
                    <div className="admin-login__form">
                        <div className="admin-login__email-display">
                            <span className="admin-login__email-label">Code envoyé à :</span>
                            <span className="admin-login__email-value">{email}</span>
                        </div>
                        <div className="admin-login__success">
                            Code envoyé ! Vérifiez votre boîte mail.
                        </div>
                        <p className="admin-login__info">
                            Entrez le code à 6 caractères reçu par email :
                        </p>
                        <div className="admin-login__code-wrapper">
                            <input
                                type="text"
                                value={code}
                                onChange={e => handleCodeChange(e.target.value)}
                                placeholder="ABC123"
                                className="admin-login__code-input"
                                maxLength={6}
                                autoFocus
                            />
                        </div>
                        <button
                            className="admin-login__btn admin-login__btn--primary"
                            onClick={handleVerifyCode}
                            disabled={isLoading || code.length < 6}
                        >
                            {isLoading ? 'Vérification...' : 'Vérifier le code'}
                        </button>
                        <button
                            className="admin-login__btn admin-login__btn--secondary"
                            onClick={() => {
                                setState('email_entry')
                                setCode('')
                            }}
                            disabled={isLoading}
                        >
                            Changer d'email
                        </button>
                        {error && <div className="admin-login__error">{error}</div>}
                    </div>
                )}
            </div>
        </div>
    )
}

export default AdminLogin
