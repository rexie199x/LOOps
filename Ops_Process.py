import streamlit as st
import pandas as pd
import psycopg2
import os

# Database connection
def get_db_connection():
    try:
        return psycopg2.connect(
            host=os.getenv("host"),
            database=os.getenv("database"),
            user=os.getenv("user"),
            password=os.getenv("password"),
        )
    except Exception as e:
        st.error(f"Error connecting to the database: {e}")
        return None

# Function to load processes data from the database
def load_processes_data():
    conn = get_db_connection()
    if not conn:
        return {}

    cur = conn.cursor()
    try:
        cur.execute("SELECT section, title, content FROM public.ops_processes")  # Change this line if using a schema
        rows = cur.fetchall()
    except Exception as e:
        st.error(f"Error executing SQL query: {e}")
        rows = []
    finally:
        cur.close()
        conn.close()

    data = {}
    for row in rows:
        section, title, content = row
        if section not in data:
            data[section] = []
        data[section].insert(0, {"title": title, "content": content})  # Insert at the beginning to ensure new processes appear at the top
    return data

# Function to save a new process to the database
def save_new_process(section, title, content):
    conn = get_db_connection()
    if not conn:
        return

    cur = conn.cursor()
    try:
        cur.execute("INSERT INTO public.ops_processes (section, title, content) VALUES (%s, %s, %s)", (section, title, content))
        conn.commit()
    except Exception as e:
        st.error(f"Error executing SQL query: {e}")
    finally:
        cur.close()
        conn.close()

    # Immediately refresh data
    st.session_state.processes_data = load_processes_data()

# Function to update an existing process in the database
def update_process(section, old_title, new_title, new_content):
    conn = get_db_connection()
    if not conn:
        return

    cur = conn.cursor()
    try:
        cur.execute("UPDATE public.ops_processes SET title = %s, content = %s WHERE section = %s AND title = %s",
                    (new_title, new_content, section, old_title))
        conn.commit()
    except Exception as e:
        st.error(f"Error executing SQL query: {e}")
    finally:
        cur.close()
        conn.close()

    # Immediately refresh data
    st.session_state.processes_data = load_processes_data()

# Function to delete a process from the database
def delete_process(section, title):
    conn = get_db_connection()
    if not conn:
        return

    cur = conn.cursor()
    try:
        cur.execute("DELETE FROM public.ops_processes WHERE section = %s AND title = %s", (section, title))
        conn.commit()
    except Exception as e:
        st.error(f"Error executing SQL query: {e}")
    finally:
        cur.close()
        conn.close()

    # Immediately refresh data
    st.session_state.processes_data = load_processes_data()

# Function to load checklist tasks from the database
def load_checklist_tasks():
    conn = get_db_connection()
    if not conn:
        return []

    cur = conn.cursor()
    try:
        cur.execute("SELECT id, task, completed FROM public.ops_checklist ORDER BY id")
        rows = cur.fetchall()
    except Exception as e:
        st.error(f"Error executing SQL query: {e}")
        rows = []
    finally:
        cur.close()
        conn.close()

    tasks = [{"id": row[0], "task": row[1], "completed": row[2]} for row in rows]
    return tasks

# Function to add a new task to the checklist
def add_checklist_task(task, completed=False):
    conn = get_db_connection()
    if not conn:
        return

    cur = conn.cursor()
    try:
        cur.execute("INSERT INTO public.ops_checklist (task, completed) VALUES (%s, %s)", (task, int(completed)))
        conn.commit()
    except Exception as e:
        st.error(f"Error executing SQL query: {e}")
    finally:
        cur.close()
        conn.close()

# Function to update a task's completion status
def update_checklist_task(task_id, completed):
    conn = get_db_connection()
    if not conn:
        return

    cur = conn.cursor()
    try:
        cur.execute("UPDATE public.ops_checklist SET completed = %s WHERE id = %s", (int(completed), task_id))
        conn.commit()
    except Exception as e:
        st.error(f"Error executing SQL query: {e}")
    finally:
        cur.close()
        conn.close()

# Function to update a task's name
def update_checklist_task_name(task_id, new_task):
    conn = get_db_connection()
    if not conn:
        return

    cur = conn.cursor()
    try:
        cur.execute("UPDATE public.ops_checklist SET task = %s WHERE id = %s", (new_task, task_id))
        conn.commit()
    except Exception as e:
        st.error(f"Error executing SQL query: {e}")
    finally:
        cur.close()
        conn.close()

# Function to delete a task from the checklist
def delete_checklist_task(task_id):
    conn = get_db_connection()
    if not conn:
        return

    cur = conn.cursor()
    try:
        cur.execute("DELETE FROM public.ops_checklist WHERE id = %s", (task_id,))
        conn.commit()
    except Exception as e:
        st.error(f"Error executing SQL query: {e}")
    finally:
        cur.close()
        conn.close()

# Initialize the processes data in session state
if 'processes_data' not in st.session_state:
    st.session_state.processes_data = load_processes_data()

# Initialize new process fields in session state
if 'new_process_title' not in st.session_state:
    st.session_state.new_process_title = ""
if 'new_process_content' not in st.session_state:
    st.session_state.new_process_content = ""

# Initialize reload flag
if 'reload_flag' not in st.session_state:
    st.session_state.reload_flag = False

# Initialize add process form visibility
if 'show_add_process_form' not in st.session_state:
    st.session_state.show_add_process_form = False

# Function to display processes for each section
def show_processes(section):
    st.title(f"{section}")

    if st.session_state.reload_flag:
        st.session_state.processes_data = load_processes_data()
        st.session_state.reload_flag = False
    
    processes = st.session_state.processes_data.get(section, [])

    # Search bar
    search_query = st.text_input("Search for an article:")
    if search_query:
        processes = [p for p in processes if search_query.lower() in p['title'].lower()]

    # Pagination logic
    items_per_page = 10
    total_pages = len(processes) // items_per_page + (1 if len(processes) % items_per_page > 0 else 0)

    if 'current_page' not in st.session_state:
        st.session_state.current_page = 1

    def go_to_prev_page():
        if st.session_state.current_page > 1:
            st.session_state.current_page -= 1

    def go_to_next_page():
        if st.session_state.current_page < total_pages:
            st.session_state.current_page += 1

    start_idx = (st.session_state.current_page - 1) * items_per_page
    end_idx = start_idx + items_per_page
    page_processes = processes[start_idx:end_idx]

    # Inject custom CSS for title size
    st.markdown(
        """
        <style>
        .custom-title {
            font-size: 20px;
            font-weight: bold;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

    # Display processes
    for i, process in enumerate(page_processes):
        expander = st.expander(f"{process['title']}", expanded=False)
        with expander:
            st.markdown(f"<div class='custom-title'>{process['title']}</div>", unsafe_allow_html=True)
            st.write(process['content'])

            col1, col2, col3 = st.columns([1, 1, 6])
            with col1:
                if st.button("Edit", key=f"edit_{section}_{start_idx + i}"):
                    st.session_state[f"edit_mode_{section}_{start_idx + i}"] = True
            with col2:
                if st.button("Delete", key=f"delete_{section}_{start_idx + i}"):
                    st.session_state[f"confirm_delete_{section}_{start_idx + i}"] = True

            if st.session_state.get(f"edit_mode_{section}_{start_idx + i}", False):
                new_title = st.text_input(f"Edit title for {process['title']}", process['title'], key=f"title_{section}_{start_idx + i}")
                new_content = st.text_area(f"Edit content for {process['title']}", process['content'], key=f"content_{section}_{start_idx + i}")
                if st.button(f"Save {process['title']}", key=f"save_{section}_{start_idx + i}"):
                    update_process(section, process['title'], new_title, new_content)
                    st.session_state[f"edit_mode_{section}_{start_idx + i}"] = False
                    st.session_state.reload_flag = True
                    st.success(f"Saved changes for {process['title']}")
                    # Immediately refresh data
                    st.session_state.processes_data = load_processes_data()

            if st.session_state.get(f"confirm_delete_{section}_{start_idx + i}", False):
                st.warning(f"Are you sure you want to delete {process['title']}?")
                col1, col2 = st.columns(2)
                with col1:
                    if st.button(f"Yes, delete {process['title']}", key=f"confirm_yes_{section}_{start_idx + i}"):
                        delete_process(section, process['title'])
                        st.session_state[f"confirm_delete_{section}_{start_idx + i}"] = False
                        st.session_state.reload_flag = True
                        st.success(f"Deleted {process['title']}")
                        # Immediately refresh data
                        st.session_state.processes_data = load_processes_data()
                with col2:
                    if st.button("No, cancel", key=f"confirm_no_{section}_{start_idx + i}"):
                        st.session_state[f"confirm_delete_{section}_{start_idx + i}"] = False

    # Pagination controls at the bottom
    if total_pages > 1:
        col1, col2, col3 = st.columns([1, 3, 1])
        with col1:
            st.button('⬅', on_click=go_to_prev_page, key="prev_button")
        with col2:
            st.markdown(f"<div style='text-align: center;'>Page {st.session_state.current_page} of {total_pages}</div>", unsafe_allow_html=True)
        with col3:
            st.button('➡', on_click=go_to_next_page, key="next_button")

    # Button to show the add process form
    if st.button("Add New Process"):
        st.session_state.show_add_process_form = not st.session_state.show_add_process_form

    # Conditionally show the add process form
    if st.session_state.show_add_process_form:
        st.write("### Add New Process")
        st.session_state.new_process_title = st.text_input("New Process Title", key=f"new_title_{section}")
        st.session_state.new_process_content = st.text_area("New Process Content", key=f"new_content_{section}")
        if st.button("Submit New Process", key=f"submit_{section}"):
            if st.session_state.new_process_title and st.session_state.new_process_content:
                save_new_process(section, st.session_state.new_process_title, st.session_state.new_process_content)
                # Clear the input fields after adding the process
                st.session_state.new_process_title = ""
                st.session_state.new_process_content = ""
                st.session_state.reload_flag = True
                st.success("New process added successfully!")

# Function to display checklist
def show_checklist():
    st.title("Checklist")

    tasks = load_checklist_tasks()

    # Show progress
    completed_tasks = [task for task in tasks if task['completed']]
    total_tasks = len(tasks)
    progress = len(completed_tasks) / total_tasks if total_tasks > 0 else 0
    st.progress(progress)

    # Display tasks with checkboxes
    for task in tasks:
        col1, col2, col3 = st.columns([4, 1, 1])
        with col1:
            task_title = task['task']
            is_completed = st.checkbox(task_title, value=task['completed'])
            if is_completed != task['completed']:
                update_checklist_task(task['id'], int(is_completed))
                st.session_state.reload_flag = True
        with col2:
            if st.button("Edit", key=f"edit_{task['id']}"):
                st.session_state[f"edit_mode_{task['id']}"] = True
        with col3:
            if st.button("Delete", key=f"delete_{task['id']}"):
                delete_checklist_task(task['id'])
                st.session_state.reload_flag = True

        if st.session_state.get(f"edit_mode_{task['id']}", False):
            new_task_title = st.text_input(f"Edit task", task_title, key=f"new_task_title_{task['id']}")
            if st.button(f"Save", key=f"save_{task['id']}"):
                update_checklist_task_name(task['id'], new_task_title)
                st.session_state[f"edit_mode_{task['id']}"] = False
                st.session_state.reload_flag = True
                st.success(f"Saved changes for {task_title}")

    # Form to add new task
    st.write("### Add New Task")
    new_task = st.text_input("Task")
    if st.button("Add Task"):
        if new_task:
            add_checklist_task(new_task)
            st.session_state.reload_flag = True
            st.success("New task added successfully!")

# Main function to run the app
def main():
    # Add the logo at the top of the sidebar
    st.sidebar.image("https://lonelyoctopus.s3.eu-north-1.amazonaws.com/LOOPS.png", width=280)
    st.sidebar.title("Menu")
    
    # Inject custom CSS
    st.markdown(
        """
        <style>
        .stButton>button:hover {
            background-color: purple !important;
            color: white !important;
        }
        .stButton>button {
            width: 100%;
        }
        .full-screen-iframe {
            position: fixed;
            top: 5;
            left: 330px;
            width: calc(100% - 350px);
            height: calc(90% - 20px);
            border: none;
            z-index: 9999;
        }
        .custom-padding {
            padding: 5px !important;
        }
        .css-1d391kg {
            width: 330px !important;
            position: fixed !important;
            top: 0;
            left: 0;
            height: 100vh;
        }
        .css-18ni7ap {
            margin-left: 330px !important;
        }
        .css-15tx938, .css-1rs6os.edgvbvh10 {
            display: none !important;
        }
        </style>
        """,
        unsafe_allow_html=True
    )
    
    menu_options = ["General Processes", "Discord Related Processes", "Templates", "Links", "Timelines", "Dashboard"]
    choice = st.sidebar.radio("Go to", menu_options, index=0)  # Default to "Dashboard" page

    if choice == "Dashboard":
        st.markdown("<div class='custom-padding'></div>", unsafe_allow_html=True)
        # Embed Looker Studio report
        st.write(
            """
            <iframe class="full-screen-iframe" src="https://lookerstudio.google.com/embed/reporting/d3b5906b-d484-41c6-b925-b0105be21448/page/rHc7D" frameborder="0" style="border:0" allowfullscreen></iframe>
            """,
            unsafe_allow_html=True
        )
    elif choice == "Checklist":
        show_checklist()
    else:
        show_processes(choice)

if __name__ == "__main__":
    main()
