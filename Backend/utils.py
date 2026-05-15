def format_timetable_for_frontend(classes, data):
    teachers_map = {f['faculty_id']:f['faculty_name'] for f in data.get('faculty',[])}
    courses_map = {c['course_id']:c['course_name'] for c in data.get('courses',[])}
    classrooms_map = {c['classroom_id']:c['classroom_name'] for c in data.get('classrooms',[])}
    batches_map = {b['batch_id']:b['batch_name'] for b in data.get('batches',[])}
    formatted=[]
    for c in classes:
        formatted.append({
            'day': c['day_of_week'],
            'time': c['time_slot'],
            'subject': courses_map.get(c['course_id']),
            'teacher': teachers_map.get(c['faculty_id']),
            'room': classrooms_map.get(c['classroom_id']),
            'batch': batches_map.get(c['batch_id']),
            'batch_id': c['batch_id'],
            'faculty_id': c['faculty_id'],
        })
    return formatted
