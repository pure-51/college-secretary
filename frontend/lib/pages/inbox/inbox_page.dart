import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../../config/theme.dart';
import '../../providers/inbox_provider.dart';
import '../../widgets/empty_state.dart';
import '../../widgets/loading_indicator.dart';
import 'import_bottom_sheet.dart';
import 'message_detail_page.dart';

class InboxPage extends StatefulWidget {
  const InboxPage({super.key});

  @override
  State<InboxPage> createState() => _InboxPageState();
}

class _InboxPageState extends State<InboxPage> {
  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      context.read<InboxProvider>().loadMessages();
    });
  }

  void _showImportSheet() {
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      backgroundColor: Colors.transparent,
      builder: (_) => Container(
        decoration: const BoxDecoration(
          color: Colors.white,
          borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
        ),
        child: const ImportBottomSheet(),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('收件箱'),
        actions: [
          Consumer<InboxProvider>(
            builder: (context, provider, _) {
              if (provider.messages.isEmpty) return const SizedBox.shrink();
              return IconButton(
                icon: const Icon(Icons.refresh_rounded, size: 22),
                tooltip: '刷新',
                onPressed: () => provider.loadMessages(),
              );
            },
          ),
        ],
      ),
      body: Consumer<InboxProvider>(
        builder: (context, provider, _) {
          if (provider.isLoading) {
            return const SkeletonLoader();
          }
          if (provider.messages.isEmpty) {
            return EmptyState(
              icon: Icons.inbox_outlined,
              message: '还没有消息\n点击下方按钮导入第一条消息',
              actionLabel: '导入消息',
              onAction: _showImportSheet,
            );
          }
          return RefreshIndicator(
            onRefresh: () => provider.loadMessages(),
            child: ListView.builder(
              padding: const EdgeInsets.fromLTRB(16, 8, 16, 80),
              itemCount: provider.messages.length,
              itemBuilder: (context, index) {
                final msg = provider.messages[index];
                return _InboxCard(
                  message: msg,
                  onTap: () => Navigator.push(
                    context,
                    MaterialPageRoute(
                      builder: (_) => MessageDetailPage(message: msg),
                    ),
                  ),
                  onDelete: () => _deleteMessage(context, msg['id'], provider),
                );
              },
            ),
          );
        },
      ),
      floatingActionButton: FloatingActionButton(
        onPressed: _showImportSheet,
        child: const Icon(Icons.add_rounded),
      ),
    );
  }

  Future<void> _deleteMessage(
      BuildContext context, dynamic id, InboxProvider provider) async {
    if (id is! int) return;
    final confirm = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('删除消息'),
        content: const Text('确定删除此消息吗？'),
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
    if (confirm == true) {
      await provider.deleteMessage(id);
    }
  }
}

class _InboxCard extends StatelessWidget {
  final Map<String, dynamic> message;
  final VoidCallback onTap;
  final VoidCallback onDelete;

  const _InboxCard({
    required this.message,
    required this.onTap,
    required this.onDelete,
  });

  @override
  Widget build(BuildContext context) {
    final status = message['status'] as String? ?? 'pending';
    final category = message['category'] as String? ?? '待分类';
    final raw = message['raw_content'] as String? ?? '';
    final sourceType = message['source_type'] as String? ?? 'text';
    final isConfirmed = status == 'confirmed';

    return Dismissible(
      key: ValueKey(message['id']),
      direction: DismissDirection.endToStart,
      background: Container(
        alignment: Alignment.centerRight,
        padding: const EdgeInsets.only(right: 24),
        margin: const EdgeInsets.only(bottom: 10),
        decoration: BoxDecoration(
          color: AppTheme.errorColor.withAlpha(30),
          borderRadius: BorderRadius.circular(14),
        ),
        child: const Icon(Icons.delete_outline, color: AppTheme.errorColor),
      ),
      confirmDismiss: (_) async {
        final confirm = await showDialog<bool>(
          context: context,
          builder: (ctx) => AlertDialog(
            title: const Text('删除消息'),
            content: const Text('确定删除此消息吗？'),
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
        if (confirm == true) {
          onDelete();
        }
        return confirm ?? false;
      },
      child: GestureDetector(
        onTap: onTap,
        child: AnimatedContainer(
          duration: const Duration(milliseconds: 200),
          margin: const EdgeInsets.only(bottom: 10),
          decoration: BoxDecoration(
            color: Colors.white,
            borderRadius: BorderRadius.circular(14),
            border: Border.all(
              color: isConfirmed
                  ? AppTheme.successColor.withAlpha(50)
                  : AppTheme.borderColor,
              width: 0.5,
            ),
          ),
          child: Padding(
            padding: const EdgeInsets.all(14),
            child: Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                // 左侧图标
                _sourceIcon(sourceType),
                const SizedBox(width: 12),
                // 内容
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        _truncate(raw, 60),
                        style: const TextStyle(
                          fontSize: 14,
                          fontWeight: FontWeight.w500,
                          color: AppTheme.textPrimary,
                          height: 1.4,
                        ),
                        maxLines: 2,
                        overflow: TextOverflow.ellipsis,
                      ),
                      const SizedBox(height: 8),
                      Row(
                        children: [
                          _CategoryBadge(label: category),
                          const SizedBox(width: 8),
                          _StatusBadge(status: status),
                        ],
                      ),
                    ],
                  ),
                ),
                const SizedBox(width: 8),
                // 右侧箭头
                Icon(
                  Icons.chevron_right_rounded,
                  size: 20,
                  color: AppTheme.textTertiary.withAlpha(120),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }

  Widget _sourceIcon(String type) {
    IconData icon;
    Color color;
    Color bg;
    switch (type) {
      case 'image':
        icon = Icons.image_rounded;
        color = const Color(0xFF10B981);
        bg = const Color(0xFF10B981).withAlpha(20);
        break;
      case 'link':
        icon = Icons.link_rounded;
        color = const Color(0xFF8B5CF6);
        bg = const Color(0xFF8B5CF6).withAlpha(20);
        break;
      default:
        icon = Icons.text_snippet_rounded;
        color = AppTheme.primaryColor;
        bg = AppTheme.primaryLight;
    }
    return Container(
      width: 40,
      height: 40,
      decoration: BoxDecoration(
        color: bg,
        borderRadius: BorderRadius.circular(10),
      ),
      child: Icon(icon, size: 20, color: color),
    );
  }

  String _truncate(String s, int max) {
    if (s.length <= max) return s;
    return '${s.substring(0, max)}...';
  }
}

class _CategoryBadge extends StatelessWidget {
  final String label;

  const _CategoryBadge({required this.label});

  @override
  Widget build(BuildContext context) {
    Color color;
    switch (label) {
      case '教务':
        color = AppTheme.primaryColor;
        break;
      case '学工':
        color = const Color(0xFF8B5CF6);
        break;
      case '社团':
        color = const Color(0xFF10B981);
        break;
      default:
        color = AppTheme.textTertiary;
    }

    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
      decoration: BoxDecoration(
        color: color.withAlpha(20),
        borderRadius: BorderRadius.circular(6),
      ),
      child: Text(
        label,
        style: TextStyle(fontSize: 11, fontWeight: FontWeight.w500, color: color),
      ),
    );
  }
}

class _StatusBadge extends StatelessWidget {
  final String status;

  const _StatusBadge({required this.status});

  @override
  Widget build(BuildContext context) {
    String label;
    Color color;
    switch (status) {
      case 'confirmed':
        label = '已确认';
        color = AppTheme.successColor;
        break;
      case 'rejected':
        label = '已拒绝';
        color = AppTheme.errorColor;
        break;
      default:
        label = '待确认';
        color = AppTheme.warningColor;
    }

    return Row(
      mainAxisSize: MainAxisSize.min,
      children: [
        Container(
          width: 6,
          height: 6,
          decoration: BoxDecoration(
            color: color,
            shape: BoxShape.circle,
          ),
        ),
        const SizedBox(width: 4),
        Text(
          label,
          style: TextStyle(fontSize: 11, color: color),
        ),
      ],
    );
  }
}
