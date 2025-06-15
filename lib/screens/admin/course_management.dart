import 'package:flutter/material.dart';
import 'package:supabase_flutter/supabase_flutter.dart';
import '../../models/schedule.dart';
import '../../services/schedule_service.dart';

class CourseManagement extends StatefulWidget {
  const CourseManagement({super.key});

  @override
  State<CourseManagement> createState() => _CourseManagementState();
}

class _CourseManagementState extends State<CourseManagement> {
  final _scheduleService = ScheduleService(Supabase.instance.client);
  List<Course> _courses = [];
  bool _isLoading = true;

  @override
  void initState() {
    super.initState();
    _loadCourses();
  }

  Future<void> _loadCourses() async {
    try {
      setState(() => _isLoading = true);
      final courses = await _scheduleService.getAllCourses();
      setState(() {
        _courses = courses;
        _isLoading = false;
      });
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Error loading courses: $e')),
      );
      setState(() => _isLoading = false);
    }
  }

  Future<void> _deleteCourse(Course course) async {
    try {
      await _scheduleService.deleteCourse(course.courseCode);
      await _loadCourses();
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Course deleted successfully')),
        );
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Error deleting course: $e')),
        );
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Course Management'),
        backgroundColor: Theme.of(context).colorScheme.primaryContainer,
      ),
      body: _isLoading
          ? const Center(child: CircularProgressIndicator())
          : ListView.builder(
              itemCount: _courses.length,
              itemBuilder: (context, index) {
                final course = _courses[index];
                return Card(
                  margin: const EdgeInsets.symmetric(
                    horizontal: 16,
                    vertical: 8,
                  ),
                  child: ListTile(
                    title: Text(course.courseName),
                    subtitle: Text(course.courseCode),
                    trailing: Row(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        IconButton(
                          icon: const Icon(Icons.edit),
                          onPressed: () => _showCourseDialog(
                            context,
                            existingCourse: course,
                          ),
                        ),
                        IconButton(
                          icon: const Icon(Icons.delete),
                          onPressed: () => _showDeleteConfirmation(course),
                        ),
                      ],
                    ),
                  ),
                );
              },
            ),
      floatingActionButton: FloatingActionButton(
        onPressed: () => _showCourseDialog(context),
        child: const Icon(Icons.add),
      ),
    );
  }

  Future<void> _showDeleteConfirmation(Course course) async {
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Delete Course'),
        content: Text(
          'Are you sure you want to delete ${course.courseName}? This will also delete all associated schedules.',
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context, false),
            child: const Text('CANCEL'),
          ),
          TextButton(
            onPressed: () => Navigator.pop(context, true),
            child: const Text('DELETE'),
          ),
        ],
      ),
    );

    if (confirmed == true && mounted) {
      await _deleteCourse(course);
    }
  }

  Future<void> _showCourseDialog(
    BuildContext context, {
    Course? existingCourse,
  }) async {
    final formKey = GlobalKey<FormState>();
    String courseCode = existingCourse?.courseCode ?? '';
    String courseName = existingCourse?.courseName ?? '';
    String? description = existingCourse?.description;
    int credits = existingCourse?.credits ?? 3;

    final saved = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: Text(existingCourse == null ? 'Add Course' : 'Edit Course'),
        content: Form(
          key: formKey,
          child: SingleChildScrollView(
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                TextFormField(
                  initialValue: courseCode,
                  decoration: const InputDecoration(
                    labelText: 'Course Code',
                    hintText: 'e.g., CS101',
                  ),
                  validator: (value) {
                    if (value == null || value.isEmpty) {
                      return 'Please enter a course code';
                    }
                    return null;
                  },
                  onSaved: (value) => courseCode = value!,
                ),
                TextFormField(
                  initialValue: courseName,
                  decoration: const InputDecoration(
                    labelText: 'Course Name',
                    hintText: 'e.g., Introduction to Programming',
                  ),
                  validator: (value) {
                    if (value == null || value.isEmpty) {
                      return 'Please enter a course name';
                    }
                    return null;
                  },
                  onSaved: (value) => courseName = value!,
                ),
                TextFormField(
                  initialValue: description,
                  decoration: const InputDecoration(
                    labelText: 'Description (Optional)',
                    hintText: 'Enter course description',
                  ),
                  maxLines: 3,
                  onSaved: (value) => description = value,
                ),
                TextFormField(
                  initialValue: credits.toString(),
                  decoration: const InputDecoration(
                    labelText: 'Credits',
                    hintText: 'e.g., 3',
                  ),
                  keyboardType: TextInputType.number,
                  validator: (value) {
                    if (value == null || value.isEmpty) {
                      return 'Please enter credits';
                    }
                    if (int.tryParse(value) == null) {
                      return 'Please enter a valid number';
                    }
                    return null;
                  },
                  onSaved: (value) => credits = int.parse(value!),
                ),
              ],
            ),
          ),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context, false),
            child: const Text('CANCEL'),
          ),
          TextButton(
            onPressed: () {
              if (formKey.currentState!.validate()) {
                formKey.currentState!.save();
                Navigator.pop(context, true);
              }
            },
            child: const Text('SAVE'),
          ),
        ],
      ),
    );

    if (saved == true && mounted) {
      try {
        final course = Course(
          courseCode: courseCode,
          courseName: courseName,
          description: description,
          credits: credits,
          createdAt: existingCourse?.createdAt ?? DateTime.now(),
          updatedAt: DateTime.now(),
        );

        if (existingCourse == null) {
          await _scheduleService.addCourse(course);
        } else {
          await _scheduleService.updateCourse(course);
        }

        await _loadCourses();

        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(
              content: Text(
                existingCourse == null
                    ? 'Course added successfully'
                    : 'Course updated successfully',
              ),
            ),
          );
        }
      } catch (e) {
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(content: Text('Error saving course: $e')),
          );
        }
      }
    }
  }
} 