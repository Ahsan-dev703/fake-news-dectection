const API_BASE_URL = "http://127.0.0.1:5000";

export const apiService = {
  async analyzeText(text) {
    const response = await fetch(`${API_BASE_URL}/predict`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text }),
    });
    return response.json();
  },

  async analyzeImage(file, { quality = 0.8, onProgress = null } = {}) {
    // Compress image client-side using canvas to reduce upload size
    const compressToBlob = (file, quality) =>
      new Promise((resolve, reject) => {
        const img = new Image();
        const url = URL.createObjectURL(file);
        img.onload = () => {
          const canvas = document.createElement("canvas");
          const maxDim = 1600;
          let w = img.width;
          let h = img.height;
          if (Math.max(w, h) > maxDim) {
            const scale = maxDim / Math.max(w, h);
            w = Math.round(w * scale);
            h = Math.round(h * scale);
          }
          canvas.width = w;
          canvas.height = h;
          const ctx = canvas.getContext("2d");
          ctx.drawImage(img, 0, 0, w, h);
          canvas.toBlob(
            (blob) => {
              URL.revokeObjectURL(url);
              resolve(blob);
            },
            "image/jpeg",
            quality,
          );
        };
        img.onerror = (e) => reject(e);
        img.src = url;
      });

    const blob = await compressToBlob(file, quality);

    return new Promise((resolve, reject) => {
      const xhr = new XMLHttpRequest();
      xhr.open("POST", `${API_BASE_URL}/api/v1/image/upload`, true);
      xhr.onreadystatechange = () => {
        if (xhr.readyState === 4) {
          try {
            const json = JSON.parse(xhr.responseText);
            resolve(json);
          } catch (e) {
            reject(e);
          }
        }
      };
      if (onProgress && xhr.upload) {
        xhr.upload.onprogress = (ev) => {
          if (ev.lengthComputable) onProgress(ev.loaded / ev.total);
        };
      }
      const fd = new FormData();
      fd.append("file", blob, file.name.replace(/\.[^/.]+$/, ".jpg"));
      xhr.send(fd);
    });
  },

  async analyzeVideo(file, { onProgress = null, async = false } = {}) {
    // Use XHR to provide upload progress information. Append async flag to query
    return new Promise((resolve, reject) => {
      const xhr = new XMLHttpRequest();
      const url = `${API_BASE_URL}/api/v1/video/upload${async ? "?async=true" : ""}`;
      xhr.open("POST", url, true);
      xhr.onreadystatechange = () => {
        if (xhr.readyState === 4) {
          try {
            const json = JSON.parse(xhr.responseText);
            resolve(json);
          } catch (e) {
            reject(e);
          }
        }
      };
      if (onProgress && xhr.upload) {
        xhr.upload.onprogress = (ev) => {
          if (ev.lengthComputable) onProgress(ev.loaded / ev.total);
        };
      }
      const fd = new FormData();
      fd.append("file", file);
      xhr.send(fd);
    });
  },

  async analyzeYouTube(url, { async = true, cookies = null } = {}) {
    const response = await fetch(`${API_BASE_URL}/api/v1/video/youtube`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ url, async, cookies }),
    });
    return response.json();
  },

  async pollJob(jobId) {
    const response = await fetch(`${API_BASE_URL}/api/v1/job/${jobId}`);
    return response.json();
  },
};
