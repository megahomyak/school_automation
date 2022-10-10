import bs4
import sys
from dataclasses import dataclass
from typing import List, Optional
from collections import OrderedDict
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
    workers_amount: int
    months: List[Month]


def get_report(file_path) -> Optional[Report]:
    document = open(file_path, encoding="utf-8").read()
    soup = bs4.BeautifulSoup(document, "html.parser")
    tables = soup.find_all("table")
    if not tables:
        return None
    month_descriptions = OrderedDict()
    for table in tables:
        title = table.find_previous("div").text
        if title.split(":")[0] == "Предмет":  # We need this table
            rows = table.find_all("tr")
            months = filter(
                # Removing the service rows (yes, even "August" is a service row)
                lambda m: m.text in (
                    "Сентябрь", "Октябрь", "Ноябрь", "Декабрь", "Январь",
                    "Февраль", "Март", "Апрель", "Май"
                ),
                rows[0].find_all("th"),  # Headings row
            )
            workers_amount = len(rows) - 2  # Rows_amount - headings_amount
            lesson_name = title.split(":")[1].strip()
            index_offset = 2  # Skipping the number and name columns
            for month in months:
                month_name = month.text
                month_description = month_descriptions.setdefault(
                    month_name, MonthDescription(0, 0)
                )
                days_amount = int(month.attrs["colspan"])
                month_description.days_amount += days_amount
                skipped_lessons_amount = 0
                for row in rows[2:]:  # Cutting the heading
                    row = row.find_all("td")
                    for i in range(days_amount):
                        cell_text = row[index_offset + i].text.strip()
                        if cell_text == "Н":
                            month_description.skipped_lessons_amount += 1
                index_offset += days_amount
    return Report(workers_amount, [
        Month(name, description.days_amount, description.skipped_lessons_amount)
        for name, description in month_descriptions.items()
    ])


def ask_for_file():
    file_path = tkinter.filedialog.askopenfilename()
    report = get_report(file_path)
    if report is None:
        report_text.delete("1.0", tkinter.END)
        report_text.insert(tkinter.INSERT, "Это не отчёт!")
    else:
        report_string_lines = []
        total_hours_amount = 0
        for month in report.months:
            hours_amount = (
                month.days_amount * report.workers_amount
                - month.skipped_lessons_amount
            )
            total_hours_amount += hours_amount
            report_string_lines.append(
                f"{month.name}: {hours_amount} человекочасов"
            )
        report_string_lines.append(f"Итого: {total_hours_amount} человекочасов")
        report_text.delete("1.0", tkinter.END)
        report_text.insert(tkinter.INSERT, "\n".join(report_string_lines))


window = tkinter.Tk()
window.title("Счётчик рабочих часов")
window.geometry("500x500")
tkinter.Button(text="Выбрать таблицу", command=ask_for_file).pack(
    padx=10, pady=10
)
report_text = tkinter.scrolledtext.ScrolledText()
report_text.pack(fill="both", expand=True)

window.mainloop()
