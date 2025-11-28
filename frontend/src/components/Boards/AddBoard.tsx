import {
  Button,
  DialogActionTrigger,
  DialogTitle,
  Input,
  Text,
  VStack,
} from "@chakra-ui/react"
import { useMutation, useQueryClient } from "@tanstack/react-query"
import { useState } from "react"
import { type SubmitHandler, useForm } from "react-hook-form"
import { FaPlus } from "react-icons/fa"

import { type BoardCreate, BoardsService } from "@/client"
import type { ApiError } from "@/client/core/ApiError"
import useCustomToast from "@/hooks/useCustomToast"
import { handleError } from "@/utils"
import {
  DialogBody,
  DialogCloseTrigger,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogRoot,
  DialogTrigger,
} from "../ui/dialog"
import { Field } from "../ui/field"

const AddBoard = () => {
  const [isOpen, setIsOpen] = useState(false)
  const queryClient = useQueryClient()
  const { showSuccessToast } = useCustomToast()
  
  const {
    register,
    handleSubmit,
    reset,
    formState: { errors, isValid, isSubmitting },
  } = useForm<BoardCreate>({
    mode: "onBlur",
    criteriaMode: "all",
    defaultValues: {
      name: "",
      visibility: "private", 
      background_image: "",
      workspace_id: "", 
    },
  })

  const mutation = useMutation({
    mutationFn: (data: BoardCreate) =>
      BoardsService.createBoard({ requestBody: data }),
    onSuccess: () => {
      showSuccessToast("Board created successfully.")
      reset()
      setIsOpen(false)
    },
    onError: (err: ApiError) => {
      handleError(err)
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ["Boards"] })
    },
  })

  const onSubmit: SubmitHandler<BoardCreate> = (data) => {
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
        <Button value="add-Board" my={4}>
          <FaPlus fontSize="16px" />
          Add Board
        </Button>
      </DialogTrigger>
      <DialogContent>
        <form onSubmit={handleSubmit(onSubmit)}>
          <DialogHeader>
            <DialogTitle>Add Board</DialogTitle>
          </DialogHeader>
          <DialogBody>
            <Text mb={4}>Fill in the details to add a new Board.</Text>
            <VStack gap={4}>
              <Field
                required
                invalid={!!errors.name}
                errorText={errors.name?.message}
                label="Name"
              >
                <Input
                  {...register("name", {
                    required: "Name is required.",
                  })}
                  placeholder="Name"
                  type="text"
                />
              </Field>

              {/* Description alanı kaldırıldı, yerine Workspace ID geldi */}
              <Field
                required
                invalid={!!errors.workspace_id}
                errorText={errors.workspace_id?.message}
                label="Workspace ID"
              >
                <Input
                  {...register("workspace_id", {
                    required: "Workspace ID is required.",
                  })}
                  placeholder="Workspace ID"
                  type="text"
                />
              </Field>

              {/* Visibility alanı eklendi */}
              <Field
                label="Visibility"
                invalid={!!errors.visibility}
                errorText={errors.visibility?.message}
              >
                {/* Chakra UI Select veya Native Select kullanılabilir */}
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
            <DialogActionTrigger asChild>
              <Button
                variant="subtle"
                colorPalette="gray"
                disabled={isSubmitting}
              >
                Cancel
              </Button>
            </DialogActionTrigger>
            <Button
              variant="solid"
              type="submit"
              disabled={!isValid}
              loading={isSubmitting}
            >
              Save
            </Button>
          </DialogFooter>
        </form>
        <DialogCloseTrigger />
      </DialogContent>
    </DialogRoot>
  )
}

export default AddBoard