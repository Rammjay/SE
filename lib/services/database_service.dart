import 'package:http/http.dart' as http;
import 'dart:convert';

class DatabaseService {
  static const String baseUrl = 'http://10.113.19.134:5000/api';  // Update with your Flask server URL

  // Get all courses from SQLite database
  Future<List<Map<String, dynamic>>> getAllCourses() async {
    try {
      final response = await http.get(Uri.parse('$baseUrl/courses'));
      if (response.statusCode == 200) {
        return List<Map<String, dynamic>>.from(json.decode(response.body));
      } else {
        throw Exception('Failed to load courses: ${response.statusCode}');
      }
    } catch (e) {
      print('Error getting courses: $e');
      return [];
    }
  }

  // Get all schedules from SQLite database
  Future<List<Map<String, dynamic>>> getAllSchedules() async {
    try {
      final response = await http.get(Uri.parse('$baseUrl/schedules'));
      if (response.statusCode == 200) {
        return List<Map<String, dynamic>>.from(json.decode(response.body));
      } else {
        throw Exception('Failed to load schedules: ${response.statusCode}');
      }
    } catch (e) {
      print('Error getting schedules: $e');
      return [];
    }
  }

  // Get schedule for a specific class
  Future<List<Map<String, dynamic>>> getClassSchedule(String classCode) async {
    try {
      final response = await http.get(Uri.parse('$baseUrl/courses/$classCode/schedule'));
      if (response.statusCode == 200) {
        return List<Map<String, dynamic>>.from(json.decode(response.body));
      } else {
        throw Exception('Failed to load class schedule: ${response.statusCode}');
      }
    } catch (e) {
      print('Error getting class schedule: $e');
      return [];
    }
  }

  // Add a new course
  Future<bool> addCourse(Map<String, dynamic> courseData) async {
    try {
      final response = await http.post(
        Uri.parse('$baseUrl/courses'),
        headers: {'Content-Type': 'application/json'},
        body: json.encode(courseData),
      );
      return response.statusCode == 200;
    } catch (e) {
      print('Error adding course: $e');
      return false;
    }
  }

  // Add a schedule for a specific class
  Future<bool> addClassSchedule(String classCode, Map<String, dynamic> scheduleData) async {
    try {
      final response = await http.post(
        Uri.parse('$baseUrl/courses/$classCode/schedule'),
        headers: {'Content-Type': 'application/json'},
        body: json.encode(scheduleData),
      );
      return response.statusCode == 200;
    } catch (e) {
      print('Error adding class schedule: $e');
      return false;
    }
  }

  // Update a schedule for a specific class
  Future<bool> updateClassSchedule(String classCode, int scheduleId, Map<String, dynamic> scheduleData) async {
    try {
      final response = await http.put(
        Uri.parse('$baseUrl/courses/$classCode/schedule/$scheduleId'),
        headers: {'Content-Type': 'application/json'},
        body: json.encode(scheduleData),
      );
      return response.statusCode == 200;
    } catch (e) {
      print('Error updating class schedule: $e');
      return false;
    }
  }

  // Delete a schedule for a specific class
  Future<bool> deleteClassSchedule(String classCode, int scheduleId) async {
    try {
      final response = await http.delete(
        Uri.parse('$baseUrl/courses/$classCode/schedule/$scheduleId'),
      );
      return response.statusCode == 200;
    } catch (e) {
      print('Error deleting class schedule: $e');
      return false;
    }
  }
} 