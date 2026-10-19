import 'dart:io';
import 'package:flutter/foundation.dart';
import '../services/api_service.dart';

class KnowledgeProvider extends ChangeNotifier {
  final ApiService _api = ApiService();
  List<dynamic> _documents = [];
  List<dynamic> _searchResults = [];
  bool _isLoading = false;

  List<dynamic> get documents => _documents;
  List<dynamic> get searchResults => _searchResults;
  bool get isLoading => _isLoading;

  Future<void> loadDocuments() async {
    _isLoading = true;
    notifyListeners();
    _documents = await _api.getDocuments();
    _isLoading = false;
    notifyListeners();
  }

  Future<void> uploadFile(File file) async {
    await _api.uploadDocument(file);
    await loadDocuments();
  }

  Future<void> search(String query) async {
    final result = await _api.searchKnowledge(query);
    _searchResults = result['results'] as List<dynamic>? ?? [];
    notifyListeners();
  }
}
