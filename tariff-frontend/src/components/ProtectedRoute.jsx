import { useEffect, useState } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import axiosClient from "../api/axiosClient";

export default function ProtectedRoute({ children }) {
    const location = useLocation();
    const navigate = useNavigate()

    useEffect(() => {
        const verifyToken = async () => {
            try {
                const token = localStorage.getItem("accessToken");
                if (!token) { // no token found
                    console.log("No token found");
                    return navigate("/login", {replace: true, state: { from: location }});
                }

                // token found
                console.log("Token found, verifying...");
                await axiosClient.post("/auth/verifyJWT", {}, {
                    headers: {
                        Authorization: `Bearer ${token}`,
                    },
                });
                console.log("Token is valid");
            } catch (error) {
                console.log("Token is invalid or error occurred", error);
                return navigate("/login", {replace: true, state: { from: location }});
            }
        }
        verifyToken();
    })
    return children;
}