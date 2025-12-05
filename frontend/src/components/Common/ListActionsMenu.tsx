import { Button, ButtonGroup } from "@chakra-ui/react"
import { useMutation, useQueryClient } from "@tanstack/react-query"

import { ListsService, type ListPublic } from "@/client"
import type { ApiError } from "@/client/core/ApiError"
import useCustomToast from "@/hooks/useCustomToast"
import { handleError } from "@/utils"

interface ListActionsMenuProps {
  list: ListPublic
}

const ListActionsMenu = ({ list }: ListActionsMenuProps) => {
  const queryClient = useQueryClient()
  const { showSuccessToast } = useCustomToast()

  const deleteMutation = useMutation({
    mutationFn: () => ListsService.deleteBoardList({ id: list.id }),
    onSuccess: () => {
      showSuccessToast("List deleted successfully.")
    },
    onError: (err: ApiError) => {
      handleError(err)
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ["Lists"] })
    },
  })

  return (
    <ButtonGroup size="xs" variant="ghost">
      <Button colorPalette="red" onClick={() => deleteMutation.mutate()}>
        Delete
      </Button>
    </ButtonGroup>
  )
}

export default ListActionsMenu