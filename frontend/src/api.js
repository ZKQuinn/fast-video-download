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
     * 获取封面图代理链接
     */
    getProxyUrl(url) {
        if (!url) return '';
        return `${API_BASE}/proxy/thumbnail?url=${encodeURIComponent(url)}`;
    },

    /**
     * 第一步：向后端申请准备视频（支持进度反馈）
     */
    async prepareDownload(url, format_id, is_audio_only = false) {
        const response = await fetch(`${API_BASE}/download/prepare`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ url, format_id, is_audio_only })
        });
        if (!response.ok) throw new Error('Failed to start server download');
        return await response.json(); // { task_id }
    },

    /**
     * 第二步：轮询下载进度
     */
    async getTaskStatus(taskId) {
        const response = await fetch(`${API_BASE}/task/status/${taskId}`);
        if (!response.ok) return { status: 'failed', progress: 0 };
        return await response.json();
    },

    /**
     * 第三步：触发浏览器真正的文件下载
     */
    downloadFile(taskId) {
        window.location.href = `${API_BASE}/download/fetch/${taskId}`;
    }
};
