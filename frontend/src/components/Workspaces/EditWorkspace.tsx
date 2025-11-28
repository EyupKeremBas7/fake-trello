import {
  Button,
  ButtonGroup,
  DialogActionTrigger,
  Input,
  Text,
  VStack,
} from "@chakra-ui/react"
import { useMutation, useQueryClient } from "@tanstack/react-query"
import { useState } from "react"
import { type SubmitHandler, useForm } from "react-hook-form"
import { FaExchangeAlt } from "react-icons/fa"

import { type ApiError, type WorkspacePublic, WorkspacesService } from "@/client"
import useCustomToast from "@/hooks/useCustomToast"
import { handleError } from "@/utils"
import {
  DialogBody,
  DialogCloseTrigger,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogRoot,
  DialogTitle,
  DialogTrigger,
} from "../ui/dialog"
import { Field } from "../ui/field"

interface EditWorkspaceProps {
  Workspace: WorkspacePublic
}

interface WorkspaceUpdateForm {
  name: string
  visibility?: 'private' | 'workspace' | 'public'
  background_image?: string
}

const EditWorkspace = ({ Workspace }: EditWorkspaceProps) => {
  const [isOpen, setIsOpen] = useState(false)
  const queryClient = useQueryClient()
  const { showSuccessToast } = useCustomToast()
  const {
    register,
    handleSubmit,
    reset,
    formState: { errors, isSubmitting },
  } = useForm<WorkspaceUpdateForm>({
    mode: "onBlur",
    criteriaMode: "all",
    defaultValues: {
      name: Workspace.name,
      visibility: Workspace.visibility,
      background_image: Workspace.background_image || "",
    },
  })

  const mutation = useMutation({
    mutationFn: (data: WorkspaceUpdateForm) =>
      WorkspacesService.updateWorkspace({ id: Workspace.id, requestBody: data }),
    onSuccess: () => {
      showSuccessToast("Workspace updated successfully.")
      reset()
      setIsOpen(false)
    },
    onError: (err: ApiError) => {
      handleError(err)
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ["Workspaces"] })
    },
  })

  const onSubmit: SubmitHandler<WorkspaceUpdateForm> = async (data) => {
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
        <Button variant="ghost">
          <FaExchangeAlt fontSize="16px" />
          Edit Workspace
        </Button>
      </DialogTrigger>
      <DialogContent>
        <form onSubmit={handleSubmit(onSubmit)}>
          <DialogHeader>
            <DialogTitle>Edit Workspace</DialogTitle>
          </DialogHeader>
          <DialogBody>
            <Text mb={4}>Update the Workspace details below.</Text>
            <VStack gap={4}>
              <Field
                required
                invalid={!!errors.name}
                errorText={errors.name?.message}
                label="Name"
              >
                <Input
                  {...register("name", {
                    required: "Name is required",
                  })}
                  placeholder="Name"
                  type="text"
                />
              </Field>

              <Field
                label="Visibility"
                invalid={!!errors.visibility}
                errorText={errors.visibility?.message}
              >
                <select
                  {...register("visibility")}
                  style={{ 
                    width: "100%", 
                    padding: "8px", 
                    borderRadius: "4px", 
                    border: "1px solid #E2E8F0" 
                  }}
                >
                  <option value="private">Private</option>
                  <option value="workspace">Workspace</option>
                  <option value="public">Public</option>
                </select>
              </Field>
            </VStack>
          </DialogBody>

          <DialogFooter gap={2}>
            <ButtonGroup>
              <DialogActionTrigger asChild>
                <Button
                  variant="subtle"
                  colorPalette="gray"
                  disabled={isSubmitting}
                >
                  Cancel
                </Button>
              </DialogActionTrigger>
              <Button variant="solid" type="submit" loading={isSubmitting}>
                Save
              </Button>
            </ButtonGroup>
          </DialogFooter>
        </form>
        <DialogCloseTrigger />
      </DialogContent>
    </DialogRoot>
  )
}

export default EditWorkspace