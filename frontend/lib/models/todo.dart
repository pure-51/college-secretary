class Todo {
  final int id;
  final String content;
  final String? deadline;
  final String? location;
  final String status;
  final String? source;
  final DateTime? createdAt;

  Todo({
    required this.id,
    required this.content,
    this.deadline,
    this.location,
    this.status = 'pending',
    this.source,
    this.createdAt,
  });

  factory Todo.fromJson(Map<String, dynamic> json) {
    return Todo(
      id: json['id'] as int,
      content: json['content'] as String? ?? '',
      deadline: json['deadline'] as String?,
      location: json['location'] as String?,
      status: json['status'] as String? ?? 'pending',
      source: json['source'] as String?,
      createdAt: json['created_at'] != null
          ? DateTime.tryParse(json['created_at'] as String)
          : null,
    );
  }

  bool get isOverdue {
    if (deadline == null) return false;
    final dt = DateTime.tryParse(deadline!);
    if (dt == null) return false;
    return dt.isBefore(DateTime.now()) && status == 'pending';
  }

  bool get isCompleted => status == 'completed';
  bool get isPending => status == 'pending';
}
