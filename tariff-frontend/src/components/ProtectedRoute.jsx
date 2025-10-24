import { useEffect, useState } from "react";
import { Outlet } from "react-router-dom";
import { verifyJWT } from "../api/axiosClient";
import { Spinner } from "./ui/shadcn-io/spinner";
import { useAuth } from "@/utils/AuthContext";
import { logout } from "@/utils/logout";

export default function ProtectedRoute() {
    const { setUser } = useAuth();
    const [isLoading, setIsLoading] = useState(true);

    useEffect(() => {
        const verifyToken = async () => {
            try {
                const token = localStorage.getItem("accessToken");
                if (!token) {
                    throw new Error("No token");
                }

                await verifyJWT(token);
                setIsLoading(false);
            } catch {
                logout(setUser);
            }
        };

        verifyToken();
    }, []);

    if (isLoading) {
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

    return <Outlet />;
}
