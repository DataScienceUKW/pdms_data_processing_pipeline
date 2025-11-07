from ._base import Base
from sqlalchemy import BINARY, BigInteger, Boolean, DateTime, Index, PrimaryKeyConstraint, Unicode
from sqlalchemy.orm import Mapped, mapped_column
from typing import Optional
import datetime

class Patient(Base):
    __tablename__ = 'CO6_Medic_Data_Patient'
    __table_args__ = (
        PrimaryKeyConstraint('ID', name='PK_CO6_Medic_Data_Patient_V'),
        Index('IXCO6_Medic_Data_Patient_PatID', 'PatID', 'deleted'),
        Index('IX_CO6_Medic_Data_Patient_Name_VName_Geb_Deleted_PatID', 'Name', 'VNAME', 'GEB', 'deleted', 'PatID'),
        Index('IX_CO6_Medic_Data_Patient_Timestamp', 'Timestamp')
    )

    ID: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    deleted: Mapped[bool] = mapped_column(Boolean)
    Timestamp: Mapped[bytes] = mapped_column(BINARY(8))
    Name: Mapped[Optional[str]] = mapped_column(Unicode(100, 'Latin1_General_CI_AS'))
    VNAME: Mapped[Optional[str]] = mapped_column(Unicode(100, 'Latin1_General_CI_AS'))
    GEB: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime)
    GESCHLECHT: Mapped[Optional[str]] = mapped_column(Unicode(50, 'Latin1_General_CI_AS'))
    PatID: Mapped[Optional[str]] = mapped_column(Unicode(50, 'Latin1_General_CI_AS'))