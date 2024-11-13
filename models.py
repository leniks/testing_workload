from datetime import datetime
from sqlalchemy import DateTime
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import Column, BigInteger, String, CheckConstraint, ForeignKey, Table
from sqlalchemy.orm import relationship

class Base(DeclarativeBase):
    __abstract__ = True
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow,
                                                 nullable=False)


group_workload_association = Table(
    'group_workload',
    Base.metadata,
    Column('group_id', BigInteger, ForeignKey('groups.id'), primary_key=True),
          Column('workload_id', BigInteger, ForeignKey('workloads.id'), primary_key=True)

)

class BaseWithId(Base):
    __abstract__ = True
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

class Employee(BaseWithId):
    __tablename__ = 'employees'  # Убедитесь, что это точно совпадает

    name = Column(String(255), nullable=False, unique=True)
    available_workload = Column(BigInteger, nullable=False)
    extra_workload = Column(BigInteger, nullable=False)

    workloads = relationship("Workload", back_populates="employee", lazy=False)

class Groups(BaseWithId):
    __tablename__ = 'groups'

    name = Column(String(255), nullable=False)
    students_count = Column(BigInteger, nullable=False)

    workloads: Mapped[list["Workload"]] = relationship(
        'Workload',
        secondary=group_workload_association,
        back_populates='groups',
        lazy=False
    )

class Lesson(BaseWithId):
    __tablename__ = 'Lesson'

    stream = Column(String(255), nullable=False)
    name = Column(String(255), nullable=False)
    year = Column(String(255), comment='2023/2024 или 2024/2025', nullable=False)
    semestr = Column(BigInteger, nullable=False)
    faculty = Column(String(255), nullable=False)

    workloads = relationship("Workload", back_populates="lesson", lazy=False)

class Workload(BaseWithId):
    __tablename__ = 'workloads'  # Используйте согласованную конвенцию именования

    type = Column(String(255), nullable=False)
    workload = Column(BigInteger, nullable=False)
    employee_id = Column(BigInteger, ForeignKey('employees.id'), nullable=True)  # Исправленная ссылка
    lesson_id = Column(BigInteger, ForeignKey('Lesson.id'), nullable=False)
    mega_workload_id = Column(BigInteger, ForeignKey('mega_workloads.id'), nullable=True)

    employee = relationship("Employee", back_populates="workloads", lazy=False)
    lesson = relationship("Lesson", back_populates="workloads", lazy=False)
    mega_workload = relationship("MegaWorkload", back_populates="workloads", lazy=False)
    groups: Mapped[list['Groups']] = relationship(
        'Groups',
        secondary=group_workload_association,
        back_populates='workloads',
        lazy=False
    )

    def __repr__(self):
        return f'Workload<id={self.id}, type={self.type}, workload={self.workload}'


class MegaWorkload(BaseWithId):
    __tablename__ = 'mega_workloads'

    type = Column(String(255), CheckConstraint("type IN ('Индивидуальная', 'Практика', 'Лабораторная')"), nullable=True)
    employee_name = Column(String(255), nullable=True)
    workloads = relationship("Workload", back_populates="mega_workload", lazy=False)
