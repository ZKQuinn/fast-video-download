import { reactive, computed } from 'vue';

export const locales = {
  zh: {
    navbar: {
      github: "GitHub"
    },
    hero: {
      titleLine1: "极速，全网视频",
      titleLine2: "一键轻松解析下载",
      subtitle: "支持抖音、B站、YouTube 等主流平台，无水印，高清画质。全网平台覆盖，简单易用。",
      inputPlaceholder: "请粘贴视频链接到这里...",
      downloadBtn: "立即解析",
      clearBtn: "清除",
      parsing: "正在解析中..."
    },
    features: {
      f1: { title: "全网平台覆盖", desc: "基于强大的底层引擎，支持主流平台包括 YouTube, Bilibili, 抖音, X/Twitter 等，几乎覆盖全网。" },
      f2: { title: "安全且纯粹", desc: "所有解析均在服务端或本地进行。没有烦人的广告，没有隐藏的弹窗，给你最极客的下载体验。" },
      f3: { title: "多画质自由选", desc: "从 4K 超清到 480P 标清，或是纯音频提取，自由掌控你的下载需求。" }
    },
    platforms: {
      title: "支持的平台",
      subtitle: "兼容几乎所有主流视频与音频网站，复制链接即可下载。"
    },
    footer: {
      madeWith: "为您精心制作",
      forYou: "由我",
      poweredBy: "基于 yt-dlp 与 Vue 3 驱动",
      disclaimer1: "免责声明: 本项目仅用于技术学习和研究目的。",
      disclaimer2: "请用户仅下载自己拥有版权或已获得合法授权的内容。用户应自行遵守所在地区的法律法规及各平台的服务条款。",
      copyRight: "© 2024 Fast Video Download. 保留所有权利。"
    },
    videoResult: {
      duration: "时长:",
      playCount: "播放:",
      resolution: "解析度:",
      platform: "平台:",
      unknown: "未知",
      videoTitlePlaceholder: "未知标题",
      videoFormatsTitle: "画质选择 (已自动融合音频)",
      audioFormatsTitle: "纯音频提取",
      downloadButton: "下载此格式",
      downloading: "正在下载...",
      errorDownloadFailed: "下载失败：",
      resUnit: "p",
      auto: "自动",
      containsAudio: "🔊 含音频",
      audioOnly: "🎵 纯音频"
    },
    app: {
      errorInvalidUrl: "请输入有效的 HTTP/HTTPS 链接",
      errorParseFailed: "解析失败: ",
      defaultError: "解析失败，请检查链接或稍后重试。"
    }
  },
  en: {
    navbar: {
      github: "GitHub"
    },
    hero: {
      titleLine1: "Fast & Professional",
      titleLine2: "Video Downloader",
      subtitle: "Support Douyin, Bilibili, YouTube and more. No watermark, HD quality. Simple and easy to use.",
      inputPlaceholder: "Paste video link here...",
      downloadBtn: "Parse Now",
      clearBtn: "Clear",
      parsing: "Parsing..."
    },
    features: {
      f1: { title: "Global Platform Coverage", desc: "Powered by a robust core engine, supporting YouTube, Bilibili, Douyin, X/Twitter and more." },
      f2: { title: "Safe & Pure", desc: "All parsing runs securely either server-side or locally. No annoying ads, no pop-ups." },
      f3: { title: "Resolution Freedom", desc: "From 4K ultra-HD to 480P or audio-only extraction, take full control of your downloads." }
    },
    platforms: {
      title: "Supported Platforms",
      subtitle: "Compatible with almost all mainstream video and audio websites. Just copy and paste."
    },
    footer: {
      madeWith: "Made with",
      forYou: "for you",
      poweredBy: "Powered by yt-dlp & Vue 3.",
      disclaimer1: "Disclaimer: This project is for technical learning and research purposes only.",
      disclaimer2: "Please only download content you own or have legal authorization for. Users are responsible for complying with local laws and platform terms.",
      copyRight: "© 2024 Fast Video Download. All Rights Reserved."
    },
    videoResult: {
      duration: "Duration:",
      playCount: "Views:",
      resolution: "Resolution:",
      platform: "Platform:",
      unknown: "Unknown",
      videoTitlePlaceholder: "Unknown Title",
      videoFormatsTitle: "Video Resolutions (Audio Merged)",
      audioFormatsTitle: "Audio Only Extraction",
      downloadButton: "Download",
      downloading: "Downloading...",
      errorDownloadFailed: "Download failed: ",
      resUnit: "p",
      auto: "Auto",
      containsAudio: "🔊 Has Audio",
      audioOnly: "🎵 Audio Only"
    },
    app: {
      errorInvalidUrl: "Please enter a valid HTTP/HTTPS url",
      errorParseFailed: "Parse failed: ",
      defaultError: "Parse failed, please check the link or try again later."
    }
  }
};

const state = reactive({
  currentLanguage: 'zh'
});

export const i18n = {
  get current() { return state.currentLanguage; },
  set current(lang) { state.currentLanguage = lang; },
  toggle() { state.currentLanguage = state.currentLanguage === 'zh' ? 'en' : 'zh'; }
};

export function useI18n() {
  const t = computed(() => locales[state.currentLanguage]);
  return { t, i18n };
}
