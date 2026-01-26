import './OrderTicket.css'

type OrderData = {
    menu?: string
    boisson?: string
    bonus?: string
    total_amount: number
    heure_reservation: string
    adresse: string
    phone: string
}

type OrderTicketProps = {
    order: OrderData
    onClose: () => void
}

const OrderTicket = ({ order, onClose }: OrderTicketProps) => {
    return (
        <div className="ticket-overlay" onClick={onClose}>
            <div className="ticket" onClick={(e) => e.stopPropagation()}>
                <div className="ticket__header">
                    <div className="ticket__logo">🍟</div>
                    <h1>Mc-INT</h1>
                    <p>Restaurant by Hypnos</p>
                    <div className="ticket__divider">-------------------------</div>
                </div>

                <div className="ticket__content">
                    <div className="ticket__section">
                        <div className="ticket__label">RESERVATION POUR</div>
                        <div className="ticket__value ticket__value--large">7 FÉVRIER 2026</div>
                    </div>

                    <div className="ticket__section">
                        <div className="ticket__label">HORAIRE DE RETRAIT</div>
                        <div className="ticket__value ticket__value--large">{order.heure_reservation}</div>
                    </div>

                    <div className="ticket__divider">-------------------------</div>

                    <div className="ticket__items">
                        <div className="ticket__item-header">
                            <span>QTE</span>
                            <span>PRODUIT</span>
                            <span>TOTAL</span>
                        </div>
                        {order.menu && (
                            <div className="ticket__item">
                                <span>1</span>
                                <span>{order.menu}</span>
                                <span>-</span>
                            </div>
                        )}
                        {order.boisson && (
                            <div className="ticket__item">
                                <span>1</span>
                                <span>{order.boisson}</span>
                                <span>-</span>
                            </div>
                        )}
                        {order.bonus && (
                            <div className="ticket__item">
                                <span>1</span>
                                <span>{order.bonus}</span>
                                <span>-</span>
                            </div>
                        )}
                    </div>

                    <div className="ticket__divider">-------------------------</div>

                    <div className="ticket__total">
                        <span>TOTAL</span>
                        <span>{order.total_amount.toFixed(2)} €</span>
                    </div>

                    <div className="ticket__section">
                        <div className="ticket__label">ADRESSE</div>
                        <div className="ticket__value">{order.adresse}</div>
                    </div>

                    <div className="ticket__section">
                        <div className="ticket__label">TEL</div>
                        <div className="ticket__value">{order.phone}</div>
                    </div>
                </div>

                <div className="ticket__footer">
                    <div className="ticket__divider">-------------------------</div>
                    <p>Merci de votre commande !</p>
                    <p>En cas de souci : 01 23 45 67 89</p>
                    <div className="ticket__barcode">|||| ||||| || |||| |||</div>
                </div>

                <button className="ticket__close" onClick={onClose}>Fermer</button>
            </div>
        </div>
    )
}

export default OrderTicket
