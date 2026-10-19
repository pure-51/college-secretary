import 'package:flutter/material.dart';
import '../../services/api_service.dart';

class DocumentDetailPage extends StatefulWidget {
  final Map<String, dynamic> document;

  const DocumentDetailPage({super.key, required this.document});

  @override
  State<DocumentDetailPage> createState() => _DocumentDetailPageState();
}

class _DocumentDetailPageState extends State<DocumentDetailPage> {
  final _questionController = TextEditingController();
  final _messages = <Map<String, String>>[];
  bool _isAsking = false;

  @override
  void dispose() {
    _questionController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final doc = widget.document;
    final isPdf = doc['file_type'] == 'pdf';
    final fileSize = doc['file_size'];
    final sizeLabel = fileSize != null ? _formatSize(fileSize as int) : '';

    return Scaffold(
      appBar: AppBar(title: Text(doc['title'] ?? '文件详情')),
      body: Column(
        children: [
          Expanded(
            child: SingleChildScrollView(
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  // 文件信息卡片
                  Card(
                    child: Padding(
                      padding: const EdgeInsets.all(16),
                      child: Row(
                        children: [
                          Icon(
                            isPdf ? Icons.picture_as_pdf : Icons.description,
                            size: 48,
                            color: isPdf ? Colors.red : Colors.blue,
                          ),
                          const SizedBox(width: 16),
                          Expanded(
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Text(
                                  doc['title'] ?? '',
                                  style: const TextStyle(
                                      fontSize: 16,
                                      fontWeight: FontWeight.bold),
                                ),
                                const SizedBox(height: 4),
                                Text(
                                  '${doc['file_type'] ?? ''}${sizeLabel.isNotEmpty ? ' · $sizeLabel' : ''}',
                                  style: TextStyle(color: Colors.grey[600]),
                                ),
                              ],
                            ),
                          ),
                        ],
                      ),
                    ),
                  ),
                  const SizedBox(height: 16),

                  // 摘要
                  if (doc['summary'] != null) ...[
                    const Text('摘要',
                        style: TextStyle(
                            fontSize: 16, fontWeight: FontWeight.bold)),
                    const SizedBox(height: 8),
                    Card(
                      child: Padding(
                        padding: const EdgeInsets.all(16),
                        child: Text(
                          doc['summary'] as String,
                          style: const TextStyle(height: 1.6, fontSize: 15),
                        ),
                      ),
                    ),
                    const SizedBox(height: 16),
                  ],

                  // 全文预览
                  if (doc['full_text'] != null) ...[
                    Row(
                      children: [
                        const Text('全文内容',
                            style: TextStyle(
                                fontSize: 16, fontWeight: FontWeight.bold)),
                        const Spacer(),
                        if ((doc['full_text'] as String).length > 500)
                          TextButton(
                            onPressed: () => _showFullText(context,
                                doc['full_text'] as String),
                            child: const Text('查看全部'),
                          ),
                      ],
                    ),
                    const SizedBox(height: 8),
                    Card(
                      child: Container(
                        constraints: const BoxConstraints(maxHeight: 300),
                        padding: const EdgeInsets.all(16),
                        child: SelectableText(
                          doc['full_text'] as String,
                          style: const TextStyle(height: 1.6, fontSize: 14),
                        ),
                      ),
                    ),
                  ],

                  // 问答区域
                  if (_messages.isNotEmpty) ...[
                    const SizedBox(height: 24),
                    const Text('问答记录',
                        style: TextStyle(
                            fontSize: 16, fontWeight: FontWeight.bold)),
                    const SizedBox(height: 8),
                    ..._messages.map((m) {
                      final isUser = m['role'] == 'user';
                      return Card(
                        color: isUser ? Colors.blue[50] : null,
                        margin: const EdgeInsets.only(bottom: 8),
                        child: Padding(
                          padding: const EdgeInsets.all(12),
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Row(
                                children: [
                                  Icon(
                                    isUser ? Icons.person : Icons.smart_toy,
                                    size: 16,
                                    color: Colors.grey[600],
                                  ),
                                  const SizedBox(width: 4),
                                  Text(
                                    isUser ? '我' : 'AI',
                                    style: TextStyle(
                                        color: Colors.grey[600],
                                        fontSize: 12),
                                  ),
                                ],
                              ),
                              const SizedBox(height: 4),
                              Text(m['content'] ?? '',
                                  style: const TextStyle(height: 1.5)),
                            ],
                          ),
                        ),
                      );
                    }),
                  ],
                ],
              ),
            ),
          ),

          // 提问输入栏
          Container(
            padding: const EdgeInsets.all(16),
            decoration: BoxDecoration(
              color: Colors.white,
              boxShadow: [
                BoxShadow(
                  color: Colors.grey.withOpacity(0.1),
                  blurRadius: 8,
                  offset: const Offset(0, -2),
                ),
              ],
            ),
            child: SafeArea(
              child: Row(
                children: [
                  Expanded(
                    child: TextField(
                      controller: _questionController,
                      decoration: InputDecoration(
                        hintText: '就此文件提问...',
                        border: OutlineInputBorder(
                          borderRadius: BorderRadius.circular(24),
                          borderSide: BorderSide.none,
                        ),
                        filled: true,
                        fillColor: Colors.grey[100],
                        contentPadding: const EdgeInsets.symmetric(
                            horizontal: 20, vertical: 12),
                      ),
                      onSubmitted: (_) => _askQuestion(context),
                    ),
                  ),
                  const SizedBox(width: 8),
                  CircleAvatar(
                    backgroundColor: const Color(0xFF4A6CF7),
                    child: IconButton(
                      icon: _isAsking
                          ? const SizedBox(
                              width: 18,
                              height: 18,
                              child: CircularProgressIndicator(
                                  strokeWidth: 2, color: Colors.white))
                          : const Icon(Icons.send,
                              color: Colors.white, size: 20),
                      onPressed: _isAsking ? null : () => _askQuestion(context),
                    ),
                  ),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }

  Future<void> _askQuestion(BuildContext context) async {
    final question = _questionController.text.trim();
    if (question.isEmpty) return;

    _questionController.clear();
    setState(() {
      _messages.add({'role': 'user', 'content': question});
      _isAsking = true;
    });

    try {
      final result = await ApiService().askAi(question);
      final answer = result['answer'] as String? ?? '暂时无法回答';
      setState(() {
        _messages.add({'role': 'assistant', 'content': answer});
        _isAsking = false;
      });
    } catch (e) {
      setState(() {
        _messages
            .add({'role': 'assistant', 'content': '回答失败: $e'});
        _isAsking = false;
      });
    }
  }

  String _formatSize(int bytes) {
    if (bytes < 1024) return '$bytes B';
    if (bytes < 1024 * 1024) return '${(bytes / 1024).toStringAsFixed(1)} KB';
    return '${(bytes / (1024 * 1024)).toStringAsFixed(1)} MB';
  }

  void _showFullText(BuildContext context, String text) {
    showDialog(
      context: context,
      builder: (_) => Dialog(
        insetPadding: const EdgeInsets.all(24),
        child: SizedBox(
          width: double.infinity,
          child: Column(
            children: [
              AppBar(
                title: const Text('全文'),
                leading: IconButton(
                  icon: const Icon(Icons.close),
                  onPressed: () => Navigator.pop(context),
                ),
              ),
              Expanded(
                child: SingleChildScrollView(
                  padding: const EdgeInsets.all(16),
                  child: SelectableText(text,
                      style: const TextStyle(height: 1.6, fontSize: 14)),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
