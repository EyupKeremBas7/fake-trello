import { Button, ButtonGroup } from "@chakra-ui/react"
import { useMutation, useQueryClient } from "@tanstack/react-query"

import { CardsService, type CardPublic } from "@/client"
import type { ApiError } from "@/client/core/ApiError"
import useCustomToast from "@/hooks/useCustomToast"
import { handleError } from "@/utils"

interface CardActionsMenuProps {
  card: CardPublic
}

const CardActionsMenu = ({ card }: CardActionsMenuProps) => {
  const queryClient = useQueryClient()
  const { showSuccessToast } = useCustomToast()

  const deleteMutation = useMutation({
    mutationFn: () => CardsService.deleteCard({ id: card.id }),
    onSuccess: () => {
      showSuccessToast("Card deleted successfully.")
    },
    onError: (err: ApiError) => {
      handleError(err)
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ["Cards"] })
    },
  })

  const archiveMutation = useMutation({
    mutationFn: () =>
      CardsService.updateCard({
        id: card.id,
        requestBody: { is_archived: !card.is_archived },
      }),
    onSuccess: () => {
      showSuccessToast(card.is_archived ? "Card unarchived." : "Card archived.")
    },
    onError: (err: ApiError) => {
      handleError(err)
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ["Cards"] })
    },
  })

  return (
    <ButtonGroup size="xs" variant="ghost">
      <Button onClick={() => archiveMutation.mutate()}>
        {card.is_archived ? "Unarchive" : "Archive"}
      </Button>
      <Button colorPalette="red" onClick={() => deleteMutation.mutate()}>
        Delete
      </Button>
    </ButtonGroup>
  )
}

export default CardActionsMenu