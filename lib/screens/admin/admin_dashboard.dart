import 'package:flutter/material.dart';
import 'package:supabase_flutter/supabase_flutter.dart';
import '../../services/auth_service.dart';
import '../../services/database_service.dart';
import 'course_management.dart';
import 'schedule_management.dart';
import '../login_screen.dart';

class AdminDashboard extends StatefulWidget {
  const AdminDashboard({super.key});

  @override
  State<AdminDashboard> createState() => _AdminDashboardState();
}

class _AdminDashboardState extends State<AdminDashboard> {
  final DatabaseService _databaseService = DatabaseService();
  List<Map<String, dynamic>> _schedules = [];
  bool _isLoading = true;

  @override
  void initState() {
    super.initState();
    _loadData();
  }

  Future<void> _loadData() async {
    setState(() => _isLoading = true);
    try {
      final schedules = await _databaseService.getAllSchedules();
      setState(() {
        _schedules = schedules;
        _isLoading = false;
      });
    } catch (e) {
      print('Error loading data: $e');
      setState(() => _isLoading = false);
    }
  }

  Future<void> _handleLogout(BuildContext context) async {
    try {
      await Supabase.instance.client.auth.signOut();
      if (context.mounted) {
        Navigator.of(context).pushAndRemoveUntil(
          MaterialPageRoute(
            builder: (_) => LoginScreen(
              authService: AuthService(Supabase.instance.client),
            ),
          ),
          (route) => false,
        );
      }
    } catch (e) {
      if (context.mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Error logging out: $e')),
        );
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Admin Dashboard'),
        backgroundColor: Theme.of(context).colorScheme.primaryContainer,
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
            tooltip: 'Refresh',
            onPressed: _loadData,
          ),
          Padding(
            padding: const EdgeInsets.only(right: 16.0),
            child: IconButton(
              icon: const Icon(Icons.logout),
              tooltip: 'Logout',
              onPressed: () => _handleLogout(context),
              iconSize: 24,
              color: Theme.of(context).colorScheme.onPrimaryContainer,
            ),
          ),
        ],
      ),
      body: _isLoading
          ? const Center(child: CircularProgressIndicator())
          : SingleChildScrollView(
              padding: const EdgeInsets.all(16.0),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    children: [
                      Expanded(
                        child: _DashboardCard(
                          title: 'Manage Courses',
                          icon: Icons.book,
                          onTap: () => Navigator.push(
                            context,
                            MaterialPageRoute(builder: (_) => const CourseManagement()),
                          ),
                        ),
                      ),
                      const SizedBox(width: 16),
                      Expanded(
                        child: _DashboardCard(
                          title: 'Manage Schedules',
                          icon: Icons.schedule,
                          onTap: () => Navigator.push(
                            context,
                            MaterialPageRoute(builder: (_) => const ScheduleManagement()),
                          ),
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 24),
                  Text(
                    'Current Schedule',
                    style: Theme.of(context).textTheme.headlineSmall,
                  ),
                  const SizedBox(height: 16),
                  Card(
                    child: SingleChildScrollView(
                      scrollDirection: Axis.horizontal,
                      child: DataTable(
                        columns: const [
                          DataColumn(label: Text('Day')),
                          DataColumn(label: Text('Period')),
                          DataColumn(label: Text('Start Time')),
                          DataColumn(label: Text('End Time')),
                          DataColumn(label: Text('Subject')),
                          DataColumn(label: Text('Room')),
                          DataColumn(label: Text('Actions')),
                        ],
                        rows: _schedules.map((schedule) {
                          return DataRow(
                            cells: [
                              DataCell(Text(schedule['day'] ?? '')),
                              DataCell(Text(schedule['period']?.toString() ?? '')),
                              DataCell(Text(schedule['start_time'] ?? '')),
                              DataCell(Text(schedule['end_time'] ?? '')),
                              DataCell(Text(schedule['subject'] ?? '')),
                              DataCell(Text(schedule['room'] ?? '')),
                              DataCell(
                                Row(
                                  mainAxisSize: MainAxisSize.min,
                                  children: [
                                    IconButton(
                                      icon: const Icon(Icons.edit),
                                      onPressed: () {
                                        Navigator.push(
                                          context,
                                          MaterialPageRoute(
                                            builder: (_) => ScheduleManagement(
                                              initialSchedule: schedule,
                                            ),
                                          ),
                                        );
                                      },
                                    ),
                                  ],
                                ),
                              ),
                            ],
                          );
                        }).toList(),
                      ),
                    ),
                  ),
                ],
              ),
            ),
      floatingActionButton: FloatingActionButton(
        onPressed: () => Navigator.push(
          context,
          MaterialPageRoute(builder: (_) => const ScheduleManagement()),
        ),
        child: const Icon(Icons.add),
      ),
    );
  }
}

class _DashboardCard extends StatelessWidget {
  final String title;
  final IconData icon;
  final VoidCallback onTap;

  const _DashboardCard({
    required this.title,
    required this.icon,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return Card(
      child: InkWell(
        onTap: onTap,
        child: Padding(
          padding: const EdgeInsets.all(16.0),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              Icon(icon, size: 48),
              const SizedBox(height: 8),
              Text(title),
            ],
          ),
        ),
      ),
    );
  }
} 