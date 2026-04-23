import os
import re
import shutil
import yt_dlp
from typing import Optional
from urllib.parse import urlparse
from dotenv import load_dotenv

load_dotenv()


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
    BASE_DIR = os.path.dirname(__file__)

    def __init__(self):
        os.makedirs(self.DOWNLOAD_DIR, exist_ok=True)
        self.ffmpeg_path = _find_ffmpeg_path()
        self.has_ffmpeg = self.ffmpeg_path is not None
        
        # 核心通用配置：初始请求头（不包含 Referer，后续动态注入）
        self.common_ytdl_opts = {
            'quiet': True,
            'no_warnings': True,
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
                'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            }
        }

    def _get_referer(self, url: str) -> str:
        """根据 URL 提取合适的 Referer"""
        try:
            parsed = urlparse(url)
            if not parsed.netloc:
                return "https://www.douyin.com/"
            return f"https://{parsed.netloc}/"
        except Exception:
            return "https://www.douyin.com/"

    @staticmethod
    def _is_bilibili_url(url: str) -> bool:
        try:
            host = urlparse(url).netloc.lower()
        except Exception:
            return False

        return any(
            domain in host
            for domain in ("bilibili.com", "b23.tv", "bili2233.cn")
        )

    def _get_bilibili_cookiefile(self) -> Optional[str]:
        cookiefile = os.getenv("BILIBILI_COOKIE_FILE", "").strip()
        if not cookiefile:
            return None

        cookiefile = os.path.expanduser(cookiefile)
        if not os.path.isabs(cookiefile):
            cookiefile = os.path.join(self.BASE_DIR, cookiefile)

        return cookiefile if os.path.exists(cookiefile) else None

    def _apply_site_options(self, ydl_opts: dict, url: str) -> dict:
        """Apply platform-specific yt-dlp options without changing download logic."""
        if not self._is_bilibili_url(url):
            return ydl_opts

        headers = ydl_opts.setdefault("http_headers", {})
        headers.update({
            "Referer": "https://www.bilibili.com/",
            "Origin": "https://www.bilibili.com",
        })

        cookiefile = self._get_bilibili_cookiefile()
        if cookiefile:
            ydl_opts["cookiefile"] = cookiefile

        return ydl_opts

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
        # 预操作：从可能包含文字的粘贴内容中提取真实 URL
        import re
        url_match = re.search(r"https?://[^\s]+", url)
        if url_match:
            url = url_match.group(0)

        # 动态设置 Referer
        referer = self._get_referer(url)
        
        ydl_opts = self.common_ytdl_opts.copy()
        ydl_opts['http_headers'] = self.common_ytdl_opts['http_headers'].copy()
        ydl_opts['http_headers']['Referer'] = referer
        
        ydl_opts.update({
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
        })
        self._apply_site_options(ydl_opts, url)
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
        从 yt-dlp 解析出的原始元数据中过滤、提取并整理成前端可用的统一格式列表。
        返回 (video_formats, audio_formats) 两个列表。
        
        解析逻辑：
        - 视频格式：优先选择包含音频的流；对于音画分离的流（Dash/HLS），标记为需合并 bestaudio。
        - 去重逻辑：同分辨率和同后缀的流只保留一个，避免列表过长。
        - 排序：按高度 (Resolution) 降序排列。
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
                # 如果没有解析出高度，给一个默认值 0 避免失败，但在标签中标记为 Auto
                actual_height = height or 0

                # 去重 key：同分辨率+格式只取一个
                key = (actual_height, ext)
                if key in seen_video_keys:
                    continue
                seen_video_keys.add(key)

                resolution_label = f"{actual_height}p" if actual_height > 0 else "Auto"

                if has_audio:
                    # 已包含音频，直接可用
                    label = f"{resolution_label} · {ext.upper()}"
                    if size_label:
                        label += f" · {size_label}"
                    download_format_id = format_id
                    audio_badge = True
                else:
                    # 仅视频流，下载时需要合并最佳音频
                    label = f"{resolution_label} · {ext.upper()}"
                    if size_label:
                        label += f" · {size_label}"
                    # 使用 yt-dlp 合并格式：当前视频流 + 最佳音频
                    download_format_id = f"{format_id}+bestaudio/best"
                    audio_badge = True  # 下载后会有音频

                video_results.append({
                    "format_id": download_format_id,
                    "ext": ext,
                    "resolution": f"{f.get('width', '?')}x{actual_height if actual_height > 0 else '?'}",
                    "height": actual_height,
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

    def download_video(self, url: str, format_id: str, is_audio_only: bool = False, progress_callback=None) -> dict:
        """
        执行实际的下载操作并支持进度回传。
        """

        def _progress_hook(d):
            if progress_callback:
                # 识别当前下载的是视频还是音频
                info = d.get("info_dict", {})
                download_type = "video"
                if info.get("vcodec") == "none":
                    download_type = "audio"
                elif info.get("acodec") == "none":
                    download_type = "video"
                
                data = {
                    "status": d.get("status"),
                    "download_type": download_type,
                    "downloaded_bytes": d.get("downloaded_bytes", 0),
                    "total_bytes": d.get("total_bytes") or d.get("total_bytes_estimate", 0),
                    "speed": d.get("speed"),
                    "eta": d.get("eta"),
                }
                if data["total_bytes"] > 0:
                    data["progress_percent"] = round((data["downloaded_bytes"] / data["total_bytes"]) * 100, 2)
                else:
                    data["progress_percent"] = 0
                progress_callback(data)

        # 如果没有 ffmpeg，无法合并流，回退到单流最佳
        if not self.has_ffmpeg and ("+" in format_id or format_id.endswith("/best")):
            format_id = "best"

        # 动态设置 Referer
        referer = self._get_referer(url)

        ydl_opts = self.common_ytdl_opts.copy()
        ydl_opts['http_headers'] = self.common_ytdl_opts['http_headers'].copy()
        ydl_opts['http_headers']['Referer'] = referer

        ydl_opts.update({
            "format": format_id,
            "outtmpl": os.path.join(self.DOWNLOAD_DIR, "%(title)s.%(ext)s"),
            "noplaylist": True,
            "progress_hooks": [_progress_hook],
        })
        self._apply_site_options(ydl_opts, url)

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
        ydl_opts = self.common_ytdl_opts.copy()
        ydl_opts['http_headers'] = self.common_ytdl_opts['http_headers'].copy()
        ydl_opts.update({
            "format": format_id,
            "quiet": True,
            "no_warnings": True,
            "noplaylist": True,
        })
        self._apply_site_options(ydl_opts, url)

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
