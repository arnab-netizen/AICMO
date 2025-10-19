from sqlalchemy.orm import declarative_base, Mapped, mapped_column
from sqlalchemy import String, TIMESTAMP
from sqlalchemy.sql import func

Base = declarative_base()


class Site(Base):
    __tablename__ = "site"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    slug: Mapped[str] = mapped_column(String, nullable=True)
    created_at: Mapped[str] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())
