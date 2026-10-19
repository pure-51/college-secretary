import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:intl/date_symbol_data_local.dart';
import 'services/api_service.dart';
import 'config/theme.dart';
import 'providers/inbox_provider.dart';
import 'providers/schedule_provider.dart';
import 'providers/knowledge_provider.dart';
import 'providers/ai_report_provider.dart';
import 'providers/ai_consult_provider.dart';
import 'providers/settings_provider.dart';
import 'providers/career_provider.dart';
import 'providers/papers_provider.dart';
import 'providers/affairs_provider.dart';
import 'providers/task_progress_provider.dart';
import 'widgets/app_scaffold.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  await initializeDateFormatting('zh_CN');
  // 从 /api/config 加载本地令牌，后续请求自动携带（ADR §6）
  await ApiService().loadTokenFromConfig();
  runApp(
    MultiProvider(
      providers: [
        ChangeNotifierProvider(create: (_) => InboxProvider()),
        ChangeNotifierProvider(create: (_) => ScheduleProvider()),
        ChangeNotifierProvider(create: (_) => KnowledgeProvider()),
        ChangeNotifierProvider(create: (_) => AiReportProvider()),
        ChangeNotifierProvider(create: (_) => AiConsultProvider()),
        ChangeNotifierProvider(create: (_) => SettingsProvider()),
        ChangeNotifierProvider(create: (_) => CareerProvider()),
        ChangeNotifierProvider(create: (_) => PapersProvider()),
        ChangeNotifierProvider(create: (_) => AffairsProvider()),
        ChangeNotifierProvider(create: (_) => TaskProgressProvider()),
      ],
      child: const CollegeSecretaryApp(),
    ),
  );
}

class CollegeSecretaryApp extends StatelessWidget {
  const CollegeSecretaryApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: '大学生秘书',
      theme: AppTheme.lightTheme,
      debugShowCheckedModeBanner: false,
      home: const AppScaffold(),
    );
  }
}
