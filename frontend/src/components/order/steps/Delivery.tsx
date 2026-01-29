import { useState, useEffect } from 'react'

export type DeliveryInfo = {
    locationType: 'maisel' | 'external'
    building?: string
    room?: string
    address?: string
    timeSlot: string
}

type AddressSuggestion = {
    label: string
    postcode: string
    city: string
}

type SlotData = {
    slot: string
    start: string
    available: boolean
    current_count: number
    max_capacity: number
}

type DeliveryProps = {
    onBack: () => void
    onContinue: (info: DeliveryInfo) => void
    initialDeliveryInfo?: DeliveryInfo | null
}

const Delivery = ({ onBack, onContinue, initialDeliveryInfo }: DeliveryProps) => {
    const [locationType, setLocationType] = useState<'maisel' | 'external'>(
        initialDeliveryInfo?.locationType || 'maisel'
    )
    const [room, setRoom] = useState(initialDeliveryInfo?.room || '')
    const [roomError, setRoomError] = useState('')

    const [addressQuery, setAddressQuery] = useState(initialDeliveryInfo?.address || '')
    const [addressSuggestions, setAddressSuggestions] = useState<AddressSuggestion[]>([])
    const [selectedAddress, setSelectedAddress] = useState(initialDeliveryInfo?.address || '')
    const [addressError, setAddressError] = useState('')
    const [isLoadingAddresses, setIsLoadingAddresses] = useState(false)

    const [selectedSlot, setSelectedSlot] = useState(initialDeliveryInfo?.timeSlot || '')

    // Slots data from API
    const [slots, setSlots] = useState<SlotData[]>([])
    const [slotsLoading, setSlotsLoading] = useState(true)
    const [slotsError, setSlotsError] = useState<string | null>(null)

    // Fetch slot availability from API
    useEffect(() => {
        const fetchSlots = async () => {
            setSlotsLoading(true)
            setSlotsError(null)
            try {
                const response = await fetch('/api/reservations/availability')
                if (!response.ok) {
                    throw new Error('Erreur lors du chargement des créneaux')
                }
                const data = await response.json()
                setSlots(data.slots || [])
            } catch (err) {
                setSlotsError(err instanceof Error ? err.message : 'Erreur inconnue')
                setSlots([])
            } finally {
                setSlotsLoading(false)
            }
        }

        fetchSlots()
    }, [])

    // Debounced address search
    useEffect(() => {
        if (locationType !== 'external' || addressQuery.length < 3) {
            setAddressSuggestions([])
            return
        }

        const timer = setTimeout(async () => {
            setIsLoadingAddresses(true)
            try {
                // Use French government address API
                const response = await fetch(
                    `https://api-adresse.data.gouv.fr/search?q=${encodeURIComponent(addressQuery)}&postcode=91000&limit=5`
                )
                const data = await response.json()

                const suggestions: AddressSuggestion[] = data.features
                    ?.filter((f: any) => {
                        const city = f.properties?.city?.toLowerCase() || ''
                        const postcode = f.properties?.postcode || ''
                        return city.includes('évry') || city.includes('evry') || postcode === '91000'
                    })
                    .map((f: any) => ({
                        label: f.properties?.label || '',
                        postcode: f.properties?.postcode || '',
                        city: f.properties?.city || ''
                    })) || []

                setAddressSuggestions(suggestions)
            } catch (err) {
                console.error('Address search error:', err)
                setAddressSuggestions([])
            } finally {
                setIsLoadingAddresses(false)
            }
        }, 300)

        return () => clearTimeout(timer)
    }, [addressQuery, locationType])

    // Room validation: must be 4 digits between 1001 and 7999
    const validateRoom = (value: string): boolean => {
        if (value.length !== 4) {
            setRoomError('Le numéro de chambre doit contenir 4 chiffres')
            return false
        }

        if (!/^\d{4}$/.test(value)) {
            setRoomError('Le numéro de chambre ne doit contenir que des chiffres')
            return false
        }

        const roomNum = parseInt(value, 10)
        if (roomNum < 1001 || roomNum > 7999) {
            setRoomError('Le numéro de chambre doit être entre 1001 et 7999')
            return false
        }

        setRoomError('')
        return true
    }

    // Get building from room number (first digit)
    const getBuildingFromRoom = (roomNum: string): string => {
        if (roomNum.length >= 1 && roomNum[0] >= '1' && roomNum[0] <= '7') {
            return `U${roomNum[0]}`
        }
        return ''
    }

    const handleRoomChange = (value: string) => {
        // Only allow digits, max 4
        const cleaned = value.replace(/\D/g, '').slice(0, 4)
        setRoom(cleaned)

        if (cleaned.length === 4) {
            validateRoom(cleaned)
        } else {
            setRoomError('')
        }
    }

    const handleAddressSelect = (suggestion: AddressSuggestion) => {
        setSelectedAddress(suggestion.label)
        setAddressQuery(suggestion.label)
        setAddressSuggestions([])
        setAddressError('')
    }

    const getSlotStatus = (slot: SlotData) => {
        const remaining = slot.max_capacity - slot.current_count
        const percentFree = remaining / slot.max_capacity

        if (!slot.available || remaining <= 0) return 'full'
        if (percentFree <= 0.5) return 'limited'
        return 'available'
    }

    const getRemainingPlaces = (slot: SlotData): number => {
        return Math.max(0, slot.max_capacity - slot.current_count)
    }

    // Convert slot start time to ID format (e.g., "08:00" -> "08:00")
    const getSlotId = (slot: SlotData): string => {
        return slot.start
    }

    // Format slot label (e.g., "08:00 - 09:00" -> "08h - 09h")
    const formatSlotLabel = (slot: SlotData): string => {
        const parts = slot.slot.split(' - ')
        if (parts.length === 2) {
            const start = parts[0].replace(':', 'h').slice(0, 3)
            const end = parts[1].replace(':', 'h').slice(0, 3)
            return `${start} - ${end}`
        }
        return slot.slot
    }

    const canContinue = () => {
        if (!selectedSlot) return false

        if (locationType === 'maisel') {
            return room.length === 4 && !roomError
        } else {
            return selectedAddress.length > 0
        }
    }

    const handleContinue = () => {
        if (!canContinue()) return

        const building = locationType === 'maisel' ? getBuildingFromRoom(room) : undefined

        onContinue({
            locationType,
            building,
            room: locationType === 'maisel' ? room : undefined,
            address: locationType === 'external' ? selectedAddress : undefined,
            timeSlot: selectedSlot
        })
    }

    return (
        <div className="delivery-step">
            <button className="delivery-step__back" onClick={onBack}>← Retour</button>
            <h2 className="delivery-step__title">Livraison</h2>

            <div className="delivery-date-notice">
                📅 Livraison le <strong>7 février 2026</strong>
            </div>

            {/* Location Type Toggle */}
            <div className="delivery-section">
                <h3>Où souhaitez-vous être livré ?</h3>
                <div className="delivery-toggle">
                    <button
                        className={`delivery-toggle__btn ${locationType === 'maisel' ? 'active' : ''}`}
                        onClick={() => setLocationType('maisel')}
                    >
                        🏠 Résidence Maisel
                    </button>
                    <button
                        className={`delivery-toggle__btn ${locationType === 'external' ? 'active' : ''}`}
                        onClick={() => setLocationType('external')}
                    >
                        📍 Évry-Courcouronnes
                    </button>
                </div>
            </div>

            {/* Location Form */}
            <div className="delivery-section">
                {locationType === 'maisel' ? (
                    <div className="delivery-maisel-form">
                        <div className="form-group">
                            <label>Numéro de chambre</label>
                            <input
                                type="text"
                                value={room}
                                onChange={e => handleRoomChange(e.target.value)}
                                placeholder="Ex: 3215"
                                className={`delivery-input ${roomError ? 'error' : ''}`}
                                maxLength={4}
                            />
                            {roomError && <span className="form-error">{roomError}</span>}
                            {room.length === 4 && !roomError && (
                                <span className="form-hint form-hint--success">
                                    ✓ Bâtiment {getBuildingFromRoom(room)}
                                </span>
                            )}
                            {room.length < 4 && (
                                <span className="form-hint">Format: 4 chiffres (ex: 3215 = U3)</span>
                            )}
                        </div>
                    </div>
                ) : (
                    <div className="delivery-external-form">
                        <div className="form-group">
                            <label>Adresse à Évry-Courcouronnes</label>
                            <div className="address-autocomplete">
                                <input
                                    type="text"
                                    value={addressQuery}
                                    onChange={e => {
                                        setAddressQuery(e.target.value)
                                        setSelectedAddress('')
                                    }}
                                    placeholder="Commencez à taper votre adresse..."
                                    className={`delivery-input ${addressError ? 'error' : ''}`}
                                />
                                {isLoadingAddresses && (
                                    <div className="address-loading">Recherche...</div>
                                )}
                                {addressSuggestions.length > 0 && (
                                    <ul className="address-suggestions">
                                        {addressSuggestions.map((s, idx) => (
                                            <li
                                                key={idx}
                                                onClick={() => handleAddressSelect(s)}
                                                className="address-suggestion"
                                            >
                                                {s.label}
                                            </li>
                                        ))}
                                    </ul>
                                )}
                            </div>
                            {addressError && <span className="form-error">{addressError}</span>}
                            {selectedAddress && (
                                <div className="address-selected">
                                    ✓ {selectedAddress}
                                </div>
                            )}
                        </div>
                    </div>
                )}
            </div>

            {/* Time Slots */}
            <div className="delivery-section">
                <h3>Choisissez votre créneau</h3>
                {slotsLoading ? (
                    <div className="time-slots-loading">Chargement des créneaux...</div>
                ) : slotsError ? (
                    <div className="time-slots-error">{slotsError}</div>
                ) : (
                    <div className="time-slots-grid">
                        {slots.map(slot => {
                            const slotId = getSlotId(slot)
                            const status = getSlotStatus(slot)
                            const isDisabled = status === 'full'
                            const isSelected = selectedSlot === slotId
                            const remaining = getRemainingPlaces(slot)

                            return (
                                <button
                                    key={slotId}
                                    className={`time-slot ${status} ${isSelected ? 'selected' : ''}`}
                                    onClick={() => !isDisabled && setSelectedSlot(slotId)}
                                    disabled={isDisabled}
                                >
                                    <span className="time-slot__label">{formatSlotLabel(slot)}</span>
                                    <span className="time-slot__remaining">
                                        {remaining > 0 ? `${remaining} place${remaining > 1 ? 's' : ''}` : 'Complet'}
                                    </span>
                                </button>
                            )
                        })}
                    </div>
                )}
                <div className="time-slots-legend">
                    <span className="legend-item available">Disponible</span>
                    <span className="legend-item limited">Dernières places</span>
                    <span className="legend-item full">Complet</span>
                </div>
            </div>

            {/* Continue Button */}
            <button
                className="delivery-step__continue"
                onClick={handleContinue}
                disabled={!canContinue()}
            >
                Continuer vers le paiement
            </button>
        </div>
    )
}

export default Delivery
