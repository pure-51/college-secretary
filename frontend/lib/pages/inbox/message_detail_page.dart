import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../../config/theme.dart';
import '../../providers/inbox_provider.dart';
import '../../services/api_service.dart';

class MessageDetailPage extends StatelessWidget {
  final Map<String, dynamic> message;

  const MessageDetailPage({super.key, required this.message});

  @override
  Widget build(BuildContext context) {
    final category = message['category'] as String? ?? '待分类';
    final status = message['status'] as String? ?? 'pending';
    final relevance = message['relevance'] as String? ?? 'pending';

    return Scaffold(
      appBar: AppBar(
        title: const Text('消息详情'),
        actions: [
          IconButton(
            icon: Icon(Icons.delete_outline_rounded,
                color: AppTheme.errorColor.withAlpha(180)),
            tooltip: '删除',
            onPressed: () => _deleteMessage(context),
          ),
        ],
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.fromLTRB(16, 8, 16, 24),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // ── 原文卡片 ──
            Text('原文内容',
                style: Theme.of(context).textTheme.titleMedium?.copyWith(
                    color: AppTheme.textPrimary,
                    fontWeight: FontWeight.w600)),
            const SizedBox(height: 10),
            Container(
              width: double.infinity,
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(
                color: const Color(0xFFF9FAFB),
                borderRadius: BorderRadius.circular(14),
                border: Border.all(color: AppTheme.borderColor, width: 0.5),
              ),
              child: SelectableText(
                message['raw_content'] ?? '',
                style: const TextStyle(
                    fontSize: 15, height: 1.7, color: AppTheme.textPrimary),
              ),
            ),
            const SizedBox(height: 24),

            // ── AI 处理结果 ──
            Text('AI 处理结果',
                style: Theme.of(context).textTheme.titleMedium?.copyWith(
                    color: AppTheme.textPrimary,
                    fontWeight: FontWeight.w600)),
            const SizedBox(height: 10),
            Container(
              width: double.infinity,
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(
                color: AppTheme.primaryLight,
                borderRadius: BorderRadius.circular(14),
              ),
              child: Column(
                children: [
                  _ResultRow(
                      icon: Icons.label_rounded,
                      label: '分类',
                      value: category,
                      color: AppTheme.primaryColor),
                  const Divider(height: 20),
                  _ResultRow(
                      icon: Icons.person_pin_rounded,
                      label: '相关性',
                      value: relevance == 'relevant' ? '相关' : '待判断',
                      color: relevance == 'relevant'
                          ? AppTheme.successColor
                          : AppTheme.warningColor),
                  const Divider(height: 20),
                  _ResultRow(
                      icon: Icons.check_circle_rounded,
                      label: '状态',
                      value: status == 'confirmed'
                          ? '已确认'
                          : status == 'rejected'
                              ? '已拒绝'
                              : '待确认',
                      color: status == 'confirmed'
                          ? AppTheme.successColor
                          : status == 'rejected'
                              ? AppTheme.errorColor
                              : AppTheme.warningColor),
                ],
              ),
            ),
            const SizedBox(height: 28),

            // ── 操作按钮 ──
            Row(
              children: [
                Expanded(
                  child: ElevatedButton.icon(
                    onPressed: () => _confirm(context),
                    icon: const Icon(Icons.check_rounded, size: 18),
                    label: const Text('确认无误'),
                    style: ElevatedButton.styleFrom(
                      backgroundColor: AppTheme.successColor,
                      foregroundColor: Colors.white,
                      padding: const EdgeInsets.symmetric(vertical: 14),
                    ),
                  ),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: OutlinedButton.icon(
                    onPressed: () => _reject(context),
                    icon: const Icon(Icons.edit_rounded, size: 18),
                    label: const Text('需要修改'),
                    style: OutlinedButton.styleFrom(
                      foregroundColor: AppTheme.textSecondary,
                      side: const BorderSide(color: AppTheme.borderColor),
                      padding: const EdgeInsets.symmetric(vertical: 14),
                    ),
                  ),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }

  Future<void> _deleteMessage(BuildContext context) async {
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('删除消息'),
        content: const Text('确定删除此消息吗？关联的待办和考试也将被删除。'),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(ctx, false),
            child: const Text('取消'),
          ),
          TextButton(
            onPressed: () => Navigator.pop(ctx, true),
            style: TextButton.styleFrom(foregroundColor: AppTheme.errorColor),
            child: const Text('删除'),
          ),
        ],
      ),
    );

    if (confirmed == true && context.mounted) {
      final id = message['id'];
      if (id is int) {
        await ApiService().deleteMessage(id);
        if (context.mounted) {
          context.read<InboxProvider>().loadMessages();
          Navigator.pop(context);
        }
      }
    }
  }

  void _confirm(BuildContext context) => Navigator.pop(context);
  void _reject(BuildContext context) => Navigator.pop(context);
}

class _ResultRow extends StatelessWidget {
  final IconData icon;
  final String label;
  final String value;
  final Color color;

  const _ResultRow({
    required this.icon,
    required this.label,
    required this.value,
    required this.color,
  });

  @override
  Widget build(BuildContext context) {
    return Row(
      children: [
        Icon(icon, size: 18, color: color),
        const SizedBox(width: 10),
        SizedBox(
          width: 64,
          child: Text(label,
              style: TextStyle(fontSize: 13, color: color.withAlpha(160))),
        ),
        Expanded(
          child: Text(value,
              style: TextStyle(
                  fontWeight: FontWeight.w600,
                  fontSize: 14,
                  color: color)),
        ),
      ],
    );
  }
}
