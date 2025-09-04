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
import { useState } from "react";

const Login = () => {
  const [isLogin, setIsLogin] = useState(true);

  const loginMode = {
    title: "Login to your account",
    description: "Enter your username below to login to your account",
    signUp: <Button variant="link" onClick={() => {setIsLogin(!isLogin)}}>Sign Up</Button>,
    submitButton: <Button type="submit" className="w-full">Login</Button>,
  };

  const registerMode = {
    title: "Create an account",
    description: "Enter a username and password below to create an account",
    signUp: <Button variant="link" onClick={() => {setIsLogin(!isLogin)}}>Sign In</Button>,
    submitButton: <Button type="submit" className="w-full">Create account</Button>,
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
        <form>
          <div className="flex flex-col gap-6">
            <div className="grid gap-2">
              <Label htmlFor="username">Username</Label>
              <Input
                id="username"
                type="text"
                placeholder=""
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
              <Input id="password" type="password" required />
            </div>
          </div>
        </form>
      </CardContent>
      <CardFooter className="flex-col gap-2">
        {cardInfo.submitButton}
      </CardFooter>
    </Card>
  );
};

export default Login;
