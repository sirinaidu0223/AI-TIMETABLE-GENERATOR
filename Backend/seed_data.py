import sqlite3
import random
import json
from faker import Faker

DATABASE = 'timetable.db'
fake = Faker('en_IN')

def setup_database():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Enable foreign key support
    cursor.execute("PRAGMA foreign_keys = ON;")

    # Drop tables if exist (in proper order considering FKs)
    tables = [
        'student_choices',
        'faculty_expertise',
        'saved_timetables',
        'semester_courses',
        'batches', # Batches must be dropped before programs/semesters
        'students',
        'courses',
        'course_types',
        'semesters',
        'programs',
        'classrooms',
        'faculty'
    ]
    for table in tables:
        cursor.execute(f"DROP TABLE IF EXISTS {table}")

    # Create tables
    cursor.execute('''
        CREATE TABLE programs (
            program_id INTEGER PRIMARY KEY AUTOINCREMENT,
            program_name TEXT NOT NULL
        )
    ''')

    cursor.execute('''
        CREATE TABLE course_types (
            type_id INTEGER PRIMARY KEY AUTOINCREMENT,
            type_name TEXT NOT NULL
        )
    ''')

    cursor.execute('''
        CREATE TABLE faculty (
            faculty_id INTEGER PRIMARY KEY AUTOINCREMENT,
            faculty_name TEXT NOT NULL,
            workload_limit_hours INTEGER,
            non_teaching_periods TEXT
        )
    ''')

    cursor.execute('''
        CREATE TABLE students (
            student_id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_name TEXT NOT NULL
        )
    ''')

    cursor.execute('''
        CREATE TABLE classrooms (
            classroom_id INTEGER PRIMARY KEY AUTOINCREMENT,
            classroom_name TEXT NOT NULL,
            capacity INTEGER,
            is_lab INTEGER
        )
    ''')

    # New `semesters` table
    cursor.execute('''
        CREATE TABLE semesters (
            semester_id INTEGER PRIMARY KEY AUTOINCREMENT,
            semester_name TEXT NOT NULL
        )
    ''')

    # Modify `batches` table to reference `semesters`
    cursor.execute('''
        CREATE TABLE batches (
            batch_id INTEGER PRIMARY KEY AUTOINCREMENT,
            batch_name TEXT NOT NULL,
            program_id INTEGER,
            semester_id INTEGER,
            FOREIGN KEY (program_id) REFERENCES programs(program_id),
            FOREIGN KEY (semester_id) REFERENCES semesters(semester_id)
        )
    ''')

    cursor.execute('''
        CREATE TABLE courses (
            course_id INTEGER PRIMARY KEY AUTOINCREMENT,
            course_name TEXT NOT NULL,
            course_code TEXT NOT NULL,
            credits INTEGER,
            is_practical INTEGER,
            type_id INTEGER,
            FOREIGN KEY (type_id) REFERENCES course_types(type_id)
        )
    ''')
    
    # New `semester_courses` table to link courses to semesters
    cursor.execute('''
        CREATE TABLE semester_courses (
            semester_id INTEGER,
            course_id INTEGER,
            PRIMARY KEY (semester_id, course_id),
            FOREIGN KEY (semester_id) REFERENCES semesters(semester_id),
            FOREIGN KEY (course_id) REFERENCES courses(course_id)
        )
    ''')

    cursor.execute('''
        CREATE TABLE faculty_expertise (
            faculty_id INTEGER,
            course_id INTEGER,
            PRIMARY KEY (faculty_id, course_id),
            FOREIGN KEY (faculty_id) REFERENCES faculty(faculty_id),
            FOREIGN KEY (course_id) REFERENCES courses(course_id)
        )
    ''')

    cursor.execute('''
        CREATE TABLE student_choices (
            student_id INTEGER PRIMARY KEY,
            batch_id INTEGER,
            major_course_id INTEGER,
            minor_course_id INTEGER,
            skill_course_id INTEGER,
            FOREIGN KEY (student_id) REFERENCES students(student_id),
            FOREIGN KEY (batch_id) REFERENCES batches(batch_id),
            FOREIGN KEY (major_course_id) REFERENCES courses(course_id),
            FOREIGN KEY (minor_course_id) REFERENCES courses(course_id),
            FOREIGN KEY (skill_course_id) REFERENCES courses(course_id)
        )
    ''')

    cursor.execute('''
        CREATE TABLE saved_timetables (
            timetable_id INTEGER PRIMARY KEY AUTOINCREMENT,
            timetable_name TEXT NOT NULL,
            schedule_data TEXT NOT NULL,
            timestamp TEXT NOT NULL
        )
    ''')

    # Insert programs
    cursor.executemany("INSERT INTO programs (program_name) VALUES (?)", [('FYUP',), ('B.Ed.',)])
    fyup_program_id = 1

    # Insert course_types
    cursor.executemany("INSERT INTO course_types (type_name) VALUES (?)", [('Major',), ('Minor',), ('Skill-Based',)])

    # Generate non-teaching periods
    time_slots_with_days = [
        f"{day} {time}" for day in ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
        for time in ['9:00-10:00', '10:00-11:00', '11:00-12:00', '13:00-14:00', '14:00-15:00']
    ]

    # Insert faculty
    for _ in range(10):
        name = fake.name()
        workload = random.randint(10, 20)
        non_teaching_periods = random.sample(time_slots_with_days, random.randint(1, 3))
        cursor.execute(
            "INSERT INTO faculty (faculty_name, workload_limit_hours, non_teaching_periods) VALUES (?, ?, ?)",
            (name, workload, json.dumps(non_teaching_periods))
        )

    # Insert students
    for _ in range(50):
        name = fake.name()
        cursor.execute("INSERT INTO students (student_name) VALUES (?)", (name,))

    # Insert classrooms
    classrooms = [
        ('Lecture Hall A', 100, 0),
        ('Physics Lab', 30, 1),
        ('Computer Lab', 40, 1),
        ('Room 205', 50, 0),
        ('Chemistry Lab', 35, 1),
    ]
    cursor.executemany("INSERT INTO classrooms (classroom_name, capacity, is_lab) VALUES (?, ?, ?)", classrooms)

    # Insert courses
    courses = [
        ('Advanced Physics', 'PHY301', 4, 0, 1),
        ('Physics Lab', 'PHY301L', 2, 1, 1),
        ('Sociology Basics', 'SOC101', 3, 0, 2),
        ('Data Science', 'CS102', 4, 0, 1),
        ('Data Science Lab', 'CS102L', 2, 1, 1),
        ('Teaching Methodology', 'BEd201', 5, 0, 1),
        ('Machine Learning', 'AI401', 4, 0, 1),
        ('Web Development', 'WEB201', 3, 0, 3),
        ('Python Programming', 'CS101', 3, 0, 3),
        ('Applied Mathematics', 'MAT301', 4, 0, 1),
    ]
    cursor.executemany("INSERT INTO courses (course_name, course_code, credits, is_practical, type_id) VALUES (?, ?, ?, ?, ?)", courses)

    # Insert Semesters and Semester-Course links
    semesters = [('sem1', 20), ('sem3', 18), ('sem5', 17), ('sem7', 15)]
    all_course_ids = [row['course_id'] for row in cursor.execute("SELECT course_id FROM courses").fetchall()]
    
    for sem_name, num_batches in semesters:
        cursor.execute("INSERT INTO semesters (semester_name) VALUES (?)", (sem_name,))
        semester_id = cursor.lastrowid
        
        # Link at least 3 courses to the semester
        semester_courses = random.sample(all_course_ids, 3)
        for course_id in semester_courses:
            cursor.execute("INSERT INTO semester_courses (semester_id, course_id) VALUES (?, ?)", (semester_id, course_id))

        # Insert new batches for this semester
        for i in range(1, num_batches + 1):
            batch_name = f"ai{i}"
            cursor.execute("INSERT INTO batches (batch_name, program_id, semester_id) VALUES (?, ?, ?)", (batch_name, fyup_program_id, semester_id))


    # Insert faculty expertise (remains the same)
    cursor.execute("SELECT faculty_id FROM faculty")
    faculty_ids = [row['faculty_id'] for row in cursor.fetchall()]
    for faculty_id in faculty_ids:
        expertise_courses = random.sample(all_course_ids, random.randint(2, 4))
        for course_id in expertise_courses:
            cursor.execute(
                "INSERT INTO faculty_expertise (faculty_id, course_id) VALUES (?, ?)",
                (faculty_id, course_id)
            )

    # Insert student choices (remains the same but links to new batches)
    cursor.execute("SELECT student_id FROM students")
    student_ids = [row['student_id'] for row in cursor.fetchall()]
    cursor.execute("SELECT batch_id FROM batches")
    batch_ids = [row['batch_id'] for row in cursor.fetchall()]
    
    major_courses = [c for c in all_course_ids if courses[c-1][4] == 1]
    minor_courses = [c for c in all_course_ids if courses[c-1][4] == 2]
    skill_courses = [c for c in all_course_ids if courses[c-1][4] == 3]

    for student_id in student_ids:
        batch_id = random.choice(batch_ids)
        major = random.choice(major_courses) if major_courses else None
        minor = random.choice(minor_courses) if minor_courses else None
        skill = random.choice(skill_courses) if skill_courses else None
        cursor.execute(
            "INSERT INTO student_choices (student_id, batch_id, major_course_id, minor_course_id, skill_course_id) VALUES (?, ?, ?, ?, ?)",
            (student_id, batch_id, major, minor, skill)
        )

    conn.commit()
    conn.close()
    print("Database 'timetable.db' created and seeded successfully.")

if __name__ == '__main__':
    setup_database()