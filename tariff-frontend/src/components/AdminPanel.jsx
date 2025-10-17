import React, { useState } from 'react';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Users, Shield } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

export default function AdminPanel() {
  const [open, setOpen] = useState(false);
  const navigate = useNavigate();

  const adminRoutes = [
    {
      name: 'User Management',
      description: 'Manage users, roles, and permissions',
      icon: Users,
      path: '/user-management',
      color: 'text-blue-600'
    }
  ];

  const handleNavigate = (path) => {
    navigate(path);
    setOpen(false);
  };

  return (
    <Dialog open={open} onOpenChange={setOpen} className="p-5">
      <DialogTrigger asChild>
        <Button variant="outline" className="gap-2" data-admin-panel-trigger>
          <Shield className="h-4 w-4" />
          Admin Panel
        </Button>
      </DialogTrigger>
      <DialogContent className="max-w-3xl max-h-[80vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="text-2xl">Admin Panel</DialogTitle>
          <DialogDescription>
            Select a section to manage your application
          </DialogDescription>
        </DialogHeader>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-4">
          {adminRoutes.map((route) => {
            const Icon = route.icon
            return (
              <button
                key={route.path}
                onClick={() => handleNavigate(route.path)}
                className={`
                  flex items-start gap-4 p-4 rounded-lg border text-left group transition-all
                  hover:bg-muted hover:border-muted-foreground/50
                  focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2
                `}
              >
                <div className={`p-2 rounded-lg ${route.color}`}>
                  <Icon className="h-5 w-5" />
                </div>
                <div className="flex-1">
                  <h3 className="font-semibold mb-1">{route.name}</h3>
                  <p className="text-sm">{route.description}</p>
                </div>
              </button>
            )
          })}
        </div>
      </DialogContent>
    </Dialog>
  );
}
