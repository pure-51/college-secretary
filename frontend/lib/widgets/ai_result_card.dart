import 'package:flutter/material.dart';

class AiResultCard extends StatelessWidget {
  final String label;
  final String? value;
  final Widget? child;
  final Color? color;

  const AiResultCard({
    super.key,
    required this.label,
    this.value,
    this.child,
    this.color,
  });

  @override
  Widget build(BuildContext context) {
    final accentColor = color ?? const Color(0xFF4A6CF7);
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Container(
                  width: 3,
                  height: 16,
                  decoration: BoxDecoration(
                    color: accentColor,
                    borderRadius: BorderRadius.circular(2),
                  ),
                ),
                const SizedBox(width: 8),
                Text(
                  label,
                  style: TextStyle(
                    fontWeight: FontWeight.w600,
                    fontSize: 15,
                    color: accentColor,
                  ),
                ),
              ],
            ),
            const SizedBox(height: 12),
            if (child != null)
              child!
            else if (value != null)
              Text(
                value!,
                style: const TextStyle(height: 1.5, fontSize: 15),
              )
            else
              Text(
                '暂无',
                style: TextStyle(color: Colors.grey[400]),
              ),
          ],
        ),
      ),
    );
  }

  static Widget confidence(double value) {
    final color = value > 0.7
        ? Colors.green
        : value > 0.4
            ? Colors.orange
            : Colors.red;
    return Row(
      children: [
        Text(
          '${(value * 100).toStringAsFixed(0)}%',
          style: TextStyle(
              color: color, fontWeight: FontWeight.w600, fontSize: 13),
        ),
        const SizedBox(width: 8),
        Expanded(
          child: ClipRRect(
            borderRadius: BorderRadius.circular(4),
            child: LinearProgressIndicator(
              value: value,
              backgroundColor: Colors.grey[200],
              valueColor: AlwaysStoppedAnimation(color),
              minHeight: 6,
            ),
          ),
        ),
      ],
    );
  }
}
