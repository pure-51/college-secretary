import 'package:flutter/material.dart';
import '../config/theme.dart';
import '../services/api_service.dart';

/// 演示横幅：显示「演示模式」状态 + 一键加载演示数据（六幕剧本林小夏）
/// 数据为虚构脱敏人物，仅作比赛演示；正式环境不出现。
class DemoBanner extends StatefulWidget {
  const DemoBanner({super.key});

  @override
  State<DemoBanner> createState() => _DemoBannerState();
}

class _DemoBannerState extends State<DemoBanner> {
  final ApiService _api = ApiService();
  bool _demoMode = false;
  bool _loading = false;

  @override
  void initState() {
    super.initState();
    _refresh();
  }

  Future<void> _refresh() async {
    final data = await _api.demoStatus();
    if (!mounted) return;
    final mode = data['demo_mode'];
    setState(() => _demoMode = mode is bool ? mode : false);
  }

  Future<void> _seed() async {
    setState(() => _loading = true);
    await _api.seedDemo();
    if (!mounted) return;
    setState(() => _loading = false);
    _refresh();
    ScaffoldMessenger.of(context).showSnackBar(const SnackBar(
      content: Text('演示数据已加载：林小夏六幕剧本'),
      duration: Duration(seconds: 2),
      behavior: SnackBarBehavior.floating,
    ));
  }

  Future<void> _clear() async {
    setState(() => _loading = true);
    await _api.clearDemo();
    if (!mounted) return;
    setState(() => _loading = false);
    _refresh();
  }

  @override
  Widget build(BuildContext context) {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
      color: AppTheme.primaryColor,
      child: SafeArea(
        bottom: false,
        child: Row(
          children: [
            const Icon(Icons.auto_awesome_rounded,
                size: 16, color: Colors.white),
            const SizedBox(width: 8),
            Expanded(
              child: Text(
                _demoMode
                    ? '演示模式 · 数据为虚构脱敏人物「林小夏」'
                    : '点击加载演示数据，走通六幕剧本',
                style: const TextStyle(
                    color: Colors.white, fontSize: 12, fontWeight: FontWeight.w500),
              ),
            ),
            if (_loading)
              const SizedBox(
                width: 14,
                height: 14,
                child: CircularProgressIndicator(
                    strokeWidth: 2, color: Colors.white),
              )
            else
              GestureDetector(
                onTap: _demoMode ? _clear : _seed,
                child: Container(
                  padding:
                      const EdgeInsets.symmetric(horizontal: 12, vertical: 5),
                  decoration: BoxDecoration(
                    color: Colors.white.withAlpha(30),
                    borderRadius: BorderRadius.circular(8),
                    border: Border.all(color: Colors.white.withAlpha(80)),
                  ),
                  child: Text(
                    _demoMode ? '清空' : '加载演示数据',
                    style: const TextStyle(
                        color: Colors.white,
                        fontSize: 11,
                        fontWeight: FontWeight.w600),
                  ),
                ),
              ),
          ],
        ),
      ),
    );
  }
}
