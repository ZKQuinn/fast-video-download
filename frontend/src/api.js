/**
 * 后端 API 接口基础路径
 */
const API_BASE = 'http://127.0.0.1:8000/api';

/**
 * 封装前端与后端的交互方法
 */
export const api = {
    // 认证相关的 Token 管理
    getToken() {
        return localStorage.getItem('auth_token');
    },

    setToken(token) {
        localStorage.setItem('auth_token', token);
    },

    clearToken() {
        localStorage.removeItem('auth_token');
    },

    getHeaders() {
        const headers = { 'Content-Type': 'application/json' };
        const token = this.getToken();
        if (token) {
            headers['Authorization'] = `Bearer ${token}`;
        }
        return headers;
    },

    /**
     * 注册逻辑
     */
    async register(email, password) {
        const response = await fetch(`${API_BASE}/auth/register`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email, password })
        });
        if (!response.ok) {
            const data = await response.json();
            throw new Error(data.detail || '注册失败');
        }
        return await response.json();
    },

    /**
     * 登录逻辑
     */
    async login(email, password) {
        const response = await fetch(`${API_BASE}/auth/login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username: email, password }) // 后端 auth.py 期望 username 字段，我们映射为 email
        });
        if (!response.ok) {
            const data = await response.json();
            throw new Error(data.detail || '登录失败');
        }
        const data = await response.json();
        this.setToken(data.access_token);
        return data;
    },

    /**
     * 获取用户信息
     */
    async getMe() {
        if (!this.getToken()) return null;
        const response = await fetch(`${API_BASE}/user/me`, {
            headers: this.getHeaders()
        });
        if (!response.ok) {
            this.clearToken();
            return null;
        }
        return await response.json();
    },

    /**
     * 创建发起 Stripe 支付会话
     */
    async createCheckoutSession() {
        const response = await fetch(`${API_BASE}/stripe/create-checkout-session`, {
            method: 'POST',
            headers: this.getHeaders()
        });
        if (!response.ok) {
            const data = await response.json();
            throw new Error(data.detail || '发起支付失败');
        }
        return await response.json();
    },

    /**
     * 调用后端接口解析视频链接
     */
    async parseVideo(url) {
        const response = await fetch(`${API_BASE}/parse`, {
            method: 'POST',
            headers: this.getHeaders(),
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
     * 第一步：向后端申请准备视频
     */
    async prepareDownload(url, format_id, is_audio_only = false) {
        const response = await fetch(`${API_BASE}/download/prepare`, {
            method: 'POST',
            headers: this.getHeaders(),
            body: JSON.stringify({ url, format_id, is_audio_only })
        });
        if (!response.ok) {
             const data = await response.json();
             throw new Error(data.detail || 'Failed to start server download');
        }
        return await response.json();
    },

    /**
     * 每秒轮询下载进度
     */
    async getTaskStatus(taskId) {
        const response = await fetch(`${API_BASE}/task/status/${taskId}`);
        if (!response.ok) return { status: 'failed', progress: 0 };
        return await response.json();
    },

    /**
     * 触发浏览器真正的文件下载
     */
    downloadFile(taskId) {
        window.location.href = `${API_BASE}/download/fetch/${taskId}`;
    }
};
