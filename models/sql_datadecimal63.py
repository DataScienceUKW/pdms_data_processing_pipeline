from ._base import Base
from sqlalchemy import BINARY, BigInteger, Boolean, DECIMAL, DateTime, Index, Integer, PrimaryKeyConstraint
from sqlalchemy.orm import Mapped, mapped_column
from typing import Optional
import datetime
import decimal

# Patient : CO6_Data_Decimal_6_3
class CO6DataDecimal63(Base):
    __tablename__ = 'CO6_Data_Decimal_6_3_V'
    __table_args__ = (
        PrimaryKeyConstraint('Version', name='PK_CO6_Data_Decimal_6_3'),
        Index('IX_CO6_Data_Decimal_6_3_FlagCurrent_Parent_ID_Parent_VarID_VarID_DateTimeTo_deleted', 'Parent_ID', 'Parent_VarID', 'VarID', 'DateTimeTo', 'FlagCurrent', 'deleted'),
        Index('IX_CO6_Data_Decimal_6_3_ID', 'ID'),
        Index('IX_CO6_Data_Decimal_6_3_SMI', 'VarID', 'deleted'),
        Index('IX_CO6_Data_Decimal_6_3_Timestamp', 'Timestamp'),
        Index('IX_SMI_BECAUSE_WHYNOT_MAX', 'VarID', 'FlagCurrent')
    )

    ID: Mapped[int] = mapped_column(BigInteger)
    VarID: Mapped[int] = mapped_column(Integer)
    Version: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    PreviousVersion: Mapped[int] = mapped_column(BigInteger)
    EntryUser: Mapped[int] = mapped_column(Integer)
    EntryTime: Mapped[datetime.datetime] = mapped_column(DateTime)
    deleted: Mapped[bool] = mapped_column(Boolean)
    Parent_ID: Mapped[int] = mapped_column(BigInteger)
    Parent_VarID: Mapped[int] = mapped_column(Integer)
    DateTimeTo: Mapped[datetime.datetime] = mapped_column(DateTime)
    validated: Mapped[bool] = mapped_column(Boolean)
    val: Mapped[decimal.Decimal] = mapped_column(DECIMAL(9, 3))
    FlagCurrent: Mapped[bool] = mapped_column(Boolean)
    Timestamp: Mapped[bytes] = mapped_column(BINARY(8))

class CO6DataDecimal63Order(Base):
    __tablename__ = 'CO6_Data_Decimal_6_3_Order_V'
    __table_args__ = (
        PrimaryKeyConstraint('Version', name='PK_CO6_Data_Decimal_6_3_Order'),
        Index('IX_CO6_Data_Decimal_6_3_Order', 'Timestamp'),
        Index('IX_CO6_Data_Decimal_6_3_Order_ID', 'ID'),
        Index('IX_CO6_Data_Decimal_6_3_Order_Parent_ID_Parent_VarID_VarID_DateTimeTo', 'Parent_ID', 'Parent_VarID', 'VarID', 'DateTimeTo', 'FlagCurrent', 'deleted')
    )

    ID: Mapped[int] = mapped_column(BigInteger)
    VarID: Mapped[int] = mapped_column(Integer)
    Version: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    PreviousVersion: Mapped[int] = mapped_column(BigInteger)
    EntryUser: Mapped[int] = mapped_column(Integer)
    EntryTime: Mapped[datetime.datetime] = mapped_column(DateTime)
    deleted: Mapped[bool] = mapped_column(Boolean)
    Parent_ID: Mapped[int] = mapped_column(BigInteger)
    Parent_VarID: Mapped[int] = mapped_column(Integer)
    DateTimeTo: Mapped[datetime.datetime] = mapped_column(DateTime)
    validated: Mapped[bool] = mapped_column(Boolean)
    val: Mapped[decimal.Decimal] = mapped_column(DECIMAL(9, 3))
    FlagCurrent: Mapped[int] = mapped_column(Integer)
    Timestamp: Mapped[bytes] = mapped_column(BINARY(8))
    RelatedOrder: Mapped[Optional[int]] = mapped_column(BigInteger)
    RelatedOrderVariable: Mapped[Optional[int]] = mapped_column(Integer)