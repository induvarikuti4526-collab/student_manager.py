from __future__ import annotations

import argparse
import csv
import json
import re
import sqlite3
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

DEFAULT_DB = "students.db"

EMAIL_PATTERN = re.compile(
    r"^[A-Za-z0-9.!#$%&'*+/=?^_`{|}~-]+@"
    r"[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)+$"
)
ROLL_PATTERN = re.compile(r"^[A-Za-z0-9/_-]{1,30}$")
NAME_PATTERN = re.compile(r"^[A-Za-z][A-Za-z .'-]{1,99}$")
GRADE_PATTERN = re.compile(r"^[A-Za-z0-9 .+_-]{1,30}$")


class StudentManagerError(Exception):
    """Base application exception."""


class ValidationError(StudentManagerError):
    """Raised when validation fails."""


class DuplicateStudentError(StudentManagerError):
    """Raised when duplicate student data is detected."""


class StudentNotFoundError(StudentManagerError):
    """Raised when a student is not found."""


class DatabaseError(StudentManagerError):
    """Raised for database errors."""


@dataclass(frozen=True)
class Student:
    id: int
    roll_number: str
    name: str
    email: str
    age: int
    grade: str
    gpa: float
    created_at: str
    updated_at: str

    @classmethod
    def from_row(cls, row: sqlite3.Row) -> "Student":
        return cls(
            id=row["id"],
            roll_number=row["roll_number"],
            name=row["name"],
            email=row["email"],
            age=row["age"],
            grade=row["grade"],
            gpa=row["gpa"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )


class Validator:
    @staticmethod
    def roll_number(value: str) -> str:
        value = str(value).strip()
        if not value:
            raise ValidationError("Roll number cannot be empty.")
        if not ROLL_PATTERN.fullmatch(value):
            raise ValidationError(
                "Roll number may contain letters, numbers, /, _ and - only."
            )
        return value

    @staticmethod
    def name(value: str) -> str:
        value = " ".join(str(value).strip().split())
        if not value:
            raise ValidationError("Name cannot be empty.")
        if not NAME_PATTERN.fullmatch(value):
            raise ValidationError(
                "Name must contain letters, spaces, apostrophes, periods or hyphens only."
            )
        return value

    @staticmethod
    def email(value: str) -> str:
        value = str(value).strip().lower()
        if not EMAIL_PATTERN.fullmatch(value):
            raise ValidationError("Please enter a valid email address.")
        return value

    @staticmethod
    def age(value: str | int) -> int:
        try:
            age = int(value)
        except (TypeError, ValueError) as exc:
            raise ValidationError("Age must be a whole number.") from exc
        if not 1 <= age <= 120:
            raise ValidationError("Age must be between 1 and 120.")
        return age

    @staticmethod
    def grade(value: str) -> str:
        value = " ".join(str(value).strip().split())
        if not value:
            raise ValidationError("Grade/Class cannot be empty.")
        if not GRADE_PATTERN.fullmatch(value):
            raise ValidationError("Invalid grade/class format.")
        return value

    @staticmethod
    def gpa(value: str | float | int) -> float:
        try:
            score = float(value)
        except (TypeError, ValueError) as exc:
            raise ValidationError("GPA/Marks must be a number.") from exc
        if not 0 <= score <= 100:
            raise ValidationError("GPA/Marks must be between 0 and 100.")
        return round(score, 2)

    @staticmethod
    def student_id(value: str | int) -> int:
        try:
            student_id = int(value)
        except (TypeError, ValueError) as exc:
            raise ValidationError("Student ID must be a number.") from exc
        if student_id <= 0:
            raise ValidationError("Student ID must be positive.")
        return student_id


class DatabaseManager:
    def __init__(self, database_path: str = DEFAULT_DB):
        self.database_path = Path(database_path).expanduser().resolve()
        try:
            self.connection = sqlite3.connect(self.database_path)
            self.connection.row_factory = sqlite3.Row
            self.connection.execute("PRAGMA foreign_keys = ON")
            self.create_tables()
        except sqlite3.Error as exc:
            raise DatabaseError(f"Could not open database: {exc}") from exc

    def create_tables(self) -> None:
        try:
            self.connection.execute(
                """
                CREATE TABLE IF NOT EXISTS students (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    roll_number TEXT NOT NULL UNIQUE,
                    name TEXT NOT NULL,
                    email TEXT NOT NULL UNIQUE,
                    age INTEGER NOT NULL,
                    grade TEXT NOT NULL,
                    gpa REAL NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )
            self.connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_students_name ON students(name)"
            )
            self.connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_students_grade ON students(grade)"
            )
            self.connection.commit()
        except sqlite3.Error as exc:
            raise DatabaseError(str(exc)) from exc

    def close(self) -> None:
        try:
            self.connection.close()
        except sqlite3.Error:
            pass


class StudentRepository:
    def __init__(self, database: DatabaseManager):
        self.db = database

    @staticmethod
    def now() -> str:
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def add(self, roll_number: str, name: str, email: str,
            age: int, grade: str, gpa: float) -> Student:
        roll_number = Validator.roll_number(roll_number)
        name = Validator.name(name)
        email = Validator.email(email)
        age = Validator.age(age)
        grade = Validator.grade(grade)
        gpa = Validator.gpa(gpa)
        timestamp = self.now()

        try:
            cursor = self.db.connection.execute(
                """
                INSERT INTO students
                (roll_number, name, email, age, grade, gpa, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (roll_number, name, email, age, grade, gpa, timestamp, timestamp),
            )
            self.db.connection.commit()
            return self.get_by_id(cursor.lastrowid)
        except sqlite3.IntegrityError as exc:
            self.db.connection.rollback()
            message = str(exc).lower()
            if "roll_number" in message:
                raise DuplicateStudentError(
                    "A student with this roll number already exists."
                ) from exc
            if "email" in message:
                raise DuplicateStudentError(
                    "A student with this email already exists."
                ) from exc
            raise DatabaseError(str(exc)) from exc
        except sqlite3.Error as exc:
            self.db.connection.rollback()
            raise DatabaseError(str(exc)) from exc

    def get_by_id(self, student_id: int) -> Student:
        student_id = Validator.student_id(student_id)
        try:
            row = self.db.connection.execute(
                "SELECT * FROM students WHERE id = ?", (student_id,)
            ).fetchone()
        except sqlite3.Error as exc:
            raise DatabaseError(str(exc)) from exc

        if row is None:
            raise StudentNotFoundError(
                f"Student with ID {student_id} was not found."
            )
        return Student.from_row(row)

    def get_all(self) -> list[Student]:
        try:
            rows = self.db.connection.execute(
                "SELECT * FROM students ORDER BY id"
            ).fetchall()
            return [Student.from_row(row) for row in rows]
        except sqlite3.Error as exc:
            raise DatabaseError(str(exc)) from exc

    def search(self, keyword: str) -> list[Student]:
        keyword = keyword.strip()
        if not keyword:
            return self.get_all()

        pattern = f"%{keyword}%"
        try:
            rows = self.db.connection.execute(
                """
                SELECT * FROM students
                WHERE roll_number LIKE ?
                   OR name LIKE ?
                   OR email LIKE ?
                   OR grade LIKE ?
                ORDER BY id
                """,
                (pattern, pattern, pattern, pattern),
            ).fetchall()
            return [Student.from_row(row) for row in rows]
        except sqlite3.Error as exc:
            raise DatabaseError(str(exc)) from exc

    def update(self, student_id: int, roll_number: Optional[str] = None,
               name: Optional[str] = None, email: Optional[str] = None,
               age: Optional[int] = None, grade: Optional[str] = None,
               gpa: Optional[float] = None) -> Student:
        existing = self.get_by_id(student_id)

        new_roll = (
            Validator.roll_number(roll_number)
            if roll_number is not None else existing.roll_number
        )
        new_name = (
            Validator.name(name)
            if name is not None else existing.name
        )
        new_email = (
            Validator.email(email)
            if email is not None else existing.email
        )
        new_age = (
            Validator.age(age)
            if age is not None else existing.age
        )
        new_grade = (
            Validator.grade(grade)
            if grade is not None else existing.grade
        )
        new_gpa = (
            Validator.gpa(gpa)
            if gpa is not None else existing.gpa
        )

        try:
            self.db.connection.execute(
                """
                UPDATE students
                SET roll_number = ?, name = ?, email = ?, age = ?,
                    grade = ?, gpa = ?, updated_at = ?
                WHERE id = ?
                """,
                (
                    new_roll, new_name, new_email, new_age,
                    new_grade, new_gpa, self.now(), existing.id
                ),
            )
            self.db.connection.commit()
            return self.get_by_id(existing.id)
        except sqlite3.IntegrityError as exc:
            self.db.connection.rollback()
            message = str(exc).lower()
            if "roll_number" in message:
                raise DuplicateStudentError(
                    "Another student already uses this roll number."
                ) from exc
            if "email" in message:
                raise DuplicateStudentError(
                    "Another student already uses this email."
                ) from exc
            raise DatabaseError(str(exc)) from exc
        except sqlite3.Error as exc:
            self.db.connection.rollback()
            raise DatabaseError(str(exc)) from exc

    def delete(self, student_id: int) -> Student:
        student = self.get_by_id(student_id)
        try:
            self.db.connection.execute(
                "DELETE FROM students WHERE id = ?", (student.id,)
            )
            self.db.connection.commit()
            return student
        except sqlite3.Error as exc:
            self.db.connection.rollback()
            raise DatabaseError(str(exc)) from exc

    def statistics(self) -> dict[str, Any]:
        try:
            total = self.db.connection.execute(
                "SELECT COUNT(*) FROM students"
            ).fetchone()[0]
            average = self.db.connection.execute(
                "SELECT AVG(gpa) FROM students"
            ).fetchone()[0]
            top_row = self.db.connection.execute(
                """
                SELECT * FROM students
                ORDER BY gpa DESC, name ASC
                LIMIT 1
                """
            ).fetchone()
            grade_rows = self.db.connection.execute(
                """
                SELECT grade, COUNT(*) AS count
                FROM students
                GROUP BY grade
                ORDER BY grade
                """
            ).fetchall()

            return {
                "total": total,
                "average_gpa": round(average or 0, 2),
                "top_student": Student.from_row(top_row) if top_row else None,
                "grade_distribution": {
                    row["grade"]: row["count"] for row in grade_rows
                },
            }
        except sqlite3.Error as exc:
            raise DatabaseError(str(exc)) from exc


class ExportService:
    HEADERS = [
        "ID", "Roll Number", "Name", "Email", "Age",
        "Grade", "GPA", "Created At", "Updated At"
    ]

    @classmethod
    def export_csv(cls, students: list[Student], filename: str) -> Path:
        path = Path(filename).expanduser().resolve()
        with path.open("w", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)
            writer.writerow(cls.HEADERS)
            for student in students:
                writer.writerow([
                    student.id, student.roll_number, student.name,
                    student.email, student.age, student.grade,
                    f"{student.gpa:.2f}", student.created_at,
                    student.updated_at
                ])
        return path

    @classmethod
    def export_json(cls, students: list[Student], filename: str) -> Path:
        path = Path(filename).expanduser().resolve()
        data = [
            {
                "id": s.id,
                "roll_number": s.roll_number,
                "name": s.name,
                "email": s.email,
                "age": s.age,
                "grade": s.grade,
                "gpa": s.gpa,
                "created_at": s.created_at,
                "updated_at": s.updated_at,
            }
            for s in students
        ]
        with path.open("w", encoding="utf-8") as file:
            json.dump(data, file, indent=4, ensure_ascii=False)
        return path


class TerminalUI:
    WIDTH = 86

    @staticmethod
    def clear() -> None:
        print("\n" * 2)

    @staticmethod
    def title() -> None:
        print("=" * TerminalUI.WIDTH)
        print(" " * 28 + "STUDENT RECORD MANAGER")
        print("=" * TerminalUI.WIDTH)

    @staticmethod
    def section(title: str) -> None:
        print("\n" + "-" * TerminalUI.WIDTH)
        print(f"  {title}")
        print("-" * TerminalUI.WIDTH)

    @staticmethod
    def success(message: str) -> None:
        print(f"\n[OK] {message}")

    @staticmethod
    def error(message: str) -> None:
        print(f"\n[ERROR] {message}")

    @staticmethod
    def info(message: str) -> None:
        print(f"\n[INFO] {message}")

    @staticmethod
    def pause() -> None:
        try:
            input("\nPress Enter to continue...")
        except EOFError:
            pass

    @staticmethod
    def prompt(label: str) -> str:
        try:
            return input(label).strip()
        except EOFError:
            raise KeyboardInterrupt

    @staticmethod
    def display_student(student: Student) -> None:
        print()
        print(f"ID          : {student.id}")
        print(f"Roll Number : {student.roll_number}")
        print(f"Name        : {student.name}")
        print(f"Email       : {student.email}")
        print(f"Age         : {student.age}")
        print(f"Grade       : {student.grade}")
        print(f"GPA/Marks   : {student.gpa:.2f}")
        print(f"Created     : {student.created_at}")
        print(f"Updated     : {student.updated_at}")

    @staticmethod
    def display_table(students: list[Student]) -> None:
        if not students:
            TerminalUI.info("No student records found.")
            return

        headers = ["ID", "Roll Number", "Name", "Email", "Age", "Grade", "GPA"]
        rows = [
            [
                str(s.id), s.roll_number, s.name, s.email,
                str(s.age), s.grade, f"{s.gpa:.2f}"
            ]
            for s in students
        ]

        widths = [
            max(len(headers[i]), max(len(row[i]) for row in rows))
            for i in range(len(headers))
        ]

        print()
        print(" | ".join(headers[i].ljust(widths[i]) for i in range(len(headers))))
        print("-+-".join("-" * width for width in widths))
        for row in rows:
            print(" | ".join(row[i].ljust(widths[i]) for i in range(len(row))))
        print(f"\nTotal records displayed: {len(students)}")


class StudentApplication:
    def __init__(self, database_path: str):
        self.db = DatabaseManager(database_path)
        self.repository = StudentRepository(self.db)

    def close(self) -> None:
        self.db.close()

    def menu(self) -> None:
        print("\n+--------------------------------------------------------------+")
        print("|                 STUDENT RECORD MANAGER                       |")
        print("+--------------------------------------------------------------+")
        print("|  1. Add Student                                              |")
        print("|  2. View All Students                                        |")
        print("|  3. View Single Student                                      |")
        print("|  4. Search Students                                          |")
        print("|  5. Update Student                                           |")
        print("|  6. Delete Student                                           |")
        print("|  7. Summary Statistics                                       |")
        print("|  8. Export CSV / JSON                                        |")
        print("|  9. Exit                                                     |")
        print("+--------------------------------------------------------------+")

    def add_student(self) -> None:
        TerminalUI.section("ADD NEW STUDENT")
        student = self.repository.add(
            TerminalUI.prompt("Roll/Registration Number: "),
            TerminalUI.prompt("Name: "),
            TerminalUI.prompt("Email: "),
            TerminalUI.prompt("Age: "),
            TerminalUI.prompt("Grade/Class: "),
            TerminalUI.prompt("GPA/Marks (0-100): "),
        )
        TerminalUI.success(
            f"Student '{student.name}' added successfully with ID {student.id}."
        )

    def view_all(self) -> None:
        TerminalUI.section("ALL STUDENT RECORDS")
        TerminalUI.display_table(self.repository.get_all())

    def view_single(self) -> None:
        TerminalUI.section("VIEW STUDENT")
        student = self.repository.get_by_id(
            TerminalUI.prompt("Enter Student ID: ")
        )
        TerminalUI.display_student(student)

    def search_students(self) -> None:
        TerminalUI.section("SEARCH STUDENTS")
        keyword = TerminalUI.prompt(
            "Enter name, email, roll number or grade: "
        )
        TerminalUI.display_table(self.repository.search(keyword))

    def update_student(self) -> None:
        TerminalUI.section("UPDATE STUDENT")
        student = self.repository.get_by_id(
            TerminalUI.prompt("Enter Student ID: ")
        )

        print("\nLeave a field empty to keep its current value.")

        updated = self.repository.update(
            student.id,
            roll_number=TerminalUI.prompt(
                f"Roll Number [{student.roll_number}]: "
            ) or None,
            name=TerminalUI.prompt(
                f"Name [{student.name}]: "
            ) or None,
            email=TerminalUI.prompt(
                f"Email [{student.email}]: "
            ) or None,
            age=TerminalUI.prompt(
                f"Age [{student.age}]: "
            ) or None,
            grade=TerminalUI.prompt(
                f"Grade [{student.grade}]: "
            ) or None,
            gpa=TerminalUI.prompt(
                f"GPA/Marks [{student.gpa:.2f}]: "
            ) or None,
        )

        TerminalUI.success(
            f"Student '{updated.name}' updated successfully."
        )

    def delete_student(self) -> None:
        TerminalUI.section("DELETE STUDENT")
        student = self.repository.get_by_id(
            TerminalUI.prompt("Enter Student ID: ")
        )
        TerminalUI.display_student(student)

        if TerminalUI.prompt("\nType DELETE to confirm: ") != "DELETE":
            TerminalUI.info("Delete operation cancelled.")
            return

        deleted = self.repository.delete(student.id)
        TerminalUI.success(
            f"Student '{deleted.name}' deleted successfully."
        )

    def statistics(self) -> None:
        TerminalUI.section("SUMMARY STATISTICS")
        stats = self.repository.statistics()

        print(f"  Total Students : {stats['total']}")
        print(f"  Average GPA    : {stats['average_gpa']:.2f}")

        if stats["top_student"]:
            s = stats["top_student"]
            print(f"  Top Performer  : {s.name} ({s.gpa:.2f})")
        else:
            print("  Top Performer  : No records")

        print("\n  Grade Distribution:")
        if stats["grade_distribution"]:
            for grade, count in stats["grade_distribution"].items():
                print(f"    {grade:<15} {count}")
        else:
            print("    No records")

    def export_data(self) -> None:
        TerminalUI.section("EXPORT STUDENT DATA")
        students = self.repository.get_all()

        if not students:
            TerminalUI.info("There are no student records to export.")
            return

        choice = TerminalUI.prompt(
            "1. Export CSV\n2. Export JSON\n\nChoose format [1-2]: "
        )

        if choice == "1":
            filename = TerminalUI.prompt(
                "CSV filename [students.csv]: "
            ) or "students.csv"
            path = ExportService.export_csv(students, filename)
            TerminalUI.success(f"CSV exported successfully: {path}")

        elif choice == "2":
            filename = TerminalUI.prompt(
                "JSON filename [students.json]: "
            ) or "students.json"
            path = ExportService.export_json(students, filename)
            TerminalUI.success(f"JSON exported successfully: {path}")

        else:
            TerminalUI.error("Invalid export option.")

    def run(self) -> None:
        TerminalUI.clear()
        TerminalUI.title()
        TerminalUI.info(f"SQLite database: {self.db.database_path}")

        while True:
            try:
                self.menu()
                choice = TerminalUI.prompt("\nSelect an option [1-9]: ")

                actions = {
                    "1": self.add_student,
                    "2": self.view_all,
                    "3": self.view_single,
                    "4": self.search_students,
                    "5": self.update_student,
                    "6": self.delete_student,
                    "7": self.statistics,
                    "8": self.export_data,
                }

                if choice == "9":
                    TerminalUI.success(
                        "Thank you for using Student Record Manager."
                    )
                    break

                action = actions.get(choice)
                if action:
                    action()
                else:
                    TerminalUI.error("Invalid option. Please select 1-9.")

                TerminalUI.pause()

            except KeyboardInterrupt:
                print("\n")
                TerminalUI.info("Application closed by user.")
                break
            except StudentManagerError as exc:
                TerminalUI.error(str(exc))
                TerminalUI.pause()
            except Exception as exc:
                TerminalUI.error(f"Unexpected error: {exc}")
                TerminalUI.pause()


def create_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Student Record Manager using SQLite."
    )
    parser.add_argument(
        "--db",
        default=DEFAULT_DB,
        help="SQLite database file.",
    )
    parser.add_argument(
        "--export-csv",
        metavar="FILE",
        help="Export all students to CSV and exit.",
    )
    parser.add_argument(
        "--export-json",
        metavar="FILE",
        help="Export all students to JSON and exit.",
    )
    return parser


def main() -> int:
    parser = create_parser()
    args = parser.parse_args()
    application = None

    try:
        application = StudentApplication(args.db)

        if args.export_csv:
            path = ExportService.export_csv(
                application.repository.get_all(),
                args.export_csv,
            )
            print(f"CSV exported successfully: {path}")
            return 0

        if args.export_json:
            path = ExportService.export_json(
                application.repository.get_all(),
                args.export_json,
            )
            print(f"JSON exported successfully: {path}")
            return 0

        application.run()
        return 0

    except StudentManagerError as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("\nApplication stopped.")
        return 0
    finally:
        if application is not None:
            application.close()


if __name__ == "__main__":
    raise SystemExit(main())