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
     * 执行下载任务：改用原生浏览器下载方式，以直观显示进度条
     * @param {string} url 视频链接
     * @param {string} format_id 选择的画质/格式 ID
     * @param {boolean} is_audio_only 是否仅下载音频
     */
    async downloadVideo(url, format_id, is_audio_only = false) {
        // 构建带有参数的 GET 请求链接
        const params = new URLSearchParams({
            url: url,
            format_id: format_id,
            is_audio_only: is_audio_only
        });
        
        const downloadUrl = `${API_BASE}/download?${params.toString()}`;
        
        // 直接通过浏览器地址跳转触发下载（后端返回 Content-Disposition: attachment）
        // 这种方式能让浏览器下载管理器接管，从而看到实时的下载进度
        window.location.href = downloadUrl;
    }
};
