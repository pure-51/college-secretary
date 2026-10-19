import 'package:flutter/material.dart';
import 'package:intl/intl.dart';

class EventDetailPage extends StatelessWidget {
  final Map<String, dynamic> event;

  const EventDetailPage({super.key, required this.event});

  @override
  Widget build(BuildContext context) {
    final isExam = event['type'] == 'exam';
    final timeStr = event['time'] as String?;
    final dt = timeStr != null ? DateTime.tryParse(timeStr) : null;

    return Scaffold(
      appBar: AppBar(title: Text(isExam ? '考试详情' : '待办详情')),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // 类型图标 + 标题
            Row(
              children: [
                CircleAvatar(
                  radius: 28,
                  backgroundColor:
                      isExam ? Colors.red[50] : Colors.blue[50],
                  child: Icon(
                    isExam ? Icons.school : Icons.task_alt,
                    color: isExam ? Colors.red : Colors.blue,
                    size: 32,
                  ),
                ),
                const SizedBox(width: 16),
                Expanded(
                  child: Text(
                    event['content'] ?? '',
                    style: const TextStyle(
                        fontSize: 20, fontWeight: FontWeight.bold),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 24),

            // 信息卡片
            Card(
              child: Padding(
                padding: const EdgeInsets.all(16),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    if (dt != null) ...[
                      _infoRow(Icons.calendar_today, '日期',
                          DateFormat('yyyy年M月d日').format(dt)),
                      const Divider(height: 16),
                      _infoRow(Icons.access_time, '时间',
                          DateFormat('HH:mm').format(dt)),
                      const Divider(height: 16),
                    ],
                    if (event['location'] != null) ...[
                      _infoRow(Icons.location_on, '地点', event['location']),
                      const Divider(height: 16),
                    ],
                    if (isExam && event['seat'] != null) ...[
                      _infoRow(Icons.confirmation_number, '座位号', event['seat']),
                      const Divider(height: 16),
                    ],
                    _infoRow(
                      Icons.label_outline,
                      '类型',
                      isExam ? '考试' : '待办事项',
                    ),
                    if (!isExam) ...[
                      const Divider(height: 16),
                      _infoRow(
                        Icons.check_circle_outline,
                        '状态',
                        event['status'] == 'completed' ? '已完成' : '待处理',
                      ),
                    ],
                  ],
                ),
              ),
            ),
            const SizedBox(height: 16),
          ],
        ),
      ),
    );
  }

  Widget _infoRow(IconData icon, String label, String value) {
    return Row(
      children: [
        Icon(icon, size: 20, color: Colors.grey[600]),
        const SizedBox(width: 12),
        SizedBox(
          width: 60,
          child: Text(label,
              style: TextStyle(color: Colors.grey[600], fontSize: 14)),
        ),
        Expanded(
          child: Text(value,
              style: const TextStyle(fontSize: 15, fontWeight: FontWeight.w500)),
        ),
      ],
    );
  }
}
