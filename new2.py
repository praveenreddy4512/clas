import streamlit as st
import pandas as pd
import tabula
import tempfile
import os


# Function to read PDF and convert to CSV
def pdf_to_csv(pdf_file):
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_pdf:
        temp_pdf.write(pdf_file.read())
        temp_pdf_path = temp_pdf.name
    csv_path = temp_pdf_path.replace('.pdf', '.csv')
    
    try:
        tabula.convert_into(temp_pdf_path, csv_path, pages="all", output_format="csv")
    except Exception as e:
        st.error(f"Error converting PDF to CSV: {e}")
    
    if os.path.exists(csv_path):
        return pd.read_csv(csv_path)
    else:
        st.error("CSV file not created.")
        return None

# Function to extract course data
def extract_course_data(df):
    course_data = {}
    for index, row in df.iterrows():
        course = row['COURSE CODE']
        slot = row['SLOT']
        if course in course_data:
            course_data[course].append(slot)
        else:
            course_data[course] = [slot]
    return course_data

# Initialize session state
if 'selected_slots' not in st.session_state:
    st.session_state.selected_slots = {}
if 'selected_course_codes' not in st.session_state:
    st.session_state.selected_course_codes = {}
if 'course_data_theory' not in st.session_state:
    st.session_state.course_data_theory = {}
if 'course_data_lab' not in st.session_state:
    st.session_state.course_data_lab = {}
if 'course_being_edited' not in st.session_state:
    st.session_state.course_being_edited = None

# Sidebar with website name
st.sidebar.markdown('<h2 style=" border-radius: 10%; padding: 10px; text-align: center;"></h2>', unsafe_allow_html=True)


# st.title("ClassSync")


theory_pdf = st.file_uploader("Upload Theory Slots PDF", type="pdf")
lab_pdf = st.file_uploader("Upload Lab Slots PDF", type="pdf")

if theory_pdf and lab_pdf:
        with st.spinner('Processing...'):
            df_theory = pdf_to_csv(theory_pdf)
            df_lab = pdf_to_csv(lab_pdf)

            if df_theory is not None and df_lab is not None:
                st.session_state.course_data_theory = extract_course_data(df_theory)
                st.session_state.course_data_lab = extract_course_data(df_lab)
                st.success("PDFs uploaded and processed successfully!")


    # Timetable data (example)
table_data = [
        ["Day/Time", "8 - 9", "9 - 10", "10 - 11", "11 - 12", "12 - 1", "1 - 1:30", "2 - 3", "3 - 4", "4 - 5", "5 - 6", "6 - 7", "7 - 7:30"],
        ["Tue", "TF1+L1", "TA1+L2", "E1+STC2+L3", "D1+L4", "B1+L5", "L6", "TA2+L31", "E2+STC1+L32", "D2+L33", "B2+L34", "TF2+L35", "L36"],
        ["Wed", "TCC1+L7", "E1+STA2+L8", "G1+TFF1+L9", "TBB1+L10", "TDD1+L11", "L12", "E2+STA1+L37", "G2+TFF2+L38", "TBB2+L39", "TDD2+L40", "TCC2+L41", "L42"],
        ["Thu", "TE1+L13", "C1+L14", "A1+L15", "F1+L16", "D1+L17", "L18", "C2+L43", "A2+L44", "F2+L45", "D2+L46", "TE2+L47", "L48"],
        ["Fri", "TAA1+L19", "TD1+L20", "B1+L21", "G1+TEE1+L22", "C1+L23", "L24", "TD2+L49", "B2+L50", "G2+TEE2+L51", "C2+L52", "TAA2+L53", "L54"],
        ["Sat", "TG1+L25", "TB1+L26", "TC1+L27", "A1+L28", "F1+L29", "L30", "TB2+L55", "TC2+L56", "A2+L57", "F2+L58", "TG2+L59", "L60"]
    ]

conflict_pairs = []
for i in range(1, len(table_data)):
    for j in range(1, len(table_data[i])):
        slots = table_data[i][j].split("+")
        conflict_pairs.append(slots)

conflict_dict = {}
for pair in conflict_pairs:
    for slot in pair:
        if slot not in conflict_dict:
            conflict_dict[slot] = set()
        conflict_dict[slot].update(pair)
        conflict_dict[slot].remove(slot)

color_dict = {
    "Red": "#FF0000",
    "Green": "#00FF00",
    "Pink": "#FF33F9",
    "Yellow": "#FFFF00",
    "Purple": "#800080",
    "Orange": "#FFA500"
}

color_options = list(color_dict.keys())

def update_table(selected_slots):
    table = [["Day/Time"] + table_data[0][1:]]
    for i in range(1, len(table_data)):  # Rows (excluding header row)
        row = [table_data[i][0]]  # Add day to the row
        for j in range(1, len(table_data[i])):  # Columns (excluding first column)
            slot = table_data[i][j]
            slot_parts = slot.split('+')
            bg_color = "transparent"  # Default background color to transparent

            # Check selected slots
            for part in slot_parts:
                if part in selected_slots:
                    bg_color = selected_slots[part]  # Use the selected slot color
                    break
            
            # Set text color based on dark mode
            text_color = "#0000FF" 
            #if st.session_state.get("dark_mode", False) else "#000"

            # Render the slot cell with transparent background
            row.append(f'<div style="background-color:{bg_color}; color: {text_color}; padding: 5px; border: 1px solid rgba(0,0,0,0.1);">{slot}</div>')
        table.append(row)
    return table



def handle_apply_color(course_code, slot, color):
    slot_parts = slot.split('+')
    conflict = False
    for part in slot_parts:
        if part in st.session_state.selected_slots or any(conflict_dict[part] & st.session_state.selected_slots.keys()):
            st.warning(f"Slot clash detected with '{part}'.")
            conflict = True
            break

    if not conflict:
        for part in slot_parts:
            st.session_state.selected_slots[part] = color_dict[color]  # Use the color name to get the hex value
        st.session_state.selected_course_codes[course_code] = slot
        st.success(f"Slot for {course_code} added successfully.")

def handle_delete_course(course_code):
    if course_code in st.session_state.selected_course_codes:
        slot = st.session_state.selected_course_codes[course_code]
        slot_parts = slot.split('+')
        for part in slot_parts:
            if part in st.session_state.selected_slots:
                del st.session_state.selected_slots[part]
        del st.session_state.selected_course_codes[course_code]
        st.success(f"Course {course_code} deleted successfully.")

def handle_edit_course(course_code):
    st.session_state.course_being_edited = course_code
    st.success(f"Editing course {course_code}.")

def handle_update_course(course_code, new_slot, new_color):
    handle_delete_course(course_code)  # Remove old course first
    handle_apply_color(course_code, new_slot, new_color)  # Apply new color and slot
    st.session_state.course_being_edited = None
    st.success(f"Course {course_code} updated successfully.")


# table_html = '<table class="table-container" style="font-size: 0.9em;">' + ''.join(['<tr>' + ''.join([f'<td>{cell}</td>' for cell in row]) + '</tr>' for row in table_data]) + '</table>'
# st.markdown(table_html, unsafe_allow_html=True)

# Add custom CSS to align the main content beside the sidebar
custom_css = """
    <style>
        .main .block-container {
            padding-top: 4rem;
            padding-right: 75rem;
            padding-left: 1rem;
            padding-bottom: 1rem;
            display: flex;
        }
        .sidebar .sidebar-content {
            padding-top: 1rem;
            padding-right: 1rem;
            padding-left: 1rem;
            padding-bottom: 1rem;
        }
        .block-container .block-container {
            display: flex;
            flex-grow: 1;
        }
        .block-container .element-container {
            flex-grow: 1;
        }
    </style>
"""
st.markdown(custom_css, unsafe_allow_html=True)



title_url = "https://sai.madhuram.xyz/wp-content/uploads/2024/07/Class.png"

# Bottom bar
st.sidebar.markdown(
    f"""
    <div style='display: flex; align-items: center; justify-content: center;'>
        <img src='{title_url}' style='height: 200px;   margin-top: -68px; margin-bottom: -50px; margin-right: 10px; margin-left: 10px;'>
    </div>
    <hr style='margin-top: -20px; margin-left: 10px;'>
    """,
    unsafe_allow_html=True
)



st.sidebar.header("Course Selection")
if 'course_data_theory' in st.session_state and 'course_data_lab' in st.session_state:
    course_type = st.sidebar.radio("Select Course Type", ("Theory", "Lab"))

    
    if course_type == "Theory":
        available_courses = list(st.session_state.course_data_theory.keys())
    else:
        available_courses = list(st.session_state.course_data_lab.keys())
    
    # Exclude already selected courses from the dropdown
    available_courses = [course for course in available_courses if course not in st.session_state.selected_course_codes]

    course_code = st.sidebar.selectbox("Select Course Code", available_courses)
    
    if course_code:
        if course_type == "Theory":
            slot = st.sidebar.selectbox("Select Slot", st.session_state.course_data_theory[course_code])
        else:
            slot = st.sidebar.selectbox("Select Slot", st.session_state.course_data_lab[course_code])
        
        color = st.sidebar.selectbox("Select Color", color_options)
        
        if st.sidebar.button("Apply Color"):
            if not course_code or not slot or not color:
                st.warning("Please select a course before applying color.")
            else:
                handle_apply_color(course_code, slot, color)  # Pass color name, not value


# Display timetable in a more compact format
# Add scrolling text beside the timetable


st.header("TimeTable")
scrolling_text = "<marquee style='margin-left: 10px;'>The new timetable will be updated after the University provides the 'Slot Timetable Annexure'.</marquee>"
st.markdown(scrolling_text, unsafe_allow_html=True)
table = update_table(st.session_state.selected_slots)
table_html = '<table class="table-container" style="font-size: 0.9em;">' + ''.join(['<tr>' + ''.join([f'<td>{cell}</td>' for cell in row]) + '</tr>' for row in table_data]) + '</table>'
st.markdown(table_html, unsafe_allow_html=True)

# Sidebar actions
st.sidebar.header("Modify Courses")
selected_course = st.sidebar.selectbox("Select a Course to Delete or Edit", list(st.session_state.selected_course_codes.keys()))
if st.sidebar.button("Delete Course"):
    if not selected_course:
        st.warning("Please select a course before attempting to delete.")
    else:
        handle_delete_course(selected_course)

if st.sidebar.button("Edit Course"):
    if not selected_course:
        st.warning("Please select a course before attempting to edit.")
    else:
        handle_edit_course(selected_course)

if st.session_state.course_being_edited:
    new_slot = st.sidebar.selectbox("Select New Slot", 
          st.session_state.course_data_theory[selected_course] if selected_course in st.session_state.course_data_theory else st.session_state.course_data_lab[selected_course])
    
    new_color = st.sidebar.selectbox("Select New Color", color_options)
    
    if st.sidebar.button("Update Course"):
        if not new_slot or not new_color:
            st.warning("Please select a new slot and color before updating.")
        else:
            handle_update_course(st.session_state.course_being_edited, new_slot, new_color)


# Reset table button
if st.sidebar.button("Reset Table"):
    if not st.session_state.selected_slots:
        st.warning("No courses to reset.")
    else:
        st.session_state.selected_slots.clear()
        st.session_state.selected_course_codes.clear()
        st.success("Table reset successfully.")


# Sidebar header for applied courses
st.sidebar.header("Applied Courses")

# Display applied courses in the sidebar
if st.session_state.selected_course_codes:
    for code, slot in st.session_state.selected_course_codes.items():
        st.sidebar.write(f"Course: {code}, Slot: {slot}")
else:
    st.sidebar.write("No courses applied yet.")


# Use markdown to create a combined header with logos side by side
# <h8 style='text-align: center; margin-top: 120px;  margin-right: -150px;margin-bottom: 10px;margin-left: 10px;'>Developed By</h8>
#         <h6 style='text-align: center; margin-top: 140px;  margin-right: 40px;margin-bottom: 10px;margin-left: 350px;'>SURYA TEJESS</h6>
#         <img src='{gfg_icon_url}' style='height: 150px;margin-top: 100px;  margin-right: 10px;margin-bottom: 10px;margin-left: 10px;'>




# Sidebar for developer info
gfg_icon_url = "https://sai.madhuram.xyz/wp-content/uploads/2024/07/VIT_AP__1_-removebg-preview.png"
team_icon_url = "https://sai.madhuram.xyz/wp-content/uploads/2024/07/1.png"
title_url = "https://sai.madhuram.xyz/wp-content/uploads/2024/07/Class.png"

# Bottom bar
st.markdown(
    f"""
    <hr style='margin-top: 170px; margin-right: -220px;'>
    <div style='display: flex; align-items: center; justify-content: center;'>
        <h15 style='text-align: center; margin-top: -135px; margin-right: -340px; margin-bottom: 10px; margin-left: 650px;'>Developed & Powered By</h15>
        <img src='{team_icon_url}' style='height: 200px; margin-top: -130px; margin-bottom: 10px; margin-right: -800px; margin-left: 300px;'>
    </div>
    """,
    unsafe_allow_html=True
)

# Footer (full width)
footer_html = """
<style>
.footer {
    width: 100%;  /* Full width */
    position: fixed;  /* Positioned relative to the page */
    bottom: 0;
    left: 0;
    right: 0;
    text-align: center;
    padding: 10px;
    font-size: 14px;
}

.powered-by {
    font-size: 12px;
    color: #555;  /* Darker color */
}

/* Light mode styles */
@media (prefers-color-scheme: light) {
    .footer {
        background-color: #f0f2f6;  /* Light background */
        color: #000;  /* Dark text */
    }
}

/* Dark mode styles */
@media (prefers-color-scheme: dark) {
    .footer {
        background-color: #262730;  /* Dark background */
        color: #fff;  /* Light text */
    }
}
</style>
<div class="footer">
    ©️ 2024 ClassSync. Python Code by 'SURYA TEJESS' Collaborated with GFG VITAP STUDENT CHAPTER.
    <div class="powered-by">Powered by APPE NEXUS</div>
</div>
"""
st.markdown(footer_html, unsafe_allow_html=True)

# Add padding to the main content to avoid overlap with the footer
st.markdown(
    """
    <style>
    .main-content {
        padding-bottom: 60px;  /* Adjust this value based on the height of your footer */
    }
    </style>
    <div class='main-content'>
    <!-- Your main content goes here -->
    </div>
    """,
    unsafe_allow_html=True
)





#gfg_icon_url = "https://sai.madhuram.xyz/wp-content/uploads/2024/07/VIT_AP__1_-removebg-preview.png"
#team_icon_url = "https://sai.madhuram.xyz/wp-content/uploads/2024/07/1.png"
#<img src='{team_icon_url}' style='height: 200px;margin-top: -130px;margin-bottom: 10px;margin-right: -800px;margin-left: 300px; '>
# st.markdown(
#     f"""
#     <div class='fixed-bottom-bar'>
#         <div style='display: flex; align-items: center; justify-content: center;'>
#         <h15 style='text-align: center; margin-top: -50px;  margin-right: -800px;margin-bottom: 10px;margin-left: 110px;'>Python Code by 'SURYA TEJESS' Collaborated with GFG VITAP STUDENT CHAPTER.</h15> 
#         </div>
#     </div>
#     """,
#     unsafe_allow_html=True
# )
# st.markdown(
#     f"""
#     <div class='fixed-bottom-bar'>
#     <div style='display: flex; align-items: center; justify-content: center;'>
#     <img src='{gfg_icon_url}' style='height: 150px;margin-top: -120px;margin-bottom: 10px;margin-right: -750px;margin-left: 840px; '>
#     </div>
#     </div>
    
#     """,
#     unsafe_allow_html=True
# )

