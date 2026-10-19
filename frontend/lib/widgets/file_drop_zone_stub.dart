/// 非 Web 平台的文件拖拽占位组件
import 'dart:typed_data';
import 'package:flutter/material.dart';

class FileDropZone extends StatelessWidget {
  final void Function(Uint8List bytes, String fileName)? onFileDropped;
  final String? hintText;
  final double? height;

  const FileDropZone({
    super.key,
    this.onFileDropped,
    this.hintText,
    this.height,
  });

  @override
  Widget build(BuildContext context) => const SizedBox.shrink();
}
