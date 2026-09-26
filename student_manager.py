import streamlit as st
import json
import re
from pathlib import Path
from datetime import datetime

# ============================================================
# STUDENT RECORD MANAGER
# Single Python File | Streamlit
# Professional animated UI | JSON storage
# ============================================================

DATA_FILE = Path("students.json")

# ------------------------- PAGE SETUP -------------------------

st.set_page_config(
    page_title="Student Record Manager",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
)

# -------------------------- STYLING ---------------------------

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=Orbitron:wght@500;700;800&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}

.stApp {
    background:
        radial-gradient(circle at 10% 10%, rgba(56,189,248,.14), transparent 28%),
        radial-gradient(circle at 90% 20%, rgba(139,92,246,.16), transparent 30%),
        radial-gradient(circle at 50% 100%, rgba(16,185,129,.08), transparent 35%),
        #050816;
    color: #e5e7eb;
}

.stApp:before {
    content: "";
    position: fixed;
    inset: 0;
    pointer-events: none;
    background-image:
        linear-gradient(rgba(255,255,255,.018) 1px, transparent 1px),
        linear-gradient(90deg, rgba(255,255,255,.018) 1px, transparent 1px);
    background-size: 45px 45px;
    mask-image: linear-gradient(to bottom, black, transparent);
}

.block-container {
    max-width: 1400px;
    padding-top: 2rem;
    padding-bottom: 4rem;
}

.hero {
    position: relative;
    padding: 38px;
    border: 1px solid rgba(255,255,255,.10);
    border-radius: 28px;
    overflow: hidden;
    background: linear-gradient(135deg,
        rgba(15,23,42,.92),
        rgba(15,23,42,.70));
    box-shadow: 0 25px 80px rgba(0,0,0,.35);
    margin-bottom: 25px;
    animation: fadeUp .8s ease both;
}

.hero:after {
    content: "";
    position: absolute;
    width: 260px;
    height: 260px;
    right: -80px;
    top: -100px;
    border-radius: 50%;
    background: linear-gradient(135deg, #38bdf8, #8b5cf6);
    filter: blur(70px);
    opacity: .28;
}

.hero-title {
    font-family: 'Orbitron', sans-serif;
    font-size: clamp(2rem, 5vw, 4.3rem);
    font-weight: 800;
    letter-spacing: -2px;
    margin: 0;
    background: linear-gradient(90deg, #67e8f9, #818cf8, #c084fc);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}

.hero-subtitle {
    color: #94a3b8;
    font-size: 1rem;
    margin-top: 12px;
}

.badge {
    display: inline-block;
    padding: 7px 13px;
    border-radius: 999px;
    background: rgba(56,189,248,.10);
    border: 1px solid rgba(56,189,248,.25);
    color: #67e8f9;
    font-size: .78rem;
    font-weight: 700;
    letter-spacing: 1px;
    margin-bottom: 16px;
}

.card {
    padding: 24px;
    border-radius: 22px;
    border: 1px solid rgba(255,255,255,.08);
    background: rgba(15,23,42,.70);
    box-shadow: 0 18px 45px rgba(0,0,0,.20);
    backdrop-filter: blur(18px);
    margin-bottom: 20px;
    animation: fadeUp .65s ease both;
}

.metric-card {
    padding: 22px;
    border-radius: 20px;
    border: 1px solid rgba(255,255,255,.08);
    background: linear-gradient(145deg, rgba(15,23,42,.9), rgba(30,41,59,.62));
    transition: transform .25s ease, border-color .25s ease;
}

.metric-card:hover {
    transform: translateY(-5px);
    border-color: rgba(103,232,249,.35);
}

.metric-icon {
    font-size: 1.6rem;
}

.metric-number {
    font-family: 'Orbitron', sans-serif;
    font-size: 2rem;
    font-weight: 800;
    color: #f8fafc;
}

.metric-label {
    color: #94a3b8;
    font-size: .85rem;
}

.section-title {
    font-family: 'Orbitron', sans-serif;
    font-size: 1.1rem;
    color: #f8fafc;
    margin-bottom: 15px;
}

.student-card {
    padding: 20px;
    border-radius: 18px;
    background: rgba(15,23,42,.72);
    border: 1px solid rgba(255,255,255,.07);
    margin-bottom: 12px;
    transition: .25s ease;
}

.student-card:hover {
    transform: translateX(4px);
    border-color: rgba(129,140,248,.35);
    box-shadow: 0 10px 30px rgba(0,0,0,.22);
}

.student-name {
    font-size: 1.05rem;
    font-weight: 800;
    color: #f8fafc;
}

.student-email {
    color: #67e8f9;
    font-size: .88rem;
}

.student-meta {
    color: #94a3b8;
    font-size: .82rem;
    margin-top: 5px;
}

.footer {
    text-align: center;
    color: #64748b;
    padding: 35px 0 10px;
    font-size: .8rem;
}

@keyframes fadeUp {
    from {
        opacity: 0;
        transform: translateY(18px);
    }
    to {
        opacity: 1;
        transform: translateY(0);
    }
}

div[data-testid="stButton"] button {
    border-radius: 12px;
    border: 1px solid rgba(103,232,249,.20);
    background: linear-gradient(135deg, #0891b2, #6366f1);
    color: white;
    font-weight: 700;
    transition: .2s ease;
}

div[data-testid="stButton"] button:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 25px rgba(99,102,241,.25);
}

.stTextInput input,
.stNumberInput input {
    border-radius: 12px !important;
    background: rgba(15,23,42,.75) !important;
}

[data-testid="stSidebar"] {
    background: rgba(2,6,23,.92);
    border-right: 1px solid rgba(255,255,255,.07);
}

[data-testid="stSidebar"] h1,
[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3 {
    font-family: 'Orbitron', sans-serif;
}

.stAlert {
    border-radius: 14px;
}

@media (max-width: 700px) {
    .hero {
        padding: 25px;
    }
    .hero-title {
        font-size: 2rem;
    }
}
</style>
""", unsafe_allow_html=True)

# ---------------------- CUSTOM EXCEPTIONS ---------------------

class ValidationError(Exception):
    """Raised when student data is invalid."""


class DuplicateStudentError(Exception):
    """Raised when a student's email already exists."""


# ---------------------- DATA FUNCTIONS ------------------------

def load_students():
    """Read student records from the JSON file."""
    try:
        if not DATA_FILE.exists():
            return []

        with open(DATA_FILE, "r", encoding="utf-8") as file:
            data = json.load(file)

        if not isinstance(data, list):
            raise ValueError("Student data must be a list.")

        return data

    except json.JSONDecodeError:
        st.error("The student data file contains invalid JSON.")
        return []
    except OSError as error:
        st.error(f"Unable to read student data: {error}")
        return []
    except ValueError as error:
        st.error(str(error))
        return []


def save_students(students):
    """Save student records to a JSON file."""
    try:
        with open(DATA_FILE, "w", encoding="utf-8") as file:
            json.dump(students, file, indent=4, ensure_ascii=False)
        return True

    except OSError as error:
        st.error(f"Unable to save student data: {error}")
        return False


def validate_name(name):
    name = name.strip()

    if not name:
        raise ValidationError("Student name cannot be empty.")

    if len(name) < 2:
        raise ValidationError("Student name must contain at least 2 characters.")

    if not re.fullmatch(r"[A-Za-z .'-]+", name):
        raise ValidationError(
            "Name can contain letters, spaces, dots, apostrophes and hyphens only."
        )

    return name


def validate_age(age):
    try:
        age = int(age)
    except (ValueError, TypeError):
        raise ValidationError("Age must be a valid number.")

    if age < 1 or age > 120:
        raise ValidationError("Age must be between 1 and 120.")

    return age


def validate_email(email):
    email = email.strip().lower()

    # Basic practical email validation using Regex.
    pattern = r"^[^\s@]+@[^\s@]+\.[^\s@]{2,}$"

    if not email:
        raise ValidationError("Email address cannot be empty.")

    if not re.fullmatch(pattern, email):
        raise ValidationError("Please enter a valid email address.")

    return email


def add_student(name, age, email):
    """Validate and add a student."""
    students = load_students()

    name = validate_name(name)
    age = validate_age(age)
    email = validate_email(email)

    if any(student.get("email", "").lower() == email for student in students):
        raise DuplicateStudentError(
            "A student with this email address already exists."
        )

    student = {
        "id": max([s.get("id", 0) for s in students], default=0) + 1,
        "name": name,
        "age": age,
        "email": email,
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }

    students.append(student)

    if save_students(students):
        return student

    raise OSError("Student could not be saved.")


def delete_student(student_id):
    """Delete a student by ID."""
    students = load_students()
    new_students = [s for s in students if s.get("id") != student_id]

    if len(new_students) == len(students):
        return False

    return save_students(new_students)


# ------------------------- SESSION -----------------------------

if "students" not in st.session_state:
    st.session_state.students = load_students()

students = load_students()

# --------------------------- SIDEBAR ---------------------------

with st.sidebar:
    st.markdown("## 🎓 SRM")
    st.caption("Student Record Manager")

    st.markdown("---")

    page = st.radio(
        "Navigation",
        ["🏠 Dashboard", "➕ Add Student", "📚 Student Records"],
        label_visibility="collapsed",
    )

    st.markdown("---")
    st.markdown("### System")
    st.caption("Python • Streamlit • JSON")
    st.caption("Regex validation • Exception handling")

    if st.button("🔄 Refresh Data", use_container_width=True):
        st.session_state.students = load_students()
        st.rerun()

# ---------------------------- HERO -----------------------------

st.markdown("""
<div class="hero">
    <div class="badge">PYTHON • DATA • MANAGEMENT</div>
    <h1 class="hero-title">Student Record Manager</h1>
    <p class="hero-subtitle">
        A professional student management dashboard built with Python,
        Regex validation, JSON file storage and exception handling.
    </p>
</div>
""", unsafe_allow_html=True)

# -------------------------- DASHBOARD -------------------------

if page == "🏠 Dashboard":

    total = len(students)
    average_age = (
        round(sum(s["age"] for s in students) / total, 1)
        if total else 0
    )
    valid_emails = sum(
        1 for s in students if re.fullmatch(
            r"^[^\s@]+@[^\s@]+\.[^\s@]{2,}$",
            s.get("email", "")
        )
    )

    st.markdown('<div class="section-title">Overview</div>', unsafe_allow_html=True)

    c1, c2, c3, c4 = st.columns(4)

    metrics = [
        (c1, "👥", total, "Total Students"),
        (c2, "✉️", valid_emails, "Valid Emails"),
        (c3, "🎂", average_age, "Average Age"),
        (c4, "💾", "JSON", "Storage"),
    ]

    for col, icon, number, label in metrics:
        with col:
            st.markdown(
                f"""
                <div class="metric-card">
                    <div class="metric-icon">{icon}</div>
                    <div class="metric-number">{number}</div>
                    <div class="metric-label">{label}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    st.markdown("<br>", unsafe_allow_html=True)

    left, right = st.columns([1.5, 1])

    with left:
        st.markdown(
            '<div class="section-title">Recent Students</div>',
            unsafe_allow_html=True,
        )

        if students:
            for student in reversed(students[-5:]):
                st.markdown(
                    f"""
                    <div class="student-card">
                        <div class="student-name">
                            #{student["id"]} &nbsp; {student["name"]}
                        </div>
                        <div class="student-email">
                            {student["email"]}
                        </div>
                        <div class="student-meta">
                            Age: {student["age"]} • Added: {student["created_at"]}
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
        else:
            st.info("No student records yet. Add your first student.")

    with right:
        st.markdown(
            '<div class="section-title">Application Features</div>',
            unsafe_allow_html=True,
        )

        features = [
            "➕ Add student records",
            "✉️ Regex email validation",
            "💾 Save data to JSON",
            "📖 Read student data",
            "⚠️ Custom exceptions",
            "🔎 Search records",
            "🗑️ Delete records",
            "📱 Responsive interface",
        ]

        st.markdown(
            '<div class="card">' +
            "".join(
                f'<p style="margin:10px 0;color:#cbd5e1;">{feature}</p>'
                for feature in features
            ) +
            "</div>",
            unsafe_allow_html=True,
        )

# ------------------------- ADD STUDENT -------------------------

elif page == "➕ Add Student":

    st.markdown(
        '<div class="section-title">Create Student Record</div>',
        unsafe_allow_html=True,
    )

    with st.form("student_form", clear_on_submit=True):

        col1, col2 = st.columns(2)

        with col1:
            name = st.text_input(
                "Student Name",
                placeholder="Enter full name",
            )

            age = st.number_input(
                "Age",
                min_value=1,
                max_value=120,
                value=18,
                step=1,
            )

        with col2:
            email = st.text_input(
                "Email Address",
                placeholder="student@example.com",
            )

            st.markdown(
                """
                <div style="
                    padding:16px;
                    border-radius:14px;
                    background:rgba(56,189,248,.06);
                    border:1px solid rgba(56,189,248,.12);
                    color:#94a3b8;
                    font-size:.85rem;
                    margin-top:5px;
                ">
                <b style="color:#67e8f9;">Validation</b><br>
                Name, age and email are validated before saving.
                Duplicate email addresses are rejected automatically.
                </div>
                """,
                unsafe_allow_html=True,
            )

        submitted = st.form_submit_button(
            "🚀 Add Student",
            use_container_width=True,
        )

        if submitted:
            try:
                student = add_student(name, age, email)
                st.session_state.students = load_students()

                st.success(
                    f"Student '{student['name']}' was added successfully!"
                )
                st.balloons()

            except ValidationError as error:
                st.error(f"❌ Validation Error: {error}")

            except DuplicateStudentError as error:
                st.warning(f"⚠️ Duplicate Record: {error}")

            except OSError as error:
                st.error(f"💾 File Error: {error}")

            except Exception as error:
                st.error(f"Unexpected error: {error}")

# ----------------------- STUDENT RECORDS ----------------------

elif page == "📚 Student Records":

    st.markdown(
        '<div class="section-title">Student Database</div>',
        unsafe_allow_html=True,
    )

    search = st.text_input(
        "🔎 Search",
        placeholder="Search by name or email...",
    )

    filtered_students = students

    if search.strip():
        query = search.strip().lower()
        filtered_students = [
            student for student in students
            if query in student.get("name", "").lower()
            or query in student.get("email", "").lower()
        ]

    st.caption(
        f"Showing {len(filtered_students)} of {len(students)} student records"
    )

    if filtered_students:
        for student in filtered_students:
            col1, col2, col3 = st.columns([4, 2, 1])

            with col1:
                st.markdown(
                    f"""
                    <div class="student-card">
                        <div class="student-name">
                            #{student["id"]} {student["name"]}
                        </div>
                        <div class="student-email">
                            {student["email"]}
                        </div>
                        <div class="student-meta">
                            Age: {student["age"]} |
                            Created: {student["created_at"]}
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

            with col2:
                st.write("")

            with col3:
                st.write("")
                if st.button(
                    "🗑️ Delete",
                    key=f"delete_{student['id']}",
                ):
                    try:
                        if delete_student(student["id"]):
                            st.success("Deleted")
                            st.session_state.students = load_students()
                            st.rerun()
                        else:
                            st.warning("Student record not found.")
                    except OSError as error:
                        st.error(f"Delete failed: {error}")

    else:
        st.info("No matching student records found.")

    st.markdown("---")

    # Export current data
    export_data = json.dumps(students, indent=4, ensure_ascii=False)

    st.download_button(
        "📥 Export Student Data",
        data=export_data,
        file_name="students.json",
        mime="application/json",
        use_container_width=True,
    )

# --------------------------- FOOTER ---------------------------

st.markdown(
    """
    <div class="footer">
        Student Record Manager • Built with Python & Streamlit<br>
        Clean architecture • Validation • Exception Handling • JSON Storage
    </div>
    """,
    unsafe_allow_html=True,
)
