import random

class Timetable:
    def __init__(self, data):
        self.data = data
        self.classes = []
        self.fitness = 0
    
    def generate_random(self):
        self.classes = []
        days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
        time_slots = ['9:00-10:00','10:00-11:00','11:00-12:00','13:00-14:00','14:00-15:00']
        
        # Map course_id to eligible faculty
        expertise_map = {}
        for entry in self.data['faculty_expertise']:
            expertise_map.setdefault(entry['course_id'], []).append(entry['faculty_id'])
        
        # New logic to gather required classes based on semesters and batches
        required_classes = []
        semester_batches_map = {}
        for batch in self.data['batches']:
            semester_batches_map.setdefault(batch['semester_id'], []).append(batch['batch_id'])

        semester_courses_map = {}
        for sc in self.data['semester_courses']:
            semester_courses_map.setdefault(sc['semester_id'], []).append(sc['course_id'])

        for semester_id, course_ids in semester_courses_map.items():
            batch_ids_for_sem = semester_batches_map.get(semester_id, [])
            for course_id in course_ids:
                for batch_id in batch_ids_for_sem:
                    required_classes.append({'course_id': course_id, 'batch_id': batch_id})

        random.shuffle(required_classes)
        
        assigned_slots = set()
        for req in required_classes:
            course_id = req['course_id']
            batch_id = req['batch_id']
            eligible_faculty_ids = expertise_map.get(course_id, [f['faculty_id'] for f in self.data['faculty']])
            
            # Determine lecture/lab rooms
            is_practical = next((c['is_practical'] for c in self.data['courses'] if c['course_id']==course_id), 0)
            eligible_rooms = [r for r in self.data['classrooms'] if (r['is_lab']==1 if is_practical else r['is_lab']==0)]
            if not eligible_rooms:
                eligible_rooms = self.data['classrooms']
            
            found = False
            random.shuffle(days)
            for day in days:
                random.shuffle(time_slots)
                for slot in time_slots:
                    batch_slot = f"batch-{batch_id}-{day}-{slot}"
                    if batch_slot in assigned_slots:
                        continue
                    available_faculty = [f for f in self.data['faculty'] if f['faculty_id'] in eligible_faculty_ids]
                    random.shuffle(available_faculty)
                    for faculty in available_faculty:
                        faculty_slot = f"faculty-{faculty['faculty_id']}-{day}-{slot}"
                        if faculty_slot in assigned_slots:
                            continue
                        for room in eligible_rooms:
                            room_slot = f"room-{room['classroom_id']}-{day}-{slot}"
                            if room_slot in assigned_slots:
                                continue
                            self.classes.append({
                                'day_of_week': day,
                                'time_slot': slot,
                                'course_id': course_id,
                                'faculty_id': faculty['faculty_id'],
                                'classroom_id': room['classroom_id'],
                                'batch_id': batch_id
                            })
                            assigned_slots.update([batch_slot, faculty_slot, room_slot])
                            found = True
                            break
                        if found: break
                    if found: break
                if found: break
    
    def calculate_fitness(self):
        conflicts = 0
        for i, c1 in enumerate(self.classes):
            for j, c2 in enumerate(self.classes):
                if i >= j: continue
                if c1['day_of_week']==c2['day_of_week'] and c1['time_slot']==c2['time_slot']:
                    if c1['faculty_id']==c2['faculty_id']: conflicts += 100
                    if c1['classroom_id']==c2['classroom_id']: conflicts += 100
                    if c1['batch_id']==c2['batch_id']: conflicts += 100
        self.fitness = 1.0/(1+conflicts)

class GeneticAlgorithm:
    def __init__(self, data, population_size=30, generations=15, mutation_rate=0.05):
        self.data = data
        self.population_size = population_size
        self.generations = generations
        self.mutation_rate = mutation_rate
        self.population = []
    
    def create_initial_population(self):
        self.population = []
        for _ in range(self.population_size):
            tt = Timetable(self.data)
            tt.generate_random()
            tt.calculate_fitness()
            self.population.append(tt)
    
    def evolve(self):
        self.create_initial_population()
        for _ in range(self.generations):
            self.population.sort(key=lambda x: x.fitness, reverse=True)
            next_gen = self.population[:max(1,int(self.population_size*0.1))]
            while len(next_gen) < self.population_size:
                p1 = self.select_parent()
                p2 = self.select_parent()
                child = self.crossover(p1,p2)
                self.mutate(child)
                child.calculate_fitness()
                next_gen.append(child)
            self.population = next_gen
    
    def select_parent(self):
        pool = random.sample(self.population, 5)
        pool.sort(key=lambda x:x.fitness, reverse=True)
        return pool[0]
    
    def crossover(self,p1,p2):
        child = Timetable(self.data)
        split = random.randint(0,len(p1.classes))
        child.classes = p1.classes[:split]+p2.classes[split:]
        return child
    
    def mutate(self,timetable):
        for c in timetable.classes:
            if random.random()<self.mutation_rate:
                if self.data['faculty']:
                    c['faculty_id']=random.choice(self.data['faculty'])['faculty_id']
                if self.data['classrooms']:
                    c['classroom_id']=random.choice(self.data['classrooms'])['classroom_id']
    
    def get_best_timetable(self):
        self.population.sort(key=lambda x:x.fitness, reverse=True)
        return self.population[0]