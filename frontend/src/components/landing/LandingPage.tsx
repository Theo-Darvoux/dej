import './LandingPage.css'

type LandingPageProps = {
    onStart: () => void
}

const LandingPage = ({ onStart }: LandingPageProps) => {
    return (
        <div className="landing">
            {/* Header with Logo */}
            <header className="landing__header">
                <div className="landing__logo-text">🍟</div>
                <h1 className="landing__title">Mc-INT</h1>
            </header>

            {/* Hero Section */}
            <section className="landing__hero">
                <div className="landing__hero-placeholder">🍔</div>
                <div className="landing__message">
                    <h2>Bienvenue</h2>
                    <p>Commandez vos plats préférés en quelques clics</p>
                </div>
            </section>

            {/* CTA Button */}
            <div className="landing__cta">
                <button className="landing__btn" onClick={onStart}>
                    Touchez pour commander
                </button>
                <p className="landing__hint">Appuyez sur l'écran pour commencer</p>
            </div>
        </div>
    )
}

export default LandingPage
