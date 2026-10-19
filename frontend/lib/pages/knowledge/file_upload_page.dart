import 'dart:io';
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:file_picker/file_picker.dart';
import '../../config/theme.dart';
import '../../providers/knowledge_provider.dart';

class FileUploadPage extends StatefulWidget {
  const FileUploadPage({super.key});

  @override
  State<FileUploadPage> createState() => _FileUploadPageState();
}

class _FileUploadPageState extends State<FileUploadPage> {
  bool _isUploading = false;
  PlatformFile? _selectedFile;

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('上传文件')),
      body: Padding(
        padding: const EdgeInsets.all(24),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            // 文件选择区
            InkWell(
              onTap: _isUploading ? null : _pickFile,
              borderRadius: BorderRadius.circular(16),
              child: Container(
                height: 200,
                decoration: BoxDecoration(
                  border: Border.all(
                    color: _selectedFile != null
                        ? AppTheme.primaryColor
                        : AppTheme.borderColor,
                    width: 2,
                    strokeAlign: BorderSide.strokeAlignInside,
                  ),
                  borderRadius: BorderRadius.circular(16),
                  color: _selectedFile != null
                      ? AppTheme.primaryLight
                      : const Color(0xFFF9FAFB),
                ),
                child: Center(
                  child: _selectedFile != null
                      ? Column(
                          mainAxisAlignment: MainAxisAlignment.center,
                          children: [
                            Icon(
                              _selectedFile!.extension == 'pdf'
                                  ? Icons.picture_as_pdf
                                  : Icons.description_rounded,
                              size: 48,
                              color: _selectedFile!.extension == 'pdf'
                                  ? AppTheme.errorColor
                                  : AppTheme.primaryColor,
                            ),
                            const SizedBox(height: 12),
                            Text(
                              _selectedFile!.name,
                              style: const TextStyle(
                                  fontSize: 16,
                                  fontWeight: FontWeight.w500,
                                  color: AppTheme.textPrimary),
                              textAlign: TextAlign.center,
                            ),
                            if (_selectedFile!.size > 0) ...[
                              const SizedBox(height: 4),
                              Text(
                                _formatSize(_selectedFile!.size),
                                style: const TextStyle(
                                    color: AppTheme.textSecondary),
                              ),
                            ],
                            const SizedBox(height: 8),
                            TextButton.icon(
                              onPressed: _pickFile,
                              icon: const Icon(Icons.refresh_rounded,
                                  size: 18),
                              label: const Text('重新选择'),
                            ),
                          ],
                        )
                      : Column(
                          mainAxisAlignment: MainAxisAlignment.center,
                          children: [
                            Icon(Icons.cloud_upload_outlined,
                                size: 64, color: AppTheme.textTertiary),
                            const SizedBox(height: 16),
                            const Text(
                              '点击选择文件',
                              style: TextStyle(
                                  fontSize: 16,
                                  color: AppTheme.textSecondary),
                            ),
                            const SizedBox(height: 8),
                            const Text(
                              '支持 PDF、Word 文档',
                              style: TextStyle(
                                  fontSize: 14,
                                  color: AppTheme.textTertiary),
                            ),
                          ],
                        ),
                ),
              ),
            ),
            const SizedBox(height: 16),

            // 提示
            Container(
              padding: const EdgeInsets.all(14),
              decoration: BoxDecoration(
                color: AppTheme.primaryLight,
                borderRadius: BorderRadius.circular(12),
              ),
              child: Row(
                children: [
                  Icon(Icons.info_outline_rounded,
                      size: 20, color: AppTheme.primaryColor),
                  const SizedBox(width: 12),
                  const Expanded(
                    child: Text(
                      '上传后，AI 将自动解析文件内容并生成摘要。'
                      '之后你可以在知识库中对文件内容进行问答。',
                      style:
                          TextStyle(fontSize: 13, color: AppTheme.textSecondary),
                    ),
                  ),
                ],
              ),
            ),
            const Spacer(),

            // 上传按钮
            SizedBox(
              height: 50,
              child: ElevatedButton.icon(
                onPressed: _isUploading || _selectedFile == null
                    ? null
                    : _uploadFile,
                icon: _isUploading
                    ? const SizedBox(
                        width: 20,
                        height: 20,
                        child: CircularProgressIndicator(
                            strokeWidth: 2, color: Colors.white))
                    : const Icon(Icons.upload_rounded),
                label: Text(_isUploading ? '上传中...' : '上传文件'),
              ),
            ),
            const SizedBox(height: 16),
          ],
        ),
      ),
    );
  }

  Future<void> _pickFile() async {
    try {
      final result = await FilePicker.platform.pickFiles(
        type: FileType.custom,
        allowedExtensions: ['pdf', 'doc', 'docx'],
      );
      if (result != null && result.files.isNotEmpty) {
        setState(() {
          _selectedFile = result.files.first;
        });
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('选择文件失败: $e')),
        );
      }
    }
  }

  Future<void> _uploadFile() async {
    if (_selectedFile == null) return;

    setState(() => _isUploading = true);

    try {
      final file = File(_selectedFile!.path!);
      if (mounted) {
        await context.read<KnowledgeProvider>().uploadFile(file);
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(
              content: Text('文件上传成功！AI 正在处理...'),
              backgroundColor: AppTheme.successColor,
            ),
          );
          Navigator.pop(context);
        }
      }
    } catch (e) {
      if (mounted) {
        setState(() => _isUploading = false);
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('上传失败: $e'),
            backgroundColor: AppTheme.errorColor,
          ),
        );
      }
    }
  }

  String _formatSize(int bytes) {
    if (bytes < 1024) return '$bytes B';
    if (bytes < 1024 * 1024) return '${(bytes / 1024).toStringAsFixed(1)} KB';
    return '${(bytes / (1024 * 1024)).toStringAsFixed(1)} MB';
  }
}
