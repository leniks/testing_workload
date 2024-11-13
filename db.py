import asyncio

import pandas as pd
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.future import select
from sqlalchemy.util import await_only
from sqlalchemy.exc import NoResultFound

from models import Groups, Workload, Lesson, BaseWithId, MegaWorkload  # Импортируйте ваши модели

DATABASE_URL = "postgresql+asyncpg://myuser:mypassword@localhost:5432/mydatabase"

# Создание асинхронного движка и сессии
engine = create_async_engine(DATABASE_URL, echo=False)
AsyncSessionLocal = sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
Base = declarative_base()


general_workloads = [("Практическое занятие", "Практические занятия нагрузка"),
                     ("Лабораторная работа", "Лабораторные работы нагрузка")]
individual_workloads = [("Курсовая работа", "Курсовая работа "),
                        ("Курсовой проект", "Курсовой проект "),
                        ("Консультация", "Конс "),
                        ("Рейтинг", "Рейтинг "),
                        ("Зачёт", "Зачёт "),
                        ("Экзамен", "Экзамен ")]


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(BaseWithId.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
        await conn.run_sync(BaseWithId.metadata.create_all)


async def group_exists(db: AsyncSession, name: str) -> bool:
    result = await db.execute(select(Groups).filter(Groups.name == name))
    return result.scalars().first() is not None


async def create_group(db: AsyncSession, name: str, number_of_students: int):
    new_group = Groups(name=name, students_count=number_of_students)
    db.add(new_group)
    return new_group


async def find_group(db: AsyncSession, name: str):
    group = await db.execute(select(Groups).filter(Groups.name == name))
    group = group.scalars().first()

    if group is None:
        raise NoResultFound(f"Группа с названием '{name}' не найдена.")

    return group


async def lesson_exists(db: AsyncSession, stream: str, name: str, semestr: int, faculty: str) -> bool:
    result = await db.execute(select(Lesson).filter(
        Lesson.stream == stream,
        Lesson.name == name,
        Lesson.semestr == semestr,
        Lesson.faculty == faculty
    ))
    return result.scalars().first() is not None


async def create_lesson(db: AsyncSession, stream: str, name: str, semestr: int, faculty: str, year="2024/2025"):
    new_lesson = Lesson(stream=stream, name=name, year=year, semestr=semestr, faculty=faculty)
    db.add(new_lesson)
    return new_lesson


async def find_lesson(db: AsyncSession, stream: str, name: str, semestr: int, faculty: str):
    lesson = await db.execute(select(Lesson).filter(
                Lesson.stream == stream,
                Lesson.name == name,
                Lesson.semestr == semestr,
                Lesson.faculty == faculty))
    lesson = lesson.scalars().first()

    if lesson is None:
        raise NoResultFound(f"Дисциплина с названием '{name}' не найдена.")

    return lesson


async def create_mega_workload(db: AsyncSession, type_m: str, employee_name=None):
    new_mega_workload = MegaWorkload(type=type_m, employee_name=employee_name)
    db.add(new_mega_workload)
    return new_mega_workload


async def create_workload(db: AsyncSession, type_w: str, workload: int, lesson: Lesson, groups: [Groups]):
    new_workload = Workload(
        type=type_w,
        workload=workload,
        lesson=lesson,
        groups=groups
    )
    db.add(new_workload)
    return new_workload


async def main():
    await init_db()  # Инициализация базы данных
    async with (AsyncSessionLocal() as db):  # Создаем асинхронную сессию
        df = pd.read_excel("itog.xlsx")

        df.columns.values[6] = "to_drop"
        df = df.drop(df.columns[0], axis=1)

        df = df.sort_values(["Поток ", "Название предмета", "Семестр ", "Лекции нагрузка"],
                            ascending=[True, True, True, False])
        df = df.reset_index(drop=True)

        for index, row in df.iterrows():
            if row['Поток '] != 0:

                group_name = row['Название']
                number_of_students = row['Студентов ']
                if not await group_exists(db, group_name):
                    group = await create_group(db, group_name, number_of_students)
                else:
                    group = await find_group(db, group_name)

                discipline_name = row['Название предмета']
                semestr = row['Семестр ']
                faculty = row['Факультет']
                stream = str(row['Поток '])

                if not await lesson_exists(db, stream, discipline_name, semestr, faculty):
                    lesson = await create_lesson(db, stream, discipline_name, semestr, faculty)
                    workload_lection = await create_workload(db, type_w="Лекция", workload=row["Лекции нагрузка"],
                                                             lesson=lesson, groups=[group])
                    megaworkload_ind = await create_mega_workload(db, type_m="Индивидуальная")
                    workload_lection.mega_workload = megaworkload_ind

                else:
                    workload_lection.groups.append(group)

                for type_of_single_workload in general_workloads + individual_workloads:
                    if row[type_of_single_workload[1]] != 0:
                        workload = await create_workload(db, type_w=type_of_single_workload[0],
                                                         workload=row[type_of_single_workload[1]], lesson=lesson,
                                                         groups=[group])

                        if type_of_single_workload[0] == "Практическое занятие":
                            type_m = "Практика"
                            megaworkload_pract = await create_mega_workload(db, type_m)
                            workload.mega_workload = megaworkload_pract

                        elif type_of_single_workload[0] == "Лабораторная работа":
                            type_m = "Лабораторная"
                            megaworkload_lab = await create_mega_workload(db, type_m)
                            workload.mega_workload = megaworkload_lab

                        else:
                            workload.mega_workload = megaworkload_ind

        await db.commit()

if __name__ == "__main__":
    asyncio.run(main())
