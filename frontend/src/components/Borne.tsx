import { ReactNode } from 'react'
import './Borne.css'

type BorneProps = {
  children?: ReactNode
}

const Borne = ({ children }: BorneProps) => {
  return (
    <div className="borne" aria-label="Borne de commande 3D">
      <div className="borne__shadow" />
      <div className="borne__body">
        <div className="borne__screen">
          <div className="borne__screen-glow" />
          <div className="borne__screen-content">
            <div className="borne__content">{children}</div>
          </div>
        </div>
        <div className="borne__slots" aria-hidden>
          <div className="borne__slot" />
          <div className="borne__slot borne__slot--long" />
        </div>
      </div>
      <div className="borne__base" />
    </div>
  )
}

export default Borne
