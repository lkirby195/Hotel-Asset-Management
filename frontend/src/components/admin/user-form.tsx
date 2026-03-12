"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { useCreateUser, useUpdateUser } from "@/hooks/use-users";
import { useProperty } from "@/providers/property-provider";
import type { UserProfile } from "@/lib/types";

interface UserFormProps {
  user: UserProfile | null; // null = create mode
  onClose: () => void;
}

export function UserForm({ user, onClose }: UserFormProps) {
  const isEditing = !!user;
  const { properties } = useProperty();
  const createUser = useCreateUser();
  const updateUser = useUpdateUser();

  const [formData, setFormData] = useState({
    clerk_id: "",
    email: user?.email ?? "",
    name: user?.name ?? "",
    role: user?.role ?? "manager",
    is_active: user?.is_active ?? true,
    property_ids: user?.property_ids ?? [],
  });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (isEditing && user) {
      await updateUser.mutateAsync({
        userId: user.id,
        body: {
          email: formData.email,
          name: formData.name,
          role: formData.role,
          is_active: formData.is_active,
          property_ids: formData.property_ids,
        },
      });
    } else {
      await createUser.mutateAsync({
        clerk_id: formData.clerk_id,
        email: formData.email,
        name: formData.name,
        role: formData.role,
        property_ids: formData.property_ids,
      });
    }
    onClose();
  };

  const toggleProperty = (propertyId: string) => {
    setFormData((prev) => ({
      ...prev,
      property_ids: prev.property_ids.includes(propertyId)
        ? prev.property_ids.filter((id) => id !== propertyId)
        : [...prev.property_ids, propertyId],
    }));
  };

  return (
    <Dialog open onOpenChange={onClose}>
      <DialogContent className="max-w-md">
        <DialogHeader>
          <DialogTitle>{isEditing ? "Edit User" : "Create User"}</DialogTitle>
        </DialogHeader>
        <form onSubmit={handleSubmit} className="space-y-4">
          {!isEditing && (
            <div className="space-y-2">
              <Label htmlFor="clerk_id">Clerk User ID</Label>
              <Input
                id="clerk_id"
                value={formData.clerk_id}
                onChange={(e) =>
                  setFormData((prev) => ({
                    ...prev,
                    clerk_id: e.target.value,
                  }))
                }
                placeholder="user_..."
                required
              />
            </div>
          )}
          <div className="space-y-2">
            <Label htmlFor="name">Name</Label>
            <Input
              id="name"
              value={formData.name}
              onChange={(e) =>
                setFormData((prev) => ({ ...prev, name: e.target.value }))
              }
              required
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="email">Email</Label>
            <Input
              id="email"
              type="email"
              value={formData.email}
              onChange={(e) =>
                setFormData((prev) => ({ ...prev, email: e.target.value }))
              }
              required
            />
          </div>
          <div className="space-y-2">
            <Label>Role</Label>
            <Select
              value={formData.role}
              onValueChange={(v) =>
                setFormData((prev) => ({
                  ...prev,
                  role: v as "admin" | "executive" | "operator" | "manager",
                }))
              }
            >
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="manager">Manager</SelectItem>
                <SelectItem value="operator">Operator</SelectItem>
                <SelectItem value="executive">Executive</SelectItem>
                <SelectItem value="admin">Admin</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <div className="space-y-2">
            <Label>Properties</Label>
            <div className="max-h-40 space-y-1 overflow-y-auto rounded border p-2">
              {properties.map((p) => (
                <label
                  key={p.id}
                  className="flex items-center gap-2 text-sm"
                >
                  <input
                    type="checkbox"
                    checked={formData.property_ids.includes(p.id)}
                    onChange={() => toggleProperty(p.id)}
                  />
                  {p.name} ({p.code})
                </label>
              ))}
            </div>
          </div>
          <div className="flex justify-end gap-2">
            <Button type="button" variant="outline" onClick={onClose}>
              Cancel
            </Button>
            <Button
              type="submit"
              disabled={createUser.isPending || updateUser.isPending}
            >
              {isEditing ? "Save" : "Create"}
            </Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  );
}
