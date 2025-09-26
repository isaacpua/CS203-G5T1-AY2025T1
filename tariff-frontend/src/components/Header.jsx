import { useNavigate } from "react-router-dom"
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import {
  NavigationMenu,
  NavigationMenuItem,
  NavigationMenuLink,
  NavigationMenuList,
  navigationMenuTriggerStyle,
} from "@/components/ui/navigation-menu"
import { getUserInitials } from "@/utils/AvatarHelpers"
import { ModeToggle } from "./mode-toggle"
import { logout } from "@/utils/logout"
import { useAuth } from "@/utils/AuthContext"
import { cn } from "@/lib/utils"

export default function Header() {
  const { user, setUser } = useAuth();
  const navigate = useNavigate()

  const handleProfileClick = () => {
    navigate("/profile")
  }

  const handleLogout = () => {
    logout(setUser);
  }

  return (
    <header className="sticky top-0 z-50 w-full border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <div className="flex h-14 items-center justify-between px-4">
        <div className="flex items-center space-x-6">
          <a className="flex items-center space-x-2" href="/">
            <span className="font-bold">TARIFIC</span>
          </a>

          {/* Navigation Menu */}
          {user && (
            <NavigationMenu>
              <NavigationMenuList>
                <NavigationMenuItem>
                  <NavigationMenuLink
                    className={cn(navigationMenuTriggerStyle(), "cursor-pointer")}
                    onClick={() => navigate("/calculator")}
                  >
                    Calculator
                  </NavigationMenuLink>
                </NavigationMenuItem>
                <NavigationMenuItem>
                  <NavigationMenuLink
                    className={cn(navigationMenuTriggerStyle(), "cursor-pointer")}
                    onClick={() => navigate("/dashboard")}
                  >
                    Dashboard
                  </NavigationMenuLink>
                </NavigationMenuItem>
                <NavigationMenuItem>
                  <NavigationMenuLink
                    className={cn(navigationMenuTriggerStyle(), "cursor-pointer")}
                    onClick={() => navigate("/historical")}
                  >
                    Historical Explorer
                  </NavigationMenuLink>
                </NavigationMenuItem>
              </NavigationMenuList>
            </NavigationMenu>
          )}
        </div>

        {/* Right-side group: Avatar (if user exists) + ModeToggle */}
        <div className="flex items-center space-x-2">
          {user && (
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <button
                  aria-label="Open user menu"
                  className="rounded-full focus:outline-none"
                >
                  <Avatar className="h-8 w-8">
                    {user.avatarUrl ? (
                      <AvatarImage src={user.avatarUrl} alt={user.username} />
                    ) : (
                      <AvatarFallback className="text-lg font-semibold bg-primary text-primary-foreground">
                        {getUserInitials(user.username)}
                      </AvatarFallback>
                    )}
                  </Avatar>
                </button>
              </DropdownMenuTrigger>

              <DropdownMenuContent align="end" className="w-40">
                <DropdownMenuItem onClick={handleProfileClick}>
                  Profile
                </DropdownMenuItem>
                <DropdownMenuItem
                  onClick={handleLogout}
                  className="text-red-600"
                >
                  Logout
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          )}

          <ModeToggle />
        </div>
      </div>
    </header>
  );
}
