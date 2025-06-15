import sqlite3

def get_db_connection():
    conn = sqlite3.connect('campus.db')
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()

    # Create courses table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS courses (
        code TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        description TEXT,
        semester TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')

    # Create timetable
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS timetable (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        day TEXT NOT NULL,
        period INTEGER NOT NULL,
        start_time TEXT NOT NULL,
        end_time TEXT NOT NULL,
        subject TEXT NOT NULL,
        room TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')

    # Create a base schedule table template
    base_schedule_sql = '''
    CREATE TABLE IF NOT EXISTS schedule_{} (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        day_of_week TEXT NOT NULL CHECK (day_of_week IN ('Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday')),
        start_time TEXT NOT NULL,
        end_time TEXT NOT NULL,
        room TEXT NOT NULL,
        instructor TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        CONSTRAINT valid_time CHECK (start_time < end_time)
    )
    '''

    conn.commit()
    conn.close()

def create_class_schedule_table(class_code):
    """Create a new schedule table for a specific class"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Sanitize class_code to be SQL-safe
    safe_class_code = ''.join(c for c in class_code if c.isalnum())
    
    # Create the class-specific schedule table
    cursor.execute(f'''
    CREATE TABLE IF NOT EXISTS schedule_{safe_class_code} (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        day_of_week TEXT NOT NULL CHECK (day_of_week IN ('Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday')),
        start_time TEXT NOT NULL,
        end_time TEXT NOT NULL,
        room TEXT NOT NULL,
        instructor TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        CONSTRAINT valid_time CHECK (start_time < end_time)
    )
    ''')
    
    conn.commit()
    conn.close()

def get_all_courses():
    """Get list of all courses"""
    conn = get_db_connection()
    courses = conn.execute('SELECT * FROM courses').fetchall()
    conn.close()
    return courses

def add_course(code, name, description, semester):
    """Add a new course and create its schedule table"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Add course to courses table
        cursor.execute('''
        INSERT INTO courses (code, name, description, semester)
        VALUES (?, ?, ?, ?)
        ''', (code, name, description, semester))
        
        # Create schedule table for this course
        create_class_schedule_table(code)
        
        conn.commit()
        return True
    except Exception as e:
        print(f"Error adding course: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

def get_class_schedule(class_code):
    """Get schedule for a specific class"""
    conn = get_db_connection()
    safe_class_code = ''.join(c for c in class_code if c.isalnum())
    schedule = conn.execute(f'SELECT * FROM schedule_{safe_class_code}').fetchall()
    conn.close()
    return schedule

def insert_sample_data():
    conn = get_db_connection()
    cursor = conn.cursor()

    # Insert some sample classes
    cursor.execute("INSERT INTO schedule (class_name, start_time, location) VALUES (?, ?, ?)",
                   ("Computer Science", "10:00 AM", "Room 101"))

    # Insert some sample events
    cursor.execute("INSERT INTO events (event_name, event_time, location) VALUES (?, ?, ?)",
                   ("Tech Talk", "2:00 PM", "Auditorium"))
    
    conn.commit()
    conn.close()

def insert_timetable_data():
    conn = get_db_connection()
    cursor = conn.cursor()
    # Clear existing timetable data
    cursor.execute('DELETE FROM timetable')
    # Timetable data: (day, period, start_time, end_time, subject, room)
    timetable_entries = [
        # MONDAY
        ('MON', 2, '9:50', '10:40', 'SOFT SKILLS', 'S302/S303'),
        ('MON', 3, '10:50', '11:40', 'DISTRIBUTED SYSTEMS', 'FF LAB'),
        ('MON', 5, '12:30', '1:20', 'LUNCH', ''),
        ('MON', 6, '1:20', '2:10', 'CLOUD', 'N106'),
        ('MON', 7, '2:10', '3:00', 'DISTRIBUTED SYSTEMS', 'N106'),
        ('MON', 9, '4:00', '4:50', 'CLOUD', 'N106'),
        # TUESDAY
        ('TUE', 1, '9:00', '9:50', 'DISTRIBUTED SYSTEMS', 'N106'),
        ('TUE', 2, '9:50', '10:40', 'COMPUTER SECURITY', 'N302'),
        ('TUE', 3, '10:50', '11:40', 'PRINCIPLES OF PL', 'N106'),
        ('TUE', 5, '12:30', '1:20', 'SOFTWARE ENGG', 'N106'),
        # LUNCH (period 4)
        # Period 6, 7, 8, 9 are empty
        # WEDNESDAY
        ('WED', 2, '9:50', '10:40', 'COMPUTER SECURITY', 'N106'),
        ('WED', 5, '12:30', '1:20', 'SOFTWARE ENGG', 'N106'),
        ('WED', 6, '1:20', '2:10', 'FULL STACK', 'N103'),
        ('WED', 7, '2:10', '3:00', 'WIRELESS', 'N106'),
        # LLM S311 C, SNA N106, SNS N106, PRINCIPLES OF PL FF LAB (periods 4, 8)
        # THURSDAY
        ('THU', 1, '9:00', '9:50', 'PRINCIPLES OF PL', 'N306'),
        ('THU', 2, '9:50', '10:40', 'FULL STACK', 'N103'),
        ('THU', 3, '10:50', '11:40', 'WIRELESS', 'N106'),
        ('THU', 4, '11:40', '12:30', 'SNS', 'N103'),
        ('THU', 5, '12:30', '1:20', 'LUNCH', ''),
        ('THU', 6, '1:20', '2:10', 'DISTRIBUTED SYSTEMS', 'N106'),
        ('THU', 7, '2:10', '3:00', 'CLOUD', 'N106'),
        ('THU', 8, '3:10', '4:00', 'SOFTWARE ENGG', 'A207 B'),
        # FRIDAY
        ('FRI', 1, '9:00', '9:50', 'VERBAL', 'N301 | N309 B'),
        ('FRI', 2, '9:50', '10:40', 'FULL STACK', 'N103'),
        ('FRI', 3, '10:50', '11:40', 'WIRELESS', 'N106'),
        ('FRI', 4, '11:40', '12:30', 'COMPUTER SECURITY', 'N302'),
        ('FRI', 5, '12:30', '1:20', 'LUNCH', ''),
        ('FRI', 6, '1:20', '2:10', 'SNS', 'N103'),
        ('FRI', 7, '2:10', '3:00', 'SNA', 'N106'),
        ('FRI', 8, '3:10', '4:00', 'APTITUDE', 'N307'),
    ]
    cursor.executemany('''
        INSERT INTO timetable (day, period, start_time, end_time, subject, room)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', timetable_entries)
    conn.commit()
    conn.close()

def print_timetable():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT day, period, start_time, end_time, subject, room FROM timetable
        ORDER BY 
            CASE day 
                WHEN "MON" THEN 1 
                WHEN "TUE" THEN 2 
                WHEN "WED" THEN 3 
                WHEN "THU" THEN 4 
                WHEN "FRI" THEN 5 
                ELSE 6 
            END, 
            period
    ''')
    rows = cursor.fetchall()
    print("\n--- Timetable ---")
    for row in rows:
        print(f"{row['day']} | Period {row['period']} | {row['start_time']}-{row['end_time']} | {row['subject']} | {row['room']}")
    conn.close()

if __name__ == '__main__':
    init_db()
    insert_sample_data()
    insert_timetable_data()
    print_timetable()
