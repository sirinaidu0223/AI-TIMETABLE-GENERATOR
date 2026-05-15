🗓️ AI Timetable Generator
An intelligent semester timetable generator powered by a Genetic Algorithm. Built with Python (Flask) for the backend and a lightweight HTML/CSS/JS frontend, this app automatically generates conflict-free academic timetables.

🚀 Live Demo

Add your deployed link here


📸 Screenshots

Add screenshots of your app here


✨ Features

🧬 Genetic Algorithm — Auto-generates optimized, conflict-free timetables
🏫 Subject & Faculty Management — Manage courses, rooms, and instructors
📅 Timetable Display — Clean visual timetable on the frontend
🗄️ SQLite Database — Lightweight local database (no setup needed)
🌐 Web Interface — Simple browser-based UI (no framework required)
🔁 Seed Data — Pre-loaded sample data to get started quickly


🛠️ Tech Stack
Layer                                                 Technology
Backend                                               Python,Flask
Algorithm                                             Genetic Algorithm (custom)
Database                                              SQLite (timetable.db)
Frontend                                              HTML, CSS, JavaScript
Routing                                               Flask + timetable_routes.py


AI-TIMETABLE/
├── Backend/
│   ├── app.py                  # Flask app entry point
│   ├── db.py                   # Database setup
│   ├── genetic_algo.py         # Core genetic algorithm logic
│   ├── models.py               # Database models
│   ├── seed_data.py            # Sample data seeder
│   ├── timetable_routes.py     # API routes
│   ├── timetable.db            # SQLite database (auto-generated)
│   └── utils.py                # Helper functions
├── Frontend/
│   ├── static/
│   │   ├── app.js              # Frontend JavaScript
│   │   └── styles.css          # Stylesheet
│   └── templates/
│       └── index.html          # Main HTML page
├── venv/                       # Python virtual environment
├── requirements.txt            # Python dependencies
├── .gitignore
└── README.md


Installation & Running
1. Clone the repository
   bashgit clone https://github.com/your-username/AI-Timetable.git
   cd AI-Timetable
2. Install dependencies
   bashpip install -r requirements.txt
3. Set up the database
   bashcd Backend
   python db.py
   python seed_data.py
4. Run the app
   bashpython app.py
5. Open in browser
    http://127.0.0.1:5000

🔧 Troubleshooting
Problem                        Fix
ModuleNotFoundError            Run pip install -r requirements.txt 
Port 5000 already in use       Edit app.py and change port=5000 to port=5001
Database errors                Delete timetable.db, re-run db.py and seed_data.py
venv activation blocked        Run Set-ExecutionPolicy RemoteSigned -Scope CurrentUser in PowerShell
(Windows)

🧬 How the Genetic Algorithm Works

Initialization — Generates a random population of timetables
Fitness Evaluation — Scores each timetable based on conflicts (room clashes, faculty clashes, etc.)
Selection — Picks the best-performing timetables
Crossover — Combines two timetables to produce a better offspring
Mutation — Randomly tweaks schedules to explore new solutions
Repeat — Runs for multiple generations until an optimal timetable is found

📄 License
This project is open source and available under the MIT License.


Problem FixModuleNotFoundErrorRun pip install -r requirements.txtPort 5000 already in useEdit app.py and change port=5000 to port=5001Database errorsDelete timetable.db, re-run db.py and seed_data.pyvenv activation blocked (Windows)Run Set-ExecutionPolicy RemoteSigned -Scope CurrentUser in PowerShell
