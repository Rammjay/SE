import 'package:json_annotation/json_annotation.dart';

part 'schedule.g.dart';

@JsonSerializable()
class Course {
  final String courseCode;
  final String courseName;
  final String? description;
  final int credits;
  final DateTime createdAt;
  final DateTime updatedAt;

  Course({
    required this.courseCode,
    required this.courseName,
    this.description,
    required this.credits,
    required this.createdAt,
    required this.updatedAt,
  });

  factory Course.fromJson(Map<String, dynamic> json) => _$CourseFromJson(json);
  Map<String, dynamic> toJson() => _$CourseToJson(this);
}

@JsonSerializable()
class Schedule {
  final String id;
  final String courseCode;
  final String dayOfWeek;
  final String startTime;
  final String endTime;
  final String roomNumber;
  final String? instructor;
  final String semester;
  final String academicYear;
  final DateTime createdAt;
  final DateTime updatedAt;

  Schedule({
    required this.id,
    required this.courseCode,
    required this.dayOfWeek,
    required this.startTime,
    required this.endTime,
    required this.roomNumber,
    this.instructor,
    required this.semester,
    required this.academicYear,
    required this.createdAt,
    required this.updatedAt,
  });

  factory Schedule.fromJson(Map<String, dynamic> json) => _$ScheduleFromJson(json);
  Map<String, dynamic> toJson() => _$ScheduleToJson(this);
} 