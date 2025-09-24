import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert"
import { logout } from "@/utils/logout";
import { AlertTriangleIcon } from "lucide-react"

export function Relogin({ setUser }) {
    function reloadPage() {
        logout(setUser);
    }
    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80">
            <div className="w-full max-w-md px-4">
                <Alert className="border-yellow-200 bg-yellow-50 text-yellow-800 dark:border-yellow-800 dark:bg-yellow-950/100 dark:text-yellow-200 [&>svg]:text-yellow-600 dark:[&>svg]:text-yellow-400">
                    <AlertTriangleIcon />
                    <AlertTitle>Session Expired</AlertTitle>
                    <AlertDescription>
                        <div>
                            Your session has expired. Please <button style={{cursor: 'pointer'}} onClick={reloadPage} className="underline hover:text-primary">log in</button> again to continue.
                        </div>
                    </AlertDescription>
                </Alert>
            </div>
        </div>
    )
}
