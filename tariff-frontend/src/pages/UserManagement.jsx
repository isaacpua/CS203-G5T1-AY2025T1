import * as React from "react"
import {
  flexRender,
  getCoreRowModel,
  getFilteredRowModel,
  getPaginationRowModel,
  getSortedRowModel,
  useReactTable,
} from "@tanstack/react-table"
import { ArrowUpDown, MoreHorizontal } from "lucide-react"

import { Button } from "@/components/ui/button"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { Input } from "@/components/ui/input"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import axiosClient from "@/api/axiosClient";
import { useEffect, useState, useRef } from "react";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { Label } from "@/components/ui/label"
import { Spinner } from "@/components/ui/shadcn-io/spinner"

import { Relogin } from "@/components/Relogin";
import { Forbidden } from "@/components/Forbidden";

const UserManagement = () => {
  const [users, setUsers] = useState([]);
  const [deleteAction, setDeleteAction] = useState(false);
  const [deleteUser, setDeleteUser] = useState(null);
  const [editAction, setEditAction] = useState(false);
  const [editUser, setEditUser] = useState(null);

  const [showRelogin, setShowRelogin] = useState(false);
  const [showForbidden, setShowForbidden] = useState(false);

  
  // If I don't have these 2 lines, then the edit users will re-render the dialog everytime something is changed.
  const usernameRef = useRef(null);
  const roleRef = useRef(null);

  useEffect(() => {
    const fetchAllUsers = async () => {
      try {
        const response = await axiosClient.get("/users/");

        if (response.status === 200) {
          console.log("Fetched users:", response.data.users);
          setUsers(response.data.users);
        }
      } catch (error) {
        if (error.response?.status === 401) {
          console.log("found 401 error wow")
          setShowRelogin(true);
          return;
        }

        if (error.response?.status === 403) {
          console.log("found 403 error wow")
          setShowForbidden(true);
          return;
        }
        console.error("Error fetching users:", error);
      }
    };

    fetchAllUsers();
  }, []);

  const closeDialogs = () => {
    setEditAction(false);
    setDeleteAction(false);
    setEditUser(null);
    setDeleteUser(null);
  };

  const SaveButton = () => {
    const [isLoading, setIsLoading] = useState(false);

    const handleSave = async (event) => {
      event.preventDefault();
      setIsLoading(true);
      
      try {
        const newUsername = usernameRef.current?.value || editUser.username;
        const newRole = roleRef.current || editUser.role;
        const userID = editUser.id;
        
        const response = await axiosClient.put(`/users/${userID}`, {
          username: newUsername,
          role: newRole,
        });
        
        if (response.status === 200) {
          console.log(response.data.message)
          location.reload();
        }
      } catch (err) {
        if (err.response?.status === 401) {
          console.log("found 401 error wow")
          setShowRelogin(true);
          return;
        }
        console.error("Error updating user:", err);
      } finally {
        setIsLoading(false);
        closeDialogs();
      }
    };

    return (
      <Button type="submit" disabled={isLoading} onClick={handleSave}>
        {isLoading ? <Spinner /> : "Save changes"}
      </Button>
    );
  };

  const DeleteButton = () => {
    const [isLoading, setIsLoading] = useState(false);

    const handleDelete = async (event) => {
      event.preventDefault();
      setIsLoading(true);
      
      try {
        const userID = deleteUser.id;
        const response = await axiosClient.delete(`/users/${userID}`);
        
        if (response.status === 200) {
          console.log(response.data.message)
          location.reload();
        }
      } catch (err) {
        if (err.response?.status === 401) {
          console.log("found 401 error wow")
          setShowRelogin(true);
          return;
        }
        console.error("Error deleting user:", err);
      } finally {
        setIsLoading(false);
        closeDialogs();
      }
    };

    return (
      <Button type="submit" disabled={isLoading} variant="destructive" onClick={handleDelete}>
        {isLoading ? <Spinner />  : "Delete"}
      </Button>
    );
  };

  const ActionsMenu = ({ user }) => {
    return (
      <Dialog open={editAction || deleteAction} onOpenChange={closeDialogs}>
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="ghost" className="h-8 w-8 p-0">
              <MoreHorizontal />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end">
            <DropdownMenuItem
              onClick={() => navigator.clipboard.writeText(user.id)}
            >
              Copy UserID
            </DropdownMenuItem>
            <DropdownMenuSeparator />
            <DropdownMenuItem
              onClick={() => {  setEditAction(true); setEditUser(user); }}
            >
              Edit User
            </DropdownMenuItem>
            <DropdownMenuSeparator />
            <DropdownMenuItem onClick={() => { setDeleteAction(true); setDeleteUser(user); }}>
              Delete User
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
        <DialogContent>
          {editAction ? <EditMenu />
            : deleteAction ? <DeleteConfirmation />
              : <></>}
        </DialogContent>
      </Dialog>
    );
  }

  const DeleteConfirmation = () => {
    return (
      <div>
        <DialogHeader>
          <DialogTitle>Are you absolutely sure?</DialogTitle>
          <DialogDescription>
            This action cannot be undone. This will permanently delete the user account
            and remove the data from our servers.
          </DialogDescription>
        </DialogHeader>
        <div className="grid gap-4 py-4">
          <span>ID: {deleteUser.id}</span>
          <span>Username: {deleteUser.username}</span>
          <span>Role: {deleteUser.role}</span>
        </div>
        <DialogFooter>
          <Button 
            type="button" 
            variant="outline"
            onClick={closeDialogs}
          >
            Cancel
          </Button>
          <DeleteButton />
        </DialogFooter>
      </div>
    );
  };

  const EditMenu = () => {
    const handleRoleChange = (value) => {
      roleRef.current = value;
    };

    return (
      <div>
        <DialogHeader>
          <DialogTitle>Edit User</DialogTitle>
          <DialogDescription>
            Make changes to the user here. Click save when you're done.
          </DialogDescription>
        </DialogHeader>
        <div className="grid gap-4 py-4">
          <div className="grid gap-2">
            <Label>Username</Label>
            <Input
              name="username"
              ref={usernameRef}
              defaultValue={editUser.username}
              required
            />
          </div>
          <div className="grid gap-2">
            <Label>Role</Label>
            <Select
              defaultValue={editUser.role}
              onValueChange={handleRoleChange}
            >
              <SelectTrigger>
                <SelectValue placeholder="Select a role" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="admin">admin</SelectItem>
                <SelectItem value="default">default</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </div>
        <DialogFooter>
          <Button 
            type="button" 
            variant="outline"
            onClick={closeDialogs}
          >
            Cancel
          </Button>
          <SaveButton />
        </DialogFooter>
      </div>
    );
  }

  const columns = [
    {
      accessorKey: "id",
      header: ({ column }) => {
        return (
          <Button
            variant="ghost"
            onClick={() => column.toggleSorting(column.getIsSorted() === "asc")}
            style={{ padding: 0 }}
          >
            ID
            <ArrowUpDown />
          </Button>
        )
      },
      cell: ({ row }) => (<div className="capitalize">{row.getValue("id")}</div>),
    },
    {
      accessorKey: "username",
      header: ({ column }) => {
        return (
          <Button
            variant="ghost"
            onClick={() => column.toggleSorting(column.getIsSorted() === "asc")}
            style={{ padding: 0 }}
          >
            Username
            <ArrowUpDown />
          </Button>
        )
      },
      cell: ({ row }) => (<div className="lowercase">{row.getValue("username")}</div>),
    },
    {
      accessorKey: "role",
      header: ({ column }) => {
        return (
          <Button
            variant="ghost"
            onClick={() => column.toggleSorting(column.getIsSorted() === "asc")}
            style={{ padding: 0 }}
            className={"text-right"}
          >
            Role
            <ArrowUpDown />
          </Button>
        )
      },
      cell: ({ row }) => (<div className="font-medium">{row.getValue("role")}</div>),
    },
    {
      id: "actions",
      enableHiding: false,
      cell: ({ row }) => {
        const user = row.original

        return <ActionsMenu user={user} />
      },
    },
  ]

  function UserTable() {
    const [sorting, setSorting] = React.useState([])
    const [columnFilters, setColumnFilters] = React.useState([])

    const table = useReactTable({
      data: users,
      columns,
      onSortingChange: setSorting,
      onColumnFiltersChange: setColumnFilters,
      getCoreRowModel: getCoreRowModel(),
      getPaginationRowModel: getPaginationRowModel(),
      getSortedRowModel: getSortedRowModel(),
      getFilteredRowModel: getFilteredRowModel(),
      state: {
        sorting,
        columnFilters,
      },
    })

    return (
      <div className="w-full p-6">
        <div className="flex items-center py-4 gap-10">
          <Input
            placeholder="Filter username..."
            value={(table.getColumn("username")?.getFilterValue()) ?? ""}
            onChange={(event) =>
              table.getColumn("username")?.setFilterValue(event.target.value)
            }
            className="max-w-sm"
          />
          <Input
            placeholder="Filter roles..."
            value={(table.getColumn("role")?.getFilterValue()) ?? ""}
            onChange={(event) =>
              table.getColumn("role")?.setFilterValue(event.target.value)
            }
            className="max-w-sm"
          />
        </div>
        <div className="overflow-hidden rounded-md border">
          <Table>
            <TableHeader>
              {table.getHeaderGroups().map((headerGroup) => (
                <TableRow key={headerGroup.id}>
                  {headerGroup.headers.map((header) => {
                    return (
                      <TableHead key={header.id}>
                        {header.isPlaceholder
                          ? null
                          : flexRender(
                            header.column.columnDef.header,
                            header.getContext()
                          )}
                      </TableHead>
                    )
                  })}
                </TableRow>
              ))}
            </TableHeader>
            <TableBody>
              {table.getRowModel().rows?.length ? (
                table.getRowModel().rows.map((row) => (
                  <TableRow
                    key={row.id}
                    data-state={row.getIsSelected() && "selected"}
                  >
                    {row.getVisibleCells().map((cell) => (
                      <TableCell key={cell.id}>
                        {flexRender(
                          cell.column.columnDef.cell,
                          cell.getContext()
                        )}
                      </TableCell>
                    ))}
                  </TableRow>
                ))
              ) : (
                <TableRow>
                  <TableCell
                    colSpan={columns.length}
                    className="h-24 text-center"
                  >
                    No results.
                  </TableCell>
                </TableRow>
              )}
            </TableBody>
          </Table>
        </div>
        <div className="flex items-center justify-end space-x-2 py-4">
          <div className="space-x-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => table.previousPage()}
              disabled={!table.getCanPreviousPage()}
            >
              Previous
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() => table.nextPage()}
              disabled={!table.getCanNextPage()}
            >
              Next
            </Button>
          </div>
        </div>
      </div>
    )
  }

  return (
    <>
    {showForbidden && <Forbidden />}
    {showRelogin && <Relogin />}
    <UserTable />
    </>
  );
};

export default UserManagement;
