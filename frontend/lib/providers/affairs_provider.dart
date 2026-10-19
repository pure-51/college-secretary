import 'package:flutter/foundation.dart';
import '../services/api_service.dart';
import '../models/affairs.dart';

class AffairsProvider extends ChangeNotifier {
  final ApiService _api = ApiService();

  String _noticeDraft = '';
  String _noticeCopyText = '';
  List<SignupInfo> _signups = [];
  Map<int, List<SignupEntry>> _entriesBySignup = {};
  Map<int, SignupStats> _statsBySignup = {};
  int _ledgerAdded = 0;
  bool _isLoading = false;
  String _error = '';

  String get noticeDraft => _noticeDraft;
  String get noticeCopyText => _noticeCopyText;
  List<SignupInfo> get signups => _signups;
  bool get isLoading => _isLoading;
  String get error => _error;
  int get ledgerAdded => _ledgerAdded;

  List<SignupEntry> entriesOf(int signupId) => _entriesBySignup[signupId] ?? [];
  SignupStats? statsOf(int signupId) => _statsBySignup[signupId];

  Future<String> generateNotice(String scene, List<String> keyPoints, {String tone = ''}) async {
    _setLoading(true);
    try {
      final data = await _api.generateNotice(scene, keyPoints, tone: tone);
      _noticeDraft = data['draft'] as String? ?? '';
      _noticeCopyText = data['copy_text'] as String? ?? '';
      _error = '';
      return '';
    } catch (e) {
      _error = '通知生成失败: $e';
      return _error;
    } finally {
      _setLoading(false);
    }
  }

  Future<String> createSignup({required String title, String? description, List<String> options = const []}) async {
    try {
      final data = await _api.createSignup(title: title, description: description, options: options);
      await loadSignups();
      return '接龙已创建：${data['title']}';
    } catch (e) {
      return '创建失败: $e';
    }
  }

  Future<void> loadSignups() async {
    _setLoading(true);
    try {
      // 后端无列表端点，用 seed 后的演示接龙 id=1 尝试；空则显示空态
      _signups = [];
      // 尝试探测：seed 数据 id=1
      final stats = await _api.getSignupStats(1);
      if (stats['signup'] != null && (stats['signup'] as Map).isNotEmpty) {
        _signups = [SignupInfo.fromJson(stats['signup'] as Map<String, dynamic>)];
        _entriesBySignup[1] = ((stats['entries'] as List<dynamic>?) ?? [])
            .map((e) => SignupEntry.fromJson(e as Map<String, dynamic>))
            .toList();
        _statsBySignup[1] = SignupStats.fromJson(stats['stats'] as Map<String, dynamic>? ?? {});
      }
    } catch (e) {
      _error = '接龙加载失败: $e';
    }
    _setLoading(false);
  }

  Future<String> importSignup(int signupId, String rawText) async {
    _setLoading(true);
    try {
      final data = await _api.importSignup(signupId, rawText);
      await loadSignups();
      return '导入成功：新增 ${data['added']}，更新 ${data['updated']}';
    } catch (e) {
      return '导入失败: $e';
    } finally {
      _setLoading(false);
    }
  }

  Future<String> signupTodo(int signupId) async {
    try {
      final data = await _api.signupTodo(signupId);
      return '已生成催办待办（${data['submitted_count']} 人已报名）';
    } catch (e) {
      return '催办生成失败: $e';
    }
  }

  Future<String> importLedger(String ocrText) async {
    _setLoading(true);
    try {
      final data = await _api.importLedger(ocrText);
      _ledgerAdded = data['added'] as int? ?? 0;
      return '台账导入成功：${_ledgerAdded} 条';
    } catch (e) {
      return '台账导入失败: $e';
    } finally {
      _setLoading(false);
    }
  }

  void _setLoading(bool v) {
    _isLoading = v;
    notifyListeners();
  }
}
