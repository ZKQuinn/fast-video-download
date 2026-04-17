import os
import re
import shutil
import yt_dlp
from typing import Optional


def _find_ffmpeg_path() -> Optional[str]:
    """查找 ffmpeg 可执行文件路径"""
    if shutil.which("ffmpeg"):
        return os.path.dirname(shutil.which("ffmpeg"))
    try:
        import static_ffmpeg
        paths = static_ffmpeg.run.get_or_fetch_platform_executables_else_raise()
        return os.path.dirname(paths[0])
    except Exception:
        return None


class VideoDownloader:
    """yt-dlp 封装层，提供视频解析、下载、直链获取能力"""

    DOWNLOAD_DIR = os.path.join(os.path.dirname(__file__), "downloads")

    def __init__(self):
        os.makedirs(self.DOWNLOAD_DIR, exist_ok=True)
        self.ffmpeg_path = _find_ffmpeg_path()
        self.has_ffmpeg = self.ffmpeg_path is not None

    @staticmethod
    def _sanitize_filename(name: str) -> str:
        return re.sub(r'[\\/*?:"<>|]', "_", name)

    @staticmethod
    def _format_filesize(size: Optional[int]) -> str:
        if not size:
            return ""
        if size < 1024 * 1024:
            return f"{size / 1024:.0f}KB"
        if size < 1024 * 1024 * 1024:
            return f"{size / (1024 * 1024):.1f}MB"
        return f"{size / (1024 * 1024 * 1024):.2f}GB"

    @staticmethod
    def _format_duration(seconds: Optional[int]) -> str:
        if not seconds:
            return "00:00"
        hours, remainder = divmod(int(seconds), 3600)
        minutes, secs = divmod(remainder, 60)
        if hours:
            return f"{hours}:{minutes:02d}:{secs:02d}"
        return f"{minutes}:{secs:02d}"

    def parse_video(self, url: str) -> dict:
        """解析视频信息，不下载文件（优化速度）"""
        ydl_opts = {
            "quiet": True,
            "no_warnings": True,
            "extract_flat": False,
            "noplaylist": True,
            # 优化：跳过章节/评论/关系等非必要信息
            "skip_download": True,
            "writethumbnail": False,
            "writeinfojson": False,
            "writesubtitles": False,
            "writeautomaticsub": False,
            # 限制格式获取数量，加速解析
            "extractor_args": {
                "youtube": {"skip": ["hls", "dash"]},
            },
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)

        if not info:
            raise ValueError("无法解析该链接")

        video_formats, audio_formats = self._extract_formats(info)
        platform = info.get("extractor", info.get("extractor_key", "Unknown"))

        return {
            "id": info.get("id", ""),
            "title": info.get("title", "未知标题"),
            "thumbnail": info.get("thumbnail", ""),
            "duration": info.get("duration"),
            "duration_string": self._format_duration(info.get("duration")),
            "uploader": info.get("uploader", info.get("channel", "未知")),
            "platform": platform,
            "view_count": info.get("view_count"),
            "upload_date": info.get("upload_date", ""),
            "description": (info.get("description") or "")[:200],
            # 视频格式和音频格式分开返回
            "formats": video_formats,
            "audio_formats": audio_formats,
        }

    def _extract_formats(self, info: dict) -> tuple[list, list]:
        """
        从 yt-dlp info 中提取并整理可用格式。
        返回 (video_formats, audio_formats) 两个列表。
        
        关键规则：
        - 视频格式：始终包含音频（有音频流的优先；无音频的视频流自动标记为需合并 bestaudio）
        - 音频格式：纯音频流，单独列在下方
        - 按清晰度从高到低排序
        """
        raw_formats = info.get("formats", [])
        if not raw_formats:
            return [], []

        video_results = []
        audio_results = []
        seen_video_keys = set()
        seen_audio_keys = set()

        for f in raw_formats:
            vcodec = f.get("vcodec", "none") or "none"
            acodec = f.get("acodec", "none") or "none"
            height = f.get("height")
            ext = f.get("ext", "mp4")
            format_id = f.get("format_id", "")

            has_video = vcodec != "none" and vcodec != ""
            has_audio = acodec != "none" and acodec != ""

            filesize = f.get("filesize") or f.get("filesize_approx")
            size_label = self._format_filesize(filesize)

            if has_video:
                # --- 视频格式处理 ---
                if not height:
                    continue  # 跳过无分辨率信息的流

                # 去重 key：同分辨率+格式只取一个
                key = (height, ext)
                if key in seen_video_keys:
                    continue
                seen_video_keys.add(key)

                if has_audio:
                    # 已包含音频，直接可用
                    label = f"{height}p · {ext.upper()}"
                    if size_label:
                        label += f" · {size_label}"
                    download_format_id = format_id
                    audio_badge = True
                else:
                    # 仅视频流，下载时需要合并最佳音频
                    label = f"{height}p · {ext.upper()}"
                    if size_label:
                        label += f" · {size_label}"
                    # 使用 yt-dlp 合并格式：当前视频流 + 最佳音频
                    download_format_id = f"{format_id}+bestaudio/best"
                    audio_badge = True  # 下载后会有音频

                video_results.append({
                    "format_id": download_format_id,
                    "ext": ext,
                    "resolution": f"{f.get('width', '?')}x{height}",
                    "height": height,
                    "filesize": filesize,
                    "vcodec": vcodec,
                    "acodec": acodec if has_audio else "merged",
                    "has_audio": audio_badge,
                    "label": label,
                    "abr": f.get("abr"),
                })

            elif has_audio and not has_video:
                # --- 纯音频格式处理 ---
                abr = f.get("abr") or f.get("tbr") or 0
                key = (ext, int(abr or 0) // 10)  # 相近码率去重
                if key in seen_audio_keys:
                    continue
                seen_audio_keys.add(key)

                abr_label = f"{int(abr)}kbps" if abr else "Auto"
                label = f"{ext.upper()} · {abr_label}"
                if size_label:
                    label += f" · {size_label}"

                audio_results.append({
                    "format_id": format_id,
                    "ext": ext,
                    "resolution": "Audio",
                    "height": 0,
                    "filesize": filesize,
                    "vcodec": "none",
                    "acodec": acodec,
                    "has_audio": True,
                    "label": label,
                    "abr": abr,
                })

        # 按清晰度从高到低排序（视频），按码率从高到低排序（音频）
        video_results.sort(key=lambda x: x["height"], reverse=True)
        audio_results.sort(key=lambda x: x.get("abr") or 0, reverse=True)

        # 如果没有任何视频格式，添加一个通用最佳格式兜底
        if not video_results:
            video_results.append({
                "format_id": "bestvideo+bestaudio/best",
                "ext": "mp4",
                "resolution": "Auto",
                "height": 9999,
                "filesize": None,
                "vcodec": "auto",
                "acodec": "merged",
                "has_audio": True,
                "label": "最佳质量 (自动)",
                "abr": None,
            })

        return video_results[:12], audio_results[:6]

    def download_video(self, url: str, format_id: str, is_audio_only: bool = False) -> dict:
        """下载视频到服务器临时目录，返回文件路径和元数据"""

        # 如果没有 ffmpeg，无法合并流，回退到单流最佳
        if not self.has_ffmpeg and ("+" in format_id or format_id.endswith("/best")):
            format_id = "best"

        ydl_opts = {
            "format": format_id,
            "outtmpl": os.path.join(self.DOWNLOAD_DIR, "%(title)s.%(ext)s"),
            "quiet": True,
            "no_warnings": True,
            "noplaylist": True,
        }

        if self.has_ffmpeg:
            ydl_opts["ffmpeg_location"] = self.ffmpeg_path
            ydl_opts["merge_output_format"] = "mp4"

        # 纯音频模式：转成 mp3
        if is_audio_only:
            ydl_opts["format"] = format_id
            ydl_opts["postprocessors"] = [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }] if self.has_ffmpeg else []

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)

        if not info:
            raise ValueError("下载失败")

        title = self._sanitize_filename(info.get("title", "video"))
        ext = "mp3" if is_audio_only and self.has_ffmpeg else info.get("ext", "mp4")
        filename = f"{title}.{ext}"
        filepath = os.path.join(self.DOWNLOAD_DIR, filename)

        # 文件路径回退查找
        if not os.path.exists(filepath):
            prepared = ydl.prepare_filename(info)
            if os.path.exists(prepared):
                filepath = prepared
                filename = os.path.basename(prepared)
            else:
                # 兜底：在 downloads 目录中找包含 title 的最新文件
                matched = [
                    f for f in os.listdir(self.DOWNLOAD_DIR)
                    if title[:20] in f
                ]
                if matched:
                    matched.sort(key=lambda f: os.path.getmtime(
                        os.path.join(self.DOWNLOAD_DIR, f)), reverse=True)
                    filename = matched[0]
                    filepath = os.path.join(self.DOWNLOAD_DIR, filename)

        return {
            "filepath": filepath,
            "filename": filename,
            "title": info.get("title", "video"),
            "ext": ext,
        }

    def get_direct_url(self, url: str, format_id: str) -> dict:
        """获取视频直链"""
        ydl_opts = {
            "format": format_id,
            "quiet": True,
            "no_warnings": True,
            "noplaylist": True,
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)

        if not info:
            raise ValueError("无法获取直链")

        direct_url = info.get("url")
        if not direct_url:
            requested = info.get("requested_formats")
            if requested and len(requested) > 0:
                direct_url = requested[0].get("url")

        if not direct_url:
            raise ValueError("该视频不支持直链下载，请使用服务端下载模式")

        return {
            "direct_url": direct_url,
            "ext": info.get("ext", "mp4"),
            "filesize": info.get("filesize") or info.get("filesize_approx"),
            "title": info.get("title", "video"),
        }
