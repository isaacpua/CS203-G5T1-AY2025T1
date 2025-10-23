import { useState, useEffect } from 'react';
import { AuthContext } from './AuthContext';
import { getRoleFromToken } from './jwtDecoder';

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [userRole, setUserRole] = useState(null);

  useEffect(() => {
    const savedUser = localStorage.getItem("user");
    const savedToken = localStorage.getItem("accessToken");
    // Must have both to be authenticated
    if (savedUser && savedToken) {
      setUser(JSON.parse(savedUser));
      const role = getRoleFromToken(savedToken);
      setUserRole(role);
    } else {
      // If we don't have any, the user shouldn't be logged in
      localStorage.removeItem("user");
      localStorage.removeItem("accessToken")
    }
  }, []);

  const value = {
    user,
    setUser,
    userRole,
    setUserRole,
    isAdmin: userRole === 'admin',
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};
