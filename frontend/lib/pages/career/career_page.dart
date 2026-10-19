import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../../config/theme.dart';
import '../../providers/career_provider.dart';
import '../../providers/task_progress_provider.dart';
import '../../widgets/empty_state.dart';
import '../../widgets/loading_indicator.dart';

/// 生涯档案官主页：档案库 / 完整性体检 / 简历生成 / 面试模拟 / 保研节点
class CareerPage extends StatefulWidget {
  const CareerPage({super.key});

  @override
  State<CareerPage> createState() => _CareerPageState();
}

class _CareerPageState extends State<CareerPage>
    with SingleTickerProviderStateMixin {
  late final TabController _tabController;
  final _directionController = TextEditingController(text: '保研-计算机');

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 5, vsync: this);
    WidgetsBinding.instance.addPostFrameCallback((_) {
      final p = context.read<CareerProvider>();
      p.loadArchiveRecords();
      p.loadHealth();
      p.loadMilestones();
    });
  }

  @override
  void dispose() {
    _tabController.dispose();
    _directionController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('生涯档案官'),
        bottom: TabBar(
          controller: _tabController,
          isScrollable: true,
          tabAlignment: TabAlignment.start,
          tabs: const [
            Tab(text: '档案库'),
            Tab(text: '完整性体检'),
            Tab(text: '简历生成'),
            Tab(text: '面试模拟'),
            Tab(text: '保研节点'),
          ],
        ),
      ),
      body: TabBarView(
        controller: _tabController,
        children: [
          _ArchiveTab(),
          _HealthTab(),
          _ResumeTab(directionController: _directionController),
          _InterviewTab(directionController: _directionController),
          _MilestonesTab(),
        ],
      ),
    );
  }
}

// ═══════════════ 档案库 ═══════════════

class _ArchiveTab extends StatelessWidget {
  final _rawTextController = TextEditingController();

  @override
  Widget build(BuildContext context) {
    final provider = context.watch<CareerProvider>();
    return Column(
      children: [
        // ── 归档录入 ──
        Padding(
          padding: const EdgeInsets.fromLTRB(16, 16, 16, 8),
          child: Row(
            children: [
              Expanded(
                child: TextField(
                  controller: _rawTextController,
                  decoration: InputDecoration(
                    hintText: '粘贴证书/通知文本，AI 自动归档...',
                    isDense: true,
                  ),
                ),
              ),
              const SizedBox(width: 8),
              ElevatedButton(
                onPressed: () async {
                  final text = _rawTextController.text.trim();
                  if (text.isEmpty) return;
                  final msg = await context
                      .read<CareerProvider>()
                      .createArchiveRecord(text);
                  _rawTextController.clear();
                  if (context.mounted) {
                    _snack(context, msg);
                  }
                },
                child: const Text('归档'),
              ),
            ],
          ),
        ),
        // ── 列表 ──
        Expanded(
          child: provider.records.isEmpty
              ? const EmptyState(
                  icon: Icons.folder_shared_outlined,
                  message: '暂无档案\n粘贴一条通知或证书文本，AI 自动结构化归档',
                )
              : ListView.builder(
                  padding: const EdgeInsets.fromLTRB(16, 4, 16, 24),
                  itemCount: provider.records.length,
                  itemBuilder: (context, index) =>
                      _ArchiveCard(record: provider.records[index]),
                ),
        ),
      ],
    );
  }
}

class _ArchiveCard extends StatelessWidget {
  final dynamic record;
  const _ArchiveCard({required this.record});

  @override
  Widget build(BuildContext context) {
    final iconColor = record.recordStatus == 'pending'
        ? AppTheme.warningColor
        : AppTheme.successColor;
    final statusLabel = record.recordStatus == 'pending' ? '待确认' : '已确认';
    return Container(
      margin: const EdgeInsets.only(bottom: 10),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(14),
        border: Border.all(color: AppTheme.borderColor, width: 0.5),
      ),
      child: Padding(
        padding: const EdgeInsets.all(14),
        child: Row(
          children: [
            Container(
              width: 40,
              height: 40,
              decoration: BoxDecoration(
                color: AppTheme.primaryLight,
                borderRadius: BorderRadius.circular(10),
              ),
              child: const Icon(Icons.verified_rounded,
                  color: AppTheme.primaryColor, size: 20),
            ),
            const SizedBox(width: 12),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    children: [
                      Expanded(
                        child: Text(
                          record.title,
                          style: const TextStyle(
                              fontWeight: FontWeight.w600, fontSize: 14),
                        ),
                      ),
                      _TypeChip(label: record.typeLabel),
                    ],
                  ),
                  const SizedBox(height: 4),
                  Text(
                    record.fields.toString().substring(0,
                        (record.fields.toString().length < 60)
                            ? record.fields.toString().length
                            : 60),
                    maxLines: 2,
                    overflow: TextOverflow.ellipsis,
                    style: const TextStyle(
                        fontSize: 12, color: AppTheme.textSecondary),
                  ),
                ],
              ),
            ),
            Column(
              children: [
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                  decoration: BoxDecoration(
                    color: iconColor.withAlpha(15),
                    borderRadius: BorderRadius.circular(6),
                  ),
                  child: Text(statusLabel,
                      style: TextStyle(
                          fontSize: 11,
                          color: iconColor,
                          fontWeight: FontWeight.w600)),
                ),
                const SizedBox(height: 4),
                IconButton(
                  icon: const Icon(Icons.check_circle_outline_rounded,
                      size: 18, color: AppTheme.successColor),
                  tooltip: '确认落库',
                  onPressed: record.recordStatus == 'pending'
                      ? () async {
                          final msg = await context
                              .read<CareerProvider>()
                              .updateArchiveRecord(record.id, {
                            'record_status': 'confirmed'
                          });
                          if (context.mounted) _snack(context, msg);
                        }
                      : null,
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }
}

class _TypeChip extends StatelessWidget {
  final String label;
  const _TypeChip({required this.label});

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
      decoration: BoxDecoration(
        color: AppTheme.primaryLight,
        borderRadius: BorderRadius.circular(6),
      ),
      child: Text(label,
          style: const TextStyle(
              fontSize: 10,
              color: AppTheme.primaryColor,
              fontWeight: FontWeight.w500)),
    );
  }
}

// ═══════════════ 完整性体检 ═══════════════

class _HealthTab extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    final provider = context.watch<CareerProvider>();
    final dims = provider.healthDimensions;
    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        // ── 进度环 ──
        Container(
          padding: const EdgeInsets.all(20),
          decoration: BoxDecoration(
            color: Colors.white,
            borderRadius: BorderRadius.circular(16),
            border: Border.all(color: AppTheme.borderColor, width: 0.5),
          ),
          child: Row(
            children: [
              Stack(
                alignment: Alignment.center,
                children: [
                  SizedBox(
                    width: 76,
                    height: 76,
                    child: CircularProgressIndicator(
                      value: provider.healthProgress / 100,
                      strokeWidth: 8,
                      backgroundColor: const Color(0xFFF0F0F0),
                      color: provider.healthProgress == 100
                          ? AppTheme.successColor
                          : AppTheme.primaryColor,
                    ),
                  ),
                  Text('${provider.healthProgress}%',
                      style: const TextStyle(
                          fontSize: 18, fontWeight: FontWeight.w700)),
                ],
              ),
              const SizedBox(width: 20),
              const Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text('简历完整性体检',
                        style: TextStyle(
                            fontWeight: FontWeight.w600, fontSize: 16)),
                    SizedBox(height: 6),
                    Text('五项维度逐项检查：材料齐全且带证据链的维度计分。\n'
                        '缺口项可一键补传。',
                        style: TextStyle(
                            fontSize: 12,
                            color: AppTheme.textSecondary,
                            height: 1.5)),
                  ],
                ),
              ),
            ],
          ),
        ),
        const SizedBox(height: 16),
        // ── 维度列表 ──
        ...dims.map((d) => Container(
              margin: const EdgeInsets.only(bottom: 8),
              padding: const EdgeInsets.all(14),
              decoration: BoxDecoration(
                color: Colors.white,
                borderRadius: BorderRadius.circular(12),
                border: Border.all(color: AppTheme.borderColor, width: 0.5),
              ),
              child: Row(
                children: [
                  Icon(
                    d.filled
                        ? (d.evidence
                            ? Icons.verified_rounded
                            : Icons.check_circle_rounded)
                        : Icons.error_outline_rounded,
                    color: d.filled
                        ? (d.evidence
                            ? AppTheme.successColor
                            : AppTheme.warningColor)
                        : AppTheme.errorColor,
                    size: 22,
                  ),
                  const SizedBox(width: 12),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(d.field,
                            style: const TextStyle(
                                fontWeight: FontWeight.w500, fontSize: 14)),
                        const SizedBox(height: 2),
                        Text(
                          d.filled
                              ? (d.evidence ? '已填，含证据链' : '已填，缺证据链')
                              : (d.required ? '缺失（必需）' : '缺失（可选）'),
                          style: const TextStyle(
                              fontSize: 12, color: AppTheme.textSecondary),
                        ),
                      ],
                    ),
                  ),
                  if (!d.filled)
                    TextButton(
                      onPressed: () => _snack(context, '请到「档案库」粘贴对应材料'),
                      child: const Text('补传'),
                    ),
                ],
              ),
            )),
      ],
    );
  }
}

// ═══════════════ 简历生成 ═══════════════

class _ResumeTab extends StatelessWidget {
  final TextEditingController directionController;
  const _ResumeTab({required this.directionController});

  @override
  Widget build(BuildContext context) {
    final provider = context.watch<CareerProvider>();
    final tasks = context.watch<TaskProgressProvider>();
    return Column(
      children: [
        Padding(
          padding: const EdgeInsets.fromLTRB(16, 16, 16, 8),
          child: Row(
            children: [
              Expanded(
                child: TextField(
                  controller: directionController,
                  decoration: const InputDecoration(
                    labelText: '求职/升学方向',
                    isDense: true,
                  ),
                ),
              ),
              const SizedBox(width: 8),
              ElevatedButton.icon(
                onPressed: provider.isLoading
                    ? null
                    : () async {
                        final taskId = await context
                            .read<CareerProvider>()
                            .generateResume(
                                direction: directionController.text.trim());
                        if (taskId != null && context.mounted) {
                          context
                              .read<TaskProgressProvider>()
                              .watchTask(taskId);
                        }
                      },
                icon: const Icon(Icons.auto_awesome_rounded, size: 18),
                label: const Text('一键生成'),
              ),
            ],
          ),
        ),
        Expanded(
          child: provider.resumeSections.isEmpty
              ? const EmptyState(
                  icon: Icons.description_outlined,
                  message: '尚未生成简历\n点击「一键生成」，AI 基于档案逐条附证据链撰写',
                )
              : ListView(
                  padding: const EdgeInsets.fromLTRB(16, 4, 16, 24),
                  children: [
                    if (tasks.activeCount > 0) _TaskBanner(tasks: tasks),
                    ...provider.resumeSections.map((sec) => Container(
                          margin: const EdgeInsets.only(bottom: 12),
                          decoration: BoxDecoration(
                            color: Colors.white,
                            borderRadius: BorderRadius.circular(14),
                            border: Border.all(
                                color: AppTheme.borderColor, width: 0.5),
                          ),
                          child: Padding(
                            padding: const EdgeInsets.all(16),
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Text('【${sec.title}】',
                                    style: const TextStyle(
                                        fontWeight: FontWeight.w600,
                                        fontSize: 15)),
                                const SizedBox(height: 8),
                                ...sec.lines.map((line) => Padding(
                                      padding:
                                          const EdgeInsets.only(bottom: 6),
                                      child: Row(
                                        crossAxisAlignment:
                                            CrossAxisAlignment.start,
                                        children: [
                                          Icon(
                                            line.missing
                                                ? Icons.pending_rounded
                                                : Icons.verified_rounded,
                                            size: 16,
                                            color: line.missing
                                                ? AppTheme.warningColor
                                                : AppTheme.successColor,
                                          ),
                                          const SizedBox(width: 8),
                                          Expanded(
                                            child: Text(
                                              line.missing
                                                  ? '${line.text} 【待补充】'
                                                  : line.text,
                                              style: const TextStyle(
                                                  fontSize: 13, height: 1.5),
                                            ),
                                          ),
                                        ],
                                      ),
                                    )),
                              ],
                            ),
                          ),
                        )),
                  ],
                ),
        ),
      ],
    );
  }
}

// ═══════════════ 面试模拟 ═══════════════

class _InterviewTab extends StatelessWidget {
  final TextEditingController directionController;
  const _InterviewTab({required this.directionController});

  @override
  Widget build(BuildContext context) {
    final provider = context.watch<CareerProvider>();
    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        Row(
          children: [
            Expanded(
              child: Text(
                provider.interviewQuestions.isEmpty
                    ? 'AI 基于你的真实档案预测面试问题\n回答后逐维度点评'
                    : '基于档案生成的 ${provider.interviewQuestions.length} 道预测题',
                style: const TextStyle(
                    fontSize: 13, color: AppTheme.textSecondary, height: 1.5),
              ),
            ),
            ElevatedButton.icon(
              onPressed: provider.isLoading
                  ? null
                  : () => context
                      .read<CareerProvider>()
                      .loadInterviewQuestions(
                          direction: directionController.text.trim()),
              icon: const Icon(Icons.psychology_rounded, size: 18),
              label: const Text('生成问题'),
            ),
          ],
        ),
        const SizedBox(height: 16),
        if (provider.interviewQuestions.isEmpty)
          const EmptyState(
            icon: Icons.record_voice_over_outlined,
            message: '还没有预测题',
          )
        else
          ...provider.interviewQuestions.asMap().entries.map((e) => Container(
                margin: const EdgeInsets.only(bottom: 10),
                padding: const EdgeInsets.all(14),
                decoration: BoxDecoration(
                  color: Colors.white,
                  borderRadius: BorderRadius.circular(12),
                  border: Border.all(color: AppTheme.borderColor, width: 0.5),
                ),
                child: Row(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Container(
                      width: 28,
                      height: 28,
                      decoration: BoxDecoration(
                        color: AppTheme.primaryLight,
                        borderRadius: BorderRadius.circular(8),
                      ),
                      child: Center(
                        child: Text('${e.key + 1}',
                            style: const TextStyle(
                                fontSize: 12,
                                fontWeight: FontWeight.w700,
                                color: AppTheme.primaryColor)),
                      ),
                    ),
                    const SizedBox(width: 12),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(e.value.question,
                              style: const TextStyle(
                                  fontSize: 14,
                                  fontWeight: FontWeight.w500,
                                  height: 1.5)),
                          const SizedBox(height: 4),
                          Text('考察点：${e.value.focus}',
                              style: const TextStyle(
                                  fontSize: 12,
                                  color: AppTheme.textTertiary)),
                        ],
                      ),
                    ),
                  ],
                ),
              )),
        if (provider.interviewFeedback != null) ...[
          const SizedBox(height: 16),
          Container(
            padding: const EdgeInsets.all(16),
            decoration: BoxDecoration(
              color: AppTheme.successColor.withAlpha(10),
              borderRadius: BorderRadius.circular(14),
              border: Border.all(
                  color: AppTheme.successColor.withAlpha(60), width: 0.5),
            ),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Text('模拟点评',
                    style: TextStyle(
                        fontWeight: FontWeight.w600, fontSize: 15)),
                const SizedBox(height: 8),
                _ScoreRow(label: '表达', score: provider.interviewFeedback!.score['expression'] ?? 0),
                _ScoreRow(label: '专业', score: provider.interviewFeedback!.score['professional'] ?? 0),
                _ScoreRow(label: '逻辑', score: provider.interviewFeedback!.score['logic'] ?? 0),
                _ScoreRow(label: '匹配', score: provider.interviewFeedback!.score['fit'] ?? 0),
                const SizedBox(height: 8),
                Text(provider.interviewFeedback!.feedback,
                    style: const TextStyle(fontSize: 13, height: 1.5)),
                const SizedBox(height: 4),
                Text('建议：${provider.interviewFeedback!.advice}',
                    style: const TextStyle(
                        fontSize: 12, color: AppTheme.textSecondary)),
              ],
            ),
          ),
        ],
      ],
    );
  }
}

class _ScoreRow extends StatelessWidget {
  final String label;
  final double score;
  const _ScoreRow({required this.label, required this.score});

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 2),
      child: Row(
        children: [
          SizedBox(
            width: 36,
            child: Text(label,
                style: const TextStyle(
                    fontSize: 12, color: AppTheme.textSecondary)),
          ),
          Expanded(
            child: ClipRRect(
              borderRadius: BorderRadius.circular(4),
              child: LinearProgressIndicator(
                value: score / 10,
                minHeight: 6,
                backgroundColor: Colors.white,
                color: AppTheme.primaryColor,
              ),
            ),
          ),
          const SizedBox(width: 8),
          Text('${score.toStringAsFixed(1)}',
              style: const TextStyle(fontSize: 12, fontWeight: FontWeight.w600)),
        ],
      ),
    );
  }
}

// ═══════════════ 保研节点 ═══════════════

class _MilestonesTab extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    final provider = context.watch<CareerProvider>();
    return provider.milestones.isEmpty
        ? const EmptyState(
            icon: Icons.route_outlined,
            message: '暂无保研关键节点',
          )
        : ListView.builder(
            padding: const EdgeInsets.all(16),
            itemCount: provider.milestones.length,
            itemBuilder: (context, index) {
              final m = provider.milestones[index];
              return Container(
                margin: const EdgeInsets.only(bottom: 10),
                padding: const EdgeInsets.all(14),
                decoration: BoxDecoration(
                  color: Colors.white,
                  borderRadius: BorderRadius.circular(12),
                  border:
                      Border.all(color: AppTheme.borderColor, width: 0.5),
                ),
                child: Row(
                  children: [
                    Container(
                      width: 36,
                      height: 36,
                      decoration: BoxDecoration(
                        color: AppTheme.primaryLight,
                        borderRadius: BorderRadius.circular(10),
                      ),
                      child: const Icon(Icons.flag_rounded,
                          color: AppTheme.primaryColor, size: 18),
                    ),
                    const SizedBox(width: 12),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(m.content,
                              style: const TextStyle(
                                  fontWeight: FontWeight.w500, fontSize: 14)),
                          if (m.deadline != null) ...[
                            const SizedBox(height: 4),
                            Text('截止 ${_fmtDate(m.deadline!)}',
                                style: const TextStyle(
                                    fontSize: 12,
                                    color: AppTheme.textSecondary)),
                          ],
                        ],
                      ),
                    ),
                    Container(
                      padding: const EdgeInsets.symmetric(
                          horizontal: 8, vertical: 3),
                      decoration: BoxDecoration(
                        color: m.status == 'completed'
                            ? AppTheme.successColor.withAlpha(15)
                            : AppTheme.primaryLight,
                        borderRadius: BorderRadius.circular(6),
                      ),
                      child: Text(m.status == 'completed' ? '已完成' : '进行中',
                          style: TextStyle(
                              fontSize: 11,
                              color: m.status == 'completed'
                                  ? AppTheme.successColor
                                  : AppTheme.primaryColor,
                              fontWeight: FontWeight.w600)),
                    ),
                  ],
                ),
              );
            },
          );
  }
}

// ═══════════════ 任务进度横幅 ═══════════════

class _TaskBanner extends StatelessWidget {
  final TaskProgressProvider tasks;
  const _TaskBanner({required this.tasks});

  @override
  Widget build(BuildContext context) {
    final first = tasks.tasks.values.where((t) => t.isRunning).firstOrNull;
    return Container(
      margin: const EdgeInsets.only(bottom: 12),
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: AppTheme.primaryLight,
        borderRadius: BorderRadius.circular(12),
      ),
      child: Row(
        children: [
          const SizedBox(
            width: 18,
            height: 18,
            child: CircularProgressIndicator(strokeWidth: 2),
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Text(first == null
                ? 'AI 处理中...'
                : '${first.skillName} · ${first.progress}%',
                style: const TextStyle(
                    fontSize: 13, color: AppTheme.primaryColor)),
          ),
        ],
      ),
    );
  }
}

// ═══════════════ 工具 ═══════════════

String _fmtDate(String iso) {
  try {
    final dt = DateTime.parse(iso);
    return '${dt.month}月${dt.day}日';
  } catch (_) {
    return iso;
  }
}

void _snack(BuildContext context, String msg) {
  ScaffoldMessenger.of(context).showSnackBar(SnackBar(
    content: Text(msg),
    duration: const Duration(seconds: 2),
    behavior: SnackBarBehavior.floating,
  ));
}
