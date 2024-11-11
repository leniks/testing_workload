import asyncio
from tokenize import group

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


async def lesson_exists(db: AsyncSession, name: str, semestr: int, faculty: str) -> bool:
    result = await db.execute(select(Lesson).filter(
        Lesson.name == name,
        Lesson.semestr == semestr,
        Lesson.faculty == faculty
    ))
    return result.scalars().first() is not None


async def create_lesson(db: AsyncSession, name: str, semestr: int, faculty: str, year="2024/2025"):
    new_lesson = Lesson(name=name, year=year, semestr=semestr, faculty=faculty)
    db.add(new_lesson)
    return new_lesson


async def find_lesson(db: AsyncSession, name: str, semestr: int, faculty: str):
    lesson = await db.execute(select(Lesson).filter(Lesson.name == name,
                Lesson.semestr == semestr,
                Lesson.faculty == faculty))
    lesson = lesson.scalars().first()

    if lesson is None:
        raise NoResultFound(f"Дисциплина с названием '{name}' не найдена.")

    return lesson

async def mega_workload_exists(db: AsyncSession, lesson_name: str, type_m: str, semestr: int, faculty: str) -> bool:
    result = await db.execute(select(MegaWorkload).filter(
        MegaWorkload.lesson_name == lesson_name,
        MegaWorkload.type == type_m,
        MegaWorkload.semestr == semestr,
        MegaWorkload.faculty == faculty
    ))
    return result.scalars().first() is not None

async def create_mega_workload(db: AsyncSession, lesson_name: str, type_m: str, semestr: int, faculty: str):
    new_mega_workload = MegaWorkload(lesson_name=lesson_name, type=type_m, semestr=semestr, faculty=faculty)
    db.add(new_mega_workload)

async def find_mega_workload(db: AsyncSession, lesson_name: str, type_m: str, semestr: int, faculty: str):
    mega_workload = await db.execute(select(MegaWorkload).filter(MegaWorkload.lesson_name == lesson_name,
                                                    MegaWorkload.type == type_m,
                                                    MegaWorkload.semestr == semestr,
                                                    MegaWorkload.faculty == faculty))
    mega_workload = mega_workload.scalars().first()

    if mega_workload is None:
        raise NoResultFound(f"Нагрузка с названием '{lesson_name}' не найдена.")

    return mega_workload

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

        for index, row in df.iterrows():
            group_name = row['Название']
            number_of_students = row['Студентов ']
            if not await group_exists(db, group_name):
                group = await create_group(db, group_name, number_of_students)
            else:
                group = await find_group(db, group_name)

            discipline_name = row['Название предмета']
            semestr = row['Семестр ']
            faculty = row['Факультет']
            if not await lesson_exists(db, discipline_name, semestr, faculty):
                lesson = await create_lesson(db, discipline_name, semestr, faculty)
            else:
                lesson = await find_lesson(db, discipline_name, semestr, faculty)

            for type_of_single_workload in general_workloads + individual_workloads:
                if row[type_of_single_workload[1]] != 0:
                    await create_workload(db, type_w=type_of_single_workload[0], workload=row[type_of_single_workload[1]], lesson=lesson,
                                          groups=[group])

                    if type_of_single_workload[0] == "Практическое занятие":
                        type_m = "Практика"

                    elif type_of_single_workload[0] == "Лабораторная работа":
                        type_m = "Лабораторная"
                    else:
                        type_m = "Индивидуальная"
                    if not await mega_workload_exists(db, discipline_name, type_m, row['Семестр '], faculty):
                        await create_mega_workload(db, discipline_name, type_m, row['Семестр '], faculty)


        df.columns.values[6] = "to_drop"
        df = df.drop(df.columns[0], axis=1)

        n = 0
        index_of_sem = df.columns.get_loc("Семестр ")
        index_of_stream = df.columns.get_loc("Поток ")

        index_of_group = df.columns.get_loc("Название")

        index_of_dicsipline = df.columns.get_loc("Название предмета")
        index_of_faculty = df.columns.get_loc("Факультет")

        lection_workload = df.columns.get_loc("Лекции нагрузка")

        df = df.sort_values(["Поток ", "Название предмета", "Семестр "])
        df = df.reset_index(drop=True)

        df.loc[len(df)] = 0
        len_df = df.shape[0]

        groups_list = []

        while n < len_df - 1:

            while df.iloc[n, index_of_stream] == 0:
                n += 1

            lesson = await find_lesson(db, df.iloc[n, index_of_dicsipline], df.iloc[n, index_of_sem],
                                 df.iloc[n, index_of_faculty])
            lec_workload = df.iloc[n, lection_workload]

            while (df.iloc[n, index_of_sem],
                   df.iloc[n, index_of_stream],
                   df.iloc[n, index_of_dicsipline]) == (df.iloc[n + 1, index_of_sem],
                                                        df.iloc[n + 1, index_of_stream],
                                                        df.iloc[n + 1, index_of_dicsipline]):

                group = await find_group(db, df.iloc[n, index_of_group])
                groups_list.append(group)
                n += 1

            group = await find_group(db, df.iloc[n, index_of_group])
            groups_list.append(group)

            await create_workload(db, type_w="Лекция", workload=lec_workload, lesson=lesson, groups=groups_list)

            groups_list.clear()

            n += 1

        workloads = await db.execute(select(Workload))
        workloads = workloads.unique().scalars().all()

        for workload in workloads:
            if workload.type == "Практическое занятие":
                type_m = "Практика"

            elif workload.type == "Лабораторная работа":
                type_m = "Лабораторная"
            else:
                type_m = "Индивидуальная"

            mega_workload = await find_mega_workload(db, workload.lesson.name, type_m, workload.lesson.semestr,
                                               workload.lesson.faculty)

            workload.mega_workload = mega_workload


        await db.commit()

if __name__ == "__main__":
    asyncio.run(main())
