import axios from 'axios';

const axiosClient = axios.create({
  baseURL: 'http://localhost:8080/api/v1', // The base URL of your Spring Boot API
  headers: {
    'Content-Type': 'application/json',
  },
});

export default axiosClient;