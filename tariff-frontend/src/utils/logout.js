export function logout(setUser) {
  setUser?.(null); // in case setUser is passed
  localStorage.removeItem("accessToken");
  window.location.reload();
}
