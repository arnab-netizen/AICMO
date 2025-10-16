from sqlalchemy import Column, Integer, String, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

Base = declarative_base()

class ExampleModel(Base):
    __tablename__ = 'example_model'
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)

def run_migrations(engine):
    Base.metadata.create_all(bind=engine)

if __name__ == "__main__":
    engine = create_engine("sqlite:///./test.db")  # Update with your database URL
    run_migrations(engine)