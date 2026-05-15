from flask import Blueprint, jsonify, request,send_file
from db import get_db_connection
from models import get_batches, get_courses, get_faculty, get_semester_courses, get_semesters, get_students, get_faculty_expertise, get_classrooms, get_student_choices
from genetic_algo import Timetable, GeneticAlgorithm
import json
from datetime import datetime
from utils import format_timetable_for_frontend
import sqlite3
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, KeepTogether
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
import io





bp = Blueprint('timetable', __name__)

# Helper for all-data fetch
def fetch_all_data():
    return {
        'faculty': get_faculty(),
        'students': get_students(),
        'classrooms': get_classrooms(),
        'batches': get_batches(),
        'courses': get_courses(),
        'faculty_expertise': get_faculty_expertise(),
        'student_choices': get_student_choices(),
        'semester_courses': get_semester_courses(),
        'semesters': get_semesters()
    }

# --- Routes (use these for all front-end calls) ---
@bp.route('/api/get_batches')
def api_batches():
    return jsonify(get_batches())
@bp.route('/api/get_courses')
def api_courses():
    return jsonify(get_courses())
@bp.route('/api/get_faculty')
def api_faculty():
    return jsonify(get_faculty())
@bp.route('/api/get_students')
def api_students():
    return jsonify(get_students())
@bp.route('/api/get_semesters')
def api_semesters():
    return jsonify(get_semesters())


@bp.route('/api/add_student', methods=['POST'])
def api_add_student():
    data = request.json
    with get_db_connection() as conn:
        cursor = conn.cursor()
        try:
            cursor.execute("INSERT INTO students (student_id, student_name) VALUES (?, ?)", (data['student_id'], data['student_name']))
            course_choices = data.get('course_choices', [])
            batch_id = data['batch_id']
            major_course_id = course_choices[0] if len(course_choices)>0 else None
            minor_course_id = course_choices[1] if len(course_choices)>1 else None
            skill_course_id = course_choices[2] if len(course_choices)>2 else None
            cursor.execute("INSERT INTO student_choices (student_id, batch_id, major_course_id, minor_course_id, skill_course_id) VALUES (?, ?, ?, ?, ?)",
                           (data['student_id'], batch_id, major_course_id, minor_course_id, skill_course_id))
            conn.commit()
            return jsonify({'message':'Student added successfully'}),200
        except Exception as e:
            conn.rollback()
            return jsonify({'error':str(e)}),500

@bp.route('/api/add_faculty', methods=['POST'])
def api_add_faculty():
    data = request.json
    with get_db_connection() as conn:
        cursor = conn.cursor()
        try:
            cursor.execute("INSERT INTO faculty (faculty_id, faculty_name, workload_limit_hours) VALUES (?, ?, ?)",
                           (data['faculty_id'], data['faculty_name'], data['workload_limit_hours']))
            for course_id in data.get('expertise',[]):
                cursor.execute("INSERT INTO faculty_expertise (faculty_id, course_id) VALUES (?, ?)", (data['faculty_id'], course_id))
            conn.commit()
            return jsonify({'message':'Faculty added successfully'}),200
        except Exception as e:
            conn.rollback()
            return jsonify({'error':str(e)}),500

@bp.route('/api/generate_optimal_timetable')
def api_generate_timetable():
    all_data = fetch_all_data()
    if not all_data['students'] or not all_data['faculty'] or not all_data['courses']:
        return jsonify({'error':'Insufficient data'}),400
    
    # New logic: Generate timetables per semester to handle large data
    final_timetable_classes = []
    semesters = all_data['semesters']
    
    for semester in semesters:
        semester_id = semester['semester_id']
        
        # Filter data for the current semester
        semester_batches = [b for b in all_data['batches'] if b['semester_id'] == semester_id]
        semester_courses = [c for c in all_data['semester_courses'] if c['semester_id'] == semester_id]
        
        # Build a temporary data object for this semester
        semester_data = {
            'faculty': all_data['faculty'],
            'students': all_data['students'],
            'classrooms': all_data['classrooms'],
            'batches': semester_batches,
            'courses': all_data['courses'],
            'faculty_expertise': all_data['faculty_expertise'],
            'semester_courses': semester_courses,
            'semesters': [semester]
        }
        
        # Run the genetic algorithm for this semester's data
        ga = GeneticAlgorithm(semester_data)
        ga.evolve()
        best_timetable_for_semester = ga.get_best_timetable()
        
        # Add the classes to the final timetable list
        final_timetable_classes.extend(best_timetable_for_semester.classes)
        
    # Format the combined timetable for the frontend
    formatted = format_timetable_for_frontend(final_timetable_classes, all_data)
    
    return jsonify(formatted)

@bp.route('/api/get_batch_timetable/<int:batch_id>')
def get_batch_timetable(batch_id):
    conn = get_db_connection()
    try:
        # Fetch the latest saved timetable
        row = conn.execute('SELECT schedule_data FROM saved_timetables ORDER BY timestamp DESC LIMIT 1').fetchone()
        if not row:
            return jsonify({'error': 'No timetable available'}), 404

        all_data = fetch_all_data()
        timetable = json.loads(row['schedule_data'])
        filtered = [c for c in timetable if c['batch_id']==batch_id]
        return jsonify(filtered)
    finally:
        conn.close()

@bp.route('/api/get_semester_timetable/<int:semester_id>')
def get_semester_timetable(semester_id):
    conn = get_db_connection()
    try:
        # Get all batches for the selected semester
        batches_in_semester = conn.execute('SELECT batch_id FROM batches WHERE semester_id = ?', (semester_id,)).fetchall()
        batch_ids = [row['batch_id'] for row in batches_in_semester]

        # Fetch the latest saved timetable
        row = conn.execute('SELECT schedule_data FROM saved_timetables ORDER BY timestamp DESC LIMIT 1').fetchone()
        if not row:
            return jsonify({'error': 'No timetable available'}), 404

        timetable = json.loads(row['schedule_data'])
        
        # Filter the timetable to include only classes for batches in this semester
        filtered = [c for c in timetable if c.get('batch_id') in batch_ids]

        return jsonify(filtered)
    finally:
        conn.close()


@bp.route('/api/get_faculty_timetable/<int:faculty_id>')
def get_faculty_timetable(faculty_id):
    conn = get_db_connection()
    try:
        # Fetch the latest saved timetable
        row = conn.execute('SELECT schedule_data FROM saved_timetables ORDER BY timestamp DESC LIMIT 1').fetchone()
        if not row:
            return jsonify({'error': 'No timetable available'}), 404

        timetable = json.loads(row['schedule_data'])
        # Filter by faculty
        filtered = [c for c in timetable if c.get('faculty_id') == faculty_id]
        return jsonify(filtered)
    finally:
        conn.close()


@bp.route('/api/get_student_timetable/<int:student_id>')
def get_student_timetable(student_id):
    conn = get_db_connection()
    try:
        # 1. Get student choices
        student_choice = conn.execute('SELECT * FROM student_choices WHERE student_id=?', (student_id,)).fetchone()
        if not student_choice:
            return jsonify({'error': 'Student not found'}), 404

        batch_id = student_choice['batch_id']
        course_ids = list(filter(None, [
            student_choice['major_course_id'],
            student_choice['minor_course_id'],
            student_choice['skill_course_id']
        ]))

        # Map course_id -> course_name
        courses_map = {c['course_id']: c['course_name'] for c in conn.execute('SELECT course_id, course_name FROM courses')}

        # Get course names for this student
        course_names = [courses_map[cid] for cid in course_ids if cid in courses_map]

        # 2. Get latest saved timetable
        row = conn.execute('SELECT schedule_data FROM saved_timetables ORDER BY timestamp DESC LIMIT 1').fetchone()
        if not row:
            return jsonify({'error': 'No timetable available'}), 404

        timetable = json.loads(row['schedule_data'])

        # 3. Filter timetable by batch and student courses (using course names)
        filtered = [c for c in timetable if c['batch_id'] == batch_id and c['subject'] in course_names]

        return jsonify(filtered)
    finally:
        conn.close()

@bp.route('/api/save_timetable', methods=['POST'])
def save_timetable():
    data = request.json
    if not data or not isinstance(data,list):
        return jsonify({'error':'Invalid timetable data'}),400
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        name = f"Timetable - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        schedule_json = json.dumps(data)
        timestamp = datetime.now().isoformat()
        cursor.execute(
            "INSERT INTO saved_timetables (timetable_name, schedule_data, timestamp) VALUES (?, ?, ?)",
            (name, schedule_json, timestamp)
        )
        conn.commit()
        return jsonify({'message':'Timetable saved successfully'}),200
    except sqlite3.Error as e:
        conn.rollback()
        return jsonify({'error':str(e)}),500
    finally:
        conn.close()

@bp.route('/api/get_saved_timetables')
def get_saved_timetables():
    conn = get_db_connection()
    try:
        rows = conn.execute(
            'SELECT timetable_id,timetable_name,schedule_data,timestamp FROM saved_timetables ORDER BY timestamp DESC'
        ).fetchall()
        timetables = []
        for row in rows:
            timetables.append({
                'timetable_id':row['timetable_id'],
                'timetable_name':row['timetable_name'],
                'timestamp':row['timestamp'],
                'schedule':json.loads(row['schedule_data'])
            })
        return jsonify(timetables)
    except sqlite3.Error as e:
        return jsonify({'error':str(e)}),500
    finally:
        conn.close()

@bp.route('/api/get_timetable/<int:timetable_id>')
def get_timetable(timetable_id):
    conn = get_db_connection()
    try:
        row = conn.execute('SELECT timetable_name,schedule_data FROM saved_timetables WHERE timetable_id=?',(timetable_id,)).fetchone()
        if not row:
            return jsonify({'error':'Timetable not found'}),404
        return jsonify(json.loads(row['schedule_data']))
    except sqlite3.Error as e:
        return jsonify({'error':str(e)}),500
    finally:
        conn.close()


# --- Export Timetables ---
@bp.route('/export', methods=['POST'])
def export_timetables():
    data = request.get_json()
    timetable_ids = data.get('ids', [])
    export_format = data.get('format', 'pdf')

    if not timetable_ids:
        return jsonify({"error": "No timetables selected"}), 400

    conn = get_db_connection()
    cursor = conn.cursor()

    placeholders = ','.join(['?'] * len(timetable_ids))
    rows = cursor.execute(
        f"SELECT timetable_name, schedule_data FROM saved_timetables WHERE timetable_id IN ({placeholders}) ORDER BY timestamp",
        timetable_ids
    ).fetchall()
    conn.close()

    if not rows:
        return jsonify({"error": "No timetables found"}), 404

    if export_format == 'pdf':
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=30)
        elements = []
        styles = getSampleStyleSheet()

        days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
        time_slots = ['9:00-10:00', '10:00-11:00', '11:00-12:00', '13:00-14:00', '14:00-15:00']

        for row in rows:
            schedule_data = json.loads(row['schedule_data'])
            
            batches = {}
            for entry in schedule_data:
                batch_name = entry.get('batch', 'Unknown Batch')
                if batch_name not in batches:
                    batches[batch_name] = []
                batches[batch_name].append(entry)

            if not batches:
                continue

            for batch_name, classes in sorted(batches.items()):
                # Create the table and its title
                title = Paragraph(f"Timetable for: {batch_name}", styles['h2'])
                spacer = Spacer(1, 10)
                
                schedule_map = {}
                for c in classes:
                    schedule_map[(c['day'], c['time'])] = c

                table_data = [['Day'] + time_slots]
                for day in days:
                    row_data = [Paragraph(day, styles['Normal'])]
                    for slot in time_slots:
                        class_info = schedule_map.get((day, slot))
                        if class_info:
                            cell_content = [
                                Paragraph(f"{class_info.get('subject', 'N/A')}", styles['Normal']),
                                Paragraph(f"{class_info.get('teacher', 'N/A')}", styles['Normal']),
                                Paragraph(f"{class_info.get('room', 'N/A')}", styles['Normal']),
                            ]
                            row_data.append(cell_content)
                        else:
                            row_data.append("")
                    table_data.append(row_data)

                t = Table(table_data, colWidths=[60] + [90] * len(time_slots))
                t.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black),
                    ('FONTSIZE', (0, 0), (-1, -1), 8),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                    ('TOPPADDING', (0, 0), (-1, -1), 6),
                ]))

                # KEY CHANGE: Wrap the title and table in KeepTogether
                # This treats the whole block as one item, preventing it from splitting across pages.
                block = KeepTogether([title, spacer, t, Spacer(1, 20)])
                elements.append(block)

        doc.build(elements)
        buffer.seek(0)
        return send_file(buffer, as_attachment=True, download_name="timetables_final.pdf", mimetype="application/pdf")

    return jsonify({"error": "Unsupported format"}), 400