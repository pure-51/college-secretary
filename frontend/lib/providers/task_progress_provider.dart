import 'dart:async';
import 'package:flutter/foundation.dart';
import '../services/api_service.dart';

class TaskInfo {
  final int taskId;
  final String skillName;
  final String status;
  final int progress;
  final List<dynamic> steps;
  final Map<String, dynamic>? result;
  final String? error;

  TaskInfo({
    required this.taskId,
    required this.skillName,
    required this.status,
    this.progress = 0,
    this.steps = const [],
    this.result,
    this.error,
  });

  factory TaskInfo.fromJson(Map<String, dynamic> json) {
    return TaskInfo(
      taskId: json['task_id'] as int? ?? 0,
      skillName: json['skill_name'] as String? ?? '',
      status: json['status'] as String? ?? 'running',
      progress: json['progress'] as int? ?? 0,
      steps: (json['steps'] as List<dynamic>?) ?? [],
      result: json['result'] as Map<String, dynamic>?,
      error: json['error'] as String?,
    );
  }

  bool get isRunning => status == 'running';
  bool get isSuccess => status == 'success';
}

/// 长任务轮询中心：任务注册后自动 800ms 轮询 /api/tasks/{id}，成功/失败停止
class TaskProgressProvider extends ChangeNotifier {
  final ApiService _api = ApiService();
  final Map<int, TaskInfo> _tasks = {};
  final Map<int, Timer> _timers = {};
  int _activeCount = 0;

  Map<int, TaskInfo> get tasks => Map.unmodifiable(_tasks);
  int get activeCount => _activeCount;
  TaskInfo? taskById(int id) => _tasks[id];

  /// 注册任务并启动轮询；onDone 在终态（success/failed/cancelled）回调，携带 TaskInfo
  void watchTask(int taskId, {void Function(TaskInfo task)? onDone}) {
    if (_timers.containsKey(taskId)) return;
    _pollOnce(taskId, onDone);
    final timer = Timer.periodic(const Duration(milliseconds: 800), (_) {
      _pollOnce(taskId, onDone);
    });
    _timers[taskId] = timer;
    _activeCount = _timers.length;
    notifyListeners();
  }

  Future<void> _pollOnce(int taskId, void Function(TaskInfo task)? onDone) async {
    final data = await _api.getTask(taskId);
    final info = TaskInfo.fromJson(data);
    _tasks[taskId] = info;
    notifyListeners();
    if (!info.isRunning) {
      final timer = _timers.remove(taskId);
      timer?.cancel();
      _activeCount = _timers.length;
      notifyListeners();
      onDone?.call(info);
    }
  }

  void clear() {
    for (final t in _timers.values) {
      t.cancel();
    }
    _timers.clear();
    _tasks.clear();
    _activeCount = 0;
    notifyListeners();
  }
}
