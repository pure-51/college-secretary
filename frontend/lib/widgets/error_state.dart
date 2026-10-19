import 'package:flutter/material.dart';
import '../config/theme.dart';

class ErrorState extends StatelessWidget {
  final String message;
  final String? detail;
  final VoidCallback? onRetry;
  final bool compact;

  const ErrorState({
    super.key,
    required this.message,
    this.detail,
    this.onRetry,
    this.compact = false,
  });

  @override
  Widget build(BuildContext context) {
    final content = Column(
      mainAxisAlignment: MainAxisAlignment.center,
      children: [
        Container(
          width: compact ? 48 : 72,
          height: compact ? 48 : 72,
          decoration: BoxDecoration(
            color: AppTheme.errorColor.withAlpha(20),
            borderRadius: BorderRadius.circular(compact ? 14 : 20),
          ),
          child: Icon(
            Icons.warning_rounded,
            size: compact ? 24 : 36,
            color: AppTheme.errorColor.withAlpha(180),
          ),
        ),
        SizedBox(height: compact ? 12 : 20),
        Text(
          message,
          textAlign: TextAlign.center,
          style: TextStyle(
            color: AppTheme.textPrimary,
            fontSize: compact ? 14 : 15,
            fontWeight: FontWeight.w500,
          ),
        ),
        if (detail != null) ...[
          const SizedBox(height: 8),
          Text(
            detail!,
            textAlign: TextAlign.center,
            style: const TextStyle(
              color: AppTheme.textSecondary,
              fontSize: 13,
            ),
          ),
        ],
        if (onRetry != null) ...[
          const SizedBox(height: 16),
          OutlinedButton.icon(
            onPressed: onRetry,
            icon: const Icon(Icons.refresh, size: 16),
            label: const Text('重试'),
          ),
        ],
      ],
    );

    if (compact) return content;

    return Center(
      child: Padding(
        padding: const EdgeInsets.all(32),
        child: content,
      ),
    );
  }
}
