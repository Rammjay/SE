from flask import Flask, request, jsonify, g, session
from flask_cors import CORS
from datetime import datetime, timedelta
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
import traceback
import random
import re
from functools import wraps
from supabase import create_client, Client
import os

app = Flask(__name__)
CORS(app, supports_credentials=True)

# Environment variables
SUPABASE_URL = os.getenv('SUPABASE_URL', 'https://vijbllygfdafmcaotxqx.supabase.co')
SUPABASE_KEY = os.getenv('SUPABASE_KEY', 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InZpamJsbHlnZmRhZm1jYW90eHF4Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDkzMDE0MTcsImV4cCI6MjA2NDg3NzQxN30.hAXuoU1OtsjUXRv-LM9c9JTlScqv6SbgZj2wCZi72SM')
PORT = int(os.getenv('PORT', 5000))
DEBUG = os.getenv('FLASK_ENV') != 'production'

# Supabase configuration
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Initialize conversation context
def get_context():
    """Get or initialize the conversation context"""
    if not hasattr(g, 'conversation_context'):
        g.conversation_context = {
            'last_class': None,
            'last_query_type': None,
            'last_day': None,
            'last_response': None,
            'greeting_done': False
        }
    return g.conversation_context

@app.before_request
def before_request():
    """Initialize context before each request"""
    get_context()

@app.teardown_appcontext
def teardown_appcontext(exception):
    """Clean up context after each request"""
    context = g.pop('conversation_context', None)

print("Loading AI model... This may take a minute...")
try:
    model_name = "microsoft/DialoGPT-small"
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForCausalLM.from_pretrained(model_name)
    print("Model loaded successfully!")
except Exception as e:
    print(f"Error loading model: {e}")
    model = None
    tokenizer = None

def verify_admin_token(token):
    """Verify the admin token with Supabase"""
    try:
        # Get user data from the token
        user = supabase.auth.get_user(token)
        if not user or not user.user:
            return False

        # Direct database query to check admin role
        response = supabase.table('user_roles') \
            .select('role') \
            .eq('user_id', user.user.id) \
            .single() \
            .execute()

        if response.data:
            return response.data.get('role') == 'admin'
        return False
    except Exception as e:
        print(f"Error verifying admin token: {e}")
        return False

def requires_admin(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            # Get the authorization header
            auth_header = request.headers.get('Authorization')
            if not auth_header or not auth_header.startswith('Bearer '):
                return jsonify({'error': 'No token provided'}), 401
            
            # Extract the token
            token = auth_header.split(' ')[1]
            
            # Verify admin status
            if not verify_admin_token(token):
                return jsonify({'error': 'Unauthorized. Admin access required.'}), 401
            
            return f(*args, **kwargs)
        except Exception as e:
            print(f"Error in admin verification: {e}")
            return jsonify({'error': 'Authentication failed'}), 401
    return decorated_function

@app.route('/admin/verify', methods=['GET'])
def verify_admin():
    """Verify if the current user is an admin"""
    try:
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({'is_admin': False, 'error': 'No token provided'}), 401
        
        token = auth_header.split(' ')[1]
        is_admin = verify_admin_token(token)
        
        return jsonify({
            'is_admin': is_admin,
            'message': 'Admin verification successful' if is_admin else 'User is not an admin'
        })
    except Exception as e:
        print(f"Error verifying admin status: {e}")
        return jsonify({
            'is_admin': False,
            'error': str(e)
        }), 500

@app.route('/admin/classes', methods=['GET'])
@requires_admin
def get_all_classes():
    """Get all classes in the timetable"""
    try:
        response = supabase.table('schedules')\
            .select('*')\
            .order('day')\
            .order('period')\
            .execute()
            
        if response.data:
            return jsonify({'classes': response.data})
        return jsonify({'classes': []})
    except Exception as e:
        print(f"Error getting classes: {e}")
        return jsonify({'error': 'Failed to fetch classes'}), 500

@app.route('/admin/classes', methods=['POST'])
@requires_admin
def add_class():
    """Add a new class to the timetable"""
    try:
        data = request.get_json()
        required_fields = ['day', 'period', 'subject', 'start_time', 'end_time', 'room']
        
        if not all(field in data for field in required_fields):
            return jsonify({'error': 'Missing required fields'}), 400
        
        # Check if a class already exists in this slot
        existing = supabase.table('schedules')\
            .select('id')\
            .eq('day', data['day'])\
            .eq('period', data['period'])\
            .execute()
            
        if existing.data:
            return jsonify({'error': 'A class already exists in this time slot'}), 409
        
        # Insert new class
        response = supabase.table('schedules')\
            .insert(data)\
            .execute()
            
        return jsonify({
            'message': 'Class added successfully',
            'class': response.data[0] if response.data else data
        }), 201
    except Exception as e:
        print(f"Error adding class: {e}")
        return jsonify({'error': 'Failed to add class'}), 500

@app.route('/admin/classes/<int:class_id>', methods=['PUT'])
@requires_admin
def update_class(class_id):
    """Update an existing class"""
    try:
        data = request.get_json()
        required_fields = ['day', 'period', 'subject', 'start_time', 'end_time', 'room']
        
        if not all(field in data for field in required_fields):
            return jsonify({'error': 'Missing required fields'}), 400
        
        # Check if the class exists
        existing = supabase.table('schedules')\
            .select('id')\
            .eq('id', class_id)\
            .execute()
            
        if not existing.data:
            return jsonify({'error': 'Class not found'}), 404
        
        # Update the class
        response = supabase.table('schedules')\
            .update(data)\
            .eq('id', class_id)\
            .execute()
            
        return jsonify({
            'message': 'Class updated successfully',
            'class': response.data[0] if response.data else data
        })
    except Exception as e:
        print(f"Error updating class: {e}")
        return jsonify({'error': 'Failed to update class'}), 500

@app.route('/admin/classes/<int:class_id>', methods=['DELETE'])
@requires_admin
def delete_class(class_id):
    """Delete a class from the timetable"""
    try:
        # Check if the class exists
        existing = supabase.table('schedules')\
            .select('id')\
            .eq('id', class_id)\
            .execute()
            
        if not existing.data:
            return jsonify({'error': 'Class not found'}), 404
        
        # Delete the class
        supabase.table('schedules')\
            .delete()\
            .eq('id', class_id)\
            .execute()
            
        return jsonify({'message': 'Class deleted successfully'})
    except Exception as e:
        print(f"Error deleting class: {e}")
        return jsonify({'error': 'Failed to delete class'}), 500

@app.route('/admin/classes/day/<day>', methods=['GET'])
@requires_admin
def get_classes_by_day(day):
    """Get all classes for a specific day"""
    try:
        response = supabase.table('schedules')\
            .select('*')\
            .eq('day', day.upper())\
            .order('period')\
            .execute()
            
        if response.data:
            return jsonify({'classes': response.data})
        return jsonify({'classes': []})
    except Exception as e:
        print(f"Error getting classes for day: {e}")
        return jsonify({'error': f'Failed to fetch classes for {day}'}), 500

def get_first_class(day):
    with app.app_context():
        first_class = ClassSchedule.query.filter_by(day_of_week=day)\
            .order_by(ClassSchedule.start_time)\
            .first()
    
    if first_class:
        context = get_context()
        context['last_class'] = {
        'class_name': first_class.class_name,
        'start_time': first_class.start_time.strftime('%H:%M'),
        'day': day
}

        return f"Your first class on {day} is {first_class.class_name} at {first_class.start_time.strftime('%H:%M')}! 😊"
    return f"You don't have any classes scheduled for {day}. Free time! 🎉"

def time_to_minutes(time_str):
    """Convert time string (HH:MM) to minutes since midnight"""
    try:
        hours, minutes = map(int, time_str.split(':'))
        return hours * 60 + minutes
    except:
        return 0

def update_context(class_info, query_type, response):
    """Update conversation context with latest query information"""
    context = get_context()
    context['last_class'] = class_info
    context['last_query_type'] = query_type
    if class_info and 'day' in class_info:
        context['last_day'] = class_info['day']
    context['last_response'] = response

def fetch_timetable(day=None):
    """Fetch timetable for a specific day or all days"""
    try:
        # Get all schedule tables
        schedule_tables = ['schedule_54321', 'schedule_65432', 'schedule_76543']
        all_schedules = []
        
        for table in schedule_tables:
            query = supabase.table(table).select('*')
            if day:
                query = query.eq('day', day)
            response = query.execute()
            if response.data:
                all_schedules.extend(response.data)
        
        # Sort combined schedules by period
        all_schedules.sort(key=lambda x: x['period'])
        return all_schedules
    except Exception as e:
        print(f"Error fetching timetable: {e}")
        return []

def get_current_class():
    """Get information about the current ongoing class"""
    try:
        now = datetime.now()
        current_day = now.strftime('%A').upper()[:3]
        current_time = now.strftime('%H:%M')
        current_minutes = time_to_minutes(current_time)
        
        classes = fetch_timetable(current_day)
        if not classes:
            response = "No classes today! 🎉"
            update_context(None, 'current_class', response)
            return response
        
        for class_ in classes:
            start_minutes = time_to_minutes(class_['start_time'])
            end_minutes = time_to_minutes(class_['end_time'])
            
            if start_minutes <= current_minutes <= end_minutes:
                class_['day'] = current_day
                response = f"You're currently in {class_['subject']} until {class_['end_time']} in {class_['room'] if class_['room'] else 'TBD'} 📚"
                update_context(class_, 'current_class', response)
                return response
        
        response = "No class right now! 😌"
        update_context(None, 'current_class', response)
        return response
    except Exception as e:
        print(f"Error getting current class: {e}")
        traceback.print_exc()
        return "Sorry, I couldn't check your current class 😅"

def get_friendly_response(text):
    """Handle general conversation"""
    text = text.lower()
    context = get_context()
    
    # Only check for greetings if they are standalone (not part of a larger query)
    if len(text.split()) <= 3:  # Only check short phrases
        # Greetings
        if any(word in text for word in ['hi', 'hello', 'hey', 'good morning', 'good afternoon', 'good evening']):
            greetings = [
                "Hello! How can I help you today? 😊",
                "Hi there! Need help with your schedule? 👋",
                "Hey! Great to see you! How can I assist? 🌟"
            ]
            context['greeting_done'] = True
            return random.choice(greetings)
        
        # How are you
        if 'how are you' in text:
            responses = [
                "I'm doing great, thanks for asking! How about you? 😊",
                "I'm excellent! Ready to help you with your schedule or just chat! 🌟",
                "All good here! What can I help you with today? 💫"
            ]
            return random.choice(responses)
        
        # Thank you
        if any(word in text for word in ['thank', 'thanks', 'thx']):
            responses = [
                "You're welcome! Need anything else? 😊",
                "Anytime! Don't hesitate to ask if you need more help! 🌟",
                "Glad I could help! Let me know if you need anything else! 💫"
            ]
            return random.choice(responses)
        
        # Goodbye
        if any(word in text for word in ['bye', 'goodbye', 'see you', 'cya']):
            responses = [
                "Goodbye! Have a great day! 👋",
                "See you later! Take care! 🌟",
                "Bye! Don't forget about your classes! 📚"
            ]
            return random.choice(responses)
    
    return None

def get_class_after(reference_class):
    """Get information about the class after a specific class"""
    try:
        if not reference_class:
            return "I'm not sure which class you're referring to. Try asking about your next class first! 🤔"
        
        day = reference_class.get('day')
        if not day:
            return "I need more context about which day you're asking about. Try asking about a specific day or your next class! 🤔"
        
        classes = fetch_timetable(day)
        current_period = reference_class.get('period')
    
        if not current_period:
            return "I couldn't determine which period you're asking about. Try asking about your next class first! 🤔"
        
        # Find the class after the reference class
        found_reference = False
        for class_ in classes:
            if found_reference:
                class_info = {
                    'subject': class_['subject'],
                    'start_time': class_['start_time'],
                    'end_time': class_['end_time'],
                    'room': class_['room'],
                    'period': class_['period'],
                    'day': day
                }
                response = f"After {reference_class['subject']}, you have {class_info['subject']} at {class_info['start_time']} in {class_info['room'] if class_info['room'] else 'TBD'} 📚"
                update_context(class_info, 'after_class', response)
                return response
            if class_['period'] == current_period:
                found_reference = True
        
        # If no more classes that day, check next day
        days = ['MON', 'TUE', 'WED', 'THU', 'FRI']
        try:
            current_day_index = days.index(day)
        except ValueError:
            return "I couldn't find the next class. Try asking about a specific day! 🤔"
        
        for i in range(current_day_index + 1, len(days)):
            next_day_classes = fetch_timetable(days[i])
            if next_day_classes and len(next_day_classes) > 0:
                next_class = next_day_classes[0]
                class_info = {
                    'subject': next_class['subject'],
                    'start_time': next_class['start_time'],
                    'end_time': next_class['end_time'],
                    'room': next_class['room'],
                    'period': next_class['period'],
                    'day': days[i]
                }
                response = f"That's your last class for {day}! Your next class is {class_info['subject']} at {class_info['start_time']} on {days[i]} in {class_info['room'] if class_info['room'] else 'TBD'} 📚"
                update_context(class_info, 'after_class', response)
                return response
        
        response = "That's your last class for the week! 🎉"
        update_context(None, 'after_class', response)
        return response
    except Exception as e:
        print(f"Error getting class after: {e}")
        traceback.print_exc()
        return "Sorry, I couldn't find the next class 😅"

def get_next_class():
    """Get information about the next scheduled class"""
    try:
        now = datetime.now()
        current_day = now.strftime('%A').upper()[:3]
        current_time = now.strftime('%H:%M')
        current_minutes = time_to_minutes(current_time)
        
        classes = fetch_timetable(current_day)
        
        # Find the next class today
        for class_ in classes:
            start_minutes = time_to_minutes(class_['start_time'])
            if start_minutes > current_minutes:
                class_info = {
                    'subject': class_['subject'],
                    'start_time': class_['start_time'],
                    'end_time': class_['end_time'],
                    'room': class_['room'],
                    'period': class_['period'],
                    'day': current_day
                }
                response = f"Your next class is {class_info['subject']} at {class_info['start_time']} in {class_info['room'] if class_info['room'] else 'TBD'} 📚"
                update_context(class_info, 'next_class', response)
                return response, class_info
        
        # If no more classes today, check next day with classes
        days = ['MON', 'TUE', 'WED', 'THU', 'FRI']
        current_day_index = days.index(current_day) if current_day in days else -1
        
        for i in range(current_day_index + 1, len(days)):
            next_day_classes = fetch_timetable(days[i])
            if next_day_classes:
                next_class = next_day_classes[0]
                class_info = {
                    'subject': next_class['subject'],
                    'start_time': next_class['start_time'],
                    'end_time': next_class['end_time'],
                    'room': next_class['room'],
                    'period': next_class['period'],
                    'day': days[i]
                }
                response = f"No more classes today! Your next class is {class_info['subject']} at {class_info['start_time']} in {class_info['room'] if class_info['room'] else 'TBD'} on {days[i]} 📚"
                update_context(class_info, 'next_class', response)
                return response, class_info
        
        response = "No more classes scheduled this week! 🎉"
        update_context(None, 'next_class', response)
        return response, None
    except Exception as e:
        print(f"Error getting next class: {e}")
        traceback.print_exc()
        return "Sorry, I couldn't check your next class 😅", None

def get_schedule_for_day(day):
    """Get the full schedule for a specific day"""
    try:
        classes = fetch_timetable(day)
        if not classes:
            return f"No classes scheduled for {day}! 🎉"
        
        schedule = [f"📅 Schedule for {day}:"]
        for class_ in classes:
            schedule.append(f"• {class_['start_time']} - {class_['end_time']}: {class_['subject']} in {class_['room'] if class_['room'] else 'TBD'}")
        
        response = "\n".join(schedule)
        update_context({'day': day}, 'day_schedule', response)
        return response
    except Exception as e:
        print(f"Error getting schedule for day: {e}")
        traceback.print_exc()
        return f"Sorry, I couldn't fetch the schedule for {day} 😅"

def get_nth_class(day, n):
    """Get the nth class for a specific day"""
    try:
        classes = fetch_timetable(day)
        
        if not classes:
            return f"No classes scheduled for {day} 📅"
        
        if n <= 0 or n > len(classes):
            return f"You only have {len(classes)} classes on {day} 🤔"
        
        class_ = classes[n-1]
        class_info = {
            'subject': class_['subject'],
            'start_time': class_['start_time'],
            'end_time': class_['end_time'],
            'room': class_['room'],
            'period': n,
            'day': day
        }
        
        ordinal = {1: "first", 2: "second", 3: "third", 4: "fourth", 5: "fifth"}.get(n, f"{n}th")
        response = f"Your {ordinal} class on {day} is {class_info['subject']} at {class_info['start_time']} in {class_info['room'] if class_info['room'] else 'TBD'} 📚"
        update_context(class_info, 'nth_class', response)
        return response

    except Exception as e:
        print(f"Error getting nth class: {e}")
        traceback.print_exc()
        return f"Sorry, I couldn't find the {n}th class for {day} 😅"

def get_class_location(subject=None, day=None):
    try:
        if subject:
            # Search for specific subject
            all_classes = fetch_timetable()
            for class_ in all_classes:
                if subject.lower() in class_['subject'].lower():
                    return f"{class_['subject']} is in {class_['room'] if class_['room'] else 'TBD'} 🏫"
            return f"I couldn't find the location for {subject} 🤔"
        else:
            # Get current class location
            now = datetime.now()
            current_day = now.strftime('%A').upper()[:3] if not day else day
            current_time = now.strftime('%H:%M')
            current_minutes = time_to_minutes(current_time)
            
            print(f"Current time: {current_time}, Day: {current_day}")  # Debug log
            
            classes = fetch_timetable(current_day)
            if not classes:
                return "No classes found for this day! 🤔"
            
            for class_ in classes:
                start_minutes = time_to_minutes(class_['start_time'])
                end_minutes = time_to_minutes(class_['end_time'])
                
                if start_minutes <= current_minutes <= end_minutes:
                    return f"{class_['subject']} is in {class_['room'] if class_['room'] else 'TBD'} 🏫"
            
            # If no current class, get next class
            for class_ in classes:
                start_minutes = time_to_minutes(class_['start_time'])
                if start_minutes > current_minutes:
                    return f"Your next class {class_['subject']} will be in {class_['room'] if class_['room'] else 'TBD'} 🏫"
            
            return "No more classes today! 🎉"
    except Exception as e:
        print(f"Error getting class location: {e}")
        traceback.print_exc()
        return "Sorry, I couldn't find the location 😅"

def get_class_time(class_obj=None):
    if class_obj is None:
        class_obj = conversation_context['last_class']
    
    if class_obj:
        day = class_obj.day_of_week
        return f"{class_obj.class_name} on {day} runs from {class_obj.start_time.strftime('%H:%M')} to {class_obj.end_time.strftime('%H:%M')} ⏰"
    return "Which class would you like to know the time for? 🤔"

def get_full_subject_name(subject):
    """Map short forms and variations to full subject names"""
    subject_mapping = {
        'PPL': 'PRINCIPLES OF PL',
        'PRINCIPLES': 'PRINCIPLES OF PL',
        'SOFTWARE': 'SOFTWARE ENGG',
        'SOFTWARE ENGINEERING': 'SOFTWARE ENGG',
        'DISTRIBUTED': 'DISTRIBUTED SYSTEMS',
        'SECURITY': 'COMPUTER SECURITY',
        'COMPUTER SEC': 'COMPUTER SECURITY'
    }
    
    return subject_mapping.get(subject.upper(), subject.upper())

def count_subject_occurrences(subject, day=None):
    """Count how many times a subject occurs on a specific day or in the week"""
    try:
        # Get the full subject name or standardized form
        full_subject = get_full_subject_name(subject)
        
        if day:
            classes = fetch_timetable(day)
            # Check for both full name and variations
            count = sum(1 for class_ in classes if any(
                variation in class_['subject'].upper() 
                for variation in [full_subject, subject.upper()]
            ))
            if count > 0:
                return f"You have {count} {full_subject} {'class' if count == 1 else 'classes'} on {day} 📚"
            return f"You don't have any {full_subject} classes on {day} 📅"
        else:
            # Count for the whole week
            days = ['MON', 'TUE', 'WED', 'THU', 'FRI']
            total_count = 0
            day_counts = {}
            
            for current_day in days:
                classes = fetch_timetable(current_day)
                day_count = sum(1 for class_ in classes if any(
                    variation in class_['subject'].upper() 
                    for variation in [full_subject, subject.upper()]
                ))
                if day_count > 0:
                    day_counts[current_day] = day_count
                    total_count += day_count
            
            if total_count == 0:
                return f"You don't have any {full_subject} classes this week 📅"
            
            # Create detailed response
            response = [f"You have {total_count} {full_subject} {'class' if total_count == 1 else 'classes'} this week:"]
            for day, count in day_counts.items():
                response.append(f"• {day}: {count} {'class' if count == 1 else 'classes'}")
            
            return "\n".join(response) + " 📚"
    except Exception as e:
        print(f"Error counting subject occurrences: {e}")
        traceback.print_exc()
        return f"Sorry, I couldn't count the {full_subject} classes 😅"

def get_day_code(text):
    """Helper function to get the day code from text including relative days"""
    days = {
        'monday': 'MON', 
        'tuesday': 'TUE', 
        'wednesday': 'WED', 
        'thursday': 'THU', 
        'friday': 'FRI',
        'saturday': None,  # No classes on weekends
        'sunday': None     # No classes on weekends
    }
    
    # First check for relative days
    now = datetime.now()
    current_day = now.strftime('%A').lower()
    print(f"Current day: {current_day}")
    
    if 'tomorrow' in text:
        # Get tomorrow's day name
        tomorrow = (now + timedelta(days=1)).strftime('%A').lower()
        print(f"Tomorrow detected. Tomorrow is: {tomorrow}")
        day_code = days.get(tomorrow)
        print(f"Day code for tomorrow: {day_code}")
        if day_code is None:
            if tomorrow in ['saturday', 'sunday']:
                # If tomorrow is a weekend, look for the next weekday
                days_to_add = 2 if tomorrow == 'saturday' else 1
                next_weekday = (now + timedelta(days=days_to_add)).strftime('%A').lower()
                print(f"Tomorrow is weekend, next weekday is: {next_weekday}")
                day_code = days.get(next_weekday)
                if day_code:
                    return day_code, f"Since tomorrow is {tomorrow.capitalize()}, here's your schedule for {next_weekday.capitalize()}"
                return None, "No classes on weekends! 🎉"
            return None, "No classes tomorrow! 🎉"
        return day_code, None
    elif 'today' in text:
        print(f"Today detected. Today is: {current_day}")
        day_code = days.get(current_day)
        print(f"Day code for today: {day_code}")
        if day_code is None:
            if current_day in ['saturday', 'sunday']:
                return None, "It's the weekend - no classes today! 🎉"
            return None, "No classes today! 🎉"
        return day_code, None
    elif 'yesterday' in text:
        yesterday = (now - timedelta(days=1)).strftime('%A').lower()
        print(f"Yesterday detected. Yesterday was: {yesterday}")
        day_code = days.get(yesterday)
        print(f"Day code for yesterday: {day_code}")
        if day_code is None:
            if yesterday in ['saturday', 'sunday']:
                return None, "That was the weekend - no classes! 🎉"
            return None, "No classes yesterday! 🎉"
        return day_code, None
    
    # Then check for specific days
    for day_name, day_code in days.items():
        if day_name in text:
            print(f"Found specific day: {day_name} -> {day_code}")
            if day_code is None:
                return None, f"No classes on {day_name.capitalize()}! 🎉"
            return day_code, None
    
    print("No day found in text")
    return None, None

def handle_schedule_query(text):
    """Main function to handle all schedule-related queries"""
    try:
        print(f"Handling schedule query: {text}")
        text = text.lower()
        print(f"Lowercased text: {text}")
        context = get_context()
        
        # First check for general conversation
        friendly_response = get_friendly_response(text)
        if friendly_response:
            print(f"Returning friendly response: {friendly_response}")
            return friendly_response
        
        # Get day code first
        mentioned_day, day_message = get_day_code(text)
        print(f"Detected day code: {mentioned_day}, message: {day_message}")
        
        # Check for ordinal numbers first since they're more specific
        ordinal_numbers = {
            'first': 1, 'second': 2, 'third': 3, 'fourth': 4, 'fifth': 5,
            '1st': 1, '2nd': 2, '3rd': 3, '4th': 4, '5th': 5,
            'last': -1
        }
        
        has_ordinal = any(ordinal in text for ordinal in ordinal_numbers.keys())
        has_numeric = bool(re.search(r'(\d+)(?:st|nd|rd|th)?\s*(?:class|period)', text))
        
        print(f"Has ordinal: {has_ordinal}, Has numeric: {has_numeric}")
        print(f"Found ordinals: {[ord for ord in ordinal_numbers.keys() if ord in text]}")
        
        # If asking about a specific period, we need a day
        if has_ordinal or has_numeric:
            print("Processing period-specific query")
            if not mentioned_day and day_message:
                print(f"No day but have message: {day_message}")
                return day_message
            elif not mentioned_day:
                print("No day mentioned")
                return "Which day would you like to know about? 🤔"
            
            # Handle ordinal numbers
            for ordinal, num in ordinal_numbers.items():
                if ordinal in text:
                    print(f"Found ordinal: {ordinal} -> {num}")
                    if num == -1:  # Handle "last class" query
                        classes = fetch_timetable(mentioned_day)
                        if classes:
                            num = len(classes)
                        else:
                            return f"No classes found for {mentioned_day} 🤔"
                    print(f"Getting {ordinal} class for {mentioned_day}")
                    return get_nth_class(mentioned_day, num)
            
            # Handle numeric references
            numeric_match = re.search(r'(\d+)(?:st|nd|rd|th)?\s*(?:class|period)', text)
            if numeric_match:
                num = int(numeric_match.group(1))
                print(f"Getting class number {num} for {mentioned_day}")
                return get_nth_class(mentioned_day, num)
        
        # If we got a specific message about the day (e.g., weekend message), return it
        if day_message:
            print(f"Returning day message: {day_message}")
            return day_message
        
        if mentioned_day:
            context['last_day'] = mentioned_day
            print(f"Setting last_day in context: {mentioned_day}")
            
            # Check if asking for full schedule
            if any(phrase in text for phrase in ['schedule', 'classes', 'periods', 'lectures']):
                print(f"Getting schedule for day: {mentioned_day}")
                return get_schedule_for_day(mentioned_day)
            
            # If just asking about the day, show full schedule
            print(f"Getting full schedule for {mentioned_day}")
            return get_schedule_for_day(mentioned_day)
        
        # Check for follow-up questions about classes
        follow_up_phrases = [
            'after that', 'following that', 'after this', 'what then', 'and then',
            'what about after', 'what follows', 'what comes after', 'what is after',
            'what class is after', 'what comes next', 'what is next after that'
        ]
        
        if any(phrase in text for phrase in follow_up_phrases):
            print("Processing follow-up question")
            if context.get('last_class') and context.get('last_query_type') in ['current_class', 'next_class', 'after_class', 'nth_class']:
                return get_class_after(context['last_class'])
            else:
                return "I'm not sure which class you're referring to. Try asking about a specific class first! 🤔"
        
        # Check for next class query
        if any(phrase in text for phrase in ['next class', 'next period', 'upcoming class', 'following class']):
            print("Getting next class")
            response, _ = get_next_class()
            return response
        
        # Check for current class query
        if any(phrase in text for phrase in ['current class', 'right now', 'this class', 'present class']):
            print("Getting current class")
            return get_current_class()
    
        # Check for full week schedule
        if "week" in text or "all" in text:
            print("Getting full week schedule")
            full_schedule = []
            for day_code in ['MON', 'TUE', 'WED', 'THU', 'FRI']:
                day_schedule = get_schedule_for_day(day_code)
                if "No classes" not in day_schedule:
                    full_schedule.append(day_schedule)
            return "\n\n".join(full_schedule) if full_schedule else "No classes scheduled this week! 🎉"
        
        # If no schedule-related query is matched, give a helpful response
        print("No specific query matched")
        if not context.get('greeting_done'):
            return "Hi! I can help you with your schedule! Try asking about your next class, current class, or schedule for any day! 😊"
        else:
            return "I'm here to help! You can ask about your schedule, next class, or just chat with me! 🌟"
            
    except Exception as e:
        print(f"Error handling schedule query: {e}")
        traceback.print_exc()
        return "Sorry, I had trouble understanding that request 😅"

def generate_ai_response(user_input):
    # Always check for schedule-related queries first
    schedule_response = handle_schedule_query(user_input)
    if schedule_response:
        return schedule_response

    # For non-schedule queries, make the AI more friendly
    if model is None or tokenizer is None:
        return "I'd love to chat more, but my AI brain isn't fully working right now 😅"
    
    try:
        # Add context about being a friendly assistant
        context = "You are a friendly and helpful AI assistant who helps students with their class schedules. "
        context += "You use emojis and casual language to make conversations more engaging. "
        enhanced_input = context + user_input
        
        # Generate response
        inputs = tokenizer.encode(enhanced_input + tokenizer.eos_token, return_tensors='pt')
        with torch.no_grad():
            outputs = model.generate(
                inputs, 
                max_length=150,
                pad_token_id=tokenizer.eos_token_id,
            temperature=0.7,
                num_return_sequences=1,
                top_k=50,
                top_p=0.9
        )
        
        response = tokenizer.decode(outputs[0], skip_special_tokens=True)
        # Add emoji based on sentiment
        if any(word in response.lower() for word in ['sorry', 'cannot', "can't", 'error']):
            response += " 😅"
        elif any(word in response.lower() for word in ['help', 'assist']):
            response += " 👍"
        else:
            response += " 😊"
        return response.strip()
    except Exception as e:
        print(f"Error generating response: {e}")
        return "Oops! Something went wrong with my thinking process 😅 Can you try asking that again?"

@app.route('/process-voice', methods=['POST'])
def process_voice():
    try:
        data = request.get_json()
        if not data:
            return jsonify({'reply': "No data received"}), 400
        
        user_input = data.get('text', '')  # Don't lowercase here
        if not user_input:
            return jsonify({'reply': "Please say something!"}), 400

        print(f"Processing voice input: {user_input}")
        
        # Process the query and get response
        response = handle_schedule_query(user_input)
        print(f"Generated response: {response}")
        return jsonify({'reply': response})
    
    except Exception as e:
        print(f"Error processing request: {e}")
        traceback.print_exc()
        return jsonify({'reply': "Sorry, an error occurred while processing your request."}), 500

@app.route('/add-class', methods=['POST'])
def add_class_schedule_legacy():
    try:
        data = request.get_json()
        if not all(k in data for k in ['class_name', 'day_of_week', 'start_time', 'end_time', 'room']):
            return jsonify({'error': 'Missing required fields'}), 400

        # Convert time strings to Time objects
        start_time = datetime.strptime(data['start_time'], '%H:%M').time()
        end_time = datetime.strptime(data['end_time'], '%H:%M').time()

        new_class = ClassSchedule(
            class_name=data['class_name'],
            day_of_week=data['day_of_week'],
            start_time=start_time,
            end_time=end_time,
            room=data['room']
        )

        db.session.add(new_class)
        db.session.commit()

        return jsonify({'message': 'Class added successfully', 'class': new_class.to_dict()}), 201

    except Exception as e:
        print(f"Error adding class: {e}")
        return jsonify({'error': 'Failed to add class'}), 500

@app.route('/api/courses', methods=['GET'])
def get_courses():
    """Get all courses"""
    try:
        response = supabase.table('courses')\
            .select('*')\
            .execute()
        return jsonify(response.data if response.data else [])
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/courses', methods=['POST'])
def add_new_course():
    """Add a new course"""
    try:
        data = request.get_json()
        if not all(k in data for k in ['code', 'name', 'semester']):
            return jsonify({'error': 'Missing required fields'}), 400
        
        response = supabase.table('courses')\
            .insert({
                'code': data['code'],
                'name': data['name'],
                'description': data.get('description', ''),
                'semester': data['semester']
            })\
            .execute()
            
        return jsonify({
            'message': 'Course added successfully',
            'course': response.data[0] if response.data else None
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/courses/<class_code>/schedule', methods=['GET'])
def get_course_schedule(class_code):
    """Get schedule for a specific course"""
    try:
        response = supabase.table('course_schedules')\
            .select('*')\
            .eq('course_code', class_code)\
            .execute()
        return jsonify(response.data if response.data else [])
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/courses/<class_code>/schedule', methods=['POST'])
def add_class_schedule(class_code):
    """Add a schedule slot for a specific course"""
    try:
        data = request.get_json()
        if not all(k in data for k in ['day_of_week', 'start_time', 'end_time', 'room']):
            return jsonify({'error': 'Missing required fields'}), 400
        
        # Validate the class exists
        course = supabase.table('courses')\
            .select('code')\
            .eq('code', class_code)\
            .execute()
            
        if not course.data:
            return jsonify({'error': 'Course not found'}), 404
        
        # Add schedule entry
        schedule_data = {
            'course_code': class_code,
            'day_of_week': data['day_of_week'],
            'start_time': data['start_time'],
            'end_time': data['end_time'],
            'room': data['room'],
            'instructor': data.get('instructor')
        }
        
        response = supabase.table('course_schedules')\
            .insert(schedule_data)\
            .execute()
            
        return jsonify({
            'message': 'Schedule added successfully',
            'schedule': response.data[0] if response.data else None
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/courses/<class_code>/schedule/<int:schedule_id>', methods=['PUT'])
def update_class_schedule(class_code, schedule_id):
    """Update a schedule slot for a specific course"""
    try:
        data = request.get_json()
        if not any(k in data for k in ['day_of_week', 'start_time', 'end_time', 'room', 'instructor']):
            return jsonify({'error': 'No fields to update'}), 400
        
        # Check if schedule exists
        schedule = supabase.table('course_schedules')\
            .select('id')\
            .eq('id', schedule_id)\
            .eq('course_code', class_code)\
            .execute()
            
        if not schedule.data:
            return jsonify({'error': 'Schedule not found'}), 404
        
        # Update schedule
        response = supabase.table('course_schedules')\
            .update(data)\
            .eq('id', schedule_id)\
            .execute()
            
        return jsonify({
            'message': 'Schedule updated successfully',
            'schedule': response.data[0] if response.data else None
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/courses/<class_code>/schedule/<int:schedule_id>', methods=['DELETE'])
def delete_class_schedule(class_code, schedule_id):
    """Delete a schedule slot for a specific course"""
    try:
        # Check if schedule exists
        schedule = supabase.table('course_schedules')\
            .select('id')\
            .eq('id', schedule_id)\
            .eq('course_code', class_code)\
            .execute()
            
        if not schedule.data:
            return jsonify({'error': 'Schedule not found'}), 404
        
        # Delete schedule
        supabase.table('course_schedules')\
            .delete()\
            .eq('id', schedule_id)\
            .execute()
            
        return jsonify({'message': 'Schedule deleted successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    # In production, the port will be provided by the hosting platform
    port = int(os.environ.get('PORT', PORT))
    app.run(host='0.0.0.0', port=port, debug=DEBUG)
