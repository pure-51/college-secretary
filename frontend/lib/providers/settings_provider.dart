import 'package:flutter/foundation.dart';
import '../services/api_service.dart';

class SettingsProvider extends ChangeNotifier {
  final ApiService _api = ApiService();
  bool _isConnected = false;
  Map<String, dynamic> _config = {};

  bool get isConnected => _isConnected;
  Map<String, dynamic> get config => _config;
  String get llmModel => _config['llm_model'] as String? ?? 'deepseek-v4-flash';

  Future<void> checkConnection() async {
    _isConnected = await _api.healthCheck();
    notifyListeners();
  }

  Future<void> loadConfig() async {
    _config = await _api.getConfig();
    notifyListeners();
  }

  Future<String> clearInbox() async {
    await _api.clearAllMessages();
    return '收件箱已清空';
  }

  Future<String> clearKnowledge() async {
    await _api.clearAllDocuments();
    return '知识库已清空';
  }

  Future<String> clearSchedule() async {
    await _api.clearAllSchedule();
    return '日程已清空';
  }

  Future<String> clearAll() async {
    await _api.clearAllMessages();
    await _api.clearAllDocuments();
    await _api.clearAllSchedule();
    return '所有数据已清空';
  }
}
