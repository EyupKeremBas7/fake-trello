import logging

from sqlmodel import Session, select

from app.core.config import settings
from app.core.db import engine
from app.core.security import get_password_hash
from app.models.users import User

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def init_db(session: Session) -> None:
    user = session.exec(
        select(User).where(User.email == settings.FIRST_SUPERUSER)
    ).first()
    
    if not user:
        user = User(
            email=settings.FIRST_SUPERUSER,
            hashed_password=get_password_hash(settings.FIRST_SUPERUSER_PASSWORD),
            is_superuser=True,
            is_active=True,
            full_name="Admin User",
        )
        session.add(user)
        session.commit()
        logger.info(f"Superuser created: {settings.FIRST_SUPERUSER}")
    else:
        logger.info(f"Superuser already exists: {settings.FIRST_SUPERUSER}")


def main() -> None:
    logger.info("Creating initial data")
    with Session(engine) as session:
        init_db(session)
    logger.info("Initial data created")


if __name__ == "__main__":
    main()