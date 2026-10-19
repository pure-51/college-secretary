/// Web 版文件拖拽上传组件
import 'dart:async';
import 'dart:html' as html;
import 'dart:typed_data';
import 'package:flutter/material.dart';

class FileDropZone extends StatefulWidget {
  final void Function(Uint8List bytes, String fileName) onFileDropped;
  final String hintText;
  final double height;

  const FileDropZone({
    super.key,
    required this.onFileDropped,
    this.hintText = '拖拽图片到此处上传',
    this.height = 120,
  });

  @override
  State<FileDropZone> createState() => _FileDropZoneState();
}

class _FileDropZoneState extends State<FileDropZone> {
  bool _isDragging = false;
  StreamSubscription? _dragOverSub;
  StreamSubscription? _dropSub;
  StreamSubscription? _dragLeaveSub;

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) => _setupListeners());
  }

  void _setupListeners() {
    _dragOverSub = html.document.onDragOver.listen((e) {
      e.preventDefault();
      if (!_isDragging) setState(() => _isDragging = true);
    });

    _dragLeaveSub = html.document.onDragLeave.listen((e) {
      e.preventDefault();
      if (_isDragging) setState(() => _isDragging = false);
    });

    _dropSub = html.document.onDrop.listen((e) {
      e.preventDefault();
      setState(() => _isDragging = false);

      final files = e.dataTransfer?.files;
      if (files != null && files.isNotEmpty) {
        final file = files[0];
        if (file.type.startsWith('image/')) {
          final reader = html.FileReader();
          reader.onLoadEnd.listen((_) {
            final bytes = reader.result as Uint8List;
            widget.onFileDropped(bytes, file.name ?? 'image.png');
          });
          reader.readAsArrayBuffer(file);
        }
      }
    });
  }

  @override
  void dispose() {
    _dragOverSub?.cancel();
    _dropSub?.cancel();
    _dragLeaveSub?.cancel();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Container(
      height: widget.height,
      width: double.infinity,
      decoration: BoxDecoration(
        border: Border.all(
          color: _isDragging ? const Color(0xFF4A6CF7) : Colors.grey[400]!,
          width: 2,
        ),
        borderRadius: BorderRadius.circular(12),
        color: _isDragging
            ? const Color(0xFF4A6CF7).withOpacity(0.05)
            : Colors.grey[50],
      ),
      child: Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(
              _isDragging ? Icons.cloud_upload : Icons.image_outlined,
              size: 36,
              color: _isDragging ? const Color(0xFF4A6CF7) : Colors.grey,
            ),
            const SizedBox(height: 8),
            Text(
              _isDragging ? '松开以上传图片' : widget.hintText,
              style: TextStyle(
                color: _isDragging ? const Color(0xFF4A6CF7) : Colors.grey[600],
                fontSize: 14,
              ),
            ),
          ],
        ),
      ),
    );
  }
}
