import 'package:flutter/foundation.dart';
import '../services/api_service.dart';

class AiReportProvider extends ChangeNotifier {
  final ApiService _api = ApiService();
  List<Map<String, String>> _messages = [];
  bool _isLoading = false;
  int _remainingTodos = 0;

  List<Map<String, String>> get messages => _messages;
  bool get isLoading => _isLoading;
  int get remainingTodos => _remainingTodos;
  bool get hasReport => _messages.any((m) => m['role'] == 'assistant');

  void _addMessage(String role, String content) {
    _messages.add({'role': role, 'content': content});
  }

  Future<void> generateReport() async {
    _isLoading = true;
    notifyListeners();

    final result = await _api.getAiReport();
    final report = result['report'] as String? ?? '暂时无法生成汇报。';

    // 清空旧对话，以汇报作为第一条
    _messages = [];
    _addMessage('assistant', report);

    _isLoading = false;
    notifyListeners();
  }

  Future<void> sendMessage(String text) async {
    if (text.trim().isEmpty) return;

    _addMessage('user', text);
    _isLoading = true;
    notifyListeners();

    // 把当前对话历史发给后端
    final result = await _api.reportChat(_messages);
    final reply = result['reply'] as String? ?? '好的，已为你处理。';
    _remainingTodos = result['remaining_todos'] as int? ?? 0;

    _addMessage('assistant', reply);
    _isLoading = false;
    notifyListeners();
  }
}
