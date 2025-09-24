import axios from 'axios';

const axiosClient = axios.create({
  baseURL: 'http://localhost:8080/api/v1',
  headers: {
    'Content-Type': 'application/json',
  },
});

axiosClient.interceptors.request.use((config) => {
  const token = localStorage.getItem("accessToken");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
    // Debug log for troubleshooting JWT Bearer issues
    console.log("[axios] Authorization header:", config.headers.Authorization);
  } else {
    console.log("[axios] No accessToken found in localStorage");
  }
  return config;
});

export default axiosClient;
