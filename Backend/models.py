from db import get_db_connection

def get_batches():
    with get_db_connection() as conn:
        return [dict(row) for row in conn.execute('SELECT * FROM batches')]
def get_courses():
    with get_db_connection() as conn:
        return [dict(row) for row in conn.execute('SELECT * FROM courses')]
def get_faculty():
    with get_db_connection() as conn:
        return [dict(row) for row in conn.execute('SELECT * FROM faculty')]
def get_students():
    with get_db_connection() as conn:
        return [dict(row) for row in conn.execute('SELECT * FROM students')]

def get_faculty_expertise():
    with get_db_connection() as conn:
        return [dict(row) for row in conn.execute('SELECT * FROM faculty_expertise')]

def get_classrooms():
    with get_db_connection() as conn:
        return [dict(row) for row in conn.execute('SELECT * FROM classrooms')]

def get_student_choices():
    with get_db_connection() as conn:
        return [
            {'student_id': row['student_id'], 'batch_id': row['batch_id'],
             'course_ids': list(filter(None, [row['major_course_id'], row['minor_course_id'], row['skill_course_id']]))}
            for row in conn.execute('SELECT * FROM student_choices')
        ]

def get_semester_courses():
    with get_db_connection() as conn:
        return [dict(row) for row in conn.execute('SELECT * FROM semester_courses')]

def get_semesters():
    with get_db_connection() as conn:
        return [dict(row) for row in conn.execute('SELECT * FROM semesters')]
# More as needed for add/update/delete