import 'package:flutter/material.dart';
import 'package:supabase_flutter/supabase_flutter.dart';
import 'package:flutter_form_builder/flutter_form_builder.dart';
import 'package:form_builder_validators/form_builder_validators.dart';

class ScheduleManagement extends StatefulWidget {
  final Map<String, dynamic>? initialSchedule;
  
  const ScheduleManagement({super.key, this.initialSchedule});

  @override
  State<ScheduleManagement> createState() => _ScheduleManagementState();
}

class _ScheduleManagementState extends State<ScheduleManagement> {
  final _formKey = GlobalKey<FormBuilderState>();
  bool _isLoading = false;

  final List<String> _days = ['MON', 'TUE', 'WED', 'THU', 'FRI', 'SAT', 'SUN'];

  @override
  void initState() {
    super.initState();
    if (widget.initialSchedule != null) {
      _formKey.currentState?.patchValue({
        'day': widget.initialSchedule!['day'],
        'period': widget.initialSchedule!['period'].toString(),
        'start_time': widget.initialSchedule!['start_time'],
        'end_time': widget.initialSchedule!['end_time'],
        'subject': widget.initialSchedule!['subject'],
        'room': widget.initialSchedule!['room'],
      });
    }
  }

  Future<void> _saveSchedule() async {
    if (_formKey.currentState?.saveAndValidate() ?? false) {
      setState(() => _isLoading = true);
      try {
        final values = _formKey.currentState!.value;
        final data = {
          'day': values['day'],
          'period': int.parse(values['period']),
          'start_time': values['start_time'],
          'end_time': values['end_time'],
          'subject': values['subject'],
          'room': values['room'],
        };

        if (widget.initialSchedule != null) {
          await Supabase.instance.client
              .from('schedules')
              .update(data)
              .eq('id', widget.initialSchedule!['id']);
        } else {
          await Supabase.instance.client.from('schedules').insert(data);
        }

        if (mounted) {
          Navigator.pop(context, true);
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(
              content: Text(
                widget.initialSchedule != null
                    ? 'Schedule updated successfully'
                    : 'Schedule created successfully',
              ),
            ),
          );
        }
      } catch (e) {
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(content: Text('Error saving schedule: $e')),
          );
        }
      } finally {
        if (mounted) {
          setState(() => _isLoading = false);
        }
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text(widget.initialSchedule != null ? 'Edit Schedule' : 'Add Schedule'),
        backgroundColor: Theme.of(context).colorScheme.primaryContainer,
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16.0),
        child: FormBuilder(
          key: _formKey,
          initialValue: widget.initialSchedule != null
              ? {
                  'day': widget.initialSchedule!['day'],
                  'period': widget.initialSchedule!['period'].toString(),
                  'start_time': widget.initialSchedule!['start_time'],
                  'end_time': widget.initialSchedule!['end_time'],
                  'subject': widget.initialSchedule!['subject'],
                  'room': widget.initialSchedule!['room'],
                }
              : {},
          child: Column(
            children: [
              FormBuilderDropdown<String>(
                name: 'day',
                decoration: const InputDecoration(
                  labelText: 'Day',
                  border: OutlineInputBorder(),
                ),
                validator: FormBuilderValidators.required(),
                items: _days
                    .map((day) => DropdownMenuItem(
                          value: day,
                          child: Text(day),
                        ))
                    .toList(),
              ),
              const SizedBox(height: 16),
              FormBuilderTextField(
                name: 'period',
                decoration: const InputDecoration(
                  labelText: 'Period',
                  border: OutlineInputBorder(),
                ),
                validator: FormBuilderValidators.compose([
                  FormBuilderValidators.required(),
                  FormBuilderValidators.numeric(),
                  FormBuilderValidators.min(1),
                  FormBuilderValidators.max(10),
                ]),
                keyboardType: TextInputType.number,
              ),
              const SizedBox(height: 16),
              FormBuilderTextField(
                name: 'start_time',
                decoration: const InputDecoration(
                  labelText: 'Start Time (HH:MM)',
                  border: OutlineInputBorder(),
                ),
                validator: FormBuilderValidators.required(),
              ),
              const SizedBox(height: 16),
              FormBuilderTextField(
                name: 'end_time',
                decoration: const InputDecoration(
                  labelText: 'End Time (HH:MM)',
                  border: OutlineInputBorder(),
                ),
                validator: FormBuilderValidators.required(),
              ),
              const SizedBox(height: 16),
              FormBuilderTextField(
                name: 'subject',
                decoration: const InputDecoration(
                  labelText: 'Subject',
                  border: OutlineInputBorder(),
                ),
                validator: FormBuilderValidators.required(),
              ),
              const SizedBox(height: 16),
              FormBuilderTextField(
                name: 'room',
                decoration: const InputDecoration(
                  labelText: 'Room',
                  border: OutlineInputBorder(),
                ),
              ),
              const SizedBox(height: 24),
              SizedBox(
                width: double.infinity,
                child: ElevatedButton(
                  onPressed: _isLoading ? null : _saveSchedule,
                  child: _isLoading
                      ? const SizedBox(
                          height: 20,
                          width: 20,
                          child: CircularProgressIndicator(strokeWidth: 2),
                        )
                      : Text(
                          widget.initialSchedule != null ? 'Update Schedule' : 'Add Schedule',
                        ),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
} 