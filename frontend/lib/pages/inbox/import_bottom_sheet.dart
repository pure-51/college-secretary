import 'dart:typed_data';
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:file_picker/file_picker.dart';
import '../../config/theme.dart';
import '../../providers/inbox_provider.dart';
import '../../widgets/file_drop_zone.dart';

class ImportBottomSheet extends StatefulWidget {
  const ImportBottomSheet({super.key});

  @override
  State<ImportBottomSheet> createState() => _ImportBottomSheetState();
}

class _ImportBottomSheetState extends State<ImportBottomSheet> {
  final _textController = TextEditingController();
  final _linkController = TextEditingController();
  bool _isImporting = false;

  Future<void> _importText(String text) async {
    if (text.trim().isEmpty) return;
    setState(() => _isImporting = true);
    await context.read<InboxProvider>().importText(text);
    if (mounted) Navigator.pop(context);
  }

  Future<void> _importLink(String url) async {
    if (url.trim().isEmpty) return;
    setState(() => _isImporting = true);
    await context.read<InboxProvider>().importLink(url);
    if (mounted) Navigator.pop(context);
  }

  @override
  void dispose() {
    _textController.dispose();
    _linkController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final bottomInset = MediaQuery.of(context).viewInsets.bottom;

    return SingleChildScrollView(
      padding: EdgeInsets.fromLTRB(24, 12, 24, bottomInset + 24),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Center(
            child: Container(
              width: 36,
              height: 4,
              decoration: BoxDecoration(
                color: Colors.grey[300],
                borderRadius: BorderRadius.circular(2),
              ),
            ),
          ),
          const SizedBox(height: 20),
          Text(
            '导入消息',
            style: Theme.of(context).textTheme.titleLarge,
          ),
          const SizedBox(height: 20),

          // ── 文本导入 ──
          _SectionHeader(icon: Icons.text_fields_rounded, label: '粘贴文本'),
          const SizedBox(height: 8),
          TextField(
            controller: _textController,
            maxLines: 3,
            decoration: const InputDecoration(
              hintText: '粘贴QQ群消息内容...',
            ),
          ),
          const SizedBox(height: 8),
          SizedBox(
            width: double.infinity,
            child: ElevatedButton(
              onPressed:
                  _isImporting ? null : () => _importText(_textController.text),
              child: _isImporting
                  ? const SizedBox(
                      width: 18,
                      height: 18,
                      child: CircularProgressIndicator(
                          strokeWidth: 2, color: Colors.white))
                  : const Text('导入文本'),
            ),
          ),

          const SizedBox(height: 24),
          const Divider(),
          const SizedBox(height: 16),

          // ── 链接导入 ──
          _SectionHeader(icon: Icons.link_rounded, label: '导入链接'),
          const SizedBox(height: 8),
          TextField(
            controller: _linkController,
            decoration: const InputDecoration(
              hintText: '粘贴网页链接...',
              prefixIcon: Icon(Icons.link),
            ),
          ),
          const SizedBox(height: 8),
          SizedBox(
            width: double.infinity,
            child: ElevatedButton(
              onPressed:
                  _isImporting ? null : () => _importLink(_linkController.text),
              child: _isImporting
                  ? const SizedBox(
                      width: 18,
                      height: 18,
                      child: CircularProgressIndicator(
                          strokeWidth: 2, color: Colors.white))
                  : const Text('导入链接'),
            ),
          ),

          const SizedBox(height: 24),
          const Divider(),
          const SizedBox(height: 16),

          // ── 图片导入 ──
          _SectionHeader(icon: Icons.image_rounded, label: '导入图片'),
          const SizedBox(height: 8),
          Container(
            decoration: BoxDecoration(
              borderRadius: BorderRadius.circular(12),
              border: Border.all(color: AppTheme.borderColor, width: 0.5),
            ),
            child: FileDropZone(
              onFileDropped: (bytes, name) => _onImageBytes(bytes, name),
            ),
          ),
          const SizedBox(height: 8),
          SizedBox(
            width: double.infinity,
            child: OutlinedButton.icon(
              onPressed: _isImporting ? null : () => _pickImage(),
              icon: const Icon(Icons.image_outlined, size: 18),
              label: const Text('选择图片'),
            ),
          ),
          const SizedBox(height: 8),
        ],
      ),
    );
  }

  Future<void> _importImageData(Uint8List bytes, String name) async {
    setState(() => _isImporting = true);
    try {
      await context.read<InboxProvider>().importImageBytes(bytes, name);
      if (mounted) Navigator.pop(context);
    } catch (e) {
      if (mounted) {
        setState(() => _isImporting = false);
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('导入图片失败: $e')),
        );
      }
    }
  }

  void _onImageBytes(Uint8List bytes, String name) {
    _importImageData(bytes, name);
  }

  Future<void> _pickImage() async {
    try {
      final result = await FilePicker.platform.pickFiles(type: FileType.image);
      if (result == null || result.files.isEmpty) return;

      final file = result.files.single;
      final bytes = file.bytes;
      if (bytes == null) {
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(content: Text('无法读取图片文件')),
          );
        }
        return;
      }

      _importImageData(bytes, file.name);
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('选择图片失败: $e')),
        );
      }
    }
  }
}

class _SectionHeader extends StatelessWidget {
  final IconData icon;
  final String label;

  const _SectionHeader({required this.icon, required this.label});

  @override
  Widget build(BuildContext context) {
    return Row(
      children: [
        Icon(icon, size: 18, color: AppTheme.primaryColor),
        const SizedBox(width: 8),
        Text(label,
            style: const TextStyle(
                fontWeight: FontWeight.w600,
                fontSize: 15,
                color: AppTheme.textPrimary)),
      ],
    );
  }
}
