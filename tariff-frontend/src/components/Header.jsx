import { useState, useEffect } from "react"
import { useNavigate, NavLink } from "react-router-dom"
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
} from "@/components/ui/navigation-menu"
import {
  Sheet,
  SheetContent,
  SheetTitle,
  SheetTrigger,
} from "@/components/ui/sheet"
import { Button } from "@/components/ui/button"
import { Menu, ChevronDown } from "lucide-react"
import { getUserInitials } from "@/utils/AvatarHelpers"
import { ModeToggle } from "./mode-toggle"
import { logout } from "@/utils/logout"
import { useAuth } from "@/utils/AuthContext"
import { cn } from "@/lib/utils"
import AdminPanel from "@/components/AdminPanel"

const useMediaQuery = (query) => {
  const [matches, setMatches] = useState(false);

  useEffect(() => {
    if (typeof window.matchMedia === 'function') {
      const media = window.matchMedia(query);
      if (media.matches !== matches) {
        setMatches(media.matches);
      }
      const listener = () => setMatches(media.matches);
      media.addEventListener('change', listener);
      return () => media.removeEventListener('change', listener);
    }
  }, [matches, query]);

  return matches;
};

const allNavigationItems = [
  { label: "Calculator", path: "/calculator" },
  { label: "Calculation History", path: "/calc-history" },
  { label: "Dashboard", path: "/dashboard" },
  { label: "Historical Explorer", path: "/historical" },
  { label: "Forecasts", path: "/forecast" },
  { label: "Newsletter", path: "/newsletter" },
  { label: "Article Analyzer", path: "/analyzer" },
  { label: "MCPAssistant", path: "/chatbot" }
]

export default function Header() {
  const { user, setUser, isAdmin } = useAuth();
  const navigate = useNavigate();
  const [isOpen, setIsOpen] = useState(false);
  const [adminPanelOpen, setAdminPanelOpen] = useState(false);

  const isXl = useMediaQuery('(min-width: 1280px)');
  const is2Xl = useMediaQuery('(min-width: 1536px)');

  const visibleCount = is2Xl ? 8 : isXl ? 6 : 4; 

  const visibleItems = allNavigationItems.slice(0, visibleCount);
  const dropdownItems = allNavigationItems.slice(visibleCount);

  const handleProfileClick = () => {
    navigate("/profile", { replace: true });
  }

  const handleLogout = () => {
    logout(setUser);
  }

  const handleNavigate = (path) => {
    navigate(path, { replace: true });
    setIsOpen(false);
  }

  return (
    <header className="sticky top-0 z-50 w-full border-b bg-background/95 backdrop-blur supports-backdrop-filter:bg-background/60">
      <div className="flex h-14 items-center justify-between px-4">
        <div className="flex items-center space-x-6">
          <NavLink
            to="/"
            replace
            className="flex items-center space-x-2 transition-colors focus:outline-none"
          >
            <span className="font-bold">TARIFIC</span>
          </NavLink>

          {user && (
            <NavigationMenu className="hidden lg:flex">
              <NavigationMenuList>
                {visibleItems.map((item) => (
                  <NavigationMenuItem key={item.path}>
                    <NavigationMenuLink asChild>
                      <NavLink
                        to={item.path}
                        replace
                        className={({ isActive }) =>
                          cn(
                            "inline-flex h-10 items-center justify-center rounded-md px-3 py-2 text-sm font-medium transition-colors focus:outline-none disabled:pointer-events-none disabled:opacity-50",
                            "hover:underline underline-offset-4 focus:underline",
                            isActive
                              ? "bg-accent/50 text-accent-foreground"
                              : "hover:bg-transparent"
                          )
                        }
                      >
                        {item.label}
                      </NavLink>
                    </NavigationMenuLink>
                  </NavigationMenuItem>
                ))}

                {dropdownItems.length > 0 && (
                  <NavigationMenuItem>
                    <DropdownMenu>
                      <DropdownMenuTrigger asChild>
                        <Button
                          variant="link"
                          className="flex h-10 items-center gap-1 rounded-md px-3 py-2 text-sm font-medium hover:underline underline-offset-4"
                        >
                          More
                          <ChevronDown className="h-4 w-4" />
                        </Button>
                      </DropdownMenuTrigger>
                      <DropdownMenuContent align="start" className="w-48">
                        {dropdownItems.map((item) => (
                          <DropdownMenuItem
                            key={item.path}
                            onClick={() => handleNavigate(item.path)}
                            className="cursor-pointer"
                          >
                            {item.label}
                          </DropdownMenuItem>
                        ))}
                      </DropdownMenuContent>
                    </DropdownMenu>
                  </NavigationMenuItem>
                )}
              </NavigationMenuList>
            </NavigationMenu>
          )}
        </div>

        {/* Right-side group: AdminPanel + Mobile menu + Avatar + ModeToggle */}
        <div className="flex items-center space-x-2">
          {/* Mobile Navigation Menu */}
          {user && (
            <Sheet open={isOpen} onOpenChange={setIsOpen}>
              <SheetTrigger asChild>
                <Button
                  variant="ghost"
                  size="icon"
                  className="lg:hidden"
                  aria-label="Open navigation menu"
                >
                  <Menu className="h-5 w-5" />
                </Button>
              </SheetTrigger>
              <SheetContent side="right" className="w-72">
                <SheetTitle>Navigation</SheetTitle>
                <div className="flex flex-col space-y-4 mt-4">
                  {/* Mobile menu maps over the *full* list */}
                  {allNavigationItems.map((item) => (
                    <Button
                      key={item.path}
                      variant="ghost"
                      className="justify-start text-left"
                      onClick={() => handleNavigate(item.path)}
                    >
                      {item.label}
                    </Button>
                  ))}
                  
                  
                  {/* Mobile Profile and Logout */}
                  <div className="border-t pt-4 mt-4">
                    <div className="text-sm font-medium mb-2 text-muted-foreground">Account</div>
                    {isAdmin && (
                      <Button
                        variant="ghost"
                        className="justify-start text-left w-full"
                        onClick={() => {
                          setIsOpen(false);
                          setAdminPanelOpen(true);
                        }}
                      >
                        Admin Panel
                      </Button>
                    )}
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
                  className="rounded-full focus:outline-none hidden lg:block"
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
                {isAdmin && (
                  <DropdownMenuItem 
                    onClick={() => setAdminPanelOpen(true)} 
                    className="cursor-pointer"
                  >
                    Admin Panel
                  </DropdownMenuItem>
                )}
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
      {isAdmin && <AdminPanel open={adminPanelOpen} onOpenChange={setAdminPanelOpen} />}
    </header>
  );
}
