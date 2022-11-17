import re
import bs4
import sys
from dataclasses import dataclass
from typing import List, Optional
from collections import OrderedDict
import os
import tkinter
import tkinter.filedialog
import tkinter.scrolledtext


@dataclass
class MonthDescription:
    days_amount: int
    skipped_lessons_amount: int


@dataclass
class Month:
    name: str
    days_amount: int
    skipped_lessons_amount: int


@dataclass
class Report:
    subject: str
    workers_amount: int
    months: List[Month]


MONTH_NAMES = ["Январь", "Февраль", "Март", "Апрель", "Май", "Июнь", "Июль", "Август", "Сентябрь", "Октябрь", "Ноябрь", "Декабрь"]


def get_report(file_path) -> Optional[Report]:
    document = open(file_path, encoding="utf-8").read()
    soup = bs4.BeautifulSoup(document, "html.parser")
    try:
        subject = soup.find("br").find_next("span").find_next("span").find_next("span").contents[1].strip()
    except AttributeError:
        return None
    tables = soup.find_all("table")
    if not tables:
        return None
    month_descriptions = OrderedDict()
    for table in tables:
        full_title = table.find_previous("div").text
        if full_title.split(":")[0] == "Предмет":  # We need this table
            rows = table.find_all("tr")
            months = list(filter(
                # Removing the service rows
                lambda m: m.text in MONTH_NAMES,
                rows[0].find_all("th"),  # Headings row
            ))
            days = iter(map(lambda day: day.text, rows[1].find_all(True)))
            workers_amount = len(rows) - 2  # Rows_amount - headings_amount
            index_offset = 2  # Skipping the number and name columns
            for month in months:
                month_name = month.text
                stated_days_amount = int(month.attrs["colspan"])
                # Looking at the day numbers, if one is weird - it is not a day, but a weirdly placed heading
                day_numbers = (next(days) for _ in range(stated_days_amount))
                actual_days_amount = len([day for day in day_numbers if re.fullmatch(r"\d+", day)])
                if actual_days_amount == 0:
                    continue
                month_description = month_descriptions.setdefault(
                    month_name,
                    MonthDescription(days_amount=0, skipped_lessons_amount=0)
                )
                month_description.days_amount += actual_days_amount
                for row in rows[2:]:  # Cutting the heading
                    row = row.find_all("td")
                    for i in range(actual_days_amount):
                        cell_text = row[index_offset + i].text.strip()
                        if cell_text == "Н":
                            month_description.skipped_lessons_amount += 1
                index_offset += actual_days_amount
    return Report(subject, workers_amount, [
        Month(name, description.days_amount, description.skipped_lessons_amount)
        for name, description in month_descriptions.items()
    ])


subject_to_report = OrderedDict()


def ask_for_a_report():
    file_path = tkinter.filedialog.askopenfilename()
    if file_path:
        report = get_report(file_path)
        if report is None:
            tkinter.messagebox.showerror("Неподходящий файл", "Выбранный файл не является отчётом!")
        else:
            subject_to_report[report.subject] = report
            report_text.delete("1.0", tkinter.END)
            report_text.insert(tkinter.INSERT, "\n".join(subject_to_report.keys()))


CSV_DELIMITER = ";"


def save_the_report():
    lines = [CSV_DELIMITER.join([""] + MONTH_NAMES + ["Итого"])]
    for report in subject_to_report.values():
        month_name_to_contents = {}
        for month in report.months:
            month_name_to_contents[month.name] = month
        hours = [report.subject]
        total_hours_amount = 0
        for month_name in MONTH_NAMES:
            try:
                month = month_name_to_contents[month_name]
            except KeyError:
                hours_amount_str = ""
            else:
                hours_amount = (
                    month.days_amount * report.workers_amount
                    - month.skipped_lessons_amount
                )
                total_hours_amount += hours_amount
                hours_amount_str = str(hours_amount)
            hours.append(hours_amount_str)
        hours.append(str(total_hours_amount))
        lines.append(CSV_DELIMITER.join(hours))
    file_number = 0
    while True:
        file_name = "report"
        if file_number:
            file_name += f" ({file_number})"
        file_name += ".csv"
        if os.path.exists(file_name):
            file_number += 1
        else:
            break
    with open(file_name, "w", encoding="cp1251") as f:
        f.write("\n".join(lines))
    tkinter.messagebox.showinfo("Сохранено", f"Таблица сохранена в файл \"{file_name}\".")


window = tkinter.Tk()
window.title("Счётчик рабочих часов")
window.geometry("500x500")
tkinter.Button(text="Выбрать таблицу", command=ask_for_a_report).pack(
    padx=10, pady=10
)
tkinter.Button(text="Сохранить", command=save_the_report).pack(
    padx=10, pady=10
)
report_text = tkinter.scrolledtext.ScrolledText()
report_text.pack(fill="both", expand=True)

window.mainloop()
