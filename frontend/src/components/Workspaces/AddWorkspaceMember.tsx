import {
  Button,
  DialogActionTrigger,
  DialogBody,
  DialogCloseTrigger,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogRoot,
  DialogTitle,
  DialogTrigger,
  Input,
  Text,
  VStack,
} from "@chakra-ui/react"
import { useMutation, useQueryClient } from "@tanstack/react-query"
import { useState } from "react"
import { type SubmitHandler, useForm } from "react-hook-form"
import { FiUserPlus } from "react-icons/fi"

import { WorkspacesService } from "@/client"
import type { ApiError } from "@/client/core/ApiError"
import useCustomToast from "@/hooks/useCustomToast"
import { handleError } from "@/utils"
import { Field } from "../ui/field"

interface AddWorkspaceMemberProps {
  workspaceId: string
}

interface MemberFormData {
  email: string
  role: string
}

const AddWorkspaceMember = ({ workspaceId }: AddWorkspaceMemberProps) => {
  const [isOpen, setIsOpen] = useState(false)
  const queryClient = useQueryClient()
  const { showSuccessToast } = useCustomToast()

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors, isValid, isSubmitting },
  } = useForm<MemberFormData>({
    mode: "onBlur",
    defaultValues: {
      email: "",
      role: "member",
    },
  })

  const mutation = useMutation({
    mutationFn: (data: MemberFormData) =>
      WorkspacesService.inviteWorkspaceMember({
        id: workspaceId,
        requestBody: {
          email: data.email,
          role: data.role as "admin" | "member" | "observer",
        },
      }),
    onSuccess: () => {
      showSuccessToast("Invitation sent successfully.")
      reset()
      setIsOpen(false)
    },
    onError: (err: ApiError) => {
      handleError(err)
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ["workspaceMembers", workspaceId] })
    },
  })

  const onSubmit: SubmitHandler<MemberFormData> = (data) => {
    mutation.mutate(data)
  }

  return (
    <DialogRoot
      size={{ base: "xs", md: "md" }}
      placement="center"
      open={isOpen}
      onOpenChange={({ open }) => setIsOpen(open)}
    >
      <DialogTrigger asChild>
        <Button size="sm" variant="outline">
          <FiUserPlus />
          Invite Member
        </Button>
      </DialogTrigger>
      <DialogContent>
        <form onSubmit={handleSubmit(onSubmit)}>
          <DialogHeader>
            <DialogTitle>Invite Member to Workspace</DialogTitle>
          </DialogHeader>
          <DialogBody>
            <Text mb={4}>Enter the email address of the person you want to invite.</Text>
            <VStack gap={4}>
              <Field
                required
                invalid={!!errors.email}
                errorText={errors.email?.message}
                label="Email Address"
              >
                <Input
                  {...register("email", {
                    required: "Email is required.",
                    pattern: {
                      value: /^[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}$/i,
                      message: "Invalid email address",
                    },
                  })}
                  placeholder="user@example.com"
                  type="email"
                />
              </Field>

              <Field
                required
                invalid={!!errors.role}
                errorText={errors.role?.message}
                label="Role"
              >
                <select
                  {...register("role", { required: "Role is required." })}
                  style={{
                    width: "100%",
                    padding: "8px",
                    borderRadius: "4px",
                    border: "1px solid var(--chakra-colors-border-subtle)",
                    background: "var(--chakra-colors-bg-subtle)",
                    color: "inherit",
                  }}
                >
                  <option value="admin">Admin - Can manage workspace and members</option>
                  <option value="member">Member - Can create and edit boards/cards</option>
                  <option value="observer">Observer - Can only view</option>
                </select>
              </Field>
            </VStack>
          </DialogBody>

          <DialogFooter gap={2}>
            <DialogActionTrigger asChild>
              <Button variant="subtle" colorPalette="gray" disabled={isSubmitting}>
                Cancel
              </Button>
            </DialogActionTrigger>
            <Button variant="solid" type="submit" disabled={!isValid} loading={isSubmitting}>
              Send Invitation
            </Button>
          </DialogFooter>
        </form>
        <DialogCloseTrigger />
      </DialogContent>
    </DialogRoot>
  )
}

export default AddWorkspaceMember