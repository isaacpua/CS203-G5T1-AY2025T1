import axiosClient from "@/api/axiosClient";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Button } from "@/components/ui/button"
import {
  Card,
  CardAction,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { decodeJWT } from "@/utils/jwtDecoder";
import { Loader2 } from "lucide-react"; import { AlertCircle, X } from "lucide-react";
import { useState } from "react";
import {useLocation, useNavigate} from "react-router-dom";

const Login = ({ setUser }) => {
  const [isLogin, setIsLogin] = useState(true);
  const [isLoading, setIsLoading] = useState(false);
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState(null);

  const navigate = useNavigate();
  const location = useLocation();
  const from = location.state?.from?.pathname || "/calculator";

  const handleLogin = async () => {
    setIsLoading(true);
    setError(null);
    const credentials = JSON.stringify({
      username: username,
      password: password,
    });
    try {
      // Edge case: Due to the new axiosClient auto sending the JWT, if you were logged into a deleted user, you are sending an invalid JWT
      // so delete the current accessToken
      localStorage.removeItem("accessToken");
      const response = await axiosClient.post("/auth/login", credentials);
      if (response.status == 200) {
        localStorage.setItem("accessToken", response.data.accessToken);
        const decodedJWT = decodeJWT(response.data.accessToken);
        const { data } = await axiosClient.get(`/users/${decodedJWT.sub}`);
        console.log(decodedJWT)
        setUser(data.user);
        return navigate(from, { replace: true }); // go to original page that required login

        // CODE FOR TESTING TOKEN EXISTENCE
        // const accessToken = localStorage.getItem("accessToken");
        // const isValid = await axiosClient.post("/auth/verifyJWT", {}, {
        //   headers: {
        //     Authorization: `Bearer ${accessToken}`,
        //   },
        // });
        // console.log(isValid.data);
      }
    } catch (err) {
      if (err.code == "ERR_NETWORK") {
        setError("Our servers are currently down. Please try again later.");
      } else if (err.response?.data?.message) {
        setError(err.response.data.message);
      } else {
        setError("An unexpected error occurred. Please try again.")
      }
    } finally {
      setIsLoading(false);
    }
  };

  const handleRegister = async () => {
    setIsLoading(true);
    setError(null);
    const credentials = JSON.stringify({
      username: username,
      password: password,
    });
    try {
      const response = await axiosClient.post("/auth/register", credentials);
      console.log(response.data);
      toggleMode(); // switch back to login mode
    } catch (err) {
      if (err.code == "ERR_NETWORK") {
        setError("Our servers are currently down. Please try again later.");
      } else if (err.response?.data?.message) {
        setError(err.response.data.message);
      } else {
        setError("An unexpected error occurred. Please try again.")
      }
    } finally {
      setIsLoading(false);
    }
  };

  const toggleMode = () => {
    setIsLogin(!isLogin);
    setError(null);
  };

  const loginMode = {
    title: "Login to your account",
    description: "Enter your username below to login to your account",
    signUp: <Button variant="link" onClick={toggleMode}>Sign Up</Button>,
    submitButton: isLoading
      ? <><Loader2 className="mr-2 h-4 w-4 animate-spin" /> Logging in...</>
      : <Button type="submit" className="w-full" onClick={handleLogin}>Login</Button>,
  };

  const registerMode = {
    title: "Create an account",
    description: "Enter a username and password below to create an account",
    signUp: <Button variant="link" onClick={toggleMode}>Sign In</Button>,
    submitButton: isLoading
      ? <><Loader2 className="mr-2 h-4 w-4 animate-spin" /> Creating account...</>
      : <Button type="submit" className="w-full" onClick={handleRegister}>Create account</Button>,
  };

  const cardInfo = isLogin ? loginMode : registerMode;

  return (
    <Card className="w-full max-w-sm">
      <CardHeader>
        <CardTitle>{cardInfo.title}</CardTitle>
        <CardDescription>
          {cardInfo.description}
        </CardDescription>
        <CardAction>
          {cardInfo.signUp}
        </CardAction>
      </CardHeader>
      <CardContent>
        <form onSubmit={(e) => e.preventDefault()}>
          <div className="flex flex-col gap-6">
            <div className="grid gap-2">
              <Label htmlFor="username">Username</Label>
              <Input
                id="username"
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                required
              />
            </div>
            <div className="grid gap-2">
              <div className="flex items-center">
                <Label htmlFor="password">Password</Label>
                {/* <a
                  href="#"
                  className="ml-auto inline-block text-sm underline-offset-4 hover:underline"
                >
                  Forgot your password?
                </a> */}
              </div>
              <Input
                id="password"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
              />
            </div>
          </div>
        </form>
      </CardContent>
      <CardFooter className="flex-col gap-2">
        {cardInfo.submitButton}
        {error != null && <Alert variant="destructive" className="mt-4">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription className="flex justify-between items-center">
            <span>{error}</span>
            <Button
              variant="ghost"
              size="sm"
              className="h-auto p-1 hover:bg-destructive/20"
              onClick={() => setError(null)}
            >
              <X className="h-3 w-3" />
            </Button>
          </AlertDescription>
        </Alert>}
      </CardFooter>
    </Card>
  );
};

export default Login;
