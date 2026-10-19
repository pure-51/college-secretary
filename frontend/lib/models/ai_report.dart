class AiReport {
  final String report;
  final ReportStats stats;
  final String? generatedAt;

  AiReport({
    required this.report,
    required this.stats,
    this.generatedAt,
  });

  factory AiReport.fromJson(Map<String, dynamic> json) {
    return AiReport(
      report: json['report'] as String? ?? '',
      stats: ReportStats.fromJson(json['stats'] as Map<String, dynamic>? ?? {}),
      generatedAt: json['generated_at'] as String?,
    );
  }
}

class ReportStats {
  final int pendingTodos;
  final int upcomingExams;
  final int pendingNotifications;
  final int weeklyProcessed;
  final int weeklyCompleted;

  ReportStats({
    this.pendingTodos = 0,
    this.upcomingExams = 0,
    this.pendingNotifications = 0,
    this.weeklyProcessed = 0,
    this.weeklyCompleted = 0,
  });

  factory ReportStats.fromJson(Map<String, dynamic> json) {
    return ReportStats(
      pendingTodos: json['pending_todos'] as int? ?? 0,
      upcomingExams: json['upcoming_exams'] as int? ?? 0,
      pendingNotifications: json['pending_notifications'] as int? ?? 0,
      weeklyProcessed: json['weekly_processed'] as int? ?? 0,
      weeklyCompleted: json['weekly_completed'] as int? ?? 0,
    );
  }
}
