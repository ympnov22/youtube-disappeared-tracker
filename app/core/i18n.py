"""
Internationalization (i18n) support for YouTube Disappeared Video Tracker.
Provides bilingual support for English and Japanese.
"""

import os
from typing import Any, Dict


class I18n:
    """Simple i18n system for bilingual support (EN/JA)."""

    def __init__(self, default_language: str = "en"):
        self.default_language = default_language
        self.current_language = default_language
        self.translations = self._load_translations()

    def _load_translations(self) -> Dict[str, Dict[str, str]]:
        """Load translation dictionaries."""
        return {
            "en": {
                "nav.channels": "Channels",
                "nav.events": "Events",
                "nav.logged_in_as": "Logged in as",
                "channels.title": "Channels",
                "channels.add_channel": "Add Channel",
                "channels.search_placeholder": "Search channels...",
                "channels.search_button": "Search",
                "channels.clear_search": "Clear",
                "channels.no_channels_title": "No channels yet",
                "channels.no_channels_description": (
                    "Start monitoring YouTube channels by adding your first "
                    "channel below. You can add up to 10 channels to track "
                    "video availability."
                ),
                "channels.add_first_channel": "Add Your First Channel",
                "channels.scan": "Scan",
                "channels.scanning": "Scanning...",
                "channels.delete": "Delete",
                "channels.delete_confirm": (
                    "Are you sure you want to delete this channel?"
                ),
                "events.title": "Disappearance Events",
                "events.filter_all": "All Types",
                "events.filter_private": "Private",
                "events.filter_deleted": "Deleted",
                "events.filter_geo_blocked": "Geo-blocked",
                "events.filter_age_restricted": "Age-restricted",
                "events.filter_unknown": "Unknown",
                "events.no_events_title": "No events yet",
                "events.no_events_description": (
                    "No videos have disappeared yet, or no channels have "
                    "been scanned."
                ),
                "pagination.previous": "← Previous",
                "pagination.next": "Next →",
                "pagination.page_of": "Page {current} of {total}",
                "form.channel_input_placeholder": (
                    "Enter YouTube channel URL, @handle, or channel ID"
                ),
                "form.add_channel": "Add Channel",
                "form.cancel": "Cancel",
                "toast.channel_added": "Channel added successfully",
                "toast.channel_deleted": "Channel deleted successfully",
                "toast.scan_started": "Channel scan started",
                "toast.error_occurred": ("An error occurred. Please try again."),
            },
            "ja": {
                "nav.channels": "チャンネル",
                "nav.events": "イベント",
                "nav.logged_in_as": "ログイン中",
                "channels.title": "チャンネル",
                "channels.add_channel": "チャンネル追加",
                "channels.search_placeholder": "チャンネルを検索...",
                "channels.search_button": "検索",
                "channels.clear_search": "クリア",
                "channels.no_channels_title": "チャンネルがありません",
                "channels.no_channels_description": (
                    "最初のチャンネルを追加してYouTubeチャンネルの監視を開始してください。"
                    "最大10個のチャンネルを追加して動画の可用性を追跡できます。"
                ),
                "channels.add_first_channel": "最初のチャンネルを追加",
                "channels.scan": "スキャン",
                "channels.scanning": "スキャン中...",
                "channels.delete": "削除",
                "channels.delete_confirm": "このチャンネルを削除してもよろしいですか？",
                "events.title": "消失イベント",
                "events.filter_all": "全種別",
                "events.filter_private": "非公開",
                "events.filter_deleted": "削除済み",
                "events.filter_geo_blocked": "地域制限",
                "events.filter_age_restricted": "年齢制限",
                "events.filter_unknown": "不明",
                "events.no_events_title": "イベントがありません",
                "events.no_events_description": "まだ動画が消失していないか、チャンネルがスキャンされていません。",
                "pagination.previous": "← 前へ",
                "pagination.next": "次へ →",
                "pagination.page_of": "{current} / {total} ページ",
                "form.channel_input_placeholder": "YouTubeチャンネルURL、@ハンドル、またはチャンネルIDを入力",
                "form.add_channel": "チャンネル追加",
                "form.cancel": "キャンセル",
                "toast.channel_added": "チャンネルが正常に追加されました",
                "toast.channel_deleted": "チャンネルが正常に削除されました",
                "toast.scan_started": "チャンネルスキャンが開始されました",
                "toast.error_occurred": "エラーが発生しました。もう一度お試しください。",
            },
        }

    def set_language(self, language: str) -> None:
        """Set current language."""
        if language in self.translations:
            self.current_language = language

    def get_language(self) -> str:
        """Get current language."""
        return self.current_language

    def t(self, key: str, **kwargs: Any) -> str:
        """Translate a key to current language with optional formatting."""
        translations = self.translations.get(self.current_language, {})
        text = translations.get(key, key)

        if kwargs:
            try:
                text = text.format(**kwargs)
            except (KeyError, ValueError):
                pass

        return text


i18n = I18n(default_language=os.getenv("DEFAULT_LANGUAGE", "en"))
