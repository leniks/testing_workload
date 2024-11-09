# import pandas as pd
#
# df = pd.read_excel("itog.xlsx")
#
# df.columns.values[6] = "to_drop"
# df = df.drop(df.columns[0], axis=1)
#
# n = 0
# index_of_sem = df.columns.get_loc("Семестр ")
# index_of_stream = df.columns.get_loc("Поток ")
# index_of_dicsipline = df.columns.get_loc("Название предмета")
# index_of_group = df.columns.get_loc("Название")
# index_of_lesson_name = df.columns.get_loc("Название предмета")
#
# df = df.sort_values(["Поток ", "Название предмета", "Семестр "])
# df = df.reset_index(drop=True)
#
# df.loc[len(df)] = 0
# len_df = df.shape[0]
#
# lesson = ''
# groups_list = []
# # df.to_excel('aaaaaaaaaaaa.xlsx')
# while n < len_df-1:
#
#     while df.iloc[n, index_of_stream] == 0:
#         n+=1
#
#     lesson = df.iloc[n, index_of_lesson_name]
#
#     while (df.iloc[n, index_of_sem],
#            df.iloc[n, index_of_stream],
#            df.iloc[n, index_of_dicsipline]) == (df.iloc[n+1, index_of_sem],
#                                                 df.iloc[n+1, index_of_stream],
#                                                 df.iloc[n+1, index_of_dicsipline]):
#
#         groups_list.append(df.iloc[n, index_of_group])
#         n+=1
#
#     groups_list.append(df.iloc[n, index_of_group])
#
#     print(lesson, groups_list)
#     lesson = ""
#     groups_list.clear()
#
#     n+=1

general_workloads = [("Практическое занятие", "Практические занятия нагрузка"),
                     ("Лабораторная работа", "Лабораторные работы нагрузка")]

individual_workloads = [("Курсовая работа", "Курсовая работа "),
                        ("Курсовой проект", "Курсовой проект "),
                        ("Консультация", "Конс "),
                        ("Рейтинг", "Рейтинг "),
                        ("Зачёт", "Зачёт "),
                        ("Экзамен", "Экзамен ")]
print(general_workloads + individual_workloads)