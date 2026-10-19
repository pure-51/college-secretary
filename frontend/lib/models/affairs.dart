/// 班务助理域模型（对应后端 schemas/affairs.py 契约）
class SignupInfo {
  final int id;
  final String title;
  final List<String> options;
  final String status;

  SignupInfo({required this.id, required this.title, this.options = const [], this.status = 'open'});

  factory SignupInfo.fromJson(Map<String, dynamic> json) {
    return SignupInfo(
      id: json['id'] as int? ?? 0,
      title: json['title'] as String? ?? '',
      options: ((json['options'] as List<dynamic>?) ?? []).map((e) => e.toString()).toList(),
      status: json['status'] as String? ?? 'open',
    );
  }
}

class SignupEntry {
  final int id;
  final String name;
  final String? detail;
  final String? option;
  final String source;
  final bool isDuplicate;

  SignupEntry({
    required this.id,
    required this.name,
    this.detail,
    this.option,
    this.source = 'text',
    this.isDuplicate = false,
  });

  factory SignupEntry.fromJson(Map<String, dynamic> json) {
    return SignupEntry(
      id: json['id'] as int? ?? 0,
      name: json['name'] as String? ?? '',
      detail: json['detail'] as String?,
      option: json['option'] as String?,
      source: json['source'] as String? ?? 'text',
      isDuplicate: json['is_duplicate'] as bool? ?? false,
    );
  }
}

class SignupStats {
  final int total;
  final int unique;
  final Map<String, int> perOption;

  SignupStats({this.total = 0, this.unique = 0, this.perOption = const {}});

  factory SignupStats.fromJson(Map<String, dynamic> json) {
    return SignupStats(
      total: json['total'] as int? ?? 0,
      unique: json['unique'] as int? ?? 0,
      perOption: ((json['per_option'] as Map<String, dynamic>?) ?? {})
          .map((k, v) => MapEntry(k, (v as num?)?.toInt() ?? 0)),
    );
  }
}
