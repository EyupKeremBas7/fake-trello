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
import { FaPlus } from "react-icons/fa"

import { type Visibility, type WorkspaceCreate, WorkspacesService } from "@/client"
import type { ApiError } from "@/client/core/ApiError"
import useCustomToast from "@/hooks/useCustomToast"
import { handleError } from "@/utils"
import { Field } from "../ui/field"

type WorkspaceCreateForm = WorkspaceCreate & {
  visibility: Visibility
  background_image?: string | null
}

const AddWorkspace = () => {
  const [isOpen, setIsOpen] = useState(false)
  const queryClient = useQueryClient()
  const { showSuccessToast } = useCustomToast()

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors, isValid, isSubmitting },
  } = useForm<WorkspaceCreateForm>({
    mode: "onBlur",
    criteriaMode: "all",
    defaultValues: {
      name: "",
      description: "",
      visibility: "workspace",
      background_image: "",
    },
  })

  const mutation = useMutation({
    mutationFn: (data: WorkspaceCreateForm) => {
      const { visibility: _visibility, background_image: _background_image, ...payload } = data
      return WorkspacesService.createWorkspace({ requestBody: payload })
    },
    onSuccess: () => {
      showSuccessToast("Workspace created successfully.")
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

  const onSubmit: SubmitHandler<WorkspaceCreateForm> = (data) => {
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
        <Button value="add-Workspace" my={4}>
          <FaPlus fontSize="16px" />
          Add Workspace
        </Button>
      </DialogTrigger>
      <DialogContent>
        <form onSubmit={handleSubmit(onSubmit)}>
          <DialogHeader>
            <DialogTitle>Add Workspace</DialogTitle>
          </DialogHeader>
          <DialogBody>
            <Text mb={4}>Fill in the details to add a new Workspace.</Text>
            <VStack gap={4}>
              <Field
                required
                invalid={!!errors.name}
                errorText={errors.name?.message}
                label="Name"
              >
                <Input
                  {...register("name", { required: "Name is required." })}
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
                  {...register("visibility", { required: "Visibility is required." })}
                  style={{
                    width: "100%",
                    padding: "8px",
                    borderRadius: "4px",
                    border: "1px solid #E2E8F0",
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
            <DialogActionTrigger asChild>
              <Button variant="subtle" colorPalette="gray" disabled={isSubmitting}>
                Cancel
              </Button>
            </DialogActionTrigger>
            <Button variant="solid" type="submit" disabled={!isValid} loading={isSubmitting}>
              Save
            </Button>
          </DialogFooter>
        </form>
        <DialogCloseTrigger />
      </DialogContent>
    </DialogRoot>
  )
}

export default AddWorkspace