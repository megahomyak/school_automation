import bs4
import sys
from dataclasses import dataclass
from typing import List
from collections import OrderedDict


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


def get_report(file_path) -> Report:
    document = open(file_path, encoding="utf-8").read()
    soup = bs4.BeautifulSoup(document, "html.parser")
    tables = soup.find_all("table")
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


report = get_report(sys.argv[1])
for month in report.months:
    taught_lessons_number = (
        month.days_amount * report.workers_amount
        - month.skipped_lessons_amount
    )
    print(f"{month.name}: {taught_lessons_number} отработанных дней")
