from ._base import Base
from typing import Optional
from sqlalchemy import BINARY, BigInteger, Boolean, DateTime, Index, PrimaryKeyConstraint, Unicode, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .sql_behandlung import Behandlung
import datetime

class Fall(Base):
    __tablename__ = 'CO6_Medic_Data_Fall'
    __table_args__ = (
        PrimaryKeyConstraint('ID', name='PK_CO6_Medic_Data_Fall_V'),
        Index('IX_CO6_Medic_Data_Fall_Deleted', 'deleted'),
        Index('IX_CO6_Medic_Data_Fall_ENTL_Deleted_AUFN', 'ENTL', 'deleted', 'AUFN'),
        Index('IX_CO6_Medic_Data_Fall_FallNr_Deleted', 'FALLNR', 'deleted'),
        Index('IX_CO6_Medic_Data_Fall_Timestamp', 'Timestamp'),
        Index('IX_CO6_Medic_Data_Fall_V_Patient_ID_AUFN_ENTL', 'Patient_ID', 'AUFN', 'ENTL')
    )

    ID: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    Patient_ID: Mapped[int] = mapped_column(BigInteger, ForeignKey("CO6_Medic_Data_Patient.ID"))
    deleted: Mapped[bool] = mapped_column(Boolean)
    Timestamp: Mapped[bytes] = mapped_column(BINARY(8))
    FALLNR: Mapped[Optional[str]] = mapped_column(Unicode(50, 'Latin1_General_CI_AS'))
    AUFN: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime)
    ENTL: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime)