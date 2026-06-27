from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, scoped_session, sessionmaker


class Base(DeclarativeBase):
    pass


engine = None
Session = scoped_session(sessionmaker(autoflush=False, expire_on_commit=False))


def init_database(url):
    global engine
    engine = create_engine(url, pool_pre_ping=True)
    Session.configure(bind=engine)


def get_session():
    return Session()
