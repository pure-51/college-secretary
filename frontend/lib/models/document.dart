class Document {
  final int id;
  final String title;
  final String fileType;
  final int version;
  final String? summary;
  final int? fileSize;
  final int? pageCount;
  final String? fullText;
  final DateTime? createdAt;

  Document({
    required this.id,
    required this.title,
    required this.fileType,
    this.version = 1,
    this.summary,
    this.fileSize,
    this.pageCount,
    this.fullText,
    this.createdAt,
  });

  factory Document.fromJson(Map<String, dynamic> json) {
    return Document(
      id: json['id'] as int,
      title: json['title'] as String? ?? '',
      fileType: json['file_type'] as String? ?? '',
      version: json['version'] as int? ?? 1,
      summary: json['summary'] as String?,
      fileSize: json['file_size'] as int?,
      pageCount: json['page_count'] as int?,
      fullText: json['full_text'] as String?,
      createdAt: json['created_at'] != null
          ? DateTime.tryParse(json['created_at'] as String)
          : null,
    );
  }

  String get sizeLabel {
    if (fileSize == null) return '';
    if (fileSize! < 1024) return '$fileSize B';
    if (fileSize! < 1024 * 1024) return '${(fileSize! / 1024).toStringAsFixed(1)} KB';
    return '${(fileSize! / (1024 * 1024)).toStringAsFixed(1)} MB';
  }
}

class SearchResult {
  final int documentId;
  final String title;
  final String content;
  final int? page;

  SearchResult({
    required this.documentId,
    required this.title,
    required this.content,
    this.page,
  });

  factory SearchResult.fromJson(Map<String, dynamic> json) {
    return SearchResult(
      documentId: json['document_id'] as int,
      title: json['title'] as String? ?? '',
      content: json['content'] as String? ?? '',
      page: json['page'] as int?,
    );
  }
}
