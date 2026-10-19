import 'package:file_picker/file_picker.dart';
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../../config/theme.dart';
import '../../providers/papers_provider.dart';
import '../../providers/task_progress_provider.dart';
import '../../widgets/empty_state.dart';

/// 科研论文库主页：文献列表 / 通俗讲解 / 单篇问答 / 文献对比 / 综述生成
class PapersPage extends StatefulWidget {
  const PapersPage({super.key});

  @override
  State<PapersPage> createState() => _PapersPageState();
}

class _PapersPageState extends State<PapersPage>
    with SingleTickerProviderStateMixin {
  late final TabController _tabController;
  final _qaQuestionController = TextEditingController();
  int? _qaDocumentId;
  final _explainQuestionController = TextEditingController();
  int? _explainDocumentId;

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 5, vsync: this);
    WidgetsBinding.instance.addPostFrameCallback((_) {
      context.read<PapersProvider>().loadPapers();
    });
  }

  @override
  void dispose() {
    _tabController.dispose();
    _qaQuestionController.dispose();
    _explainQuestionController.dispose();
    super.dispose();
  }

  void _goExplain(int id) {
    _explainDocumentId = id;
    _tabController.animateTo(1);
  }

  void _goQA(int id) {
    setState(() => _qaDocumentId = id);
    _tabController.animateTo(2);
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('科研论文库'),
        bottom: TabBar(
          controller: _tabController,
          isScrollable: true,
          tabAlignment: TabAlignment.start,
          tabs: const [
            Tab(text: '文献列表'),
            Tab(text: '通俗讲解'),
            Tab(text: '单篇问答'),
            Tab(text: '文献对比'),
            Tab(text: '综述生成'),
          ],
        ),
      ),
      body: TabBarView(
        controller: _tabController,
        children: [
          _PapersTab(
            onPickForExplain: _goExplain,
            onPickForQA: _goQA,
          ),
          _ExplainTab(questionController: _explainQuestionController),
          _QATab(
            questionController: _qaQuestionController,
            documentId: _qaDocumentId,
            onPickDocument: (id) => setState(() => _qaDocumentId = id),
          ),
          _CompareTab(),
          _ReviewTab(),
        ],
      ),
    );
  }
}

// ═══════════════ 文献列表 ═══════════════

class _PapersTab extends StatelessWidget {
  final void Function(int documentId) onPickForExplain;
  final void Function(int documentId) onPickForQA;
  const _PapersTab({
    required this.onPickForExplain,
    required this.onPickForQA,
  });

  @override
  Widget build(BuildContext context) {
    final provider = context.watch<PapersProvider>();
    return Column(
      children: [
        Padding(
          padding: const EdgeInsets.fromLTRB(16, 16, 16, 8),
          child: Row(
            children: [
              Expanded(
                child: Text(
                  '共 ${provider.papers.length} 篇 · AI 自动抽取题录',
                  style: const TextStyle(
                      fontSize: 13, color: AppTheme.textSecondary),
                ),
              ),
              ElevatedButton.icon(
                onPressed: () => _pickAndUpload(context),
                icon: const Icon(Icons.upload_file_rounded, size: 18),
                label: const Text('上传论文'),
              ),
            ],
          ),
        ),
        Expanded(
          child: provider.papers.isEmpty
              ? const EmptyState(
                  icon: Icons.menu_book_outlined,
                  message: '文献库为空\n上传 PDF/Word 论文，自动抽取题录元数据',
                )
              : ListView.builder(
                  padding: const EdgeInsets.fromLTRB(16, 4, 16, 24),
                  itemCount: provider.papers.length,
                  itemBuilder: (context, index) {
                    final p = provider.papers[index];
                    return Container(
                      margin: const EdgeInsets.only(bottom: 10),
                      padding: const EdgeInsets.all(14),
                      decoration: BoxDecoration(
                        color: Colors.white,
                        borderRadius: BorderRadius.circular(14),
                        border: Border.all(
                            color: AppTheme.borderColor, width: 0.5),
                      ),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Row(
                            children: [
                              Expanded(
                                child: Text(
                                  p.title,
                                  style: const TextStyle(
                                      fontWeight: FontWeight.w600,
                                      fontSize: 14,
                                      height: 1.4),
                                ),
                              ),
                              if (p.metaStatus == 'manual')
                                Container(
                                  padding: const EdgeInsets.symmetric(
                                      horizontal: 8, vertical: 2),
                                  decoration: BoxDecoration(
                                    color: AppTheme.warningColor.withAlpha(15),
                                    borderRadius: BorderRadius.circular(6),
                                  ),
                                  child: const Text('已人工校订',
                                      style: TextStyle(
                                          fontSize: 10,
                                          color: AppTheme.warningColor)),
                                ),
                            ],
                          ),
                          const SizedBox(height: 6),
                          Text(
                            [p.authors, p.journal, p.year?.toString()]
                                .where((e) => e != null && e.isNotEmpty)
                                .join(' · '),
                            maxLines: 1,
                            overflow: TextOverflow.ellipsis,
                            style: const TextStyle(
                                fontSize: 12,
                                color: AppTheme.textSecondary),
                          ),
                          const SizedBox(height: 10),
                          Row(
                            children: [
                              _SmallAction(
                                icon: Icons.school_outlined,
                                label: '讲解',
                                onTap: () => onPickForExplain(p.documentId),
                              ),
                              const SizedBox(width: 8),
                              _SmallAction(
                                icon: Icons.question_answer_outlined,
                                label: '问答',
                                onTap: () => onPickForQA(p.documentId),
                              ),
                            ],
                          ),
                        ],
                      ),
                    );
                  },
                ),
        ),
      ],
    );
  }
}

class _SmallAction extends StatelessWidget {
  final IconData icon;
  final String label;
  final VoidCallback onTap;
  const _SmallAction(
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

Future<void> _pickAndUpload(BuildContext context) async {
  try {
    final result = await FilePicker.platform.pickFiles(
      type: FileType.custom,
      allowedExtensions: ['pdf', 'doc', 'docx', 'txt'],
    );
    if (result == null || result.files.isEmpty) return;
    final file = result.files.first;
    final bytes = file.bytes;
    if (bytes == null) {
      _snack(context, '无法读取文件内容，请重试');
      return;
    }
    final msg = await context
        .read<PapersProvider>()
        .uploadPaper(bytes, file.name, title: file.name);
    if (context.mounted) _snack(context, msg);
  } catch (e) {
    _snack(context, '选择文件失败: $e');
  }
}

// ═══════════════ 通俗讲解 ═══════════════

class _ExplainTab extends StatelessWidget {
  final TextEditingController questionController;
  const _ExplainTab({required this.questionController});

  @override
  Widget build(BuildContext context) {
    final provider = context.watch<PapersProvider>();
    final tasks = context.watch<TaskProgressProvider>();
    return Column(
      children: [
        Padding(
          padding: const EdgeInsets.fromLTRB(16, 16, 16, 8),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const Text('选择一篇论文，AI 用通俗语言分步讲解核心内容',
                  style: TextStyle(
                      fontSize: 13, color: AppTheme.textSecondary)),
              const SizedBox(height: 12),
              _PaperPicker(
                onPick: (id) async {
                  final taskId = await provider.explainPaper(id);
                  if (taskId != null && context.mounted) {
                    context.read<TaskProgressProvider>().watchTask(taskId);
                  }
                },
              ),
            ],
          ),
        ),
        Expanded(
          child: provider.explainParts.isEmpty
              ? const EmptyState(
                  icon: Icons.menu_book_outlined,
                  message: '选择论文后生成通俗讲解')
              : ListView(
                  padding: const EdgeInsets.fromLTRB(16, 4, 16, 24),
                  children: [
                    if (tasks.activeCount > 0)
                      Container(
                        padding: const EdgeInsets.all(12),
                        decoration: BoxDecoration(
                          color: AppTheme.primaryLight,
                          borderRadius: BorderRadius.circular(12),
                        ),
                        child: const Row(
                          children: [
                            SizedBox(
                              width: 18,
                              height: 18,
                              child: CircularProgressIndicator(strokeWidth: 2),
                            ),
                            SizedBox(width: 12),
                            Text('AI 讲解中...',
                                style: TextStyle(
                                    fontSize: 13,
                                    color: AppTheme.primaryColor)),
                          ],
                        ),
                      ),
                    ...provider.explainParts.map((part) => Container(
                          margin: const EdgeInsets.only(bottom: 10),
                          padding: const EdgeInsets.all(14),
                          decoration: BoxDecoration(
                            color: Colors.white,
                            borderRadius: BorderRadius.circular(12),
                            border: Border.all(
                                color: AppTheme.borderColor, width: 0.5),
                          ),
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Text(part.title,
                                  style: const TextStyle(
                                      fontWeight: FontWeight.w600,
                                      fontSize: 14)),
                              const SizedBox(height: 6),
                              Text(part.content,
                                  style: const TextStyle(
                                      fontSize: 13, height: 1.6)),
                            ],
                          ),
                        )),
                  ],
                ),
        ),
      ],
    );
  }
}

// ═══════════════ 单篇问答 ═══════════════

class _QATab extends StatelessWidget {
  final TextEditingController questionController;
  final int? documentId;
  final void Function(int documentId) onPickDocument;
  const _QATab({
    required this.questionController,
    required this.documentId,
    required this.onPickDocument,
  });

  @override
  Widget build(BuildContext context) {
    final provider = context.watch<PapersProvider>();
    return Column(
      children: [
        Padding(
          padding: const EdgeInsets.fromLTRB(16, 16, 16, 8),
          child: Column(
            children: [
              const Text('基于单篇论文上下文回答，带来源引用',
                  style: TextStyle(
                      fontSize: 13, color: AppTheme.textSecondary)),
              const SizedBox(height: 12),
              _PaperPicker(
                onPick: onPickDocument,
              ),
              const SizedBox(height: 12),
              Row(
                children: [
                  Expanded(
                    child: TextField(
                      controller: questionController,
                      decoration: const InputDecoration(
                        hintText: '输入关于论文的问题...',
                        isDense: true,
                      ),
                    ),
                  ),
                  const SizedBox(width: 8),
                  ElevatedButton(
                    onPressed: () {
                      final q = questionController.text.trim();
                      final docId = documentId;
                      if (q.isEmpty) return;
                      if (docId == null) {
                        _snack(context, '请先选择论文');
                        return;
                      }
                      provider.askPaper(docId, q);
                    },
                    child: const Text('提问'),
                  ),
                ],
              ),
            ],
          ),
        ),
        Expanded(
          child: provider.qaAnswer.isEmpty
              ? const EmptyState(
                  icon: Icons.help_outline_rounded, message: '还没有提问')
              : ListView(
                  padding: const EdgeInsets.fromLTRB(16, 4, 16, 24),
                  children: [
                    Container(
                      padding: const EdgeInsets.all(14),
                      decoration: BoxDecoration(
                        color: AppTheme.primaryLight,
                        borderRadius: BorderRadius.circular(12),
                      ),
                      child: Text(provider.qaAnswer,
                          style: const TextStyle(
                              fontSize: 14, height: 1.6)),
                    ),
                    if (provider.qaCitations.isNotEmpty) ...[
                      const SizedBox(height: 12),
                      Text('来源引用（${provider.qaCitations.length}）',
                          style: const TextStyle(
                              fontSize: 12,
                              color: AppTheme.textSecondary)),
                      const SizedBox(height: 6),
                      ...provider.qaCitations.map((c) => Container(
                            margin: const EdgeInsets.only(bottom: 6),
                            padding: const EdgeInsets.all(10),
                            decoration: BoxDecoration(
                              color: Colors.white,
                              borderRadius: BorderRadius.circular(10),
                              border: Border.all(
                                  color: AppTheme.borderColor, width: 0.5),
                            ),
                            child: Text(
                                '切片 #${c.chunkId} · 置信度 ${(c.confidence * 100).toStringAsFixed(0)}%',
                                style: const TextStyle(fontSize: 12)),
                          )),
                    ],
                  ],
                ),
        ),
      ],
    );
  }
}

// ═══════════════ 文献对比 ═══════════════

class _CompareTab extends StatefulWidget {
  @override
  State<_CompareTab> createState() => _CompareTabState();
}

class _CompareTabState extends State<_CompareTab> {
  final Set<int> _selected = {};

  @override
  Widget build(BuildContext context) {
    final provider = context.watch<PapersProvider>();
    return Column(
      children: [
        Padding(
          padding: const EdgeInsets.fromLTRB(16, 16, 16, 8),
          child: Row(
            children: [
              Expanded(
                child: Text(
                  '勾选 ≥2 篇论文，多维度对比',
                  style: const TextStyle(
                      fontSize: 13, color: AppTheme.textSecondary),
                ),
              ),
              ElevatedButton.icon(
                onPressed: _selected.length >= 2
                    ? () => context
                        .read<PapersProvider>()
                        .comparePapers(_selected.toList())
                    : null,
                icon: const Icon(Icons.compare_arrows_rounded, size: 18),
                label: Text('对比${_selected.isEmpty ? '' : '(${_selected.length})'}'),
              ),
            ],
          ),
        ),
        Expanded(
          child: provider.papers.isEmpty
              ? const EmptyState(icon: Icons.compare_arrows_rounded, message: '暂无论文')
              : ListView(
                  padding: const EdgeInsets.fromLTRB(16, 4, 16, 24),
                  children: [
                    ...provider.papers.map((p) => CheckboxListTile(
                          value: _selected.contains(p.documentId),
                          onChanged: (v) => setState(() {
                            if (v == true) {
                              _selected.add(p.documentId);
                            } else {
                              _selected.remove(p.documentId);
                            }
                          }),
                          title: Text(p.title,
                              style: const TextStyle(
                                  fontSize: 13, fontWeight: FontWeight.w500)),
                          subtitle: Text(p.journal ?? '',
                              style: const TextStyle(fontSize: 11)),
                          controlAffinity: ListTileControlAffinity.leading,
                        )),
                    if (provider.compareTable.columns.isNotEmpty) ...[
                      const SizedBox(height: 8),
                      _CompareTable(table: provider.compareTable),
                    ],
                  ],
                ),
        ),
      ],
    );
  }
}

class _CompareTable extends StatelessWidget {
  final dynamic table;
  const _CompareTable({required this.table});

  @override
  Widget build(BuildContext context) {
    return SingleChildScrollView(
      scrollDirection: Axis.horizontal,
      child: Table(
        border: TableBorder.all(color: AppTheme.borderColor, width: 0.5),
        defaultColumnWidth: const IntrinsicColumnWidth(),
        children: [
          TableRow(
            decoration: const BoxDecoration(color: AppTheme.primaryLight),
            children: table.columns
                .map((c) => Padding(
                      padding: const EdgeInsets.all(10),
                      child: Text(c,
                          style: const TextStyle(
                              fontWeight: FontWeight.w600, fontSize: 12)),
                    ))
                .toList(),
          ),
          ...table.rows.map((row) => TableRow(
                children: (row as List)
                    .map((cell) => Padding(
                          padding: const EdgeInsets.all(10),
                          child: Text(cell.toString(),
                              style: const TextStyle(
                                  fontSize: 12, height: 1.4)),
                        ))
                    .toList(),
              )),
        ],
      ),
    );
  }
}

// ═══════════════ 综述生成 ═══════════════

class _ReviewTab extends StatefulWidget {
  @override
  State<_ReviewTab> createState() => _ReviewTabState();
}

class _ReviewTabState extends State<_ReviewTab> {
  final Set<int> _selected = {};

  @override
  Widget build(BuildContext context) {
    final provider = context.watch<PapersProvider>();
    final tasks = context.watch<TaskProgressProvider>();
    return Column(
      children: [
        Padding(
          padding: const EdgeInsets.fromLTRB(16, 16, 16, 8),
          child: Row(
            children: [
              Expanded(
                child: Text(
                  '选择论文，AI 分章节撰写综述（逐句引用）',
                  style: const TextStyle(
                      fontSize: 13, color: AppTheme.textSecondary),
                ),
              ),
              ElevatedButton.icon(
                onPressed: _selected.isEmpty
                    ? null
                    : () async {
                        final taskId = await context
                            .read<PapersProvider>()
                            .generateReview(_selected.toList());
                        if (taskId != null && context.mounted) {
                          context
                              .read<TaskProgressProvider>()
                              .watchTask(taskId);
                        }
                      },
                icon: const Icon(Icons.auto_stories_rounded, size: 18),
                label: const Text('生成综述'),
              ),
            ],
          ),
        ),
        Expanded(
          child: provider.papers.isEmpty
              ? const EmptyState(icon: Icons.auto_stories_rounded, message: '暂无论文')
              : ListView(
                  padding: const EdgeInsets.fromLTRB(16, 4, 16, 24),
                  children: [
                    ...provider.papers.map((p) => CheckboxListTile(
                          value: _selected.contains(p.documentId),
                          onChanged: (v) => setState(() {
                            if (v == true) {
                              _selected.add(p.documentId);
                            } else {
                              _selected.remove(p.documentId);
                            }
                          }),
                          title: Text(p.title,
                              style: const TextStyle(
                                  fontSize: 13, fontWeight: FontWeight.w500)),
                          controlAffinity: ListTileControlAffinity.leading,
                        )),
                    if (provider.reviewSections.isNotEmpty) ...[
                      const SizedBox(height: 8),
                      if (tasks.activeCount > 0)
                        Container(
                          padding: const EdgeInsets.all(12),
                          decoration: BoxDecoration(
                            color: AppTheme.primaryLight,
                            borderRadius: BorderRadius.circular(12),
                          ),
                          child: const Row(
                            children: [
                              SizedBox(
                                width: 18,
                                height: 18,
                                child:
                                    CircularProgressIndicator(strokeWidth: 2),
                              ),
                              SizedBox(width: 12),
                              Text('综述撰写中...',
                                  style: TextStyle(
                                      fontSize: 13,
                                      color: AppTheme.primaryColor)),
                            ],
                          ),
                        ),
                      ...provider.reviewSections.map((sec) => Container(
                            margin: const EdgeInsets.only(bottom: 10),
                            padding: const EdgeInsets.all(14),
                            decoration: BoxDecoration(
                              color: Colors.white,
                              borderRadius: BorderRadius.circular(12),
                              border: Border.all(
                                  color: AppTheme.borderColor, width: 0.5),
                            ),
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Text(sec.title,
                                    style: const TextStyle(
                                        fontWeight: FontWeight.w600,
                                        fontSize: 14)),
                                const SizedBox(height: 6),
                                Text(sec.content,
                                    style: const TextStyle(
                                        fontSize: 13, height: 1.6)),
                              ],
                            ),
                          )),
                    ],
                  ],
                ),
        ),
      ],
    );
  }
}

// ═══════════════ 论文选择器 ═══════════════

class _PaperPicker extends StatelessWidget {
  final void Function(int documentId) onPick;
  const _PaperPicker({required this.onPick});

  @override
  Widget build(BuildContext context) {
    final provider = context.watch<PapersProvider>();
    if (provider.papers.isEmpty) {
      return const Align(
        alignment: Alignment.centerLeft,
        child: Text('请先在「文献列表」上传或加载论文',
            style: TextStyle(
                fontSize: 12, color: AppTheme.textTertiary)),
      );
    }
    return Wrap(
      spacing: 8,
      runSpacing: 8,
      children: provider.papers
          .map((p) => ActionChip(
                label: Text(p.title,
                    style: const TextStyle(fontSize: 12)),
                onPressed: () => onPick(p.documentId),
              ))
          .toList(),
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
