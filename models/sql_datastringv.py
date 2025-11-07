from ._base import Base
from sqlalchemy import BINARY, BigInteger, Boolean, DateTime, Index, Integer, PrimaryKeyConstraint, Unicode
from sqlalchemy.orm import Mapped, mapped_column
from typing import Optional
import datetime

class DataStringV(Base):
    __tablename__ = 'CO6_Data_String_V'
    __table_args__ = (
        PrimaryKeyConstraint('Version', name='PK_CO6_Data_String'),
        Index('IX_CO6_Data_String_ID', 'ID'),
        Index('IX_CO6_Data_String_Parent_ID_Parent_VarID_VarID_DateTimeTo', 'Parent_ID', 'Parent_VarID', 'VarID', 'DateTimeTo', 'FlagCurrent', 'deleted'),
        Index('IX_CO6_Data_String_Parent_ID_Parent_VarID_VarID_Deleted_FlagCurrent', 'Parent_ID', 'Parent_VarID', 'VarID', 'deleted', 'FlagCurrent'),
        Index('IX_CO6_Data_String_Timestamp', 'Timestamp'),
        Index('IX_CO6_Data_String_VarID_FlagCurrent', 'VarID', 'FlagCurrent')
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
    val: Mapped[str] = mapped_column(Unicode(collation='Latin1_General_CI_AS'))
    FlagCurrent: Mapped[bool] = mapped_column(Boolean)
    Timestamp: Mapped[bytes] = mapped_column(BINARY(8))

class CO6DataStringOrder(Base):
    __tablename__ = 'CO6_Data_String_Order_V'
    __table_args__ = (
        PrimaryKeyConstraint('Version', name='PK_CO6_Data_String_Order'),
        Index('IX_CO6_Data_String_Order', 'Timestamp'),
        Index('IX_CO6_Data_String_Order_ID', 'ID'),
        Index('IX_CO6_Data_String_Order_Parent_ID_Parent_VarID_VarID_DateTimeTo', 'Parent_ID', 'Parent_VarID', 'VarID', 'DateTimeTo', 'FlagCurrent', 'deleted')
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
    val: Mapped[str] = mapped_column(Unicode(collation='Latin1_General_CI_AS'))
    FlagCurrent: Mapped[bool] = mapped_column(Boolean)
    Timestamp: Mapped[bytes] = mapped_column(BINARY(8))
    RelatedOrder: Mapped[Optional[int]] = mapped_column(BigInteger)
    RelatedOrderVariable: Mapped[Optional[int]] = mapped_column(Integer)