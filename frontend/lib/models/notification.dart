class Notification {
  final int id;
  final String sourceType;
  final String rawContent;
  final String? category;
  final String relevance;
  final String status;
  final DateTime? createdAt;
  final List<TodoItem> todos;
  final List<ExamItem> exams;

  Notification({
    required this.id,
    required this.sourceType,
    required this.rawContent,
    this.category,
    this.relevance = 'pending',
    this.status = 'pending',
    this.createdAt,
    this.todos = const [],
    this.exams = const [],
  });

  factory Notification.fromJson(Map<String, dynamic> json) {
    return Notification(
      id: json['id'] as int,
      sourceType: json['source_type'] as String? ?? 'text',
      rawContent: json['raw_content'] as String? ?? '',
      category: json['category'] as String?,
      relevance: json['relevance'] as String? ?? 'pending',
      status: json['status'] as String? ?? 'pending',
      createdAt: json['created_at'] != null
          ? DateTime.tryParse(json['created_at'] as String)
          : null,
      todos: (json['todos'] as List<dynamic>?)
              ?.map((e) => TodoItem.fromJson(e as Map<String, dynamic>))
              .toList() ??
          [],
      exams: (json['exams'] as List<dynamic>?)
              ?.map((e) => ExamItem.fromJson(e as Map<String, dynamic>))
              .toList() ??
          [],
    );
  }
}

class TodoItem {
  final int? id;
  final String content;
  final String? deadline;
  final String? location;

  TodoItem({this.id, required this.content, this.deadline, this.location});

  factory TodoItem.fromJson(Map<String, dynamic> json) {
    return TodoItem(
      id: json['id'] as int?,
      content: json['content'] as String? ?? '',
      deadline: json['deadline'] as String?,
      location: json['location'] as String?,
    );
  }
}

class ExamItem {
  final int? id;
  final String subject;
  final String? examTime;
  final String? location;
  final String? seatNumber;

  ExamItem({this.id, required this.subject, this.examTime, this.location, this.seatNumber});

  factory ExamItem.fromJson(Map<String, dynamic> json) {
    return ExamItem(
      id: json['id'] as int?,
      subject: json['subject'] as String? ?? '',
      examTime: json['exam_time'] as String?,
      location: json['location'] as String?,
      seatNumber: json['seat_number'] as String?,
    );
  }
}
