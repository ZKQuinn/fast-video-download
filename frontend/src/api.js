const API_BASE = 'http://127.0.0.1:8000/api';

export const api = {
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

    getProxyUrl(url) {
        if (!url) return '';
        return `${API_BASE}/proxy/thumbnail?url=${encodeURIComponent(url)}`;
    },

    getDownloadUrl(url, format_id, is_audio_only = false) {
        const params = new URLSearchParams({
            url: url,
            format_id: format_id,
            is_audio_only: is_audio_only
        });
        // We will do a direct browser download approach, so we need to encode everything
        // Or we can do a fetch and blob download if we want to show progress
        return params; // Not directly used as url in <a> yet
    },

    async downloadVideo(url, format_id, is_audio_only = false, onProgress) {
        // Implementation for downloading via fetch to get a Blob (useful if we want progress,
        // but simple link click is easier. Since this is a backend stream, fetch also works if we don't care about memory limits for small vids.
        // For '万能下载', videos can be large. It's better to construct a POST request using a hidden form or 
        // downloading it via a standard POST fetch and Object URL.
        
        const response = await fetch(`${API_BASE}/download`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ url, format_id, is_audio_only })
        });

        if (!response.ok) {
             throw new Error('Download failed');
        }

        const contentDisposition = response.headers.get('Content-Disposition');
        let filename = 'video_download.mp4';
        if (contentDisposition) {
            const match = contentDisposition.match(/filename="(.+?)"/);
            if (match && match.length === 2) {
                filename = match[1];
            }
        }

        const blob = await response.blob();
        const objectUrl = URL.createObjectURL(blob);
        
        const a = document.createElement('a');
        a.href = objectUrl;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(objectUrl);
    }
};
