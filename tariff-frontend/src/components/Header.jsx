import { useState } from "react"
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
import {
  Sheet,
  SheetContent,
  SheetTrigger,
} from "@/components/ui/sheet"
import { Button } from "@/components/ui/button"
import { Menu } from "lucide-react"
import { getUserInitials } from "@/utils/AvatarHelpers"
import { ModeToggle } from "./mode-toggle"
import { logout } from "@/utils/logout"
import { useAuth } from "@/utils/AuthContext"
import { cn } from "@/lib/utils"
import AdminPanel from "@/components/AdminPanel"

export default function Header() {
  const { user, setUser, isAdmin } = useAuth();
  const navigate = useNavigate();
  const [isOpen, setIsOpen] = useState(false);

  const handleProfileClick = () => {
    navigate("/profile");
  }

  const handleLogout = () => {
    logout(setUser);
  }

  const handleNavigate = (path) => {
    navigate(path);
    setIsOpen(false);
  }

  const navigationItems = [
    { label: "Calculator", path: "/calculator" },
    { label: "Dashboard", path: "/dashboard" },
    { label: "Historical Explorer", path: "/historical" },
  ]

  return (
    <header className="sticky top-0 z-50 w-full border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <div className="flex h-14 items-center justify-between px-4">
        <div className="flex items-center space-x-6">
          <a className="flex items-center space-x-2" href="/">
            <span className="font-bold">TARIFIC</span>
          </a>

          {/* Desktop Navigation Menu */}
          {user && (
            <NavigationMenu className="hidden md:flex">
              <NavigationMenuList>
                {navigationItems.map((item) => (
                  <NavigationMenuItem key={item.path}>
                    <NavigationMenuLink
                      className={cn(navigationMenuTriggerStyle(), "cursor-pointer")}
                      onClick={() => navigate(item.path)}
                    >
                      {item.label}
                    </NavigationMenuLink>
                  </NavigationMenuItem>
                ))}
              </NavigationMenuList>
            </NavigationMenu>
          )}
        </div>

        {/* Right-side group: AdminPanel + Mobile menu + Avatar + ModeToggle */}
        <div className="flex items-center space-x-2">
          {user && isAdmin && (
            <div className="hidden md:block">
              <AdminPanel />
            </div>
          )}

          {/* Mobile Navigation Menu */}
          {user && (
            <Sheet open={isOpen} onOpenChange={setIsOpen}>
              <SheetTrigger asChild>
                <Button
                  variant="ghost"
                  size="icon"
                  className="md:hidden"
                  aria-label="Open navigation menu"
                >
                  <Menu className="h-5 w-5" />
                </Button>
              </SheetTrigger>
              <SheetContent side="right" className="w-72">
                <div className="flex flex-col space-y-4 mt-8">
                  <div className="text-lg font-semibold mb-4">Navigation</div>
                  {navigationItems.map((item) => (
                    <Button
                      key={item.path}
                      variant="ghost"
                      className="justify-start text-left"
                      onClick={() => handleNavigate(item.path)}
                    >
                      {item.label}
                    </Button>
                  ))}
                  {/* Admin Panel (mobile version) */}
                  {isAdmin && (
                    <Button
                      variant="ghost"
                      className="justify-start text-left"
                      onClick={() => {
                        setIsOpen(false)
                        setIsOpen(true)
                        document.querySelector('[data-admin-panel-trigger]')?.click()
                      }}
                    >
                      Admin Panel
                    </Button>
                  )}
                  {/* Mobile Profile and Logout */}
                  <div className="border-t pt-4 mt-4">
                    <div className="text-sm font-medium mb-2 text-muted-foreground">Account</div>
                    <Button
                      variant="ghost"
                      className="justify-start text-left w-full"
                      onClick={() => {
                        handleProfileClick();
                        setIsOpen(false);
                      }}
                    >
                      Profile
                    </Button>
                    <Button
                      variant="ghost"
                      className="justify-start text-left w-full text-red-600 hover:text-red-700 hover:bg-red-50 dark:hover:bg-red-900/20"
                      onClick={() => {
                        handleLogout();
                        setIsOpen(false);
                      }}
                    >
                      Logout
                    </Button>
                  </div>
                </div>
              </SheetContent>
            </Sheet>
          )}

          {/* Desktop Avatar Dropdown */}
          {user && (
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <button
                  aria-label="Open user menu"
                  className="rounded-full focus:outline-none hidden md:block"
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
