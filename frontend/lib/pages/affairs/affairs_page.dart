import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:provider/provider.dart';
import '../../config/theme.dart';
import '../../providers/affairs_provider.dart';
import '../../services/api_service.dart';
import '../../widgets/empty_state.dart';

/// 班务助理主页：通知生成 / 接龙管理 / 班费台账
class AffairsPage extends StatefulWidget {
  const AffairsPage({super.key});

  @override
  State<AffairsPage> createState() => _AffairsPageState();
}

class _AffairsPageState extends State<AffairsPage>
    with SingleTickerProviderStateMixin {
  late final TabController _tabController;

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 3, vsync: this);
    WidgetsBinding.instance.addPostFrameCallback((_) {
      context.read<AffairsProvider>().loadSignups();
    });
  }

  @override
  void dispose() {
    _tabController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('班务助理'),
        bottom: TabBar(
          controller: _tabController,
          isScrollable: true,
          tabAlignment: TabAlignment.start,
          tabs: const [
            Tab(text: '通知生成'),
            Tab(text: '接龙管理'),
            Tab(text: '班费台账'),
          ],
        ),
      ),
      body: TabBarView(
        controller: _tabController,
        children: const [
          _NoticeTab(),
          _SignupTab(),
          _LedgerTab(),
        ],
      ),
    );
  }
}

// ═══════════════ 通知生成 ═══════════════

class _NoticeTab extends StatefulWidget {
  const _NoticeTab();

  @override
  State<_NoticeTab> createState() => _NoticeTabState();
}

class _NoticeTabState extends State<_NoticeTab> {
  final _sceneController = TextEditingController();
  final _pointsController = TextEditingController();

  @override
  void dispose() {
    _sceneController.dispose();
    _pointsController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final provider = context.watch<AffairsProvider>();
    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        const Text('班级通知一键生成，可选通知场景与要点',
            style: TextStyle(fontSize: 13, color: AppTheme.textSecondary)),
        const SizedBox(height: 12),
        TextField(
          controller: _sceneController,
          decoration: const InputDecoration(
            labelText: '通知场景',
            hintText: '例：本周六班级团建通知',
          ),
        ),
        const SizedBox(height: 12),
        TextField(
          controller: _pointsController,
          maxLines: 2,
          decoration: const InputDecoration(
            labelText: '要点（逗号分隔）',
            hintText: '例：下午2点南门集合,校园烧烤区,携带学生证',
          ),
        ),
        const SizedBox(height: 12),
        ElevatedButton.icon(
          onPressed: provider.isLoading
              ? null
              : () async {
                  final scene = _sceneController.text.trim();
                  if (scene.isEmpty) {
                    _snack(context, '请填写通知场景');
                    return;
                  }
                  final points = _pointsController.text
                      .split(',')
                      .map((e) => e.trim())
                      .where((e) => e.isNotEmpty)
                      .toList();
                  await context
                      .read<AffairsProvider>()
                      .generateNotice(scene, points);
                },
          icon: const Icon(Icons.auto_awesome_rounded, size: 18),
          label: const Text('生成通知'),
        ),
        if (provider.noticeDraft.isNotEmpty) ...[
          const SizedBox(height: 20),
          Container(
            padding: const EdgeInsets.all(16),
            decoration: BoxDecoration(
              color: Colors.white,
              borderRadius: BorderRadius.circular(14),
              border: Border.all(color: AppTheme.borderColor, width: 0.5),
            ),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Text('通知草稿',
                    style:
                        TextStyle(fontWeight: FontWeight.w600, fontSize: 15)),
                const SizedBox(height: 10),
                SelectableText(provider.noticeDraft,
                    style: const TextStyle(fontSize: 13, height: 1.6)),
                const Divider(height: 24),
                Text('精简复制版：${provider.noticeCopyText}',
                    style: const TextStyle(
                        fontSize: 12, color: AppTheme.textSecondary)),
                const SizedBox(height: 10),
                Row(
                  children: [
                    TextButton.icon(
                      onPressed: () {
                        // 复制文本
                        Clipboard.setData(
                            ClipboardData(text: provider.noticeDraft));
                        _snack(context, '已复制到剪贴板');
                      },
                      icon: const Icon(Icons.copy_rounded, size: 16),
                      label: const Text('复制'),
                    ),
                  ],
                ),
              ],
            ),
          ),
        ],
      ],
    );
  }
}

// ═══════════════ 接龙管理 ═══════════════

class _SignupTab extends StatelessWidget {
  const _SignupTab();

  @override
  Widget build(BuildContext context) {
    final provider = context.watch<AffairsProvider>();
    return provider.signups.isEmpty
        ? EmptyState(
            icon: Icons.list_alt_rounded,
            message: '暂无接龙\n创建接龙后即可导入名单、统计去重',
            actionLabel: '创建接龙',
            onAction: () => _showCreateSignupDialog(context),
          )
        : ListView(
            padding: const EdgeInsets.fromLTRB(16, 12, 16, 24),
            children: [
              ...provider.signups.map((s) => _SignupCard(signup: s)),
              const SizedBox(height: 8),
              Center(
                child: TextButton.icon(
                  onPressed: () => _showCreateSignupDialog(context),
                  icon: const Icon(Icons.add_rounded),
                  label: const Text('新建接龙'),
                ),
              ),
            ],
          );
  }
}

class _SignupCard extends StatelessWidget {
  final dynamic signup;
  const _SignupCard({required this.signup});

  @override
  Widget build(BuildContext context) {
    final provider = context.watch<AffairsProvider>();
    final stats = provider.statsOf(signup.id);
    final entries = provider.entriesOf(signup.id);
    return Container(
      margin: const EdgeInsets.only(bottom: 12),
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(14),
        border: Border.all(color: AppTheme.borderColor, width: 0.5),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Container(
                width: 36,
                height: 36,
                decoration: BoxDecoration(
                  color: AppTheme.primaryLight,
                  borderRadius: BorderRadius.circular(10),
                ),
                child: const Icon(Icons.how_to_reg_rounded,
                    color: AppTheme.primaryColor, size: 18),
              ),
              const SizedBox(width: 10),
              Expanded(
                child: Text(signup.title,
                    style: const TextStyle(
                        fontWeight: FontWeight.w600, fontSize: 14)),
              ),
              if (stats != null)
                Container(
                  padding:
                      const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                  decoration: BoxDecoration(
                    color: AppTheme.successColor.withAlpha(15),
                    borderRadius: BorderRadius.circular(6),
                  ),
                  child: Text('${stats.unique} 人已报',
                      style: TextStyle(
                          fontSize: 11,
                          color: AppTheme.successColor,
                          fontWeight: FontWeight.w600)),
                ),
            ],
          ),
          if (stats != null) ...[
            const SizedBox(height: 12),
            Wrap(
              spacing: 8,
              children: stats.perOption.entries.map((e) => Container(
                    padding: const EdgeInsets.symmetric(
                        horizontal: 10, vertical: 4),
                    decoration: BoxDecoration(
                      color: const Color(0xFFF3F4F6),
                      borderRadius: BorderRadius.circular(8),
                    ),
                    child: Text('${e.key}：${e.value}',
                        style: const TextStyle(
                            fontSize: 12, color: AppTheme.textSecondary)),
                  )).toList(),
            ),
          ],
          if (entries.isNotEmpty) ...[
            const SizedBox(height: 10),
            Wrap(
              spacing: 6,
              runSpacing: 6,
              children: entries.take(12).map((e) => Container(
                    padding: const EdgeInsets.symmetric(
                        horizontal: 8, vertical: 3),
                    decoration: BoxDecoration(
                      color: e.option == '不去'
                          ? AppTheme.errorColor.withAlpha(10)
                          : AppTheme.successColor.withAlpha(10),
                      borderRadius: BorderRadius.circular(6),
                    ),
                    child: Text(
                        '${e.name}${e.option == null ? '' : '·${e.option}'}',
                        style: TextStyle(
                            fontSize: 11,
                            color: e.option == '不去'
                                ? AppTheme.errorColor
                                : AppTheme.successColor)),
                  )).toList(),
            ),
          ],
          const SizedBox(height: 12),
          Row(
            children: [
              _InlineAction(
                icon: Icons.upload_rounded,
                label: '导入名单',
                onTap: () => _showImportDialog(context, signup.id),
              ),
              const SizedBox(width: 8),
              _InlineAction(
                icon: Icons.pending_actions_rounded,
                label: '催办未报名',
                onTap: () async {
                  final msg = await context
                      .read<AffairsProvider>()
                      .signupTodo(signup.id);
                  if (context.mounted) _snack(context, msg);
                },
              ),
            ],
          ),
        ],
      ),
    );
  }
}

class _InlineAction extends StatelessWidget {
  final IconData icon;
  final String label;
  final VoidCallback onTap;
  const _InlineAction(
      {required this.icon, required this.label, required this.onTap});

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 5),
        decoration: BoxDecoration(
          color: AppTheme.primaryLight,
          borderRadius: BorderRadius.circular(8),
        ),
        child: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(icon, size: 14, color: AppTheme.primaryColor),
            const SizedBox(width: 4),
            Text(label,
                style: const TextStyle(
                    fontSize: 12, color: AppTheme.primaryColor)),
          ],
        ),
      ),
    );
  }
}

Future<void> _showCreateSignupDialog(BuildContext context) async {
  final titleController = TextEditingController();
  final pointsController = TextEditingController(text: '去,不去');
  await showDialog(
    context: context,
    builder: (ctx) => AlertDialog(
      title: const Text('创建接龙'),
      content: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          TextField(
            controller: titleController,
            decoration: const InputDecoration(labelText: '接龙标题'),
          ),
          const SizedBox(height: 12),
          TextField(
            controller: pointsController,
            decoration: const InputDecoration(
                labelText: '选项（逗号分隔）', hintText: '例：去,不去'),
          ),
        ],
      ),
      actions: [
        TextButton(
            onPressed: () => Navigator.pop(ctx), child: const Text('取消')),
        TextButton(
          onPressed: () async {
            final title = titleController.text.trim();
            if (title.isEmpty) return;
            final options = pointsController.text
                .split(',')
                .map((e) => e.trim())
                .where((e) => e.isNotEmpty)
                .toList();
            final msg = await context
                .read<AffairsProvider>()
                .createSignup(title: title, options: options);
            if (ctx.mounted) {
              Navigator.pop(ctx);
              if (context.mounted) _snack(context, msg);
            }
          },
          child: const Text('创建'),
        ),
      ],
    ),
  );
}

Future<void> _showImportDialog(BuildContext context, int signupId) async {
  final textController = TextEditingController(
      text: '张三 去\n李四 不去\n王五 去');
  await showDialog(
    context: context,
    builder: (ctx) => AlertDialog(
      title: const Text('导入接龙名单'),
      content: TextField(
        controller: textController,
        maxLines: 6,
        decoration: const InputDecoration(hintText: '粘贴接龙文本，AI 自动解析'),
      ),
      actions: [
        TextButton(
            onPressed: () => Navigator.pop(ctx), child: const Text('取消')),
        TextButton(
          onPressed: () async {
            final msg = await context
                .read<AffairsProvider>()
                .importSignup(signupId, textController.text);
            if (ctx.mounted) {
              Navigator.pop(ctx);
              if (context.mounted) _snack(context, msg);
            }
          },
          child: const Text('导入'),
        ),
      ],
    ),
  );
}

// ═══════════════ 班费台账 ═══════════════

class _LedgerTab extends StatefulWidget {
  const _LedgerTab();

  @override
  State<_LedgerTab> createState() => _LedgerTabState();
}

class _LedgerTabState extends State<_LedgerTab> {
  final _textController = TextEditingController(
      text: '8月1日 团建烧烤材料 -150.5\n8月3日 班费余额 200\n8月5日 打印奖状 12.5');

  @override
  void dispose() {
    _textController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final provider = context.watch<AffairsProvider>();
    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        Container(
          padding: const EdgeInsets.all(14),
          decoration: BoxDecoration(
            color: AppTheme.warningColor.withAlpha(8),
            borderRadius: BorderRadius.circular(12),
            border: Border.all(
                color: AppTheme.warningColor.withAlpha(40), width: 0.5),
          ),
          child: const Row(
            children: [
              Icon(Icons.lock_outline_rounded,
                  size: 16, color: AppTheme.warningColor),
              SizedBox(width: 8),
              Expanded(
                child: Text('演示模式：台账金额仅本地存储，展示打码为 ¥***（ADR §6）',
                    style: TextStyle(
                        fontSize: 12, color: AppTheme.warningColor)),
              ),
            ],
          ),
        ),
        const SizedBox(height: 12),
        TextField(
          controller: _textController,
          maxLines: 5,
          decoration: const InputDecoration(
            hintText: '粘贴台账 OCR 文本，AI 自动提取条目',
          ),
        ),
        const SizedBox(height: 12),
        Row(
          children: [
            Expanded(
              child: ElevatedButton.icon(
                onPressed: provider.isLoading
                    ? null
                    : () async {
                        final msg = await context
                            .read<AffairsProvider>()
                            .importLedger(_textController.text);
                        if (context.mounted) _snack(context, msg);
                      },
                icon: const Icon(Icons.table_view_rounded, size: 18),
                label: const Text('导入台账'),
              ),
            ),
            const SizedBox(width: 8),
            OutlinedButton.icon(
              onPressed: () async {
                final data = await ApiService().exportLedger();
                if (data['file_url'] != null) {
                  _snack(context, '已导出：${data['filename']}');
                }
              },
              icon: const Icon(Icons.download_rounded, size: 18),
              label: const Text('导出'),
            ),
          ],
        ),
        if (provider.ledgerAdded > 0) ...[
          const SizedBox(height: 16),
          Container(
            padding: const EdgeInsets.all(14),
            decoration: BoxDecoration(
              color: AppTheme.successColor.withAlpha(10),
              borderRadius: BorderRadius.circular(12),
            ),
            child: Text('本次导入 ${provider.ledgerAdded} 条条目（金额已打码）',
                style: const TextStyle(
                    fontSize: 13, color: AppTheme.successColor)),
          ),
        ],
      ],
    );
  }
}

void _snack(BuildContext context, String msg) {
  ScaffoldMessenger.of(context).showSnackBar(SnackBar(
    content: Text(msg),
    duration: const Duration(seconds: 2),
    behavior: SnackBarBehavior.floating,
  ));
}
