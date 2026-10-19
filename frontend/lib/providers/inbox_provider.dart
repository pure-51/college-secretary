import 'dart:io';
import 'dart:typed_data';
import 'package:flutter/foundation.dart';
import '../services/api_service.dart';

class InboxProvider extends ChangeNotifier {
  final ApiService _api = ApiService();
  List<dynamic> _messages = [];
  bool _isLoading = false;

  List<dynamic> get messages => _messages;
  bool get isLoading => _isLoading;

  Future<void> loadMessages() async {
    _isLoading = true;
    notifyListeners();
    _messages = await _api.getMessages();
    _isLoading = false;
    notifyListeners();
  }

  Future<void> importText(String text) async {
    await _api.importText(text);
    await loadMessages();
  }

  Future<void> importImage(File imageFile) async {
    await _api.importImage(imageFile);
    await loadMessages();
  }

  Future<void> importImageBytes(Uint8List bytes, String filename) async {
    await _api.importImageBytes(bytes, filename);
    await loadMessages();
  }

  Future<void> importLink(String url) async {
    await _api.importLink(url);
    await loadMessages();
  }

  Future<void> deleteMessage(int id) async {
    await _api.deleteMessage(id);
    await loadMessages();
  }

  Future<void> confirmMessage(int id, {String? notes}) async {
    await _api.confirmMessage(id, notes: notes);
    await loadMessages();
  }
}
