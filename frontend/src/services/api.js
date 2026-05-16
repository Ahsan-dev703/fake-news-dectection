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

  async analyzeImage(file) {
    const formData = new FormData();
    formData.append("file", file);
    const response = await fetch(`${API_BASE_URL}/api/v1/image/upload`, {
      method: "POST",
      body: formData,
    });
    return response.json();
  },

  async analyzeVideo(file) {
    const formData = new FormData();
    formData.append("file", file);
    const response = await fetch(`${API_BASE_URL}/api/v1/video/upload`, {
      method: "POST",
      body: formData,
    });
    return response.json();
  },
};
