import 'dart:convert';
import 'dart:io';
import 'dart:typed_data';
import 'package:http/http.dart' as http;
import '../config/api_config.dart';

class ApiService {
  static final ApiService _instance = ApiService._();
  factory ApiService() => _instance;
  ApiService._();

  String? _localToken;

  /// 从 /api/config 读取本地令牌并缓存，后续请求自动携带 X-Local-Token（ADR §6）
  Future<void> loadTokenFromConfig() async {
    final config = await getConfig();
    final token = config['local_token'] as String?;
    if (token != null && token.isNotEmpty) {
      _localToken = token;
    }
  }

  Map<String, String> _headers({bool json = false}) {
    return {
      if (_localToken != null && _localToken!.isNotEmpty) 'X-Local-Token': _localToken!,
      if (json) 'Content-Type': 'application/json',
    };
  }

  void _applyAuth(http.MultipartRequest request) {
    if (_localToken != null && _localToken!.isNotEmpty) {
      request.headers['X-Local-Token'] = _localToken!;
    }
  }

  Future<bool> healthCheck() async {
    try {
      final response = await http.get(Uri.parse(ApiConfig.health), headers: _headers()).timeout(const Duration(seconds: 5));
      return response.statusCode == 200;
    } catch (_) {
      return false;
    }
  }

  Future<Map<String, dynamic>> getConfig() async {
    try {
      final response = await http.get(Uri.parse(ApiConfig.config), headers: _headers()).timeout(const Duration(seconds: 5));
      if (response.statusCode == 200) {
        return json.decode(response.body);
      }
    } catch (_) {}
    return {'llm_model': 'deepseek-v4-flash', 'ocr_enabled': true};
  }

  // --- 收件箱 ---
  Future<List<dynamic>> getMessages({String? status, String? category}) async {
    final params = <String, String>{};
    if (status != null) params['status'] = status;
    if (category != null) params['category'] = category;
    final uri = Uri.parse('${ApiConfig.inbox}/messages').replace(queryParameters: params.isNotEmpty ? params : null);
    final response = await http.get(uri, headers: _headers());
    if (response.statusCode == 200) {
      final data = json.decode(response.body);
      return data['items'] as List<dynamic>;
    }
    return [];
  }

  Future<Map<String, dynamic>> importText(String text) async {
    final response = await http.post(
      Uri.parse('${ApiConfig.inbox}/messages'),
      headers: _headers(json: true),
      body: json.encode({'source_type': 'text', 'raw_content': text}),
    );
    if (response.statusCode != 200) {
      return {'error': '导入失败: ${response.statusCode}'};
    }
    return json.decode(response.body);
  }

  Future<Map<String, dynamic>> importImage(File imageFile) async {
    final request = http.MultipartRequest('POST', Uri.parse('${ApiConfig.inbox}/messages/image'));
    _applyAuth(request);
    request.files.add(await http.MultipartFile.fromPath('file', imageFile.path));
    final streamedResponse = await request.send();
    final response = await http.Response.fromStream(streamedResponse);
    if (response.statusCode != 200) {
      return {'error': '图片导入失败: ${response.statusCode}'};
    }
    return json.decode(response.body);
  }

  Future<Map<String, dynamic>> importImageBytes(Uint8List bytes, String filename) async {
    final request = http.MultipartRequest('POST', Uri.parse('${ApiConfig.inbox}/messages/image'));
    _applyAuth(request);
    request.files.add(http.MultipartFile.fromBytes('file', bytes, filename: filename));
    final streamedResponse = await request.send();
    final response = await http.Response.fromStream(streamedResponse);
    if (response.statusCode != 200) {
      return {'error': '图片导入失败: ${response.statusCode}'};
    }
    return json.decode(response.body);
  }

  Future<Map<String, dynamic>> importLink(String url) async {
    final response = await http.post(
      Uri.parse('${ApiConfig.inbox}/messages'),
      headers: _headers(json: true),
      body: json.encode({'source_type': 'link', 'raw_content': url}),
    );
    if (response.statusCode != 200) {
      return {'error': '链接导入失败: ${response.statusCode}'};
    }
    return json.decode(response.body);
  }

  Future<Map<String, dynamic>> getMessageDetail(int id) async {
    final response = await http.get(Uri.parse('${ApiConfig.inbox}/messages/$id'), headers: _headers());
    if (response.statusCode == 200) {
      return json.decode(response.body);
    }
    return {};
  }

  Future<void> deleteMessage(int id) async {
    await http.delete(Uri.parse('${ApiConfig.inbox}/messages/$id'), headers: _headers());
  }

  Future<void> clearAllMessages() async {
    await http.delete(Uri.parse('${ApiConfig.inbox}/messages'), headers: _headers());
  }

  Future<void> clearAllDocuments() async {
    await http.delete(Uri.parse('${ApiConfig.knowledge}/documents'), headers: _headers());
  }

  Future<void> clearAllSchedule() async {
    await http.delete(Uri.parse('${ApiConfig.schedule}/all'), headers: _headers());
  }

  Future<Map<String, dynamic>> confirmMessage(int id, {String? notes}) async {
    final response = await http.put(
      Uri.parse('${ApiConfig.inbox}/messages/$id/confirm'),
      headers: _headers(json: true),
      body: json.encode({'user_notes': notes ?? ''}),
    );
    return json.decode(response.body);
  }

  Future<Map<String, dynamic>> rejectMessage(int id, {String? notes}) async {
    final response = await http.put(
      Uri.parse('${ApiConfig.inbox}/messages/$id/reject'),
      headers: _headers(json: true),
      body: json.encode({'user_notes': notes ?? ''}),
    );
    return json.decode(response.body);
  }

  Future<Map<String, dynamic>> markIrrelevant(int id) async {
    final response = await http.put(Uri.parse('${ApiConfig.inbox}/messages/$id/irrelevant'), headers: _headers());
    return json.decode(response.body);
  }

  // --- 知识库 ---
  Future<List<dynamic>> getDocuments({String? search, String? fileType}) async {
    final params = <String, String>{};
    if (search != null) params['search'] = search;
    if (fileType != null) params['file_type'] = fileType;
    final uri = Uri.parse('${ApiConfig.knowledge}/documents').replace(queryParameters: params.isNotEmpty ? params : null);
    final response = await http.get(uri, headers: _headers());
    if (response.statusCode == 200) {
      return json.decode(response.body)['items'] as List<dynamic>;
    }
    return [];
  }

  Future<Map<String, dynamic>> uploadDocument(File file) async {
    final request = http.MultipartRequest('POST', Uri.parse('${ApiConfig.knowledge}/documents'));
    _applyAuth(request);
    request.files.add(await http.MultipartFile.fromPath('file', file.path));
    final streamedResponse = await request.send();
    final response = await http.Response.fromStream(streamedResponse);
    return json.decode(response.body);
  }

  Future<Map<String, dynamic>> searchKnowledge(String query) async {
    final response = await http.get(
      Uri.parse('${ApiConfig.knowledge}/search?q=$query'),
      headers: _headers(),
    );
    if (response.statusCode == 200) {
      return json.decode(response.body);
    }
    return {'results': [], 'total': 0};
  }

  // --- 日程 ---
  Future<List<dynamic>> getEvents({String? date, bool upcoming = false}) async {
    final params = <String, String>{};
    if (date != null) params['date'] = date;
    if (upcoming) params['upcoming'] = 'true';
    final uri = Uri.parse('${ApiConfig.schedule}/events').replace(queryParameters: params.isNotEmpty ? params : null);
    final response = await http.get(uri, headers: _headers());
    if (response.statusCode == 200) {
      return json.decode(response.body)['items'] as List<dynamic>;
    }
    return [];
  }

  // --- AI ---
  Future<Map<String, dynamic>> getAiReport() async {
    final response = await http.post(Uri.parse(ApiConfig.aiReport), headers: _headers());
    if (response.statusCode == 200) {
      return json.decode(response.body);
    }
    return {'report': '获取汇报失败', 'stats': {}};
  }

  Future<Map<String, dynamic>> reportChat(List<Map<String, String>> messages) async {
    final response = await http.post(
      Uri.parse(ApiConfig.aiReportChat),
      headers: _headers(json: true),
      body: json.encode({'messages': messages}),
    );
    if (response.statusCode == 200) {
      return json.decode(response.body);
    }
    return {'reply': '处理失败', 'actions_taken': 0, 'remaining_todos': 0};
  }

  Future<Map<String, dynamic>> askAi(String question) async {
    final response = await http.post(
      Uri.parse(ApiConfig.aiConsult),
      headers: _headers(json: true),
      body: json.encode({'question': question}),
    );
    if (response.statusCode == 200) {
      return json.decode(response.body);
    }
    return {'answer': '抱歉，暂时无法回答', 'sources': []};
  }

  // ───────────────── 生涯档案官（career） ─────────────────
  Future<List<dynamic>> getArchiveRecords({String? recordType, String? status, String? search}) async {
    final params = <String, String>{};
    if (recordType != null) params['record_type'] = recordType;
    if (status != null) params['status'] = status;
    if (search != null) params['search'] = search;
    final uri = Uri.parse('${ApiConfig.career}/archive-records').replace(queryParameters: params.isNotEmpty ? params : null);
    final response = await http.get(uri, headers: _headers());
    if (response.statusCode == 200) {
      return json.decode(response.body)['items'] as List<dynamic>;
    }
    return [];
  }

  Future<Map<String, dynamic>> getArchiveRecord(int id) async {
    final response = await http.get(Uri.parse('${ApiConfig.career}/archive-records/$id'), headers: _headers());
    if (response.statusCode == 200) {
      return json.decode(response.body);
    }
    return {};
  }

  Future<Map<String, dynamic>> createArchiveRecord(String rawText, {String? recordTypeHint}) async {
    final response = await http.post(
      Uri.parse('${ApiConfig.career}/archive-records'),
      headers: _headers(json: true),
      body: json.encode({
        'raw_text': rawText,
        if (recordTypeHint != null) 'record_type_hint': recordTypeHint,
      }),
    );
    return json.decode(response.body);
  }

  Future<Map<String, dynamic>> updateArchiveRecord(int id, Map<String, dynamic> payload) async {
    final response = await http.put(
      Uri.parse('${ApiConfig.career}/archive-records/$id'),
      headers: _headers(json: true),
      body: json.encode(payload),
    );
    return json.decode(response.body);
  }

  Future<void> deleteArchiveRecord(int id) async {
    await http.delete(Uri.parse('${ApiConfig.career}/archive-records/$id'), headers: _headers());
  }

  Future<Map<String, dynamic>> careerHealthCheck() async {
    final response = await http.get(Uri.parse('${ApiConfig.career}/health-check'), headers: _headers());
    if (response.statusCode == 200) {
      return json.decode(response.body);
    }
    return {'progress': 0, 'dimensions': [], 'gaps': []};
  }

  Future<Map<String, dynamic>> generateResume({String direction = '保研-计算机', List<int>? archiveRecordIds, String template = ''}) async {
    final response = await http.post(
      Uri.parse('${ApiConfig.career}/resume/generate'),
      headers: _headers(json: true),
      body: json.encode({
        'direction': direction,
        if (archiveRecordIds != null) 'archive_record_ids': archiveRecordIds,
        'template': template,
      }),
    );
    return json.decode(response.body);
  }

  Future<List<dynamic>> listResumes() async {
    final response = await http.get(Uri.parse('${ApiConfig.career}/resume'), headers: _headers());
    if (response.statusCode == 200) {
      return json.decode(response.body)['items'] as List<dynamic>;
    }
    return [];
  }

  Future<Map<String, dynamic>> resumeNewVersion(int artifactId, {String? direction, String template = ''}) async {
    final response = await http.post(
      Uri.parse('${ApiConfig.career}/resume/$artifactId/versions'),
      headers: _headers(json: true),
      body: json.encode({'direction': direction ?? '', 'template': template}),
    );
    return json.decode(response.body);
  }

  Future<Map<String, dynamic>> interviewQuestions({String direction = '保研-计算机'}) async {
    final response = await http.post(
      Uri.parse('${ApiConfig.career}/interview/questions'),
      headers: _headers(json: true),
      body: json.encode({'direction': direction}),
    );
    return json.decode(response.body);
  }

  Future<Map<String, dynamic>> interviewFeedback(String direction, List<Map<String, dynamic>> qaPairs) async {
    final response = await http.post(
      Uri.parse('${ApiConfig.career}/interview/feedback'),
      headers: _headers(json: true),
      body: json.encode({'direction': direction, 'qa_pairs': qaPairs}),
    );
    return json.decode(response.body);
  }

  Future<Map<String, dynamic>> exportArtifact(int artifactId) async {
    final response = await http.post(Uri.parse('${ApiConfig.career}/artifacts/$artifactId/export'), headers: _headers());
    if (response.statusCode == 200) {
      return json.decode(response.body);
    }
    return {'error': '导出失败: ${response.statusCode}'};
  }

  Future<List<dynamic>> careerMilestones() async {
    final response = await http.get(Uri.parse('${ApiConfig.career}/milestones'), headers: _headers());
    if (response.statusCode == 200) {
      return json.decode(response.body)['items'] as List<dynamic>;
    }
    return [];
  }

  // ───────────────── 科研论文库（papers） ─────────────────
  Future<List<dynamic>> listPapers({String? search}) async {
    final uri = Uri.parse(ApiConfig.papers).replace(queryParameters: search != null ? {'search': search} : null);
    final response = await http.get(uri, headers: _headers());
    if (response.statusCode == 200) {
      return json.decode(response.body)['items'] as List<dynamic>;
    }
    return [];
  }

  Future<Map<String, dynamic>> uploadPaper(Uint8List bytes, String filename, {String? title}) async {
    final request = http.MultipartRequest('POST', Uri.parse('${ApiConfig.papers}/upload'));
    _applyAuth(request);
    request.files.add(http.MultipartFile.fromBytes('file', bytes, filename: filename));
    if (title != null && title.isNotEmpty) {
      request.fields['title'] = title;
    }
    final streamedResponse = await request.send();
    final response = await http.Response.fromStream(streamedResponse);
    if (response.statusCode == 200) {
      return json.decode(response.body);
    }
    return {'error': '上传失败: ${response.statusCode}'};
  }

  Future<Map<String, dynamic>> explainPaper(int documentId, {String question = ''}) async {
    final response = await http.post(
      Uri.parse('${ApiConfig.papers}/$documentId/explain'),
      headers: _headers(json: true),
      body: json.encode({'question': question}),
    );
    return json.decode(response.body);
  }

  Future<Map<String, dynamic>> askPaper(int documentId, String question) async {
    final response = await http.post(
      Uri.parse('${ApiConfig.papers}/$documentId/ask'),
      headers: _headers(json: true),
      body: json.encode({'question': question, 'history': []}),
    );
    return json.decode(response.body);
  }

  Future<Map<String, dynamic>> updatePaperMeta(int documentId, Map<String, dynamic> payload) async {
    final response = await http.put(
      Uri.parse('${ApiConfig.papers}/meta/$documentId'),
      headers: _headers(json: true),
      body: json.encode(payload),
    );
    return json.decode(response.body);
  }

  Future<Map<String, dynamic>> comparePapers(List<int> documentIds, {List<String> dimensions = const []}) async {
    final response = await http.post(
      Uri.parse('${ApiConfig.papers}/compare'),
      headers: _headers(json: true),
      body: json.encode({'document_ids': documentIds, 'dimensions': dimensions}),
    );
    return json.decode(response.body);
  }

  Future<Map<String, dynamic>> generateReview(List<int> documentIds, {List<String>? sections}) async {
    final response = await http.post(
      Uri.parse('${ApiConfig.papers}/review/generate'),
      headers: _headers(json: true),
      body: json.encode({
        'document_ids': documentIds,
        if (sections != null) 'sections': sections,
      }),
    );
    return json.decode(response.body);
  }

  Future<Map<String, dynamic>> getReview(int artifactId) async {
    final response = await http.get(Uri.parse('${ApiConfig.papers}/review/$artifactId'), headers: _headers());
    if (response.statusCode == 200) {
      return json.decode(response.body);
    }
    return {'sections': []};
  }

  // ───────────────── 班务助理（affairs） ─────────────────
  Future<Map<String, dynamic>> generateNotice(String scene, List<String> keyPoints, {String tone = ''}) async {
    final response = await http.post(
      Uri.parse('${ApiConfig.affairs}/notices/generate'),
      headers: _headers(json: true),
      body: json.encode({'scene': scene, 'key_points': keyPoints, 'tone': tone}),
    );
    return json.decode(response.body);
  }

  Future<Map<String, dynamic>> createSignup({required String title, String? description, List<String> options = const [], String? deadline}) async {
    final response = await http.post(
      Uri.parse('${ApiConfig.affairs}/signups'),
      headers: _headers(json: true),
      body: json.encode({
        'title': title,
        if (description != null) 'description': description,
        'options': options,
        if (deadline != null) 'deadline': deadline,
      }),
    );
    return json.decode(response.body);
  }

  Future<Map<String, dynamic>> importSignup(int signupId, String rawText) async {
    final response = await http.post(
      Uri.parse('${ApiConfig.affairs}/signups/$signupId/import'),
      headers: _headers(json: true),
      body: json.encode({'raw_text': rawText, 'source': 'text'}),
    );
    return json.decode(response.body);
  }

  Future<Map<String, dynamic>> getSignupStats(int signupId) async {
    final response = await http.get(Uri.parse('${ApiConfig.affairs}/signups/$signupId'), headers: _headers());
    if (response.statusCode == 200) {
      return json.decode(response.body);
    }
    return {'signup': {}, 'entries': [], 'stats': {}};
  }

  Future<Map<String, dynamic>> signupTodo(int signupId) async {
    final response = await http.post(Uri.parse('${ApiConfig.affairs}/signups/$signupId/todo'), headers: _headers());
    if (response.statusCode == 200) {
      return json.decode(response.body);
    }
    return {'error': '催办待办创建失败'};
  }

  Future<Map<String, dynamic>> importLedger(String ocrText) async {
    final response = await http.post(
      Uri.parse('${ApiConfig.affairs}/ledger/import'),
      headers: _headers(json: true),
      body: json.encode({'ocr_text': ocrText}),
    );
    return json.decode(response.body);
  }

  Future<Map<String, dynamic>> exportLedger() async {
    final response = await http.post(Uri.parse('${ApiConfig.affairs}/ledger/export'), headers: _headers());
    if (response.statusCode == 200) {
      return json.decode(response.body);
    }
    return {'error': '导出失败: ${response.statusCode}'};
  }

  // ───────────────── 统一长任务（tasks） ─────────────────
  Future<Map<String, dynamic>> getTask(int taskId) async {
    final response = await http.get(Uri.parse('${ApiConfig.tasks}/$taskId'), headers: _headers());
    if (response.statusCode == 200) {
      return json.decode(response.body);
    }
    return {'status': 'unknown'};
  }

  // ───────────────── 统一路由（orchestrate） ─────────────────
  Future<Map<String, dynamic>> orchestrate(String query) async {
    final response = await http.post(
      Uri.parse(ApiConfig.orchestrate),
      headers: _headers(json: true),
      body: json.encode({'query': query}),
    );
    if (response.statusCode == 200) {
      return json.decode(response.body);
    }
    return {'domain': '', 'task': '', 'reply': '路由失败', 'needs_clarification': false};
  }

  // ───────────────── 演示数据（admin） ─────────────────
  Future<Map<String, dynamic>> seedDemo() async {
    final response = await http.post(Uri.parse('${ApiConfig.admin}/seed'), headers: _headers());
    if (response.statusCode == 200) {
      return json.decode(response.body);
    }
    return {'ok': false, 'error': 'seed 失败: ${response.statusCode}'};
  }

  Future<Map<String, dynamic>> clearDemo() async {
    final response = await http.post(Uri.parse('${ApiConfig.admin}/clear'), headers: _headers());
    if (response.statusCode == 200) {
      return json.decode(response.body);
    }
    return {'ok': false, 'error': 'clear 失败: ${response.statusCode}'};
  }

  Future<Map<String, dynamic>> demoStatus() async {
    final response = await http.get(Uri.parse('${ApiConfig.admin}/demo-status'), headers: _headers());
    if (response.statusCode == 200) {
      return json.decode(response.body);
    }
    return {'demo_mode': false};
  }
}
