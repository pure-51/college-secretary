import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../../config/theme.dart';
import '../../providers/settings_provider.dart';

class SettingsPage extends StatefulWidget {
  const SettingsPage({super.key});

  @override
  State<SettingsPage> createState() => _SettingsPageState();
}

class _SettingsPageState extends State<SettingsPage> {
  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      final p = context.read<SettingsProvider>();
      p.checkConnection();
      p.loadConfig();
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('设置')),
      body: Consumer<SettingsProvider>(
        builder: (context, provider, _) {
          return ListView(
            padding: const EdgeInsets.fromLTRB(16, 8, 16, 24),
            children: [
              // ── 连接状态 ──
              _SettingsCard(
                children: [
                  ListTile(
                    contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 4),
                    leading: Container(
                      width: 40, height: 40,
                      decoration: BoxDecoration(
                        color: provider.isConnected
                            ? AppTheme.successColor.withAlpha(20)
                            : AppTheme.errorColor.withAlpha(20),
                        borderRadius: BorderRadius.circular(10),
                      ),
                      child: Icon(
                        Icons.wifi_rounded,
                        color: provider.isConnected
                            ? AppTheme.successColor
                            : AppTheme.errorColor,
                        size: 20,
                      ),
                    ),
                    title: Text(
                      provider.isConnected ? '后端已连接' : '后端未连接',
                      style: const TextStyle(
                        fontWeight: FontWeight.w500,
                        fontSize: 15,
                      ),
                    ),
                    subtitle: Text(
                      provider.isConnected ? '127.0.0.1:8002' : '点击重试',
                      style: const TextStyle(fontSize: 13),
                    ),
                    trailing: TextButton(
                      onPressed: () => provider.checkConnection(),
                      child: const Text('重试'),
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 12),

              // ── 模型配置 ──
              _SettingsCard(
                children: [
                  ListTile(
                    contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 4),
                    leading: Container(
                      width: 40, height: 40,
                      decoration: BoxDecoration(
                        color: AppTheme.primaryLight,
                        borderRadius: BorderRadius.circular(10),
                      ),
                      child: const Icon(Icons.api_rounded,
                          color: AppTheme.primaryColor, size: 20),
                    ),
                    title: const Text('LLM 模型',
                        style: TextStyle(fontWeight: FontWeight.w500, fontSize: 15)),
                    subtitle: Text(provider.llmModel,
                        style: const TextStyle(fontSize: 13)),
                    trailing: const Icon(Icons.chevron_right_rounded,
                        color: AppTheme.textTertiary, size: 20),
                  ),
                  const Divider(height: 1, indent: 72),
                  ListTile(
                    contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 4),
                    leading: Container(
                      width: 40, height: 40,
                      decoration: BoxDecoration(
                        color: AppTheme.successColor.withAlpha(20),
                        borderRadius: BorderRadius.circular(10),
                      ),
                      child: const Icon(Icons.image_rounded,
                          color: AppTheme.successColor, size: 20),
                    ),
                    title: const Text('OCR 识别',
                        style: TextStyle(fontWeight: FontWeight.w500, fontSize: 15)),
                    subtitle: const Text('已启用',
                        style: TextStyle(fontSize: 13)),
                    trailing: const Icon(Icons.chevron_right_rounded,
                        color: AppTheme.textTertiary, size: 20),
                  ),
                ],
              ),
              const SizedBox(height: 12),

              // ── 数据管理 ──
              _SettingsCard(
                children: [
                  _DataActionTile(
                    icon: Icons.inbox_rounded,
                    iconColor: const Color(0xFFF59E0B),
                    title: '清空收件箱',
                    subtitle: '删除所有消息和AI处理记录',
                    onTap: () => _showClearDialog(context, '收件箱',
                        '确定清空所有消息吗？关联的待办和考试也会被删除。',
                        () => provider.clearInbox()),
                  ),
                  const Divider(height: 1, indent: 72),
                  _DataActionTile(
                    icon: Icons.calendar_month_rounded,
                    iconColor: AppTheme.primaryColor,
                    title: '清空日程',
                    subtitle: '删除所有待办事项和考试安排',
                    onTap: () => _showClearDialog(context, '日程',
                        '确定清空所有日程吗？包括待办事项和考试安排。',
                        () => provider.clearSchedule()),
                  ),
                  const Divider(height: 1, indent: 72),
                  _DataActionTile(
                    icon: Icons.menu_book_rounded,
                    iconColor: const Color(0xFF10B981),
                    title: '清空知识库',
                    subtitle: '删除所有上传的政策文件',
                    onTap: () => _showClearDialog(context, '知识库',
                        '确定清空知识库吗？所有上传的文件将被删除。',
                        () => provider.clearKnowledge()),
                  ),
                  const Divider(height: 1, indent: 72),
                  _DataActionTile(
                    icon: Icons.delete_sweep_rounded,
                    iconColor: AppTheme.errorColor,
                    title: '清空所有数据',
                    subtitle: '删除收件箱、日程、知识库全部数据',
                    isDestructive: true,
                    onTap: () => _showClearDialog(context, '所有数据',
                        '此操作不可恢复！\n包括：所有消息、待办、考试、文档。',
                        () => provider.clearAll()),
                  ),
                ],
              ),
              const SizedBox(height: 12),

              // ── 关于 ──
              _SettingsCard(
                children: [
                  ListTile(
                    contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 4),
                    leading: Container(
                      width: 40, height: 40,
                      decoration: BoxDecoration(
                        color: AppTheme.primaryLight,
                        borderRadius: BorderRadius.circular(10),
                      ),
                      child: const Icon(Icons.info_outline_rounded,
                          color: AppTheme.primaryColor, size: 20),
                    ),
                    title: const Text('大学生秘书 v1.0.0',
                        style: TextStyle(fontWeight: FontWeight.w500, fontSize: 15)),
                    subtitle: const Text('AI-powered College Secretary',
                        style: TextStyle(fontSize: 13)),
                  ),
                ],
              ),
            ],
          );
        },
      ),
    );
  }

  void _showClearDialog(BuildContext context, String title, String message,
      Future<String> Function() clearAction) {
    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        title: Text('清空$title'),
        content: Text(message),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(ctx),
            child: const Text('取消'),
          ),
          TextButton(
            onPressed: () async {
              Navigator.pop(ctx);
              final msg = await clearAction();
              if (mounted) {
                ScaffoldMessenger.of(context).showSnackBar(
                  SnackBar(
                    content: Text(msg),
                    backgroundColor: title == '所有数据'
                        ? AppTheme.errorColor
                        : AppTheme.successColor,
                  ),
                );
              }
            },
            child: Text('确定',
                style: TextStyle(
                  color: title == '所有数据'
                      ? AppTheme.errorColor
                      : AppTheme.primaryColor,
                )),
          ),
        ],
      ),
    );
  }
}

class _SettingsCard extends StatelessWidget {
  final List<Widget> children;

  const _SettingsCard({required this.children});

  @override
  Widget build(BuildContext context) {
    return Container(
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(14),
        border: Border.all(color: AppTheme.borderColor, width: 0.5),
      ),
      child: Column(children: children),
    );
  }
}

class _DataActionTile extends StatelessWidget {
  final IconData icon;
  final Color iconColor;
  final String title;
  final String subtitle;
  final VoidCallback onTap;
  final bool isDestructive;

  const _DataActionTile({
    required this.icon,
    required this.iconColor,
    required this.title,
    required this.subtitle,
    required this.onTap,
    this.isDestructive = false,
  });

  @override
  Widget build(BuildContext context) {
    return ListTile(
      contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 4),
      leading: Container(
        width: 40,
        height: 40,
        decoration: BoxDecoration(
          color: iconColor.withAlpha(20),
          borderRadius: BorderRadius.circular(10),
        ),
        child: Icon(icon, color: iconColor, size: 20),
      ),
      title: Text(title,
          style: TextStyle(
            fontWeight: FontWeight.w500,
            fontSize: 15,
            color: isDestructive ? AppTheme.errorColor : AppTheme.textPrimary,
          )),
      subtitle: Text(subtitle, style: const TextStyle(fontSize: 13)),
      trailing: isDestructive
          ? Container(
              padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
              decoration: BoxDecoration(
                color: AppTheme.errorColor.withAlpha(15),
                borderRadius: BorderRadius.circular(6),
              ),
              child: const Text('危险',
                  style: TextStyle(
                      fontSize: 11,
                      color: AppTheme.errorColor,
                      fontWeight: FontWeight.w500)),
            )
          : const Icon(Icons.chevron_right_rounded,
              color: AppTheme.textTertiary, size: 20),
      onTap: onTap,
    );
  }
}
