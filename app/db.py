from sqlmodel import SQLModel, Session, create_engine, delete
from sqlalchemy.pool import NullPool, QueuePool

from app.core.config import Settings
from app.models import AuditLog, Campaign, DeliveryAttempt, Recipient

settings = Settings()

is_sqlite = settings.database_url.startswith("sqlite")

if is_sqlite:
    engine = create_engine(
        settings.database_url,
        echo=False,
        connect_args={"check_same_thread": False},
        poolclass=NullPool,
    )
else:
    engine = create_engine(
        settings.database_url,
        echo=False,
        poolclass=QueuePool,
        pool_size=settings.db_pool_size,
        max_overflow=settings.db_max_overflow,
        pool_pre_ping=True,
    )


def init_db() -> None:
    SQLModel.metadata.create_all(engine)


def get_session() -> Session:
    return Session(engine)


def reset_db() -> None:
    init_db()
    with Session(engine) as session:
        session.exec(delete(DeliveryAttempt))
        session.exec(delete(AuditLog))
        session.exec(delete(Recipient))
        session.exec(delete(Campaign))
        session.commit()
