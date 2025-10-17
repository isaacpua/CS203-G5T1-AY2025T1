import axios from 'axios';

const axiosClient = axios.create({
  baseURL: "/api/v1",
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

export const verifyJWT = async (token) => {
  await axiosClient.post("/auth/verifyJWT", {}, {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });
};

export const getDashboardData = async (params) => {
  return await axiosClient.get(`/dashboard/tariffs?${params.toString()}`);
};

export const updateTariff = async (id, formData) => {
  await axiosClient.patch(`/dashboard/tariffs/${id.toString()}`, formData);
};

export const createTariff = async (formData) => {
  await axiosClient.post("/dashboard/tariffs", formData);
}

export const deleteTariff = async (id) => {
  await axiosClient.delete(`/dashboard/tariffs/${id.toString()}`);
};

export const getTariffRecommendations = async () => {
  return await axiosClient.get("/tariffs/recommendations");
};

export const getTariffHistory = async (params) => {
  return await axiosClient.get("/tariffs/history", {
    params,
  });
};

export const loginUser = async (credentials) => {
  return await axiosClient.post("/auth/login", credentials);
};

export const getUserData = async (username) => {
  return await axiosClient.get(`/users/${username.toString()}`);
};

export const registerUser = async (credentials) => {
  return await axiosClient.post("/auth/register", credentials);
}

export const updateUsername = async (id, usernameUpdateDTO) => {
  await axiosClient.put(
    `/users/${id.toString()}/username`,
    usernameUpdateDTO
  );
};

export const updatePassword = async (id, newPassword) => {
  await axiosClient.put(`/users/${id.toString()}/password`, {
    password: newPassword.trim(),
  });
};

const URL_PARTNERS_ALL = "/tariffs/countries/partners";
const URL_REPORTERS_ALL = "/tariffs/countries/reporters";
const URL_REPORTERS_FROM = (fromId) => `/tariffs/countries/reporters?fromId=${fromId.toString()}`;
const URL_PARTNERS_BY_TO = (toId) => `/tariffs/countries/partners?toId=${toId.toString()}`;
const URL_SEARCH = "/tariffs/search";
const URL_CALC = "/tariffs/calc";

export const getAllPartnerCountries = async () => {
  return await axiosClient.get(URL_PARTNERS_ALL);
};

export const getAllReporterCountries = async () => {
  return await axiosClient.get(URL_REPORTERS_ALL);
};

export const getReportersFrom = async (fromId) => {
  return await axiosClient.get(URL_REPORTERS_FROM(fromId));
};

export const getPartnersByTo = async (toId) => {
  return await axiosClient.get(URL_PARTNERS_BY_TO(toId));
};

export const searchTariff = async (params) => {
  return await axiosClient.get(`${URL_SEARCH}?${params.toString()}`);
};

export const calculateTariff = async (payload) => {
  return await axiosClient.post(URL_CALC, payload);
};

export const getAllUsers = async () => {
  return await axiosClient.get("/users/");
};

export const updateUsernameAndRole = async (userID, newUsername, newRole) => {
  return await axiosClient.put(`/users/${userID.toString()}`, {
    username: newUsername,
    role: newRole,
  });
};

export const deleteUserByID = async (userID) => {
  return await axiosClient.delete(`/users/${userID.toString()}`);
};

export default axiosClient;
