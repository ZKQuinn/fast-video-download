/**
 * 后端 API 接口基础路径
 */
const API_BASE = 'http://127.0.0.1:8000/api';

/**
 * 封装前端与后端的交互方法
 */
export const api = {
    /**
     * 调用后端接口解析视频链接
     * @param {string} url 
     */
    async parseVideo(url) {
        const response = await fetch(`${API_BASE}/parse`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ url })
        });
        
        if (!response.ok) {
            let err = 'Failed to parse video';
            try {
                const data = await response.json();
                err = data.detail || err;
            } catch (e) {}
            throw new Error(err);
        }
        
        return await response.json();
    },

    /**
     * 获取封面图代理链接（处理防盗链问题）
     * @param {string} url 原始封面图 URL
     */
    getProxyUrl(url) {
        if (!url) return '';
        return `${API_BASE}/proxy/thumbnail?url=${encodeURIComponent(url)}`;
    },

    /**
     * 执行下载任务并处理文件保存
     * @param {string} url 视频链接
     * @param {string} format_id 选择的画质/格式 ID
     * @param {boolean} is_audio_only 是否仅下载音频
     */
    async downloadVideo(url, format_id, is_audio_only = false) {
        // 向后端发起下载请求
        const response = await fetch(`${API_BASE}/download`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ url, format_id, is_audio_only })
        });

        if (!response.ok) {
             throw new Error('下载失败，请稍后重试');
        }

        // 从响应头解析文件名 (支持 UTF-8 编码的特殊字符)
        const contentDisposition = response.headers.get('Content-Disposition');
        let filename = 'video_download.mp4';
        if (contentDisposition) {
            // 解析兼容 RFC 5987 的文件名格式
            const utf8Match = contentDisposition.match(/filename\*=UTF-8''(.+?)(?:;|$)/i);
            const stdMatch = contentDisposition.match(/filename="(.+?)"/);
            if (utf8Match && utf8Match[1]) {
                filename = decodeURIComponent(utf8Match[1]);
            } else if (stdMatch && stdMatch[1]) {
                filename = stdMatch[1];
            }
        }

        // 将媒体流转换为 Blob 对象
        const blob = await response.blob();
        // 创建临时的对象 URL 并发起浏览器下载动作
        const objectUrl = URL.createObjectURL(blob);
        
        const a = document.createElement('a');
        a.style.display = 'none';
        a.href = objectUrl;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        
        // 清理现场：移除元素并释放 URL 对象占用内存
        document.body.removeChild(a);
        URL.revokeObjectURL(objectUrl);
    }
};
