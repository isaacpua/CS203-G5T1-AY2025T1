import React, { useEffect, useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Avatar, AvatarFallback } from '@/components/ui/avatar';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { User, Shield, Hash, Edit } from 'lucide-react';
import axiosClient from '@/api/axiosClient';
import { getUserInitials } from '@/utils/AvatarHelpers';

const Profile = ({ user }) => {
  const [userDetails, setUserDetails] = useState({
    id: "NULL",
    username: "NULL",
    role: "NULL"
  });

  const [editUsername, setEditUsername] = useState("");
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [isLoading, setIsLoading] = useState(false);

  // ✅ Only update userDetails when `user` changes
  useEffect(() => {
    if (user) {
      setUserDetails(user);
    }
  }, [user]);

  useEffect(() => {
    const getUserData = async () => {
      try {
        const { data } = await axiosClient.get(`/users/${userDetails.username}`);
        if (!data.user) {
          throw new Error();
        }
        setUserDetails(data.user);
        setEditUsername(data.user.username);
      } catch (err) {
        console.error(err);
      }
    };

    if (userDetails.username !== "NULL") {
      getUserData();
    }
  }, [userDetails.username]); // ✅ only refetch when username changes

  const handleEditProfile = async () => {
    if (!editUsername.trim()) {
      alert("Username cannot be empty");
      return;
    }

    if (editUsername.trim() === userDetails.username) {
      alert("Username hasn't changed");
      return;
    }

    setIsLoading(true);
    try {
      const usernameUpdateDTO = { username: editUsername.trim() };
      await axiosClient.put(`/users/${userDetails.id}/username`, usernameUpdateDTO);
      location.reload();
      setIsDialogOpen(false);
    } catch (err) {
      console.error("Error updating username:", err);
      if (err.response?.status === 400 && err.response?.data?.message) {
        alert(err.response.data.message);
      } else if (err.response?.status === 403) {
        alert("You don't have permission to update this username.");
      } else {
        alert("Failed to update username. Please try again.");
      }
    } finally {
      setIsLoading(false);
    }
  };

  const handleDialogClose = () => {
    setEditUsername(userDetails.username);
    setIsDialogOpen(false);
  };

  const getRoleColor = (role) => {
    switch (role.toLowerCase()) {
      case 'admin':
        return 'bg-red-100 dark:bg-red-900/30 text-red-800 dark:text-red-400 hover:bg-red-200 dark:hover:bg-red-900/50';
      case 'default':
        return 'bg-muted text-muted-foreground hover:bg-muted/80';
      default:
        return 'bg-primary/10 text-primary hover:bg-primary/20';
    }
  };

  return (
    <div className="min-h-screen bg-background py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-2xl mx-auto">
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-foreground mb-2">User Profile</h1>
          <p className="text-muted-foreground">View and manage user account details</p>
        </div>

        {/* Profile Card */}
        <Card className="shadow-lg">
          <CardHeader className="pb-6">
            <div className="flex items-center space-x-4">
              <Avatar className="h-16 w-16">
                <AvatarFallback className="text-lg font-semibold bg-primary text-primary-foreground">
                  {getUserInitials(userDetails.username)}
                </AvatarFallback>
              </Avatar>
              <div>
                <CardTitle className="text-2xl font-bold text-foreground">
                  {userDetails.username}
                </CardTitle>
                <CardDescription className="text-muted-foreground mt-1">
                  User account information
                </CardDescription>
              </div>
            </div>
          </CardHeader>

          <CardContent className="space-y-6">
            {/* Username Section */}
            <div className="flex items-start space-x-3 p-4 rounded-lg bg-muted/30">
              <User className="h-5 w-5 text-muted-foreground mt-0.5" />
              <div className="flex-1">
                <h3 className="text-sm font-medium text-foreground mb-1">Username</h3>
                <p className="text-foreground/80 font-mono text-sm">{userDetails.username}</p>
              </div>
            </div>

            {/* Role Section */}
            <div className="flex items-start space-x-3 p-4 rounded-lg bg-muted/30">
              <Shield className="h-5 w-5 text-muted-foreground mt-0.5" />
              <div className="flex-1">
                <h3 className="text-sm font-medium text-foreground mb-2">Role</h3>
                <Badge className={getRoleColor(userDetails.role)}>
                  {userDetails.role}
                </Badge>
              </div>
            </div>

            {/* User ID Section */}
            <div className="flex items-start space-x-3 p-4 rounded-lg bg-muted/30">
              <Hash className="h-5 w-5 text-muted-foreground mt-0.5" />
              <div className="flex-1">
                <h3 className="text-sm font-medium text-foreground mb-1">User ID</h3>
                <p className="text-muted-foreground font-mono text-xs break-all">{userDetails.id}</p>
              </div>
            </div>

            {/* Additional Actions */}
            <div className="pt-6 border-t border-border">
              <div className="flex space-x-3">
                <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
                  <DialogTrigger asChild>
                    <Button className="flex-1" variant="default">
                      <Edit className="h-4 w-4 mr-2" />
                      Edit Profile
                    </Button>
                  </DialogTrigger>
                  <DialogContent className="sm:max-w-[425px]">
                    <DialogHeader>
                      <DialogTitle>Edit Profile</DialogTitle>
                      <DialogDescription>
                        Update your username. Your role cannot be changed.
                        You will be required to relogin after this.
                      </DialogDescription>
                    </DialogHeader>
                    <div className="space-y-4 py-4">
                      <div className="space-y-2">
                        <Label htmlFor="username">Username</Label>
                        <Input
                          id="username"
                          value={editUsername}
                          onChange={(e) => setEditUsername(e.target.value)}
                          placeholder="Enter your username"
                          disabled={isLoading}
                        />
                      </div>
                      <div className="space-y-2">
                        <Label htmlFor="role">Role (Read-only)</Label>
                        <Input
                          id="role"
                          value={userDetails.role}
                          disabled
                          className="bg-muted"
                        />
                      </div>
                    </div>
                    <div className="flex justify-end space-x-2">
                      <Button
                        variant="outline"
                        onClick={handleDialogClose}
                        disabled={isLoading}
                      >
                        Cancel
                      </Button>
                      <Button
                        onClick={handleEditProfile}
                        disabled={isLoading || !editUsername.trim() || editUsername === userDetails.username}
                      >
                        {isLoading ? "Updating..." : "Save Changes"}
                      </Button>
                    </div>
                  </DialogContent>
                </Dialog>
                <Button variant="secondary" className="flex-1">
                  Change Password
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default Profile;
