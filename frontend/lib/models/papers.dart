/// 科研论文库域模型（对应后端 schemas/papers.py 契约）
class PaperMeta {
  final int metaId;
  final int documentId;
  final String title;
  final String? authors;
  final String? journal;
  final int? year;
  final String? doi;
  final String? language;
  final String metaStatus;

  PaperMeta({
    required this.metaId,
    required this.documentId,
    required this.title,
    this.authors,
    this.journal,
    this.year,
    this.doi,
    this.language,
    this.metaStatus = 'auto',
  });

  factory PaperMeta.fromJson(Map<String, dynamic> json) {
    return PaperMeta(
      metaId: json['meta_id'] as int? ?? 0,
      documentId: json['document_id'] as int? ?? 0,
      title: json['title'] as String? ?? '',
      authors: json['authors'] as String?,
      journal: json['journal'] as String?,
      year: json['year'] as int?,
      doi: json['doi'] as String?,
      language: json['language'] as String?,
      metaStatus: json['meta_status'] as String? ?? 'auto',
    );
  }
}

class ExplainPart {
  final String title;
  final String content;
  final int? sourceChunkId;

  ExplainPart({required this.title, required this.content, this.sourceChunkId});

  factory ExplainPart.fromJson(Map<String, dynamic> json) {
    return ExplainPart(
      title: json['title'] as String? ?? '',
      content: json['content'] as String? ?? '',
      sourceChunkId: json['source_chunk_id'] as int?,
    );
  }
}

class Citation {
  final int chunkId;
  final double confidence;

  Citation({required this.chunkId, required this.confidence});

  factory Citation.fromJson(Map<String, dynamic> json) {
    return Citation(
      chunkId: json['chunk_id'] as int? ?? 0,
      confidence: (json['confidence'] as num?)?.toDouble() ?? 0.0,
    );
  }
}

class CompareTable {
  final List<String> columns;
  final List<List<String>> rows;

  const CompareTable({this.columns = const [], this.rows = const []});

  factory CompareTable.fromJson(Map<String, dynamic> json) {
    return CompareTable(
      columns: ((json['columns'] as List<dynamic>?) ?? []).map((e) => e.toString()).toList(),
      rows: ((json['rows'] as List<dynamic>?) ?? [])
          .map((row) => ((row as List<dynamic>?) ?? []).map((e) => e.toString()).toList())
          .toList(),
    );
  }
}

class ReviewSection {
  final String title;
  final String content;

  ReviewSection({required this.title, required this.content});

  factory ReviewSection.fromJson(Map<String, dynamic> json) {
    return ReviewSection(
      title: json['title'] as String? ?? '',
      content: json['content'] as String? ?? '',
    );
  }
}
