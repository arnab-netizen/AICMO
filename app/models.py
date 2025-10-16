from __future__ import annotations
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import String, BigInteger


class Base(DeclarativeBase):
    pass


class Site(Base):
    __tablename__ = "site"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    slug: Mapped[str] = mapped_column(String(120), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)


class SiteSection(Base):
    __tablename__ = "site_section"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    site_id: Mapped[int] = mapped_column(BigInteger)
    type: Mapped[str] = mapped_column(String(120), nullable=False)
    props: Mapped[str] = mapped_column(String, nullable=False)  # JSON string of props
    order: Mapped[int] = mapped_column(BigInteger, nullable=False)
