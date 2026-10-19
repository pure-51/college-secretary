import 'package:flutter/foundation.dart';
import '../services/api_service.dart';
import '../models/career.dart';

class CareerProvider extends ChangeNotifier {
  final ApiService _api = ApiService();

  List<ArchiveRecord> _records = [];
  List<ResumeSection> _resumeSections = [];
  List<InterviewQuestion> _interviewQuestions = [];
  InterviewFeedback? _interviewFeedback;
  List<HealthDimension> _healthDimensions = [];
  int _healthProgress = 0;
  List<Milestone> _milestones = [];
  bool _isLoading = false;
  String _error = '';

  List<ArchiveRecord> get records => _records;
  List<ResumeSection> get resumeSections => _resumeSections;
  List<InterviewQuestion> get interviewQuestions => _interviewQuestions;
  InterviewFeedback? get interviewFeedback => _interviewFeedback;
  List<HealthDimension> get healthDimensions => _healthDimensions;
  int get healthProgress => _healthProgress;
  List<Milestone> get milestones => _milestones;
  bool get isLoading => _isLoading;
  String get error => _error;

  Future<void> loadArchiveRecords() async {
    _setLoading(true);
    try {
      final items = await _api.getArchiveRecords();
      _records = items.map((e) => ArchiveRecord.fromJson(e as Map<String, dynamic>)).toList();
    } catch (e) {
      _error = '档案加载失败: $e';
    }
    _setLoading(false);
  }

  Future<void> loadHealth() async {
    final data = await _api.careerHealthCheck();
    _healthProgress = data['progress'] as int? ?? 0;
    _healthDimensions = ((data['dimensions'] as List<dynamic>?) ?? [])
        .map((e) => HealthDimension.fromJson(e as Map<String, dynamic>))
        .toList();
    notifyListeners();
  }

  Future<void> loadMilestones() async {
    final items = await _api.careerMilestones();
    _milestones = items.map((e) => Milestone.fromJson(e as Map<String, dynamic>)).toList();
    notifyListeners();
  }

  /// 一键简历：返回 task_id 供 TaskProgressProvider 轮询
  Future<int?> generateResume({String direction = '保研-计算机'}) async {
    _setLoading(true);
    try {
      final data = await _api.generateResume(direction: direction);
      _error = '';
      // 后端同步阻塞执行，返回即终态：直接填充 sections
      if (data['sections'] is List) {
        setResumeFromJson(data['sections']);
      }
      return data['task_id'] as int?;
    } catch (e) {
      _error = '简历生成失败: $e';
      return null;
    } finally {
      _setLoading(false);
    }
  }

  /// 解析简历内容（generateResume 同步返回时也带 sections）
  void setResumeFromJson(List<dynamic>? sections) {
    _resumeSections = (sections ?? [])
        .map((e) => ResumeSection.fromJson(e as Map<String, dynamic>))
        .toList();
    notifyListeners();
  }

  Future<void> loadInterviewQuestions({String direction = '保研-计算机'}) async {
    _setLoading(true);
    try {
      final data = await _api.interviewQuestions(direction: direction);
      _interviewQuestions = ((data['questions'] as List<dynamic>?) ?? [])
          .map((e) => InterviewQuestion.fromJson(e as Map<String, dynamic>))
          .toList();
    } catch (e) {
      _error = '面试问题生成失败: $e';
    }
    _setLoading(false);
  }

  Future<void> submitInterviewFeedback(String direction, List<Map<String, dynamic>> qaPairs) async {
    _setLoading(true);
    try {
      final data = await _api.interviewFeedback(direction, qaPairs);
      _interviewFeedback = InterviewFeedback.fromJson(data);
    } catch (e) {
      _error = '面试点评失败: $e';
    }
    _setLoading(false);
  }

  Future<String> createArchiveRecord(String rawText, {String? hint}) async {
    try {
      final data = await _api.createArchiveRecord(rawText, recordTypeHint: hint);
      await loadArchiveRecords();
      return '档案已建：${data['title']}';
    } catch (e) {
      return '归档失败: $e';
    }
  }

  Future<String> deleteArchiveRecord(int id) async {
    await _api.deleteArchiveRecord(id);
    await loadArchiveRecords();
    return '已删除档案';
  }

  Future<String> updateArchiveRecord(int id, Map<String, dynamic> payload) async {
    try {
      final data = await _api.updateArchiveRecord(id, payload);
      await loadArchiveRecords();
      return '已确认: ${data['status']}';
    } catch (e) {
      return '更新失败: $e';
    }
  }

  void _setLoading(bool v) {
    _isLoading = v;
    notifyListeners();
  }
}
