import 'package:flutter/material.dart';
import '../config/theme.dart';
import '../pages/inbox/inbox_page.dart';
import '../pages/schedule/schedule_page.dart';
import '../pages/knowledge/knowledge_page.dart';
import '../pages/ai_report/ai_report_page.dart';
import '../pages/ai_consult/ai_consult_page.dart';
import '../pages/settings/settings_page.dart';
import '../pages/career/career_page.dart';
import '../pages/papers/papers_page.dart';
import '../pages/affairs/affairs_page.dart';
import 'demo_banner.dart';

/// 应用主框架：左侧竖向目录框 + 右侧内容区
/// 通过左侧菜单切换各功能页面。
class AppScaffold extends StatefulWidget {
  const AppScaffold({super.key});

  @override
  State<AppScaffold> createState() => _AppScaffoldState();
}

class _AppScaffoldState extends State<AppScaffold> {
  int _currentIndex = 0;

  // 页面顺序与 _sections 平铺顺序一一对应
  final List<Widget> _pages = const [
    InboxPage(), // 0 收件箱
    SchedulePage(), // 1 日程
    KnowledgePage(), // 2 知识库
    AiReportPage(), // 3 AI汇报
    AiConsultPage(), // 4 AI咨询
    CareerPage(), // 5 生涯
    PapersPage(), // 6 论文
    AffairsPage(), // 7 班务
    SettingsPage(), // 8 设置
  ];

  static const _sections = <_NavSection>[
    _NavSection('我的助理', [
      _NavItem(
        icon: Icons.inbox_rounded,
        activeIcon: Icons.inbox_rounded,
        label: '收件箱',
      ),
      _NavItem(
        icon: Icons.calendar_month_outlined,
        activeIcon: Icons.calendar_month_rounded,
        label: '日程',
      ),
      _NavItem(
        icon: Icons.menu_book_outlined,
        activeIcon: Icons.menu_book_rounded,
        label: '知识库',
      ),
      _NavItem(
        icon: Icons.auto_awesome_outlined,
        activeIcon: Icons.auto_awesome_rounded,
        label: 'AI汇报',
      ),
      _NavItem(
        icon: Icons.chat_bubble_outline_rounded,
        activeIcon: Icons.chat_bubble_rounded,
        label: 'AI咨询',
      ),
    ]),
    _NavSection('成长档案', [
      _NavItem(
        icon: Icons.folder_shared_outlined,
        activeIcon: Icons.folder_shared_rounded,
        label: '生涯',
      ),
      _NavItem(
        icon: Icons.library_books_outlined,
        activeIcon: Icons.library_books_rounded,
        label: '论文',
      ),
      _NavItem(
        icon: Icons.how_to_reg_outlined,
        activeIcon: Icons.how_to_reg_rounded,
        label: '班务',
      ),
    ]),
    _NavSection('系统', [
      _NavItem(
        icon: Icons.settings_outlined,
        activeIcon: Icons.settings_rounded,
        label: '设置',
      ),
    ]),
  ];

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Row(
        children: [
          _buildSidebar(),
          // 右侧内容区
          Expanded(
            child: Column(
              children: [
                // 演示横幅（仅演示环境）
                const DemoBanner(),
                // 主内容：最大宽度约束 + 居中
                Expanded(
                  child: Center(
                    child: ConstrainedBox(
                      constraints: const BoxConstraints(maxWidth: 1200),
                      child: AnimatedSwitcher(
                        duration: const Duration(milliseconds: 200),
                        switchInCurve: Curves.easeOut,
                        switchOutCurve: Curves.easeIn,
                        transitionBuilder: (child, animation) {
                          return FadeTransition(
                              opacity: animation, child: child);
                        },
                        child: KeyedSubtree(
                          key: ValueKey(_currentIndex),
                          child: _pages[_currentIndex],
                        ),
                      ),
                    ),
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  // ── 左侧竖向目录框 ───────────────────────────
  Widget _buildSidebar() {
    return Container(
      width: 236,
      color: AppTheme.cardColor,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          _buildBrand(),
          const Divider(height: 1, thickness: 1),
          Expanded(
            child: ListView(
              padding: const EdgeInsets.symmetric(vertical: 8),
              children: _buildNavChildren(),
            ),
          ),
          const Divider(height: 1, thickness: 1),
          // 底部版本信息
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 14),
            child: Row(
              children: [
                Container(
                  width: 6,
                  height: 6,
                  decoration: const BoxDecoration(
                    color: AppTheme.successColor,
                    shape: BoxShape.circle,
                  ),
                ),
                const SizedBox(width: 8),
                const Text(
                  '大学生秘书 v1.0 · 本地运行',
                  style: TextStyle(fontSize: 11, color: AppTheme.textTertiary),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  /// 平铺所有分组导航项，返回侧边栏列表 children
  List<Widget> _buildNavChildren() {
    final children = <Widget>[];
    var index = 0;
    for (final section in _sections) {
      if (index > 0) children.add(const SizedBox(height: 8));
      children.add(Padding(
        padding: const EdgeInsets.fromLTRB(20, 12, 20, 6),
        child: Text(
          section.title,
          style: const TextStyle(
            fontSize: 11,
            fontWeight: FontWeight.w500,
            color: AppTheme.textTertiary,
            letterSpacing: 1.2,
          ),
        ),
      ));
      for (final item in section.items) {
        final i = index++;
        children.add(_SidebarItem(
          item: item,
          isSelected: i == _currentIndex,
          onTap: () => setState(() => _currentIndex = i),
        ));
      }
    }
    return children;
  }

  Widget _buildBrand() {
    return Container(
      padding: const EdgeInsets.fromLTRB(20, 20, 20, 16),
      child: Row(
        children: [
          Container(
            width: 40,
            height: 40,
            decoration: BoxDecoration(
              color: AppTheme.primaryLight,
              borderRadius: BorderRadius.circular(12),
            ),
            child: const Icon(
              Icons.school_rounded,
              color: AppTheme.primaryColor,
              size: 22,
            ),
          ),
          const SizedBox(width: 12),
          const Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                '大学生秘书',
                style: TextStyle(
                  fontSize: 16,
                  fontWeight: FontWeight.w700,
                  color: AppTheme.textPrimary,
                  letterSpacing: 0.2,
                ),
              ),
              SizedBox(height: 2),
              Text(
                '一站式校园 AI 助手',
                style: TextStyle(fontSize: 11, color: AppTheme.textTertiary),
              ),
            ],
          ),
        ],
      ),
    );
  }
}

// ── 数据模型 ─────────────────────────────────

class _NavSection {
  final String title;
  final List<_NavItem> items;
  const _NavSection(this.title, this.items);
}

class _NavItem {
  final IconData icon;
  final IconData activeIcon;
  final String label;
  const _NavItem({
    required this.icon,
    required this.activeIcon,
    required this.label,
  });
}

// ── 侧边栏导航项 ─────────────────────────────

class _SidebarItem extends StatefulWidget {
  final _NavItem item;
  final bool isSelected;
  final VoidCallback onTap;

  const _SidebarItem({
    required this.item,
    required this.isSelected,
    required this.onTap,
  });

  @override
  State<_SidebarItem> createState() => _SidebarItemState();
}

class _SidebarItemState extends State<_SidebarItem> {
  bool _hovered = false;

  @override
  Widget build(BuildContext context) {
    final selected = widget.isSelected;
    final item = widget.item;
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 2),
      child: MouseRegion(
        onEnter: (_) => setState(() => _hovered = true),
        onExit: (_) => setState(() => _hovered = false),
        child: AnimatedContainer(
          duration: const Duration(milliseconds: 150),
          decoration: BoxDecoration(
            color: selected
                ? AppTheme.primaryLight
                : (_hovered ? const Color(0xFFF3F4F6) : Colors.transparent),
            borderRadius: BorderRadius.circular(10),
          ),
          child: Material(
            color: Colors.transparent,
            child: InkWell(
              borderRadius: BorderRadius.circular(10),
              onTap: widget.onTap,
              child: Padding(
                padding:
                    const EdgeInsets.symmetric(horizontal: 10, vertical: 10),
                child: Row(
                  children: [
                    // 选中指示条
                    AnimatedContainer(
                      duration: const Duration(milliseconds: 150),
                      width: 3,
                      height: 16,
                      decoration: BoxDecoration(
                        color: selected
                            ? AppTheme.primaryColor
                            : Colors.transparent,
                        borderRadius: BorderRadius.circular(2),
                      ),
                    ),
                    const SizedBox(width: 10),
                    Icon(
                      selected ? item.activeIcon : item.icon,
                      size: 20,
                      color: selected
                          ? AppTheme.primaryColor
                          : AppTheme.textTertiary,
                    ),
                    const SizedBox(width: 10),
                    Expanded(
                      child: Text(
                        item.label,
                        style: TextStyle(
                          fontSize: 14,
                          fontWeight:
                              selected ? FontWeight.w600 : FontWeight.w500,
                          color: selected
                              ? AppTheme.primaryColor
                              : AppTheme.textSecondary,
                        ),
                      ),
                    ),
                  ],
                ),
              ),
            ),
          ),
        ),
      ),
    );
  }
}
