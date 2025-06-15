import 'package:supabase_flutter/supabase_flutter.dart';
import '../models/schedule.dart';

class ScheduleService {
  final SupabaseClient _supabase;

  ScheduleService(this._supabase);

  // Get all courses
  Future<List<Course>> getAllCourses() async {
    final response = await _supabase
        .from('courses')
        .select()
        .order('course_code');
    
    return (response as List)
        .map((json) => Course.fromJson(json))
        .toList();
  }

  // Get course by code
  Future<Course> getCourseByCode(String courseCode) async {
    final response = await _supabase
        .from('courses')
        .select()
        .eq('course_code', courseCode)
        .single();
    
    return Course.fromJson(response);
  }

  // Get schedules for a specific course
  Future<List<Schedule>> getSchedulesForCourse(String courseCode) async {
    final response = await _supabase
        .from('schedules')
        .select()
        .eq('course_code', courseCode)
        .order('day_of_week')
        .order('start_time');
    
    return (response as List)
        .map((json) => Schedule.fromJson(json))
        .toList();
  }

  // Get schedules for current semester
  Future<List<Schedule>> getCurrentSemesterSchedules() async {
    final response = await _supabase
        .from('current_semester_schedules')
        .select();
    
    return (response as List)
        .map((json) => Schedule.fromJson(json))
        .toList();
  }

  // Get schedules for a specific day
  Future<List<Schedule>> getSchedulesForDay(String dayOfWeek) async {
    final response = await _supabase
        .from('schedules')
        .select('*, courses(*)')
        .eq('day_of_week', dayOfWeek)
        .order('start_time');
    
    return (response as List)
        .map((json) => Schedule.fromJson(json))
        .toList();
  }

  // Add a new course (admin only)
  Future<Course> addCourse(Course course) async {
    final response = await _supabase
        .from('courses')
        .insert(course.toJson())
        .select()
        .single();
    
    return Course.fromJson(response);
  }

  // Add a new schedule (admin only)
  Future<Schedule> addSchedule(Schedule schedule) async {
    final response = await _supabase
        .from('schedules')
        .insert(schedule.toJson())
        .select()
        .single();
    
    return Schedule.fromJson(response);
  }

  // Update a course (admin only)
  Future<Course> updateCourse(Course course) async {
    final response = await _supabase
        .from('courses')
        .update(course.toJson())
        .eq('course_code', course.courseCode)
        .select()
        .single();
    
    return Course.fromJson(response);
  }

  // Update a schedule (admin only)
  Future<Schedule> updateSchedule(Schedule schedule) async {
    final response = await _supabase
        .from('schedules')
        .update(schedule.toJson())
        .eq('id', schedule.id)
        .select()
        .single();
    
    return Schedule.fromJson(response);
  }

  // Delete a course (admin only)
  Future<void> deleteCourse(String courseCode) async {
    await _supabase
        .from('courses')
        .delete()
        .eq('course_code', courseCode);
  }

  // Delete a schedule (admin only)
  Future<void> deleteSchedule(String scheduleId) async {
    await _supabase
        .from('schedules')
        .delete()
        .eq('id', scheduleId);
  }
} 