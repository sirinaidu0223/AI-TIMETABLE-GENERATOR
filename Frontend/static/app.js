const BASE_URL = "http://127.0.0.1:5000";

// Global variables
let timetableData = [];
let batches = [];
let students = [];
let faculty = [];
let courses = [];
let classrooms = [];
let semesters = [];

// Global element refs
let timetableContainer, timetableTitle, timetableBody, fitnessScoreDiv;

document.addEventListener("DOMContentLoaded", () => {
  timetableContainer = document.getElementById("timetable-container");
  timetableTitle = document.getElementById("timetable-title");
  timetableBody = document.getElementById("timetableBody");
  fitnessScoreDiv = document.getElementById("fitness-score");

  fetchDataAndPopulateForms();
  setupEventListeners();
});

// ----------------- Fetch + Populate -----------------
async function fetchDataAndPopulateForms() {
  try {
    const [batchesRes, coursesRes, facultyRes, studentsRes, semestersRes] = await Promise.all([
      fetch(`${BASE_URL}/api/get_batches`),
      fetch(`${BASE_URL}/api/get_courses`),
      fetch(`${BASE_URL}/api/get_faculty`),
      fetch(`${BASE_URL}/api/get_students`),
      fetch(`${BASE_URL}/api/get_semesters`), // New endpoint for semesters
    ]);

    if (!batchesRes.ok || !coursesRes.ok || !facultyRes.ok || !studentsRes.ok || !semestersRes.ok) {
        throw new Error("One or more API endpoints failed to load.");
    }
    
    batches = await batchesRes.json();
    courses = await coursesRes.json();
    faculty = await facultyRes.json();
    students = await studentsRes.json();
    semesters = await semestersRes.json();

    populateSelect("student-batch-select", batches, "batch_id", "batch_name");
    populateSelect("view-semester-select", semesters, "semester_id", "semester_name", "All Semesters");
    populateSelect("student-courses-select", courses, "course_id", "course_name");
    populateSelect("faculty-expertise-select", courses, "course_id", "course_name");
    populateSelect("view-faculty-select", faculty, "faculty_id", "faculty_name", "All Faculty");
    populateSelect("view-student-select", students, "student_id", "student_name", "All Students");
  } catch (error) {
    console.error("Failed to fetch initial data:", error);
    showModal("Error", `Failed to load data. Backend may be down. Error: ${error.message}`);
  }
}

function populateSelect(selectId, data, valueKey, textKey, defaultOptionText = null) {
  const selectElement = document.getElementById(selectId);
  if (!selectElement) return;

  selectElement.innerHTML = "";
  if (defaultOptionText) {
    const defaultOption = document.createElement("option");
    defaultOption.value = "all";
    defaultOption.textContent = defaultOptionText;
    selectElement.appendChild(defaultOption);
  }

  data.forEach((item) => {
    const option = document.createElement("option");
    option.value = item[valueKey];
    option.textContent = item[textKey];
    selectElement.appendChild(option);
  });
}

function showModal(title, message) {
    const messageModal = document.getElementById('message-modal');
    document.getElementById('modal-title').textContent = title;
    document.getElementById('modal-body').textContent = message;
    messageModal.classList.remove('hidden');
}

// ----------------- Event Listeners -----------------
function setupEventListeners() {
  // Modal buttons
  document.getElementById("modal-ok-btn").addEventListener("click", () => {
    document.getElementById("message-modal").classList.add("hidden");
  });
  document.getElementById("close-saved-modal-btn").addEventListener("click", () => {
    document.getElementById("saved-timetables-modal").classList.add("hidden");
  });

  // Tab switching
  document.querySelectorAll(".tab-button").forEach((button) => {
    button.addEventListener("click", () => {
      document.querySelectorAll(".tab-button").forEach((btn) => btn.classList.remove("active"));
      button.classList.add("active");
      document.querySelectorAll(".tab-content").forEach((content) => content.classList.add("hidden"));
      document.getElementById(button.id + "-content").classList.remove("hidden");
    });
  });

  // Generate timetable
  document.getElementById("generateBtn").addEventListener("click", async () => {
    document.getElementById("loading").classList.remove("hidden");
    document.getElementById("loading").innerHTML = '<svg class="animate-spin h-5 w-5 mr-3 inline" viewBox="0 0 24 24"></svg><span>Generating timetable. This may take a while for large datasets...</span>';
    timetableContainer.classList.add("hidden");
    document.getElementById("message").textContent = "";

    try {
      const response = await fetch(`${BASE_URL}/api/generate_optimal_timetable`);
      const data = await response.json();
      if (!response.ok) throw new Error(data.error || "Unknown server error.");

      timetableData = data;
      displayTimetable(timetableData, "Optimal Timetable (AI)");
      showModal("Success", "Timetable generated successfully!");
    } catch (error) {
      console.error("Generation Error:", error);
      showModal("Error", `Failed to generate timetable: ${error.message}`);
    } finally {
      document.getElementById("loading").classList.add("hidden");
    }
  });

  // Save timetable
  document.getElementById("saveBtn").addEventListener("click", async () => {
    if (timetableData.length === 0) {
      showModal("Error", "Please generate a timetable before saving.");
      return;
    }
    try {
      const response = await fetch(`${BASE_URL}/api/save_timetable`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(timetableData),
      });
      const result = await response.json();
      if (!response.ok) throw new Error(result.error || "Unknown server error.");
      showModal("Success", result.message || "Timetable saved!");
    } catch (error) {
      console.error("Save Error:", error);
      showModal("Error", `Failed to save timetable: ${error.message}`);
    }
  });

  // Load timetable
  document.getElementById("loadBtn").addEventListener("click", async () => {
    const unifiedList = document.getElementById('unified-timetables-list');
    const modal = document.getElementById('saved-timetables-modal');
    const exportBtn = document.getElementById('exportPdfBtn');
    const selectAllCheckbox = document.getElementById('select-all-checkbox');

    modal.classList.remove('hidden');
    unifiedList.innerHTML = '<p class="text-center text-gray-500">Loading...</p>';
    exportBtn.disabled = true;
    selectAllCheckbox.checked = false;
    selectAllCheckbox.parentElement.classList.add('hidden'); // Hide until items are loaded

    try {
        const response = await fetch('/api/get_saved_timetables');
        const savedTimetables = await response.json();
        
        if (!response.ok) throw new Error(savedTimetables.error || "Unknown server error.");

        unifiedList.innerHTML = ""; // Clear the loading text

        if (savedTimetables.length === 0) {
            unifiedList.innerHTML = '<p class="text-center text-gray-500">No saved timetables found.</p>';
            return; // Exit if no timetables
        }

        // Show the "Select All" checkbox now that we have items
        selectAllCheckbox.parentElement.classList.remove('hidden');

        savedTimetables.forEach((tt) => {
            const itemContainer = document.createElement("div");
            itemContainer.className = "flex items-center justify-between p-3 bg-gray-50 rounded-lg hover:bg-gray-100 transition";

            const infoDiv = document.createElement("div");
            infoDiv.className = "flex items-center";

            const checkbox = document.createElement("input");
            checkbox.type = "checkbox";
            checkbox.value = tt.timetable_id;
            checkbox.className = "h-5 w-5 text-indigo-600 border-gray-300 rounded focus:ring-indigo-500 timetable-check";

            const link = document.createElement("a");
            link.href = "#";
            link.textContent = tt.timetable_name;
            link.className = "ml-4 font-medium text-indigo-600 hover:underline cursor-pointer";
            link.onclick = (e) => {
                e.preventDefault();
                modal.classList.add("hidden");
                loadSpecificTimetable(tt.timetable_id, tt.timetable_name);
            };
            
            infoDiv.appendChild(checkbox);
            infoDiv.appendChild(link);
            
            const timestamp = document.createElement("span");
            timestamp.className = "text-xs text-gray-500";
            timestamp.textContent = new Date(tt.timestamp).toLocaleString();
            
            itemContainer.appendChild(infoDiv);
            itemContainer.appendChild(timestamp);
            unifiedList.appendChild(itemContainer);
        });

        // --- Logic for checkbox synchronization ---
        const allCheckboxes = document.querySelectorAll('.timetable-check');

        const updateExportButtonState = () => {
            const anyChecked = document.querySelector('.timetable-check:checked');
            exportBtn.disabled = !anyChecked;
        };

        const syncSelectAllState = () => {
            const totalChecked = document.querySelectorAll('.timetable-check:checked').length;
            selectAllCheckbox.checked = totalChecked > 0 && totalChecked === allCheckboxes.length;
            updateExportButtonState();
        };

        selectAllCheckbox.addEventListener('change', () => {
            allCheckboxes.forEach(cb => cb.checked = selectAllCheckbox.checked);
            updateExportButtonState();
        });

        allCheckboxes.forEach(cb => {
            cb.addEventListener('change', syncSelectAllState);
        });

    } catch (error) {
        console.error("Load Error:", error);
        unifiedList.innerHTML = `<p class="text-red-500 text-center">Failed to load timetables: ${error.message}</p>`;
    }
  });


  // Helper function to load a specific timetable (add this with your other functions)
  async function loadSpecificTimetable(timetableId, timetableName) {
    document.getElementById("loading").classList.remove("hidden");
    try {
        const timetableRes = await fetch(`/api/get_timetable/${timetableId}`);
        const loadedData = await timetableRes.json();
        if (!timetableRes.ok) throw new Error(loadedData.error || "Unknown server error.");
        
        timetableData = loadedData; // Make sure timetableData is a global variable
        displayTimetable(loadedData, `Loaded: ${timetableName}`);
        showModal("Success", "Timetable loaded successfully!");
    } catch (err) {
        console.error("Load Timetable Error:", err);
        showModal("Error", `Failed to load timetable: ${err.message}`);
    } finally {
        document.getElementById("loading").classList.add("hidden");
    }
  }


   // Export buttons
    document.getElementById('exportPdfBtn').addEventListener('click', () => exportTimetables('pdf'));

  async function exportTimetables(format) {
  const checkboxes = document.querySelectorAll('.timetable-check:checked');
  if (checkboxes.length === 0) {
    showModal('Error', 'Please select at least one timetable to export.');
    return;
  }
  const ids = Array.from(checkboxes).map(cb => parseInt(cb.value));
  try {
    const response = await fetch(`${BASE_URL}/export`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ ids, format }),
    });
    if (!response.ok) throw new Error('Failed to export timetables.');
    const blob = await response.blob();
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'timetables.pdf';
    document.body.appendChild(a);
    a.click();
    a.remove();
    window.URL.revokeObjectURL(url);
    showModal('Success', 'Timetable exported successfully!');
  } catch (err) {
    console.error('Export error:', err);
    showModal('Error', `Export failed: ${err.message}`);
  }
}


  // Add Student
  document.getElementById("studentForm").addEventListener("submit", async (e) => {
    e.preventDefault();
    const studentData = {
      student_id: Date.now(),
      student_name: document.getElementById("student_name").value,
      batch_id: parseInt(document.getElementById("student-batch-select").value),
      course_choices: Array.from(document.getElementById("student-courses-select").selectedOptions).map((opt) =>
        parseInt(opt.value)
      ),
    };
    try {
      const response = await fetch(`${BASE_URL}/api/add_student`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(studentData),
      });
      const result = await response.json();
      if (!response.ok) throw new Error(result.error || "Unknown server error.");
      showModal("Success", result.message);
      e.target.reset();
      fetchDataAndPopulateForms();
    } catch (error) {
      console.error("Add Student Error:", error);
      showModal("Error", `Failed to add student: ${error.message}`);
    }
  });

  // Add Faculty
  document.getElementById("facultyForm").addEventListener("submit", async (e) => {
    e.preventDefault();
    const facultyData = {
      faculty_id: Date.now(),
      faculty_name: document.getElementById("faculty_name").value,
      workload_limit_hours: parseInt(document.getElementById("workload_limit_hours").value),
      expertise: Array.from(document.getElementById("faculty-expertise-select").selectedOptions).map((opt) =>
        parseInt(opt.value)
      ),
    };
    try {
      const response = await fetch(`${BASE_URL}/api/add_faculty`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(facultyData),
      });
      const result = await response.json();
      if (!response.ok) throw new Error(result.error || "Unknown server error.");
      showModal("Success", result.message);
      e.target.reset();
      fetchDataAndPopulateForms();
    } catch (error) {
      console.error("Add Faculty Error:", error);
      showModal("Error", `Failed to add faculty: ${error.message}`);
    }
  });

  // View Filters
  document.getElementById("view-semester-select").addEventListener("change", async (e) => {
    const semesterId = e.target.value;
    if (semesterId === "all") {
      displayTimetable(timetableData, "Optimal Timetable (AI)");
      return;
    }
    try {
      const response = await fetch(`${BASE_URL}/api/get_semester_timetable/${semesterId}`);
      const data = await response.json();
      if (!response.ok) throw new Error(data.error || "Unknown server error.");
      displayTimetable(data, `Timetable for Semester: ${e.target.selectedOptions[0].textContent}`);
    } catch (error) {
      console.error("View Semester Error:", error);
      showModal("Error", `Failed to load semester timetable: ${error.message}`);
    }
  });

  document.getElementById("view-faculty-select").addEventListener("change", async (e) => {
    const facultyId = e.target.value;
    if (facultyId === "all") {
      displayTimetable(timetableData, "Optimal Timetable (AI)");
      return;
    }
    try {
      const response = await fetch(`${BASE_URL}/api/get_faculty_timetable/${facultyId}`);
      const data = await response.json();
      if (!response.ok) throw new Error(data.error || "Unknown server error.");
      displayTimetable(data, `Timetable for Faculty: ${e.target.selectedOptions[0].textContent}`);
    } catch (error) {
      console.error("View Faculty Error:", error);
      showModal("Error", `Failed to load faculty timetable: ${error.message}`);
    }
  });

  document.getElementById("view-student-select").addEventListener("change", async (e) => {
    const studentId = e.target.value;
    if (studentId === "all") {
      displayTimetable(timetableData, "Optimal Timetable (AI)");
      return;
    }
    try {
      const response = await fetch(`${BASE_URL}/api/get_student_timetable/${studentId}`);
      const data = await response.json();
      if (!response.ok) throw new Error(data.error || "Unknown server error.");
      displayTimetable(data, `Timetable for Student: ${e.target.selectedOptions[0].textContent}`);
    } catch (error) {
      console.error("View Student Error:", error);
      showModal("Error", `Failed to load student timetable: ${error.message}`);
    }
  });
}

// ----------------- Display Timetable -----------------
function displayTimetable(data, title = "Timetable") {
  const timetableHeader = document.getElementById("timetableHeader");
  const timetableBody = document.getElementById("timetableBody");

  timetableHeader.innerHTML = "";
  timetableBody.innerHTML = "";

  if (!data || data.length === 0) {
    timetableBody.innerHTML = "<tr><td colspan='6' class='py-4 text-center text-gray-500'>No data available</td></tr>";
    timetableContainer.classList.remove("hidden");
    return;
  }

  const days = [...new Set(data.map((item) => item.day))];
  const timeSlots = [...new Set(data.map((item) => item.time))];

  const slotOrder = ["9:00-10:00", "10:00-11:00", "11:00-12:00", "13:00-14:00", "14:00-15:00"];
  timeSlots.sort((a, b) => slotOrder.indexOf(a) - slotOrder.indexOf(b));

  const dayOrder = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"];
  days.sort((a, b) => dayOrder.indexOf(a) - dayOrder.indexOf(b));

  // Header
  let headerRow = `<th class="py-2 px-4 border bg-gray-200">Day</th>`;
  timeSlots.forEach((slot) => {
    headerRow += `<th class="py-2 px-4 border bg-gray-200">${slot}</th>`;
  });
  timetableHeader.innerHTML = headerRow;

  // Rows
  days.forEach((day) => {
    let row = `<tr><td class="py-2 px-4 border font-semibold bg-gray-100">${day}</td>`;
    timeSlots.forEach((slot) => {
      const classItem = data.find((item) => item.day === day && item.time === slot);
      if (classItem) {
        row += `<td class="py-2 px-4 border text-sm">
            <div class="font-medium">${classItem.subject}</div>
            <div class="text-gray-600">${classItem.teacher}</div>
            <div class="text-gray-500">${classItem.room}</div>
          </td>`;
      } else {
        row += `<td class="py-2 px-4 border text-gray-400">--</td>`;
      }
    });
    row += `</tr>`;
    timetableBody.innerHTML += row;
  });

  // Fitness score
  if (data.length > 0 && data[0].fitness !== undefined) {
    fitnessScoreDiv.textContent = `Fitness Score: ${data[0].fitness.toFixed(4)}`;
    fitnessScoreDiv.classList.remove("hidden");
  } else {
    fitnessScoreDiv.classList.add("hidden");
  }

  timetableTitle.textContent = title;
  timetableContainer.classList.remove("hidden");
}