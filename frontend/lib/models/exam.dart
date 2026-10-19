class Exam {
  final int id;
  final String subject;
  final String? examTime;
  final String? location;
  final String? seatNumber;
  final String? notes;

  Exam({
    required this.id,
    required this.subject,
    this.examTime,
    this.location,
    this.seatNumber,
    this.notes,
  });

  factory Exam.fromJson(Map<String, dynamic> json) {
    return Exam(
      id: json['id'] as int,
      subject: json['subject'] as String? ?? '',
      examTime: json['exam_time'] as String?,
      location: json['location'] as String?,
      seatNumber: json['seat_number'] as String?,
      notes: json['notes'] as String?,
    );
  }

  DateTime? get parsedTime =>
      examTime != null ? DateTime.tryParse(examTime!) : null;

  bool get isUpcoming {
    final dt = parsedTime;
    if (dt == null) return false;
    return dt.isAfter(DateTime.now());
  }
}
