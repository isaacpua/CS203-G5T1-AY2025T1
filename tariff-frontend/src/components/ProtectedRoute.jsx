import { useEffect, useState } from "react";
import { Navigate, Outlet, useLocation } from "react-router-dom";
import axiosClient from "../api/axiosClient";
import { Spinner } from "./ui/shadcn-io/spinner";

export default function ProtectedRoute() {
    const location = useLocation();
    const [authState, setAuthState] = useState("loading");

    useEffect(() => {
        const verifyToken = async () => {
            try {
                const token = localStorage.getItem("accessToken");
                if (!token) {
                    console.log("No token found");
                    setAuthState("unauthenticated");
                    return;
                }

                console.log("Token found, verifying...");
                await axiosClient.post("/auth/verifyJWT", {}, {
                    headers: {
                        Authorization: `Bearer ${token}`,
                    },
                });
                console.log("Token is valid");
                setAuthState("authenticated");
            } catch (error) {
                console.log("Token is invalid or error occurred", error);
                setAuthState("unauthenticated");
            }
        };

        verifyToken();
    }, []);

    if (authState === "loading") {
        return (
            <div
                className="flex flex-col items-center justify-center gap-4 mt-30 p-10"
            >
                <Spinner variant={"infinte"} className="text-blue-500" size={64} />
                <span className="font-mono text-muted-foreground text-xl">
                    Please wait while we check if you are authenticated...
                </span>
            </div>
        );
    }

    if (authState === "unauthenticated") {
        return <Navigate to="/login" replace state={{ from: location }} />;
    }

    // Render nested routes
    return <Outlet />;
}
