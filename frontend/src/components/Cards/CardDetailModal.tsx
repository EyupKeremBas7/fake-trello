import {
  Box,
  Button,
  Checkbox,
  Heading,
  HStack,
  IconButton,
  Input,
  Progress,
  Spinner,
  Text,
  Textarea,
  VStack,
} from "@chakra-ui/react"
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { useState } from "react"
import {
  FiCalendar,
  FiCheckSquare,
  FiMessageSquare,
  FiPlus,
  FiTrash2,
  FiX,
} from "react-icons/fi"

import {
  CardsService,
  ChecklistsService,
  CommentsService,
  type CardPublic,
} from "@/client"
import type { ApiError } from "@/client/core/ApiError"
import {
  DialogBackdrop,
  DialogBody,
  DialogCloseTrigger,
  DialogContent,
  DialogHeader,
  DialogRoot,
  DialogTitle,
} from "@/components/ui/dialog"
import CardMembersInfo from "@/components/Cards/CardMembersInfo"
import CardAssigneeSelector from "@/components/Cards/CardAssigneeSelector"
import useCustomToast from "@/hooks/useCustomToast"
import { handleError } from "@/utils"

interface CardDetailModalProps {
  card: CardPublic
  isOpen: boolean
  onClose: () => void
  workspaceId?: string
}

const ChecklistSection = ({ cardId }: { cardId: string }) => {
  const [newItemTitle, setNewItemTitle] = useState("")
  const [showAddForm, setShowAddForm] = useState(false)
  const queryClient = useQueryClient()
  const { showSuccessToast } = useCustomToast()

  const { data, isLoading } = useQuery({
    queryKey: ["checklists", cardId],
    queryFn: () => ChecklistsService.readChecklistItems({ cardId }),
  })

  const createMutation = useMutation({
    mutationFn: () =>
      ChecklistsService.createChecklistItem({
        requestBody: {
          title: newItemTitle,
          card_id: cardId,
        },
      }),
    onSuccess: () => {
      showSuccessToast("Checklist item added.")
      setNewItemTitle("")
      setShowAddForm(false)
    },
    onError: (err: ApiError) => handleError(err),
    onSettled: () => queryClient.invalidateQueries({ queryKey: ["checklists", cardId] }),
  })

  const toggleMutation = useMutation({
    mutationFn: (id: string) => ChecklistsService.toggleChecklistItem({ id }),
    onSettled: () => queryClient.invalidateQueries({ queryKey: ["checklists", cardId] }),
  })

  const deleteMutation = useMutation({
    mutationFn: (id: string) => ChecklistsService.deleteChecklistItem({ id }),
    onSuccess: () => showSuccessToast("Item deleted."),
    onSettled: () => queryClient.invalidateQueries({ queryKey: ["checklists", cardId] }),
  })

  if (isLoading) return <Spinner size="sm" />

  const items = data?.data ?? []
  const completedCount = items.filter((item) => item.is_completed).length
  const progress = items.length > 0 ? (completedCount / items.length) * 100 : 0

  return (
    <Box>
      <HStack mb={3}>
        <FiCheckSquare />
        <Heading size="sm">Checklist</Heading>
        <Text fontSize="xs" color="fg.muted">
          ({completedCount}/{items.length})
        </Text>
      </HStack>

      {items.length > 0 && (
        <Progress.Root value={progress} mb={3} size="sm" colorPalette={progress === 100 ? "green" : "blue"}>
          <Progress.Track>
            <Progress.Range />
          </Progress.Track>
        </Progress.Root>
      )}

      <VStack align="stretch" gap={2}>
        {items.map((item) => (
          <HStack
            key={item.id}
            p={2}
            bg="bg.subtle"
            borderRadius="md"
            justify="space-between"
          >
            <HStack>
              <Checkbox.Root
                checked={item.is_completed}
                onCheckedChange={() => toggleMutation.mutate(item.id)}
              >
                <Checkbox.HiddenInput />
                <Checkbox.Control />
              </Checkbox.Root>
              <Text
                fontSize="sm"
                textDecoration={item.is_completed ? "line-through" : "none"}
                color={item.is_completed ? "fg.muted" : "fg"}
              >
                {item.title}
              </Text>
            </HStack>
            <IconButton
              aria-label="Delete item"
              size="xs"
              variant="ghost"
              colorPalette="red"
              onClick={() => deleteMutation.mutate(item.id)}
            >
              <FiTrash2 />
            </IconButton>
          </HStack>
        ))}
      </VStack>

      {showAddForm ? (
        <Box mt={3}>
          <Input
            placeholder="Add an item..."
            size="sm"
            value={newItemTitle}
            onChange={(e) => setNewItemTitle(e.target.value)}
            autoFocus
          />
          <HStack mt={2}>
            <Button
              size="sm"
              colorPalette="blue"
              onClick={() => createMutation.mutate()}
              loading={createMutation.isPending}
              disabled={!newItemTitle.trim()}
            >
              Add
            </Button>
            <IconButton
              aria-label="Cancel"
              size="sm"
              variant="ghost"
              onClick={() => setShowAddForm(false)}
            >
              <FiX />
            </IconButton>
          </HStack>
        </Box>
      ) : (
        <Button
          variant="ghost"
          size="sm"
          mt={2}
          onClick={() => setShowAddForm(true)}
        >
          <FiPlus />
          <Text ml={2}>Add an item</Text>
        </Button>
      )}
    </Box>
  )
}

const CommentsSection = ({ cardId }: { cardId: string }) => {
  const [newComment, setNewComment] = useState("")
  const queryClient = useQueryClient()
  const { showSuccessToast } = useCustomToast()

  const { data, isLoading } = useQuery({
    queryKey: ["comments", cardId],
    queryFn: () => CommentsService.readComments({ cardId }),
  })

  const createMutation = useMutation({
    mutationFn: () =>
      CommentsService.createComment({
        requestBody: {
          content: newComment,
          card_id: cardId,
        },
      }),
    onSuccess: () => {
      showSuccessToast("Comment added.")
      setNewComment("")
    },
    onError: (err: ApiError) => handleError(err),
    onSettled: () => queryClient.invalidateQueries({ queryKey: ["comments", cardId] }),
  })

  const deleteMutation = useMutation({
    mutationFn: (id: string) => CommentsService.deleteComment({ id }),
    onSuccess: () => showSuccessToast("Comment deleted."),
    onSettled: () => queryClient.invalidateQueries({ queryKey: ["comments", cardId] }),
  })

  if (isLoading) return <Spinner size="sm" />

  const comments = data?.data ?? []

  return (
    <Box>
      <HStack mb={3}>
        <FiMessageSquare />
        <Heading size="sm">Comments</Heading>
        <Text fontSize="xs" color="fg.muted">
          ({comments.length})
        </Text>
      </HStack>

      <Box mb={4}>
        <Textarea
          placeholder="Write a comment..."
          size="sm"
          value={newComment}
          onChange={(e) => setNewComment(e.target.value)}
          rows={3}
        />
        <Button
          size="sm"
          colorPalette="blue"
          mt={2}
          onClick={() => createMutation.mutate()}
          loading={createMutation.isPending}
          disabled={!newComment.trim()}
        >
          Save
        </Button>
      </Box>

      <VStack align="stretch" gap={3}>
        {comments.map((comment) => (
          <Box
            key={comment.id}
            p={3}
            bg="bg.subtle"
            borderRadius="md"
            borderWidth="1px"
            borderColor="border.subtle"
          >
            <HStack justify="space-between" mb={2}>
              <HStack>
                <Box
                  w={8}
                  h={8}
                  bg="blue.500"
                  borderRadius="full"
                  display="flex"
                  alignItems="center"
                  justifyContent="center"
                  color="white"
                  fontSize="xs"
                  fontWeight="bold"
                >
                  {(comment.user_full_name || comment.user_email || "U")
                    .charAt(0)
                    .toUpperCase()}
                </Box>
                <VStack align="start" gap={0}>
                  <Text fontSize="sm" fontWeight="medium">
                    {comment.user_full_name || comment.user_email}
                  </Text>
                  <Text fontSize="xs" color="fg.muted">
                    {new Date(comment.created_at).toLocaleString()}
                  </Text>
                </VStack>
              </HStack>
              <IconButton
                aria-label="Delete comment"
                size="xs"
                variant="ghost"
                colorPalette="red"
                onClick={() => deleteMutation.mutate(comment.id)}
              >
                <FiTrash2 />
              </IconButton>
            </HStack>
            <Text fontSize="sm" whiteSpace="pre-wrap">
              {comment.content}
            </Text>
          </Box>
        ))}
      </VStack>
    </Box>
  )
}

export const CardDetailModal = ({
  card,
  isOpen,
  onClose,
  workspaceId,
}: CardDetailModalProps) => {
  const [description, setDescription] = useState(card.description || "")
  const [isEditingDesc, setIsEditingDesc] = useState(false)
  const queryClient = useQueryClient()
  const { showSuccessToast } = useCustomToast()

  const updateMutation = useMutation({
    mutationFn: (data: { description?: string }) =>
      CardsService.updateCard({
        id: card.id,
        requestBody: data,
      }),
    onSuccess: () => {
      showSuccessToast("Card updated.")
      setIsEditingDesc(false)
    },
    onError: (err: ApiError) => handleError(err),
    onSettled: () => queryClient.invalidateQueries({ queryKey: ["cards"] }),
  })

  return (
    <DialogRoot open={isOpen} onOpenChange={(e) => !e.open && onClose()} size="xl">
      <DialogBackdrop />
      <DialogContent maxH="90vh" overflow="auto">
        <DialogHeader>
          <DialogTitle>{card.title}</DialogTitle>
          <DialogCloseTrigger />
        </DialogHeader>

        <DialogBody pb={6}>
          <VStack align="stretch" gap={6}>
            {/* Due Date */}
            {card.due_date && (
              <HStack color="blue.500">
                <FiCalendar />
                <Text fontSize="sm">
                  Due: {new Date(card.due_date).toLocaleDateString()}
                </Text>
              </HStack>
            )}

            {/* Owner & Assignee */}
            <Box>
              <Heading size="sm" mb={2}>Members</Heading>
              <CardMembersInfo card={card} />
            </Box>

            {/* Assign Member */}
            {workspaceId && (
              <Box>
                <CardAssigneeSelector card={card} workspaceId={workspaceId} />
              </Box>
            )}

            {/* Description */}
            <Box>
              <Heading size="sm" mb={2}>
                Description
              </Heading>
              {isEditingDesc ? (
                <Box>
                  <Textarea
                    value={description}
                    onChange={(e) => setDescription(e.target.value)}
                    rows={4}
                  />
                  <HStack mt={2}>
                    <Button
                      size="sm"
                      colorPalette="blue"
                      onClick={() =>
                        updateMutation.mutate({ description })
                      }
                      loading={updateMutation.isPending}
                    >
                      Save
                    </Button>
                    <Button
                      size="sm"
                      variant="ghost"
                      onClick={() => {
                        setDescription(card.description || "")
                        setIsEditingDesc(false)
                      }}
                    >
                      Cancel
                    </Button>
                  </HStack>
                </Box>
              ) : (
                <Box
                  p={3}
                  bg="bg.subtle"
                  borderRadius="md"
                  cursor="pointer"
                  onClick={() => setIsEditingDesc(true)}
                  minH="60px"
                >
                  <Text fontSize="sm" color={description ? "fg" : "fg.muted"}>
                    {description || "Add a more detailed description..."}
                  </Text>
                </Box>
              )}
            </Box>

            {/* Checklist */}
            <ChecklistSection cardId={card.id} />

            {/* Comments */}
            <CommentsSection cardId={card.id} />
          </VStack>
        </DialogBody>
      </DialogContent>
    </DialogRoot>
  )
}

export default CardDetailModal

