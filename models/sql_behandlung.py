from ._base import Base
from typing import Optional
from sqlalchemy import BINARY, BigInteger, Boolean, DateTime, Index, Integer, PrimaryKeyConstraint, Unicode, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
import datetime

# Behandlung : CO6_Medic_Data_Behandlung
class Behandlung(Base):
    __tablename__ = 'CO6_Medic_Data_Behandlung'
    __table_args__ = (
        PrimaryKeyConstraint('ID', name='PK_CO6_Medic_Data_Behandlung_V'),
        Index('IX_CO6_Medic_Data_Behandlung_Ende_deleted_POE', 'Ende', 'deleted', 'POE'),
        Index('IX_CO6_Medic_Data_Behandlung_FOE', 'FOE'),
        Index('IX_CO6_Medic_Data_Behandlung_Geschlossen', 'Geschlossen'),
        Index('IX_CO6_Medic_Data_Behandlung_POE', 'POE'),
        Index('IX_CO6_Medic_Data_Behandlung_Timestamp', 'Timestamp'),
        Index('IX_CO6_Medic_Data_Behandlung_V_Fall_ID_Start_Ende', 'Fall_ID', 'Start', 'Ende')
    )

    ID: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    Fall_ID: Mapped[int] = mapped_column(BigInteger, ForeignKey("CO6_Medic_Data_Fall.ID"), )
    deleted: Mapped[bool] = mapped_column(Boolean)
    Timestamp: Mapped[bytes] = mapped_column(BINARY(8))
    Auftrag: Mapped[Optional[str]] = mapped_column(Unicode(collation='Latin1_General_CI_AS'))
    Start: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime)
    Ende: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime)
    POE: Mapped[Optional[int]] = mapped_column(Integer)
    FOE: Mapped[Optional[int]] = mapped_column(Integer)
    Geschlossen: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime)
    Nummer: Mapped[Optional[str]] = mapped_column(Unicode(50, 'Latin1_General_CI_AS'))