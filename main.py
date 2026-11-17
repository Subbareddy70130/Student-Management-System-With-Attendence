from pathlib import Path
import sqlite3
from typing import Literal

from fastapi import FastAPI, Form, Request
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field, ValidationError

# Every path is built from this file's own location, so the app works
# no matter which folder you start uvicorn from.
BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "students.db"


class Student(BaseModel):
    name: str = Field(max_length=30, min_length=4)
    age: int = Field(le=120, ge=12)
    gender: Literal["male", "female", "others"]
    marks: int = Field(le=100, ge=0)
    cource: str = Field(min_length=1)
    image: str = ""
    status: Literal[0, 1]


def get_connection():
    return sqlite3.connect(DB_PATH)


def create_table():
    connection = get_connection()
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS students(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            age INTEGER,
            gender TEXT,
            marks INTEGER,
            cource TEXT,
            image TEXT,
            status INTEGER)
        """
    )
    connection.commit()
    connection.close()


create_table()


def clean_row(row):
    """Replace NULLs so the templates never crash on missing values.
    Row order: id, name, age, gender, marks, cource, image, status."""
    if row is None:
        return None
    id_, name, age, gender, marks, cource, image, status = row
    return (
        id_,
        name or "",
        age or 0,
        gender or "",
        marks or 0,
        cource or "",
        image or "",
        1 if status == 1 else 0,
    )


def friendly_errors(error: ValidationError):
    labels = {"name": "Name", "age": "Age", "gender": "Gender", "marks": "Marks",
              "cource": "Course", "image": "Photo link", "status": "Status"}
    return [f"{labels.get(e['loc'][0], e['loc'][0])}: {e['msg']}" for e in error.errors()]


templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))
app = FastAPI()
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")


@app.get("/")
def home(req: Request):
    connection = get_connection()
    rows = connection.execute("SELECT * FROM students ORDER BY id").fetchall()
    connection.close()
    return templates.TemplateResponse(
        request=req, name="home.html", context={"stds": [clean_row(r) for r in rows]}
    )


@app.get("/students/add")
def show_form(req: Request):
    return templates.TemplateResponse(request=req, name="add-student.html", context={})


@app.post("/students/add")
def add_details(
    req: Request,
    name: str = Form(),
    age: int = Form(),
    gender: str = Form(),
    marks: int = Form(),
    cource: str = Form(),
    image: str = Form(default=""),
    status: int = Form(),
):
    submitted = (None, name, age, gender, marks, cource, image, status)
    try:
        obj = Student(name=name.strip(), age=age, gender=gender, marks=marks,
                      cource=cource.strip(), image=image.strip(), status=status)
    except ValidationError as e:
        # Show the form again with what the user typed, plus the problems.
        return templates.TemplateResponse(
            request=req, name="add-student.html", status_code=422,
            context={"form_std": submitted, "errors": friendly_errors(e)},
        )

    connection = get_connection()
    connection.execute(
        "INSERT INTO students(name, age, gender, marks, cource, image, status) VALUES (?,?,?,?,?,?,?)",
        (obj.name, obj.age, obj.gender, obj.marks, obj.cource, obj.image, obj.status),
    )
    connection.commit()
    connection.close()
    return RedirectResponse(url="/", status_code=303)


@app.get("/students/{std_id:int}")
def single_std(req: Request, std_id: int):
    connection = get_connection()
    row = connection.execute("SELECT * FROM students WHERE id = ?", (std_id,)).fetchone()
    connection.close()
    student = clean_row(row)
    return templates.TemplateResponse(
        request=req, name="single-details.html", context={"std": student},
        status_code=200 if student else 404,
    )


@app.get("/students/edit/{std_id:int}")
def edit_student(req: Request, std_id: int):
    connection = get_connection()
    row = connection.execute("SELECT * FROM students WHERE id = ?", (std_id,)).fetchone()
    connection.close()
    student = clean_row(row)
    return templates.TemplateResponse(
        request=req, name="edit-student.html", context={"std": student},
        status_code=200 if student else 404,
    )


@app.post("/students/edit/{std_id:int}")
def edit_std_details(
    req: Request,
    std_id: int,
    name: str = Form(),
    age: int = Form(),
    gender: str = Form(),
    marks: int = Form(),
    cource: str = Form(),
    image: str = Form(default=""),
    status: int = Form(),
):
    submitted = (std_id, name, age, gender, marks, cource, image, status)
    try:
        obj = Student(name=name.strip(), age=age, gender=gender, marks=marks,
                      cource=cource.strip(), image=image.strip(), status=status)
    except ValidationError as e:
        return templates.TemplateResponse(
            request=req, name="edit-student.html", status_code=422,
            context={"std": submitted, "errors": friendly_errors(e)},
        )

    connection = get_connection()
    connection.execute(
        """UPDATE students
           SET name = ?, age = ?, gender = ?, marks = ?, cource = ?, image = ?, status = ?
           WHERE id = ?""",
        (obj.name, obj.age, obj.gender, obj.marks, obj.cource, obj.image, obj.status, std_id),
    )
    connection.commit()
    connection.close()
    return RedirectResponse(url="/", status_code=303)


@app.post("/students/delete/{std_id:int}")
def delete_one(std_id: int):
    connection = get_connection()
    connection.execute("DELETE FROM students WHERE id = ?", (std_id,))
    connection.commit()
    connection.close()
    return RedirectResponse(url="/", status_code=303)
