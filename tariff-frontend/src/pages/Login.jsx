import React, { useState } from "react"; // Added React import
import { getUserData, loginUser, registerUser } from "@/api/axiosClient";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useAuth } from "@/utils/AuthContext";
import { decodeJWT, getRoleFromToken } from "@/utils/jwtDecoder";
import { Loader2, AlertCircle, X, Ship } from "lucide-react"; // Removed unused BarChart
import { useLocation, useNavigate } from "react-router-dom";
import { cn } from "@/lib/utils";
// --- Corrected Recharts Imports ---
import { AreaChart, Area, BarChart, Bar, CartesianGrid, Tooltip, XAxis, YAxis, ResponsiveContainer } from 'recharts';
// Note: defs, linearGradient, stop are NOT imported directly

const Login = () => {
  const { setUser, setUserRole } = useAuth();
  const [isLogin, setIsLogin] = useState(true);
  const [isLoading, setIsLoading] = useState(false);
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState(null);

  const navigate = useNavigate();
  const location = useLocation();
  const from = location.state?.from?.pathname || "/"; // Default to landing page

  // --- Data for the Chart ---
  const chartData = [
    { date: '2014', value: 100, volume: 50 }, { date: '2015', value: 120, volume: 60 },
    { date: '2016', value: 110, volume: 45 }, { date: '2017', value: 130, volume: 70 },
    { date: '2018', value: 125, volume: 55 }, { date: '2019', value: 140, volume: 80 },
    { date: '2020', value: 135, volume: 65 }, { date: '2021', value: 150, volume: 90 },
    { date: '2022', value: 145, volume: 75 }, { date: '2023', value: 160, volume: 95 },
    { date: '2024', value: 155, volume: 85 }, { date: '2025', value: 170, volume: 100 },
  ];
  // --- End Chart Data ---

  // --- Authentication Logic ---
  const handleLogin = async () => {
    setIsLoading(true);
    setError(null);
    try {
      localStorage.removeItem("accessToken");
      const trimmedUsername = username.trim();
      const trimmedPassword = password.trim();
      if (!trimmedUsername || !trimmedPassword) throw "BLANK";
      const credentials = JSON.stringify({ username: trimmedUsername, password: trimmedPassword });
      const response = await loginUser(credentials);
      if (response.status === 200 && response.data?.accessToken) {
        localStorage.setItem("accessToken", response.data.accessToken);
        const role = getRoleFromToken(response.data.accessToken);
        setUserRole(role);
        const decodedJWT = decodeJWT(response.data.accessToken);
        const { data: userData } = await getUserData(decodedJWT.sub);
        localStorage.setItem("user", JSON.stringify(userData.user));
        setUser(userData.user);
        navigate(from, { replace: true });
      } else {
        throw new Error(response.data?.message || "Login failed, please try again.");
      }
    } catch (err) {
      handleAuthError(err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleRegister = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const trimmedUsername = username.trim();
      const trimmedPassword = password.trim();
      if (!trimmedUsername || !trimmedPassword) throw "BLANK";
      const credentials = JSON.stringify({ username: trimmedUsername, password: trimmedPassword });
      const response = await registerUser(credentials);
      if (response.status === 200 && response.data?.success) {
         console.log(response.data);
         // toast.success("Registration successful! Please log in."); // Optional success feedback
         toggleMode();
      } else {
          throw new Error(response.data?.message || "Registration failed.");
      }
    } catch (err) {
      handleAuthError(err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleAuthError = (err) => {
    if (err === "BLANK") setError("Username or password cannot be blank!");
    else if (err.code === "ERR_NETWORK") setError("Cannot connect to the server. Please try again later.");
    else if (err.response?.data?.message) setError(err.response.data.message);
    else if (err instanceof Error) setError(err.message);
    else {
      console.error("Login/Register Error:", err);
      setError("An unexpected error occurred. Please try again.");
    }
  };
  // --- End Authentication Logic ---

  // Switch between Login and Register modes
  const toggleMode = () => {
    setIsLogin(!isLogin);
    setError(null);
    setUsername("");
    setPassword("");
  };

  // Configuration object for text based on login/register mode
  const modeConfig = isLogin
    ? { title: "Log In", description: "Access your TARIFIC dashboard.", switchText: "Need an account?", switchAction: "Register", submitButtonText: "Sign In", submitLoadingText: "Signing In..." }
    : { title: "Get Started", description: "Create your TARIFIC account.", switchText: "Already have an account?", switchAction: "Log In", submitButtonText: "Register", submitLoadingText: "Registering..." };

  return (
    // --- Full Page Container ---
    <div className="flex items-center justify-center min-h-screen bg-background p-4 lg:p-8">
      {/* --- Login Box (Card-like structure) --- */}
      <div className="w-full max-w-4xl bg-card rounded-xl shadow-2xl overflow-hidden md:grid md:grid-cols-2 lg:grid-cols-5">

        {/* --- Left Visual Panel (Hidden on Mobile) --- */}
        <div className="hidden md:block lg:col-span-2 bg-gradient-to-br from-blue-600 to-indigo-700 p-8 text-white relative overflow-hidden">
          {/* Decorative background shapes */}
          <div className="absolute top-0 left-0 w-32 h-32 bg-white/10 rounded-full -translate-x-1/3 -translate-y-1/3 blur-xl opacity-70"></div>
          <div className="absolute bottom-0 right-0 w-48 h-48 bg-white/5 rounded-full translate-x-1/4 translate-y-1/4 blur-2xl opacity-50"></div>

          <div className="relative z-10 flex flex-col justify-between h-full">
            {/* Top section: Icon, Title, Tagline */}
            <div>
              <Ship className="h-10 w-10 mb-4 opacity-80" /> {/* App Icon */}
              <h2 className="text-3xl font-bold mb-2">TARIFIC</h2>
              <p className="text-base opacity-80 leading-relaxed">
                Navigate global trade tariffs with ease and precision.
              </p>
            </div>

            {/* --- Stylized Area/Bar Chart Element --- */}
            <div className="mt-12 h-48 w-full relative">
                 {/* Background gradient for the chart area */}
                <div className="absolute inset-0 bg-gradient-to-br from-blue-700/50 to-indigo-900/50 rounded-lg opacity-80"></div>

                <ResponsiveContainer width="100%" height="100%">
                    <AreaChart data={chartData} margin={{ top: 10, right: 0, left: 0, bottom: 0 }}>
                        {/* Use SVG defs tag directly inside the chart component */}
                        <defs>
                            <linearGradient id="colorValueLogin" x1="0" y1="0" x2="0" y2="1">
                                <stop offset="5%" stopColor="#8884d8" stopOpacity={0.6}/>
                                <stop offset="95%" stopColor="#8884d8" stopOpacity={0}/>
                            </linearGradient>
                            <linearGradient id="colorVolumeLogin" x1="0" y1="0" x2="0" y2="1">
                                <stop offset="20%" stopColor="#4B5563" stopOpacity={0.6}/>
                                <stop offset="95%" stopColor="#4B5563" stopOpacity={0.1}/>
                            </linearGradient>
                        </defs>

                        <XAxis hide dataKey="date" />
                        <YAxis hide domain={['dataMin - 30', 'dataMax + 10']} />
                        <CartesianGrid stroke="#FFFFFF" strokeOpacity={0.1} vertical={false} />

                        <Tooltip
                            cursor={{ stroke: '#FFFFFF', strokeOpacity: 0.2, strokeDasharray: '3 3' }}
                            contentStyle={{ backgroundColor: 'rgba(30, 41, 59, 0.85)', border: 'none', borderRadius: '4px', fontSize: '12px', padding: '5px 10px', boxShadow: '0 2px 8px rgba(0,0,0,0.3)' }}
                            labelStyle={{ color: '#FFFFFF', fontWeight: 'bold', marginBottom: '5px', display: 'block' }}
                            itemStyle={{ color: '#E0E0E0' }}
                            formatter={(value, name) => [`${value}`, name.charAt(0).toUpperCase() + name.slice(1)]}
                        />

                        {/* Area must come after Tooltip usually, Bars can be before or after */}
                         <Bar dataKey="volume" fill="url(#colorVolumeLogin)" barSize={10} />
                        <Area
                            type="monotone"
                            dataKey="value"
                            stroke="#8884d8"
                            strokeWidth={2.5}
                            fillOpacity={1}
                            fill="url(#colorValueLogin)"
                            isAnimationActive={false}
                            dot={false}
                        />
                    </AreaChart>
                </ResponsiveContainer>
            </div> {/* End Chart Element */}
          </div> {/* End Relative Z-10 container */}
        </div> {/* End Left Panel */}

        {/* --- Right Form Panel --- */}
        <div className="lg:col-span-3 p-8 md:p-12 flex flex-col justify-center bg-card text-card-foreground">
          <h1 className="text-2xl font-semibold mb-2">{modeConfig.title}</h1>
          <p className="text-muted-foreground mb-8">{modeConfig.description}</p>

          <form onSubmit={(e) => { e.preventDefault(); isLogin ? handleLogin() : handleRegister(); }} className="space-y-6">
            <div className="grid gap-2">
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
            <div className="grid gap-2">
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
                   <Button variant="link" size="sm" className="h-auto p-0 text-xs text-muted-foreground hover:text-primary">
                     Forgot Password?
                   </Button>
                 </div>
               )}
            </div>

            {/* --- Error Alert --- */}
            {error != null && (
              <Alert variant="destructive" className="bg-destructive/10 border-destructive/30 text-destructive" role="alert">
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

            {/* --- Submit Button --- */}
            <Button
              type="submit"
              className="w-full bg-primary hover:bg-primary/90 text-primary-foreground text-base py-3 shadow-md hover:shadow-lg transition-all"
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

          {/* --- Switch Mode --- */}
          <div className="mt-8 text-center text-sm">
            <span className="text-muted-foreground">{modeConfig.switchText}</span>
            <Button variant="link" onClick={toggleMode} className="pl-1 font-semibold text-primary hover:text-primary/80 transition-colors">
              {modeConfig.switchAction}
            </Button>
          </div>
        </div> {/* End Right Panel */}

      </div> {/* End Login Box */}
    </div> // End Full Page Container
  );
};

export default Login;