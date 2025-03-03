from sqlalchemy import Column, Integer, String, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Используем SQLite для локального хранения данных; файл bot_data.db создастся в корневой папке проекта
engine = create_engine('sqlite:///bot_data.db', echo=False)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

class Teacher(Base):
    __tablename__ = "teachers"
    id = Column(Integer, primary_key=True, index=True)
    telegram_id = Column(Integer, unique=True, index=True, nullable=False)
    login = Column(String, nullable=False)
    role = Column(String, default="Участник школы и студии")

class Student(Base):
    __tablename__ = "students"
    id = Column(Integer, primary_key=True, index=True)
    telegram_id = Column(Integer, unique=True, index=True, nullable=False)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    phone = Column(String, nullable=False)
    role = Column(String, default="Ученик")
    next_lesson = Column(String, nullable=True)
    homework = Column(String, nullable=True)

# Создаем таблицы, если они ещё не существуют
Base.metadata.create_all(bind=engine)
