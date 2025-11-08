import { useState } from "react"
import { getUserData, loginUser, registerUser } from "@/api/axiosClient"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { useAuth } from "@/utils/AuthContext"
import { decodeJWT, getRoleFromToken } from "@/utils/jwtDecoder"
import { Loader2, AlertCircle, X, Sprout } from "lucide-react"
import { useLocation, useNavigate } from "react-router-dom"
import { motion } from "framer-motion"
import { toast } from "sonner"

const Login = () => {
  const { setUser, setUserRole } = useAuth()
  const [isLogin, setIsLogin] = useState(true)
  const [isLoading, setIsLoading] = useState(false)
  const [username, setUsername] = useState("")
  const [password, setPassword] = useState("")
  const [error, setError] = useState(null)

  const navigate = useNavigate()
  const location = useLocation()
  const from = location.state?.from?.pathname || "/" // Default to landing page

  const handleLogin = async () => {
    setIsLoading(true)
    setError(null)
    try {
      localStorage.removeItem("accessToken")
      const trimmedUsername = username.trim()
      const trimmedPassword = password.trim()
      if (!trimmedUsername || !trimmedPassword) throw "BLANK"
      const credentials = JSON.stringify({ username: trimmedUsername, password: trimmedPassword })
      const response = await loginUser(credentials)
      if (response.status === 200 && response.data?.accessToken) {
        localStorage.setItem("accessToken", response.data.accessToken)
        const role = getRoleFromToken(response.data.accessToken)
        setUserRole(role)
        const decodedJWT = decodeJWT(response.data.accessToken)
        const { data: userData } = await getUserData(decodedJWT.sub)
        localStorage.setItem("user", JSON.stringify(userData.user))
        setUser(userData.user)
        navigate(from, { replace: true })
      } else {
        throw new Error(response.data?.message || "Login failed, please try again.")
      }
    } catch (err) {
      handleAuthError(err)
    } finally {
      setIsLoading(false)
    }
  }

  const handleRegister = async () => {
    setIsLoading(true)
    setError(null)
    try {
      const trimmedUsername = username.trim()
      const trimmedPassword = password.trim()
      if (!trimmedUsername || !trimmedPassword) throw "BLANK"
      const credentials = JSON.stringify({ username: trimmedUsername, password: trimmedPassword })
      const response = await registerUser(credentials)
      if (response.status === 200 && response.data?.success) {
        // console.log(response.data)
        toast.success("Registration successful! Please log in.");
        toggleMode()
      } else {
        throw new Error(response.data?.message || "Registration failed.")
      }
    } catch (err) {
      handleAuthError(err)
    } finally {
      setIsLoading(false)
    }
  }

  const handleAuthError = (err) => {
    if (err === "BLANK") setError("Username or password cannot be blank!")
    else if (err.code === "ERR_NETWORK") setError("Cannot connect to the server. Please try again later.")
    else if (err.response?.data?.message) setError(err.response.data.message)
    else if (err instanceof Error) setError(err.message)
    else {
      // console.error("Login/Register Error:", err)
      setError("An unexpected error occurred. Please try again.")
    }
  }

  // Switch between Login and Register modes
  const toggleMode = () => {
    setIsLogin(!isLogin)
    setError(null)
    setUsername("")
    setPassword("")
  }

  // Configuration object for text based on login/register mode
  const modeConfig = isLogin
    ? {
        title: "Log In",
        description: "Access your TARIFIC dashboard.",
        switchText: "Need an account?",
        switchAction: "Register",
        submitButtonText: "Sign In",
        submitLoadingText: "Signing In...",
      }
    : {
        title: "Get Started",
        description: "Create your TARIFIC account.",
        switchText: "Already have an account?",
        switchAction: "Log In",
        submitButtonText: "Register",
        submitLoadingText: "Registering...",
      }

  return (
    <div className="relative flex items-center justify-center min-h-screen overflow-hidden">
      {/* Video Background */}
      <div className="fixed inset-0 z-0 pointer-events-none">
        <video autoPlay loop muted playsInline className="absolute inset-0 w-full h-full object-cover">
          <source src="/Serenity_Animation.mp4" type="video/mp4" />
        </video>
        <div className="absolute inset-0 bg-black/50" />
      </div>

      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6 }}
        className="    w-[min(92vw,900px)] sm:w-[min(92vw,800px)] mx-4">
        <div className="bg-white/95 dark:bg-card/95 backdrop-blur-xl rounded-3xl shadow-3xl overflow-hidden border border-white/20 p-2 md:p-4">
          {/* Logo and branding */}
          <div className="p-8 pb-6 text-center border-b border-border/50">
            <motion.div
              initial={{ scale: 0 }}
              animate={{ scale: 1 }}
              transition={{ type: "spring", stiffness: 200, delay: 0.2 }}
              className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-primary/10 mb-4"
            >
              <Sprout className="w-8 h-8 text-primary" />
            </motion.div>
            <h2 className="text-2xl font-bold text-foreground">TARIFIC</h2>
            <p className="text-sm text-muted-foreground mt-1">Agricultural Trade Solutions</p>
          </div>

          {/* Form content */}
          <div className="p-8">
            <h1 className="text-xl font-semibold mb-2 text-foreground">{modeConfig.title}</h1>
            <p className="text-muted-foreground mb-6 text-sm">{modeConfig.description}</p>

            <form
              onSubmit={(e) => {
                e.preventDefault()
                isLogin ? handleLogin() : handleRegister()
              }}
              className="space-y-4"
            >
              <div className="space-y-2">
                <Label htmlFor="username">Username</Label>
                <Input
                  id="username"
                  type="text"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  required
                  className="bg-input/50 focus:border-primary focus:ring-primary/20"
                  placeholder="e.g., trader_joe"
                  aria-label="Username"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="password">Password</Label>
                <Input
                  id="password"
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                  className="bg-input/50 focus:border-primary focus:ring-primary/20"
                  placeholder="Enter your password"
                  aria-label="Password"
                />
                {isLogin && (
                  <div className="text-right">
                  </div>
                )}
              </div>

              {error != null && (
                <Alert
                  variant="destructive"
                  className="bg-destructive/10 border-destructive/30 text-destructive"
                  role="alert"
                >
                  <AlertCircle className="h-4 w-4" />
                  <AlertDescription className="flex justify-between items-center text-sm">
                    <span className="flex-1 mr-2">{error}</span>
                    <Button
                      variant="ghost"
                      size="sm"
                      className="h-auto p-1 text-destructive hover:bg-destructive/20"
                      onClick={() => setError(null)}
                      aria-label="Dismiss error"
                    >
                      <X className="h-3 w-3" />
                    </Button>
                  </AlertDescription>
                </Alert>
              )}

              <Button
                type="submit"
                className="w-full bg-primary hover:bg-primary/90 text-primary-foreground text-base py-6 shadow-md hover:shadow-lg transition-all"
                disabled={isLoading}
              >
                {isLoading ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    {modeConfig.submitLoadingText}
                  </>
                ) : (
                  modeConfig.submitButtonText
                )}
              </Button>
            </form>

            <div className="mt-6 text-center text-sm">
              <span className="text-muted-foreground">{modeConfig.switchText}</span>
              <Button
                variant="link"
                onClick={toggleMode}
                className="pl-1 font-semibold text-primary hover:text-primary/80 transition-colors"
              >
                {modeConfig.switchAction}
              </Button>
            </div>
          </div>
        </div>
      </motion.div>
    </div>
  )
}

export default Login
