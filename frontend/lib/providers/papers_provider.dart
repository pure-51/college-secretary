import 'dart:typed_data';
import 'package:flutter/foundation.dart';
import '../services/api_service.dart';
import '../models/papers.dart';

class PapersProvider extends ChangeNotifier {
  final ApiService _api = ApiService();

  List<PaperMeta> _papers = [];
  List<ExplainPart> _explainParts = [];
  String _qaAnswer = '';
  List<Citation> _qaCitations = [];
  CompareTable _compareTable = const CompareTable();
  List<ReviewSection> _reviewSections = [];
  String _reviewTitle = '';
  bool _isLoading = false;
  String _error = '';

  List<PaperMeta> get papers => _papers;
  List<ExplainPart> get explainParts => _explainParts;
  String get qaAnswer => _qaAnswer;
  List<Citation> get qaCitations => _qaCitations;
  CompareTable get compareTable => _compareTable;
  List<ReviewSection> get reviewSections => _reviewSections;
  String get reviewTitle => _reviewTitle;
  bool get isLoading => _isLoading;
  String get error => _error;

  Future<void> loadPapers() async {
    _setLoading(true);
    try {
      final items = await _api.listPapers();
      _papers = items.map((e) => PaperMeta.fromJson(e as Map<String, dynamic>)).toList();
    } catch (e) {
      _error = '论文列表加载失败: $e';
    }
    _setLoading(false);
  }

  Future<String> uploadPaper(Uint8List bytes, String filename, {String? title}) async {
    try {
      final data = await _api.uploadPaper(bytes, filename, title: title);
      await loadPapers();
      return '上传成功：${data['title']}';
    } catch (e) {
      return '上传失败: $e';
    }
  }

  /// 论文讲解（长任务）：返回 task_id，结果经轮询后由 setExplainFromJson 填充
  Future<int?> explainPaper(int documentId, {String question = ''}) async {
    _setLoading(true);
    try {
      final data = await _api.explainPaper(documentId, question: question);
      _error = '';
      // 同步模式直接返回 parts；否则返回 task_id 轮询
      if (data['parts'] is List && (data['parts'] as List).isNotEmpty) {
        setExplainFromJson(data['parts']);
      }
      return data['task_id'] as int?;
    } catch (e) {
      _error = '讲解生成失败: $e';
      return null;
    } finally {
      _setLoading(false);
    }
  }

  void setExplainFromJson(dynamic parts) {
    _explainParts = ((parts as List<dynamic>?) ?? [])
        .map((e) => ExplainPart.fromJson(e as Map<String, dynamic>))
        .toList();
    notifyListeners();
  }

  Future<void> askPaper(int documentId, String question) async {
    _setLoading(true);
    try {
      final data = await _api.askPaper(documentId, question);
      _qaAnswer = data['answer'] as String? ?? '';
      _qaCitations = ((data['citations'] as List<dynamic>?) ?? [])
          .map((e) => Citation.fromJson(e as Map<String, dynamic>))
          .toList();
    } catch (e) {
      _qaAnswer = '问答失败: $e';
    }
    _setLoading(false);
  }

  Future<void> comparePapers(List<int> documentIds) async {
    _setLoading(true);
    try {
      final data = await _api.comparePapers(documentIds);
      _compareTable = CompareTable.fromJson(data['table'] as Map<String, dynamic>? ?? {});
    } catch (e) {
      _error = '对比失败: $e';
    }
    _setLoading(false);
  }

  /// 综述生成（长任务）：返回 task_id，结果经轮询后由 setReviewFromJson 填充
  Future<int?> generateReview(List<int> documentIds) async {
    _setLoading(true);
    try {
      final data = await _api.generateReview(documentIds);
      _error = '';
      if (data['sections'] is List && (data['sections'] as List).isNotEmpty) {
        setReviewFromJson(data['title'], data['sections']);
      }
      return data['task_id'] as int?;
    } catch (e) {
      _error = '综述生成失败: $e';
      return null;
    } finally {
      _setLoading(false);
    }
  }

  void setReviewFromJson(dynamic title, dynamic sections) {
    _reviewTitle = (title as String?) ?? '';
    _reviewSections = ((sections as List<dynamic>?) ?? [])
        .map((e) => ReviewSection.fromJson(e as Map<String, dynamic>))
        .toList();
    notifyListeners();
  }

  void _setLoading(bool v) {
    _isLoading = v;
    notifyListeners();
  }
}
