from __future__ import annotations

"""Utility helpers for lightweight UI localization."""

from typing import Dict, Iterable

from .settings import get_settings

DEFAULT_LANGUAGE = "en"
AVAILABLE_LANGUAGES = ["en", "de", "es", "fr", "zh-CN", "zh-TW"]

LANGUAGE_LABELS: Dict[str, str] = {
    "en": "English",
    "de": "Deutsch",
    "es": "Español",
    "fr": "Français",
    "zh-CN": "简体中文",
    "zh-TW": "繁體中文",
}

ZH_SIMPLIFIED: Dict[str, str] = {
    "Media Manager": "媒体管理器",
    "Grid View": "网格视图",
    "Table View": "表格视图",
    "Thumbnail Size:": "缩略图尺寸：",
    "Small": "小",
    "Medium": "中",
    "Large": "大",
    "Extra Large": "超大",
    "All": "全部",
    "Movies": "电影",
    "TV Shows": "电视剧",
    "Library": "媒体库",
    "Dashboard": "仪表板",
    "Search": "搜索",
    "Recent": "最近",
    "Favorites": "收藏",
    "Matching": "匹配",
    "&File": "&文件",
    "&Open": "&打开",
    "Manage &Libraries...": "管理&媒体库...",
    "E&xit": "退&出",
    "&Edit": "&编辑",
    "&Preferences": "&偏好设置",
    "Batch &Operations...": "批量&操作...",
    "&Export Media...": "&导出媒体...",
    "&Import Media...": "&导入媒体...",
    "&View": "&视图",
    "Toggle &Panes": "切换&面板",
    "&Help": "&帮助",
    "&Help Center": "&帮助中心",
    "Show &Onboarding Wizard": "显示&引导向导",
    "&About": "&关于",
    "Ready": "就绪",
    "0 items": "0 个项目",
    "Open File": "打开文件",
    "All Files (*)": "所有文件 (*)",
    "Preferences updated": "偏好设置已更新",
    "About Media Manager": "关于媒体管理器",
    "Media Manager v0.1.0\n\nA PySide6-based media management application.\n\nBuilt with Python and PySide6.": "媒体管理器 v0.1.0\n\n一款基于 PySide6 的媒体管理应用。\n\n由 Python 与 PySide6 构建。",
    "View Details": "查看详情",
    "Edit Metadata": "编辑元数据",
    "Play": "播放",
    "Quick Tags": "快速标签",
    "+ Add New Tag...": "+ 添加新标签...",
    "Toggle Favorite": "切换收藏",
    "Batch Operations...": "批量操作...",
    "Refresh": "刷新",
    "New Tag": "新建标签",
    "Enter tag name:": "输入标签名称：",
    "Help Center": "帮助中心",
    "◀ Back": "◀ 返回",
    "Forward ▶": "前进 ▶",
    "Search help topics...": "搜索帮助主题...",
    "Close": "关闭",
    "Error": "错误",
    "Help topic file not found: {filename}": "找不到帮助主题文件：{filename}",
    "Failed to load help content: {error}": "无法加载帮助内容：{error}",
    "Preferences": "偏好设置",
    "Libraries": "媒体库",
    "Metadata": "元数据",
    "Providers": "提供者",
    "Downloads": "下载",
    "UI": "界面",
    "Advanced": "高级",
    "Theme:": "主题：",
    "Language:": "语言：",
    "Remember window layout between sessions": "记住窗口布局",
    "System": "系统",
    "Light": "浅色",
    "Dark": "深色",
    "Opened: {path}": "已打开：{path}",
    "Panes shown": "面板已显示",
    "Panes hidden": "面板已隐藏",
    "{count} items": "{count} 个项目",
    "Select one or more items to run batch operations": "请选择一个或多个项目以运行批量操作",
    "Export completed successfully": "导出成功完成",
    "Export cancelled": "导出已取消",
    "Import completed successfully": "导入成功完成",
    "Import cancelled": "导入已取消",
    "Viewing {library} - {media_type}": "正在查看 {library} - {media_type}",
    "No libraries found. Please create a library to get started.": "未找到媒体库。请先创建一个媒体库。",
    "Queue cleared": "队列已清空",
    "Added {count} items to scan queue": "已向扫描队列添加 {count} 个项目",
    "Loaded {count} media items": "已加载 {count} 个媒体项目",
    "Activated: {title}": "已打开：{title}",
    "Editing: {title}": "正在编辑：{title}",
    "Playing: {path}": "正在播放：{path}",
    "Created and added tag '{tag}' to {title}": "已创建标签“{tag}”并添加到 {title}",
    "Error creating tag: {error}": "创建标签时出错：{error}",
    "Removed tag '{tag}' from {title}": "已从 {title} 移除标签“{tag}”",
    "Added tag '{tag}' to {title}": "已将标签“{tag}”添加到 {title}",
    "Error toggling tag: {error}": "切换标签时出错：{error}",
    "Removed {title} from favorites": "已将 {title} 从收藏中移除",
    "Added {title} to favorites": "已将 {title} 添加到收藏",
    "Error toggling favorite: {error}": "切换收藏状态时出错：{error}",
    "Library '{name}' created": "已创建资料库“{name}”",
    "Library '{name}' updated": "已更新资料库“{name}”",
    "Library deleted": "资料库已删除",
    "{title} Settings": "{title} 设置",
}

ZH_TRADITIONAL: Dict[str, str] = {
    "Media Manager": "媒體管理器",
    "Grid View": "網格檢視",
    "Table View": "表格檢視",
    "Thumbnail Size:": "縮圖大小：",
    "Small": "小",
    "Medium": "中",
    "Large": "大",
    "Extra Large": "特大",
    "All": "全部",
    "Movies": "電影",
    "TV Shows": "電視劇",
    "Library": "媒體庫",
    "Dashboard": "儀表板",
    "Search": "搜尋",
    "Recent": "最近",
    "Favorites": "最愛",
    "Matching": "比對",
    "&File": "&檔案",
    "&Open": "&開啟",
    "Manage &Libraries...": "管理&媒體庫...",
    "E&xit": "退&出",
    "&Edit": "&編輯",
    "&Preferences": "&偏好設定",
    "Batch &Operations...": "批次&作業...",
    "&Export Media...": "&匯出媒體...",
    "&Import Media...": "&匯入媒體...",
    "&View": "&檢視",
    "Toggle &Panes": "切換&面板",
    "&Help": "&說明",
    "&Help Center": "&說明中心",
    "Show &Onboarding Wizard": "顯示&導覽精靈",
    "&About": "&關於",
    "Ready": "就緒",
    "0 items": "0 個項目",
    "Open File": "開啟檔案",
    "All Files (*)": "所有檔案 (*)",
    "Preferences updated": "偏好設定已更新",
    "About Media Manager": "關於媒體管理器",
    "Media Manager v0.1.0\n\nA PySide6-based media management application.\n\nBuilt with Python and PySide6.": "媒體管理器 v0.1.0\n\n一款基於 PySide6 的媒體管理應用程式。\n\n使用 Python 與 PySide6 建置。",
    "View Details": "檢視詳細資料",
    "Edit Metadata": "編輯中繼資料",
    "Play": "播放",
    "Quick Tags": "快速標籤",
    "+ Add New Tag...": "+ 新增標籤...",
    "Toggle Favorite": "切換收藏",
    "Batch Operations...": "批次作業...",
    "Refresh": "重新整理",
    "New Tag": "新增標籤",
    "Enter tag name:": "輸入標籤名稱：",
    "Help Center": "說明中心",
    "◀ Back": "◀ 返回",
    "Forward ▶": "前進 ▶",
    "Search help topics...": "搜尋說明主題...",
    "Close": "關閉",
    "Error": "錯誤",
    "Help topic file not found: {filename}": "找不到說明主題檔案：{filename}",
    "Failed to load help content: {error}": "無法載入說明內容：{error}",
    "Preferences": "偏好設定",
    "Libraries": "媒體庫",
    "Metadata": "中繼資料",
    "Providers": "提供者",
    "Downloads": "下載",
    "UI": "介面",
    "Advanced": "進階",
    "Theme:": "主題：",
    "Language:": "語言：",
    "Remember window layout between sessions": "記住視窗配置",
    "System": "系統",
    "Light": "淺色",
    "Dark": "深色",
    "Opened: {path}": "已開啟：{path}",
    "Panes shown": "面板已顯示",
    "Panes hidden": "面板已隱藏",
    "{count} items": "{count} 個項目",
    "Select one or more items to run batch operations": "請選擇一個或多個項目以執行批次作業",
    "Export completed successfully": "匯出已成功完成",
    "Export cancelled": "匯出已取消",
    "Import completed successfully": "匯入已成功完成",
    "Import cancelled": "匯入已取消",
    "Viewing {library} - {media_type}": "正在檢視 {library} - {media_type}",
    "No libraries found. Please create a library to get started.": "找不到媒體庫。請先建立一個媒體庫。",
    "Queue cleared": "佇列已清空",
    "Added {count} items to scan queue": "已將 {count} 個項目加入掃描佇列",
    "Loaded {count} media items": "已載入 {count} 個媒體項目",
    "Activated: {title}": "已開啟：{title}",
    "Editing: {title}": "正在編輯：{title}",
    "Playing: {path}": "正在播放：{path}",
    "Created and added tag '{tag}' to {title}": "已建立標籤「{tag}」並加到 {title}",
    "Error creating tag: {error}": "建立標籤時發生錯誤：{error}",
    "Removed tag '{tag}' from {title}": "已從 {title} 移除標籤「{tag}」",
    "Added tag '{tag}' to {title}": "已將標籤「{tag}」加到 {title}",
    "Error toggling tag: {error}": "切換標籤時發生錯誤：{error}",
    "Removed {title} from favorites": "已將 {title} 從最愛中移除",
    "Added {title} to favorites": "已將 {title} 加入最愛",
    "Error toggling favorite: {error}": "切換收藏狀態時發生錯誤：{error}",
    "Library '{name}' created": "已建立資料庫「{name}」",
    "Library '{name}' updated": "已更新資料庫「{name}」",
    "Library deleted": "資料庫已刪除",
    "{title} Settings": "{title} 設定",
}

TRANSLATIONS: Dict[str, Dict[str, str]] = {
    "zh": ZH_SIMPLIFIED,
    "zh-CN": ZH_SIMPLIFIED,
    "zh-TW": ZH_TRADITIONAL,
}


def get_available_languages() -> list[str]:
    """Return the language codes exposed in the UI."""
    return list(AVAILABLE_LANGUAGES)


def get_language_label(language_code: str) -> str:
    """Return a human-friendly label for a language code."""
    return LANGUAGE_LABELS.get(language_code, language_code)


def _normalize_language(code: str | None) -> str:
    if not code:
        return DEFAULT_LANGUAGE
    normalized = code.replace("_", "-")
    parts = normalized.split("-", maxsplit=1)
    if len(parts) == 1:
        return parts[0].lower()
    return f"{parts[0].lower()}-{parts[1].upper()}"


def _language_candidates(code: str) -> Iterable[str]:
    normalized = _normalize_language(code)
    yield normalized
    if "-" in normalized:
        yield normalized.split("-")[0]
    if normalized != DEFAULT_LANGUAGE:
        yield DEFAULT_LANGUAGE


def translate(text: str) -> str:
    """Translate a UI string into the active language when possible."""
    try:
        language = get_settings().get_language()
    except Exception:
        language = DEFAULT_LANGUAGE

    for candidate in _language_candidates(language):
        table = TRANSLATIONS.get(candidate)
        if table and text in table:
            return table[text]
    return text
