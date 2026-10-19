import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:table_calendar/table_calendar.dart';
import 'package:intl/intl.dart';
import '../../config/theme.dart';
import '../../providers/schedule_provider.dart';
import '../../widgets/empty_state.dart';
import '../../widgets/loading_indicator.dart';
import 'event_detail_page.dart';

class SchedulePage extends StatefulWidget {
  const SchedulePage({super.key});

  @override
  State<SchedulePage> createState() => _SchedulePageState();
}

class _SchedulePageState extends State<SchedulePage> {
  DateTime _selectedDay = DateTime.now();
  DateTime _focusedDay = DateTime.now();

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      context.read<ScheduleProvider>().loadEvents();
    });
  }

  List<dynamic> _eventsForDay(List<dynamic> events, DateTime day) {
    return events.where((e) {
      final time = e['time'] as String?;
      if (time == null) return false;
      try {
        final dt = DateTime.parse(time);
        return dt.year == day.year && dt.month == day.month && dt.day == day.day;
      } catch (_) {
        return false;
      }
    }).toList();
  }

  List<dynamic> _eventsWithoutDate(List<dynamic> events) {
    return events.where((e) {
      final time = e['time'] as String?;
      return time == null;
    }).toList();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('日程')),
      body: Consumer<ScheduleProvider>(
        builder: (context, provider, _) {
          if (provider.isLoading) {
            return const SkeletonLoader(itemCount: 3);
          }

          final dayEvents = _eventsForDay(provider.events, _selectedDay);
          final noDateEvents = _eventsWithoutDate(provider.events);
          final hasEvents = dayEvents.isNotEmpty || noDateEvents.isNotEmpty;

          return Column(
            children: [
              // ── 日历 ──
              _CalendarHeader(focusedDay: _focusedDay),
              TableCalendar(
                firstDay: DateTime(2024),
                lastDay: DateTime(2028),
                focusedDay: _focusedDay,
                selectedDayPredicate: (day) => isSameDay(_selectedDay, day),
                onDaySelected: (selectedDay, focusedDay) {
                  setState(() {
                    _selectedDay = selectedDay;
                    _focusedDay = focusedDay;
                  });
                },
                headerVisible: false,
                calendarStyle: CalendarStyle(
                  selectedDecoration: const BoxDecoration(
                    color: AppTheme.primaryColor,
                    shape: BoxShape.circle,
                  ),
                  todayDecoration: BoxDecoration(
                    color: AppTheme.primaryColor.withAlpha(30),
                    shape: BoxShape.circle,
                  ),
                  todayTextStyle: const TextStyle(
                    color: AppTheme.primaryColor,
                    fontWeight: FontWeight.w600,
                  ),
                  selectedTextStyle: const TextStyle(
                    color: Colors.white,
                    fontWeight: FontWeight.w600,
                  ),
                  defaultTextStyle: const TextStyle(
                    color: AppTheme.textPrimary,
                  ),
                  weekendTextStyle: const TextStyle(
                    color: AppTheme.textSecondary,
                  ),
                  outsideTextStyle: TextStyle(
                    color: AppTheme.textTertiary.withAlpha(100),
                  ),
                  cellMargin: const EdgeInsets.all(4),
                ),
                daysOfWeekStyle: const DaysOfWeekStyle(
                  weekdayStyle: TextStyle(
                    color: AppTheme.textSecondary,
                    fontSize: 12,
                    fontWeight: FontWeight.w500,
                  ),
                  weekendStyle: TextStyle(
                    color: AppTheme.textSecondary,
                    fontSize: 12,
                    fontWeight: FontWeight.w500,
                  ),
                ),
                locale: 'zh_CN',
              ),
              const Divider(height: 1),

              // ── 日期标题 ──
              Container(
                width: double.infinity,
                padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
                color: AppTheme.surfaceColor,
                child: Row(
                  children: [
                    Text(
                      DateFormat('M月d日 EEEE', 'zh_CN').format(_selectedDay),
                      style: const TextStyle(
                        fontWeight: FontWeight.w600,
                        fontSize: 14,
                        color: AppTheme.textPrimary,
                      ),
                    ),
                    const Spacer(),
                    Text(
                      '${dayEvents.length + noDateEvents.length} 项',
                      style: const TextStyle(
                        fontSize: 13,
                        color: AppTheme.textTertiary,
                      ),
                    ),
                  ],
                ),
              ),

              // ── 事件列表 ──
              Expanded(
                child: !hasEvents
                    ? const EmptyState(
                        icon: Icons.event_available_outlined,
                        message: '今天没有安排',
                      )
                    : ListView(
                        padding: const EdgeInsets.fromLTRB(16, 8, 16, 16),
                        children: [
                          if (dayEvents.isNotEmpty) ...[
                            const Text('当日安排',
                                style: TextStyle(
                                  fontSize: 13,
                                  fontWeight: FontWeight.w600,
                                  color: AppTheme.textSecondary,
                                )),
                            const SizedBox(height: 8),
                            ...dayEvents.map((e) => _buildEventCard(e)),
                          ],
                          if (dayEvents.isNotEmpty && noDateEvents.isNotEmpty)
                            const SizedBox(height: 12),
                          if (noDateEvents.isNotEmpty) ...[
                            const Text('其他待办',
                                style: TextStyle(
                                  fontSize: 13,
                                  fontWeight: FontWeight.w600,
                                  color: AppTheme.textSecondary,
                                )),
                            const SizedBox(height: 8),
                            ...noDateEvents.map((e) => _buildEventCard(e)),
                          ],
                        ],
                      ),
              ),
            ],
          );
        },
      ),
    );
  }

  Widget _buildEventCard(dynamic event) {
    final isExam = event['type'] == 'exam';
    final timeStr = event['time'] as String? ?? '';
    final displayTime = timeStr.length >= 16 ? timeStr.substring(11, 16) : '';
    final color = isExam ? AppTheme.examColor : AppTheme.todoColor;
    final bgColor = isExam
        ? AppTheme.examColor.withAlpha(15)
        : AppTheme.todoColor.withAlpha(15);

    return GestureDetector(
      onTap: () => Navigator.push(
        context,
        MaterialPageRoute(
          builder: (_) => EventDetailPage(event: event),
        ),
      ),
      child: Container(
        margin: const EdgeInsets.only(bottom: 8),
        padding: const EdgeInsets.all(14),
        decoration: BoxDecoration(
          color: bgColor,
          borderRadius: BorderRadius.circular(12),
        ),
        child: Row(
          children: [
            // 左侧色条
            Container(
              width: 3,
              height: 40,
              decoration: BoxDecoration(
                color: color,
                borderRadius: BorderRadius.circular(2),
              ),
            ),
            const SizedBox(width: 12),
            // 内容
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    event['content'] ?? '',
                    style: const TextStyle(
                      fontWeight: FontWeight.w500,
                      fontSize: 14,
                      color: AppTheme.textPrimary,
                    ),
                  ),
                  const SizedBox(height: 4),
                  Row(
                    children: [
                      if (displayTime.isNotEmpty) ...[
                        Icon(Icons.access_time_rounded,
                            size: 13, color: AppTheme.textTertiary),
                        const SizedBox(width: 4),
                        Text(displayTime,
                            style: const TextStyle(
                                fontSize: 12, color: AppTheme.textTertiary)),
                        const SizedBox(width: 12),
                      ],
                      if (event['location'] != null) ...[
                        Icon(Icons.location_on_rounded,
                            size: 13, color: AppTheme.textTertiary),
                        const SizedBox(width: 4),
                        Text(event['location'],
                            style: const TextStyle(
                                fontSize: 12, color: AppTheme.textTertiary)),
                      ],
                    ],
                  ),
                ],
              ),
            ),
            if (isExam && event['seat'] != null)
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                decoration: BoxDecoration(
                  color: Colors.white,
                  borderRadius: BorderRadius.circular(6),
                  border: Border.all(color: AppTheme.borderColor, width: 0.5),
                ),
                child: Text(
                  '座位 ${event['seat']}',
                  style: const TextStyle(fontSize: 11, color: AppTheme.textSecondary),
                ),
              ),
          ],
        ),
      ),
    );
  }
}

class _CalendarHeader extends StatelessWidget {
  final DateTime focusedDay;

  const _CalendarHeader({required this.focusedDay});

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.fromLTRB(16, 8, 8, 4),
      child: Row(
        children: [
          Text(
            DateFormat('yyyy年 M月', 'zh_CN').format(focusedDay),
            style: const TextStyle(
              fontSize: 16,
              fontWeight: FontWeight.w600,
              color: AppTheme.textPrimary,
            ),
          ),
        ],
      ),
    );
  }
}
