"use client"

import { useState } from "react"
import { useNavigate } from "react-router-dom"
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from "@/components/ui/dropdown-menu"
import {
  NavigationMenu,
  NavigationMenuItem,
  NavigationMenuLink,
  NavigationMenuList,
  navigationMenuTriggerStyle,
} from "@/components/ui/navigation-menu"
import { Sheet, SheetContent, SheetTitle, SheetTrigger } from "@/components/ui/sheet"
import { Button } from "@/components/ui/button"
import { Menu, Sprout } from "lucide-react"
import { getUserInitials } from "@/utils/AvatarHelpers"
import { ModeToggle } from "./mode-toggle"
import { logout } from "@/utils/logout"
import { useAuth } from "@/utils/AuthContext"
import { cn } from "@/lib/utils"
import AdminPanel from "@/components/AdminPanel"
import { motion } from "framer-motion"

const navigationItems = [
  { label: "Calculator", path: "/calculator" },
  { label: "Calculation History", path: "/calc-history" },
  { label: "Dashboard", path: "/dashboard" },
  { label: "Historical Explorer", path: "/historical" },
  { label: "Forecasts", path: "/forecast" },
  { label: "Newsletter", path: "/newsletter" },
  { label: "MCP Assistant", path: "/chatbot" },
]

export default function Header() {
  const { user, setUser, isAdmin } = useAuth()
  const navigate = useNavigate()
  const [isOpen, setIsOpen] = useState(false)
  const [adminPanelOpen, setAdminPanelOpen] = useState(false)

  const handleProfileClick = () => {
    navigate("/profile")
  }

  const handleLogout = () => {
    logout(setUser)
  }

  const handleNavigate = (path) => {
    navigate(path)
    setIsOpen(false)
  }

  return (
    <motion.header
      className="sticky top-0 z-50 w-full border-b border-border/50 bg-background/80 backdrop-blur-lg supports-[backdrop-filter]:bg-background/60 shadow-sm"
      initial={{ y: -100 }}
      animate={{ y: 0 }}
      transition={{ duration: 0.5, ease: "easeOut" }}
    >
      <div className="flex h-16 items-center justify-between px-4">
        <div className="flex items-center space-x-6">
          <motion.a
            className="flex items-center space-x-2 group"
            href="#"
            onClick={() => {
              navigate("/")
            }}
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
          >
            <Sprout className="w-6 h-6 text-primary transition-transform duration-300 group-hover:rotate-12" />
            <span className="font-bold text-lg text-primary">TARIFIC</span>
          </motion.a>

          {user && (
            <NavigationMenu className="hidden md:flex">
              <NavigationMenuList>
                {navigationItems.map((item, index) => (
                  <NavigationMenuItem key={item.path}>
                    <motion.div
                      initial={{ opacity: 0, y: -10 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ duration: 0.3, delay: index * 0.05 }}
                    >
                      <NavigationMenuLink
                        className={cn(
                          navigationMenuTriggerStyle(),
                          "cursor-pointer transition-all duration-300 hover:bg-primary/10",
                        )}
                        onClick={() => navigate(item.path)}
                      >
                        {item.label}
                      </NavigationMenuLink>
                    </motion.div>
                  </NavigationMenuItem>
                ))}
              </NavigationMenuList>
            </NavigationMenu>
          )}
        </div>

        <div className="flex items-center space-x-2">
          {user && isAdmin && (
            <div className="hidden md:block">
              <AdminPanel open={adminPanelOpen} onOpenChange={setAdminPanelOpen} />
            </div>
          )}

          {user && (
            <Sheet open={isOpen} onOpenChange={setIsOpen}>
              <SheetTrigger asChild>
                <Button
                  variant="ghost"
                  size="icon"
                  className="md:hidden hover:bg-primary/10 transition-colors duration-300"
                  aria-label="Open navigation menu"
                >
                  <Menu className="h-5 w-5" />
                </Button>
              </SheetTrigger>
              <SheetContent side="right" className="w-72">
                <SheetTitle>Navigation</SheetTitle>
                <div className="flex flex-col space-y-4 mt-4">
                  {navigationItems.map((item) => (
                    <Button
                      key={item.path}
                      variant="ghost"
                      className="justify-start text-left hover:bg-primary/10 transition-colors duration-300"
                      onClick={() => handleNavigate(item.path)}
                    >
                      {item.label}
                    </Button>
                  ))}
                  {isAdmin && (
                    <Button
                      variant="ghost"
                      className="justify-start text-left hover:bg-primary/10 transition-colors duration-300"
                      onClick={() => {
                        setIsOpen(false)
                        setAdminPanelOpen(true)
                      }}
                    >
                      Admin Panel
                    </Button>
                  )}
                  <div className="border-t pt-4 mt-4">
                    <div className="text-sm font-medium mb-2 text-muted-foreground">Account</div>
                    <Button
                      variant="ghost"
                      className="justify-start text-left w-full hover:bg-primary/10 transition-colors duration-300"
                      onClick={() => {
                        handleProfileClick()
                        setIsOpen(false)
                      }}
                    >
                      Profile
                    </Button>
                    <Button
                      variant="ghost"
                      className="justify-start text-left w-full text-destructive hover:text-destructive hover:bg-destructive/10 transition-colors duration-300"
                      onClick={() => {
                        handleLogout()
                        setIsOpen(false)
                      }}
                    >
                      Logout
                    </Button>
                  </div>
                </div>
              </SheetContent>
            </Sheet>
          )}

          {user && (
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <motion.button
                  aria-label="Open user menu"
                  className="rounded-full focus:outline-none hidden md:block ring-2 ring-transparent hover:ring-primary/30 transition-all duration-300"
                  whileHover={{ scale: 1.1 }}
                  whileTap={{ scale: 0.95 }}
                >
                  <Avatar className="h-9 w-9">
                    {user.avatarUrl ? (
                      <AvatarImage src={user.avatarUrl || "/placeholder.svg"} alt={user.username} />
                    ) : (
                      <AvatarFallback className="text-lg font-semibold bg-primary text-primary-foreground">
                        {getUserInitials(user.username)}
                      </AvatarFallback>
                    )}
                  </Avatar>
                </motion.button>
              </DropdownMenuTrigger>

              <DropdownMenuContent align="end" className="w-40">
                <DropdownMenuItem onClick={handleProfileClick} className="cursor-pointer">
                  Profile
                </DropdownMenuItem>
                <DropdownMenuItem onClick={handleLogout} className="text-destructive cursor-pointer">
                  Logout
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          )}

          <ModeToggle />
        </div>
      </div>
    </motion.header>
  )
}
