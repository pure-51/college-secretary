class ApiConfig {
  static const String baseUrl = 'http://127.0.0.1:8002';

  static const String inbox = '$baseUrl/api/inbox';
  static const String knowledge = '$baseUrl/api/knowledge';
  static const String schedule = '$baseUrl/api/schedule';
  static const String aiReport = '$baseUrl/api/ai/report';
  static const String aiReportChat = '$baseUrl/api/ai/report/chat';
  static const String aiConsult = '$baseUrl/api/ai/consult';
  static const String ocr = '$baseUrl/api/ocr';
  static const String health = '$baseUrl/api/health';
  static const String config = '$baseUrl/api/config';

  // ── S1-S4 新增域 ──
  static const String career = '$baseUrl/api/career';
  static const String papers = '$baseUrl/api/papers';
  static const String affairs = '$baseUrl/api/affairs';
  static const String tasks = '$baseUrl/api/tasks';
  static const String orchestrate = '$baseUrl/api/ai/orchestrate';
  static const String admin = '$baseUrl/api/admin';
}
