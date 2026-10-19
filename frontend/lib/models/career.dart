/// 生涯档案域模型（对应后端 schemas/career.py 契约）
class ArchiveRecord {
  final int id;
  final String recordType;
  final String title;
  final Map<String, dynamic> fields;
  final String? summary;
  final String sensitivity;
  final String recordStatus;
  final double evidenceConfidence;

  ArchiveRecord({
    required this.id,
    required this.recordType,
    required this.title,
    this.fields = const {},
    this.summary,
    this.sensitivity = 'internal',
    this.recordStatus = 'pending',
    this.evidenceConfidence = 0.0,
  });

  factory ArchiveRecord.fromJson(Map<String, dynamic> json) {
    return ArchiveRecord(
      id: json['id'] as int? ?? 0,
      recordType: json['record_type'] as String? ?? 'activity',
      title: json['title'] as String? ?? '',
      fields: (json['fields'] as Map<String, dynamic>?) ?? {},
      summary: json['summary'] as String?,
      sensitivity: json['sensitivity'] as String? ?? 'internal',
      recordStatus: json['record_status'] as String? ?? 'pending',
      evidenceConfidence: (json['evidence_confidence'] as num?)?.toDouble() ?? 0.0,
    );
  }

  String get typeLabel {
    const labels = {
      'honor': '荣誉奖项',
      'score': '成绩绩点',
      'internship': '实习经历',
      'activity': '技能活动',
      'skill': '技能证书',
      'paper_meta': '科研成果',
      'ledger': '班费记录',
      'signup_row': '接龙记录',
      'certificate': '证书证明',
    };
    return labels[recordType] ?? recordType;
  }
}

class ResumeLine {
  final String text;
  final bool missing;
  final Map<String, dynamic>? evidence;

  ResumeLine({required this.text, this.missing = false, this.evidence});

  factory ResumeLine.fromJson(Map<String, dynamic> json) {
    return ResumeLine(
      text: json['text'] as String? ?? '',
      missing: json['missing'] as bool? ?? false,
      evidence: json['evidence'] as Map<String, dynamic>?,
    );
  }
}

class ResumeSection {
  final String title;
  final List<ResumeLine> lines;

  ResumeSection({required this.title, this.lines = const []});

  factory ResumeSection.fromJson(Map<String, dynamic> json) {
    return ResumeSection(
      title: json['title'] as String? ?? '',
      lines: ((json['lines'] as List<dynamic>?) ?? [])
          .map((e) => ResumeLine.fromJson(e as Map<String, dynamic>))
          .toList(),
    );
  }
}

class InterviewQuestion {
  final String question;
  final String focus;
  final int? relatedRecordId;

  InterviewQuestion({required this.question, required this.focus, this.relatedRecordId});

  factory InterviewQuestion.fromJson(Map<String, dynamic> json) {
    return InterviewQuestion(
      question: json['question'] as String? ?? '',
      focus: json['focus'] as String? ?? '',
      relatedRecordId: json['related_record_id'] as int?,
    );
  }
}

class InterviewFeedback {
  final Map<String, double> score;
  final String feedback;
  final String advice;

  InterviewFeedback({this.score = const {}, this.feedback = '', this.advice = ''});

  factory InterviewFeedback.fromJson(Map<String, dynamic> json) {
    final s = (json['score'] as Map<String, dynamic>?) ?? {};
    return InterviewFeedback(
      score: s.map((k, v) => MapEntry(k, (v as num?)?.toDouble() ?? 0.0)),
      feedback: json['feedback'] as String? ?? '',
      advice: json['advice'] as String? ?? '',
    );
  }
}

class HealthDimension {
  final String field;
  final bool required;
  final bool filled;
  final bool evidence;

  HealthDimension({required this.field, this.required = false, this.filled = false, this.evidence = false});

  factory HealthDimension.fromJson(Map<String, dynamic> json) {
    return HealthDimension(
      field: json['field'] as String? ?? '',
      required: json['required'] as bool? ?? false,
      filled: json['filled'] as bool? ?? false,
      evidence: json['evidence'] as bool? ?? false,
    );
  }
}

class Milestone {
  final int id;
  final String label;
  final String content;
  final String? deadline;
  final String status;

  Milestone({required this.id, required this.label, required this.content, this.deadline, this.status = 'pending'});

  factory Milestone.fromJson(Map<String, dynamic> json) {
    return Milestone(
      id: json['id'] as int? ?? 0,
      label: json['label'] as String? ?? '',
      content: json['content'] as String? ?? '',
      deadline: json['deadline'] as String?,
      status: json['status'] as String? ?? 'pending',
    );
  }
}
