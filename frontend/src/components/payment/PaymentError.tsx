import './PaymentReturn.css'

type PaymentErrorProps = {
    onClose: () => void
}

const PaymentError = ({ onClose }: PaymentErrorProps) => {
    return (
        <div className="payment-return">
            <div className="payment-return__card">
                <div className="payment-return__icon payment-return__icon--error">❌</div>
                <h1>Paiement interrompu</h1>
                <p>
                    Le paiement n'a pas pu être finalisé. Aucun montant n'a été débité.
                </p>
                <p className="payment-return__details">
                    Tu peux réessayer ou nous contacter si le problème persiste.
                </p>
                <button className="payment-return__btn" onClick={onClose}>
                    Réessayer
                </button>
            </div>
        </div>
    )
}

export default PaymentError
