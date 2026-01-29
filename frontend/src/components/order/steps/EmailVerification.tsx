import { useState } from 'react'

type EmailVerificationProps = {
    onBack: () => void
    onVerified: (isCotisant: boolean, email: string) => void
    initialEmail?: string
}

type VerificationState = 'email_entry' | 'code_sent' | 'verifying' | 'verified' | 'error'

const EmailVerification = ({ onBack, onVerified, initialEmail = '' }: EmailVerificationProps) => {
    const [state, setState] = useState<VerificationState>('email_entry')
    const [email, setEmail] = useState(initialEmail)
    const [code, setCode] = useState('')
    const [error, setError] = useState('')
    const [isLoading, setIsLoading] = useState(false)
    const [isCotisant, setIsCotisant] = useState<boolean | null>(null)

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

            // Handle non-JSON responses (502, HTML error pages, etc.)
            const contentType = response.headers.get('content-type')
            if (!contentType || !contentType.includes('application/json')) {
                throw new Error('Erreur serveur. Réessayez dans quelques instants.')
            }

            const data = await response.json()

            if (!response.ok) {
                throw new Error(data.detail || 'Code invalide ou expiré')
            }

            setIsCotisant(data.is_cotisant)
            setState('verified')

            if (data.is_cotisant) {
                // Small delay to show success state
                setTimeout(() => {
                    onVerified(true, email)
                }, 1500)
            }
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Erreur de vérification')
            // Stay in code_sent state to allow retry
        } finally {
            setIsLoading(false)
        }
    }

    const handleCodeChange = (value: string) => {
        // Only allow alphanumeric, max 6 chars - preserve case
        const cleaned = value.replace(/[^a-zA-Z0-9]/g, '').slice(0, 6)
        setCode(cleaned)
        if (error) setError('')
    }

    const handleEmailChange = (value: string) => {
        setEmail(value.trim().toLowerCase())
        if (error) setError('')
    }

    return (
        <div className="verification-step">
            <button className="verification-step__back" onClick={onBack}>← Retour</button>
            <h2 className="verification-step__title">Vérification Email</h2>

            {/* Step 1: Enter Email */}
            {(state === 'email_entry' || state === 'error') && !isCotisant && (
                <div className="verification-section">
                    <p className="verification-info">
                        Pour valider votre commande, nous devons vérifier que vous êtes bien cotisant BDE.
                        Entrez votre adresse email d'école :
                    </p>
                    <div className="form-group">
                        <label>Email</label>
                        <input
                            type="email"
                            value={email}
                            onChange={e => handleEmailChange(e.target.value)}
                            placeholder="prenom.nom@telecom-sudparis.eu"
                            className="verification-email-input"
                        />
                    </div>
                    <button
                        className="verification-btn verification-btn--primary"
                        onClick={handleRequestCode}
                        disabled={isLoading || !email}
                    >
                        {isLoading ? 'Envoi en cours...' : '📧 Envoyer le code de vérification'}
                    </button>
                    {error && <div className="verification-error">{error}</div>}
                </div>
            )}

            {/* Step 2: Enter Code */}
            {state === 'code_sent' && (
                <div className="verification-section">
                    <div className="verification-email-display">
                        <span className="verification-email-label">Code envoyé à :</span>
                        <span className="verification-email-value">{email}</span>
                    </div>
                    <div className="verification-success-msg">
                        ✅ Code envoyé ! Vérifiez votre boîte mail.
                    </div>
                    <a
                        href="https://cerbere.imt.fr/zimbra"
                        target="_blank"
                        rel="noopener noreferrer"
                        className="verification-webmail-link"
                    >
                        📬 Ouvrir ma boîte mail IMT
                    </a>
                    <p className="verification-info">
                        Entrez le code à 6 caractères reçu par email :
                    </p>
                    <div className="verification-code-input-wrapper">
                        <input
                            type="text"
                            value={code}
                            onChange={e => handleCodeChange(e.target.value)}
                            placeholder="ABC123"
                            className="verification-code-input"
                            maxLength={6}
                            autoFocus
                        />
                    </div>
                    <button
                        className="verification-btn verification-btn--primary"
                        onClick={handleVerifyCode}
                        disabled={isLoading || code.length < 6}
                    >
                        {isLoading ? 'Vérification...' : '✓ Vérifier le code'}
                    </button>
                    <button
                        className="verification-btn verification-btn--secondary"
                        onClick={() => {
                            setState('email_entry')
                            setCode('')
                        }}
                        disabled={isLoading}
                    >
                        Changer d'email
                    </button>
                    {error && <div className="verification-error">{error}</div>}
                </div>
            )}

            {/* Step 3: Verified */}
            {state === 'verified' && (
                <div className="verification-section">
                    {isCotisant ? (
                        <div className="verification-result verification-result--success">
                            <div className="verification-result__icon">✅</div>
                            <h3>Email vérifié !</h3>
                            <p>Vous êtes bien cotisant BDE. Redirection vers le paiement...</p>
                        </div>
                    ) : (
                        <div className="verification-result verification-result--error">
                            <div className="verification-result__icon">❌</div>
                            <h3>Non cotisant BDE</h3>
                            <p>
                                Désolé, les commandes Mc'INT sont réservées aux cotisants BDE.
                            </p>
                            <p className="verification-result__hint">
                                Vous pouvez cotiser sur le site du BDE puis réessayer.
                            </p>
                        </div>
                    )}
                </div>
            )}
        </div>
    )
}

export default EmailVerification

