import 'package:flutter/foundation.dart';
import '../services/api_service.dart';

class AiConsultProvider extends ChangeNotifier {
  final ApiService _api = ApiService();
  List<Map<String, String>> _messages = [];
  bool _isLoading = false;

  List<Map<String, String>> get messages => _messages;
  bool get isLoading => _isLoading;

  Future<void> askQuestion(String question) async {
    _isLoading = true;
    _messages.add({'role': 'user', 'content': question});
    notifyListeners();

    final result = await _api.askAi(question);
    final answer = result['answer'] as String? ?? '抱歉，我暂时无法回答这个问题。';
    _messages.add({'role': 'assistant', 'content': answer});
    _isLoading = false;
    notifyListeners();
  }
}
