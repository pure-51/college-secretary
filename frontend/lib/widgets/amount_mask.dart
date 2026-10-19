import 'package:flutter/material.dart';
import '../config/theme.dart';

/// 金额脱敏展示（ADR §6：台账金额只本地存 amount，展示用 amount_masked）
/// 敏感字段一律显示 ¥***，杜绝真实金额外泄到前端展示层。
class AmountMask extends StatelessWidget {
  final double? amount;
  final bool compact;

  const AmountMask({super.key, this.amount, this.compact = false});

  @override
  Widget build(BuildContext context) {
    return Row(
      mainAxisSize: MainAxisSize.min,
      children: [
        Icon(
          Icons.lock_outline_rounded,
          size: compact ? 12 : 14,
          color: AppTheme.textTertiary,
        ),
        const SizedBox(width: 4),
        Text(
          amount == null ? '¥***' : '¥***',
          style: TextStyle(
            fontSize: compact ? 12 : 13,
            fontWeight: FontWeight.w600,
            color: AppTheme.textSecondary,
            letterSpacing: 0.5,
          ),
        ),
      ],
    );
  }
}

/// 敏感字段值脱敏（如身份证号/学号等，仅演示打码逻辑）
class SensitiveMask extends StatelessWidget {
  final String value;
  final bool sensitive;

  const SensitiveMask({super.key, required this.value, this.sensitive = true});

  @override
  Widget build(BuildContext context) {
    if (!sensitive) {
      return Text(value,
          style: const TextStyle(fontSize: 13, color: AppTheme.textPrimary));
    }
    return Row(
      mainAxisSize: MainAxisSize.min,
      children: [
        Icon(Icons.visibility_off_outlined,
            size: 13, color: AppTheme.warningColor),
        const SizedBox(width: 4),
        Text(
          '${value.length > 6 ? value.substring(0, 6) : value}****',
          style: const TextStyle(
              fontSize: 13,
              color: AppTheme.warningColor,
              fontWeight: FontWeight.w500),
        ),
      ],
    );
  }
}
