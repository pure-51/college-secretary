import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../../config/theme.dart';
import '../../providers/knowledge_provider.dart';
import '../../widgets/empty_state.dart';
import '../../widgets/loading_indicator.dart';
import 'file_upload_page.dart';
import 'document_detail_page.dart';

class KnowledgePage extends StatefulWidget {
  const KnowledgePage({super.key});

  @override
  State<KnowledgePage> createState() => _KnowledgePageState();
}

class _KnowledgePageState extends State<KnowledgePage> {
  final _searchController = TextEditingController();
  String _selectedCategory = '全部';

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      context.read<KnowledgeProvider>().loadDocuments();
    });
  }

  @override
  void dispose() {
    _searchController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('知识库')),
      body: Consumer<KnowledgeProvider>(
        builder: (context, provider, _) {
          final displayList = provider.searchResults.isNotEmpty
              ? provider.searchResults
              : provider.documents;
          final isEmpty =
              provider.documents.isEmpty && provider.searchResults.isEmpty;

          return Column(
            children: [
              // ── 搜索栏 ──
              Padding(
                padding: const EdgeInsets.fromLTRB(16, 16, 16, 8),
                child: TextField(
                  controller: _searchController,
                  decoration: InputDecoration(
                    hintText: '搜索所有通知和政策文件...',
                    prefixIcon: const Icon(Icons.search_rounded),
                    suffixIcon: IconButton(
                      icon: const Icon(Icons.send_rounded, size: 18),
                      onPressed: () =>
                          provider.search(_searchController.text),
                    ),
                  ),
                  onSubmitted: (query) => provider.search(query),
                ),
              ),

              // ── 分类标签 ──
              SizedBox(
                height: 36,
                child: ListView(
                  scrollDirection: Axis.horizontal,
                  padding: const EdgeInsets.symmetric(horizontal: 16),
                  children: ['全部', '教务', '学工', '社团', '政策文件']
                      .map((label) => Padding(
                            padding: const EdgeInsets.only(right: 8),
                            child: GestureDetector(
                              onTap: () => setState(() => _selectedCategory = label),
                              child: AnimatedContainer(
                                duration: const Duration(milliseconds: 200),
                                padding: const EdgeInsets.symmetric(
                                    horizontal: 14, vertical: 6),
                                decoration: BoxDecoration(
                                  color: _selectedCategory == label
                                      ? AppTheme.primaryLight
                                      : const Color(0xFFF3F4F6),
                                  borderRadius: BorderRadius.circular(8),
                                ),
                                child: Text(
                                  label,
                                  style: TextStyle(
                                    fontSize: 13,
                                    fontWeight: _selectedCategory == label
                                        ? FontWeight.w600
                                        : FontWeight.w400,
                                    color: _selectedCategory == label
                                        ? AppTheme.primaryColor
                                        : AppTheme.textSecondary,
                                  ),
                                ),
                              ),
                            ),
                          ))
                      .toList(),
                ),
              ),
              const SizedBox(height: 4),

              // ── 内容列表 ──
              Expanded(
                child: provider.isLoading
                    ? const SkeletonLoader()
                    : isEmpty
                        ? EmptyState(
                            icon: Icons.menu_book_outlined,
                            message: '知识库为空',
                            actionLabel: '上传文件',
                            onAction: () => _uploadFile(context),
                          )
                        : RefreshIndicator(
                            onRefresh: () => provider.loadDocuments(),
                            child: ListView.builder(
                              padding:
                                  const EdgeInsets.fromLTRB(16, 8, 16, 80),
                              itemCount: displayList.length,
                              itemBuilder: (context, index) {
                                final item = displayList[index];
                                final isPdf =
                                    item['file_type'] == 'pdf';
                                final iconColor =
                                    isPdf ? AppTheme.errorColor : AppTheme.primaryColor;
                                final icon = isPdf
                                    ? Icons.picture_as_pdf
                                    : Icons.description_rounded;

                                return GestureDetector(
                                  onTap: () => Navigator.push(
                                    context,
                                    MaterialPageRoute(
                                      builder: (_) =>
                                          DocumentDetailPage(document: item),
                                    ),
                                  ),
                                  child: AnimatedContainer(
                                    duration: const Duration(milliseconds: 200),
                                    margin: const EdgeInsets.only(bottom: 10),
                                    decoration: BoxDecoration(
                                      color: Colors.white,
                                      borderRadius: BorderRadius.circular(14),
                                      border: Border.all(
                                          color: AppTheme.borderColor,
                                          width: 0.5),
                                    ),
                                    child: Padding(
                                      padding: const EdgeInsets.all(14),
                                      child: Row(
                                        children: [
                                          Container(
                                            width: 44,
                                            height: 44,
                                            decoration: BoxDecoration(
                                              color: iconColor.withAlpha(15),
                                              borderRadius:
                                                  BorderRadius.circular(12),
                                            ),
                                            child: Icon(icon,
                                                size: 22, color: iconColor),
                                          ),
                                          const SizedBox(width: 12),
                                          Expanded(
                                            child: Column(
                                              crossAxisAlignment:
                                                  CrossAxisAlignment.start,
                                              children: [
                                                Text(
                                                  item['title'] ?? '未命名',
                                                  style: const TextStyle(
                                                    fontWeight: FontWeight.w500,
                                                    fontSize: 14,
                                                    color: AppTheme.textPrimary,
                                                  ),
                                                ),
                                                const SizedBox(height: 4),
                                                Text(
                                                  item['summary'] ??
                                                      item['file_type'] ?? '',
                                                  maxLines: 2,
                                                  overflow:
                                                      TextOverflow.ellipsis,
                                                  style: const TextStyle(
                                                    fontSize: 12,
                                                    color: AppTheme.textSecondary,
                                                  ),
                                                ),
                                              ],
                                            ),
                                          ),
                                          Icon(
                                            Icons.chevron_right_rounded,
                                            size: 20,
                                            color:
                                                AppTheme.textTertiary.withAlpha(120),
                                          ),
                                        ],
                                      ),
                                    ),
                                  ),
                                );
                              },
                            ),
                          ),
              ),
            ],
          );
        },
      ),
      floatingActionButton: FloatingActionButton(
        onPressed: () => _uploadFile(context),
        child: const Icon(Icons.upload_file_rounded),
      ),
    );
  }

  void _uploadFile(BuildContext context) {
    Navigator.push(
      context,
      MaterialPageRoute(builder: (_) => const FileUploadPage()),
    );
  }
}
