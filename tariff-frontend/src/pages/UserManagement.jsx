import * as React from "react"
import {
  flexRender,
  getCoreRowModel,
  getFilteredRowModel,
  getPaginationRowModel,
  getSortedRowModel,
  useReactTable,
} from "@tanstack/react-table"
import { ArrowUpDown, ChevronDown, MoreHorizontal } from "lucide-react"

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
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import axiosClient from "@/api/axiosClient";
import { useEffect, useState } from "react";

const UserManagement = () => {
  const [users, setUsers] = useState([]);
  useEffect(() => {
    const fetchAllUsers = async () => {
      try {
        const response = await axiosClient.get("/users/");

        if (response.status === 200) {
          console.log("Fetched users:", response.data.users);
          setUsers(response.data.users);
        }
      } catch (error) {
        console.error("Error fetching users:", error);
      }
    };

    fetchAllUsers();
  }, []);

  const columns = [
    {
      accessorKey: "id",
      header: "ID",
      cell: ({ row }) => (<div className="capitalize">{row.getValue("id")}</div>),
    },
    {
      accessorKey: "username",
      header: ({ column }) => {
        return (
          <Button
            variant="ghost"
            onClick={() => column.toggleSorting(column.getIsSorted() === "asc")}
            style={{padding: 0}}
          >
            Username
            <ArrowUpDown />
          </Button>
        )
      },
      cell: ({ row }) => (<div className="lowercase">{row.getValue("username")}</div>),
    },
    {
      accessorKey: "roles",
      header: () => <div className="text-right">Roles</div>,
      cell: ({ row }) => (<div className="text-right font-medium">{row.getValue("roles")}</div>),
    },
    {
      id: "actions",
      enableHiding: false,
      cell: ({ row }) => {
        const user = row.original

        return (
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="ghost" className="h-8 w-8 p-0">
                <span className="sr-only">Open menu</span>
                <MoreHorizontal />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
              <DropdownMenuItem
                onClick={() => navigator.clipboard.writeText(user.id)}
              >
                Copy user ID
              </DropdownMenuItem>
              <DropdownMenuSeparator />
              <DropdownMenuItem>Edit User</DropdownMenuItem>
              <DropdownMenuItem>Delete User</DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        )
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
            value={(table.getColumn("roles")?.getFilterValue()) ?? ""}
            onChange={(event) =>
              table.getColumn("roles")?.setFilterValue(event.target.value)
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
    <UserTable />
  );
};

export default UserManagement;
