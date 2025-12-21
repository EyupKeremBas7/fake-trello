import {
  Box,
  Button,
  Container,
  Flex,
  Heading,
  HStack,
  IconButton,
  Input,
  SimpleGrid,
  Spinner,
  Text,
  VStack,
} from "@chakra-ui/react"
import {
  DndContext,
  DragOverlay,
  closestCorners,
  KeyboardSensor,
  PointerSensor,
  useSensor,
  useSensors,
  type DragStartEvent,
  type DragEndEvent,
  type DragOverEvent,
} from "@dnd-kit/core"
import {
  SortableContext,
  sortableKeyboardCoordinates,
  useSortable,
  verticalListSortingStrategy,
  horizontalListSortingStrategy,
} from "@dnd-kit/sortable"
import { CSS } from "@dnd-kit/utilities"
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { createFileRoute, Link as RouterLink } from "@tanstack/react-router"
import { useState, useMemo } from "react"
import { FiArrowLeft, FiCheckSquare, FiImage, FiMessageSquare, FiMoreHorizontal, FiPlus, FiX } from "react-icons/fi"
import { z } from "zod"

import { BoardsService, CardsService, ChecklistsService, CommentsService, ListsService, type CardPublic, type ListPublic } from "@/client"
import type { ApiError } from "@/client/core/ApiError"
import CardDetailModal from "@/components/Cards/CardDetailModal"
import {
  DialogBody,
  DialogCloseTrigger,
  DialogContent,
  DialogHeader,
  DialogRoot,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog"
import useCustomToast from "@/hooks/useCustomToast"

const BoardDetailSearchSchema = z.object({
  page: z.number().optional().catch(1),
})

export const Route = createFileRoute("/_layout/board/$boardId")({
  component: BoardDetail,
  validateSearch: (search) => BoardDetailSearchSchema.parse(search),
})
interface SortableCardProps {
  card: CardPublic
  onClick: () => void
}

function SortableCard({ card, onClick }: SortableCardProps) {
  const {
    attributes,
    listeners,
    setNodeRef,
    transform,
    transition,
    isDragging,
  } = useSortable({ id: card.id })

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
    opacity: isDragging ? 0.5 : 1,
  }

  const { data: checklistData } = useQuery({
    queryKey: ["checklists", card.id],
    queryFn: () => ChecklistsService.readChecklistItems({ cardId: card.id }),
  })

  const { data: commentsData } = useQuery({
    queryKey: ["comments", card.id],
    queryFn: () => CommentsService.readComments({ cardId: card.id }),
  })

  const checklistCount = checklistData?.count ?? 0
  const completedCount = checklistData?.data?.filter((item) => item.is_completed).length ?? 0
  const commentsCount = commentsData?.count ?? 0

  return (
    <Box
      ref={setNodeRef}
      style={style}
      {...attributes}
      {...listeners}
      bg="bg.panel"
      p={3}
      borderRadius="md"
      boxShadow="sm"
      cursor="grab"
      _hover={{ bg: "bg.subtle" }}
      borderWidth="1px"
      borderColor="border.subtle"
      onClick={onClick}
    >
      <Text fontSize="sm" fontWeight="medium">
        {card.title}
      </Text>
      {card.description && (
        <Text fontSize="xs" color="fg.muted" mt={1} lineClamp={2}>
          {card.description}
        </Text>
      )}
      <HStack mt={2} gap={3}>
        {card.due_date && (
          <Text fontSize="xs" color="blue.500">
            📅 {new Date(card.due_date).toLocaleDateString()}
          </Text>
        )}
        {checklistCount > 0 && (
          <HStack fontSize="xs" color={completedCount === checklistCount ? "green.500" : "fg.muted"}>
            <FiCheckSquare size={12} />
            <Text>{completedCount}/{checklistCount}</Text>
          </HStack>
        )}
        {commentsCount > 0 && (
          <HStack fontSize="xs" color="fg.muted">
            <FiMessageSquare size={12} />
            <Text>{commentsCount}</Text>
          </HStack>
        )}
      </HStack>
    </Box>
  )
}

function CardDragOverlay({ card }: { card: CardPublic }) {
  return (
    <Box
      bg="bg.panel"
      p={3}
      borderRadius="md"
      boxShadow="xl"
      borderWidth="2px"
      borderColor="blue.500"
      opacity={0.9}
      transform="rotate(3deg)"
      w="260px"
    >
      <Text fontSize="sm" fontWeight="medium">
        {card.title}
      </Text>
    </Box>
  )
}

const AddCardForm = ({ listId, onClose }: { listId: string; onClose: () => void }) => {
  const [title, setTitle] = useState("")
  const queryClient = useQueryClient()
  const { showSuccessToast, showErrorToast } = useCustomToast()

  const mutation = useMutation({
    mutationFn: () =>
      CardsService.createCard({
        requestBody: {
          title,
          list_id: listId,
        },
      }),
    onSuccess: () => {
      showSuccessToast("Card created successfully.")
      setTitle("")
      onClose()
    },
    onError: (err: ApiError) => {
      showErrorToast(err.message || "Failed to create card")
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ["cards"] })
    },
  })

  return (
    <Box bg="bg.panel" p={2} borderRadius="md" mt={2}>
      <Input
        placeholder="Enter card title..."
        size="sm"
        value={title}
        onChange={(e) => setTitle(e.target.value)}
        autoFocus
        onKeyDown={(e) => {
          if (e.key === "Enter" && title.trim()) {
            mutation.mutate()
          }
        }}
      />
      <HStack mt={2}>
        <Button
          size="sm"
          colorPalette="blue"
          onClick={() => mutation.mutate()}
          loading={mutation.isPending}
          disabled={!title.trim()}
        >
          Add Card
        </Button>
        <IconButton aria-label="Cancel" size="sm" variant="ghost" onClick={onClose}>
          <FiX />
        </IconButton>
      </HStack>
    </Box>
  )
}

interface SortableListColumnProps {
  list: ListPublic
  cards: CardPublic[]
  onCardClick: (card: CardPublic) => void
}

function SortableListColumn({ list, cards, onCardClick }: SortableListColumnProps) {
  const [showAddCard, setShowAddCard] = useState(false)

  const {
    attributes,
    listeners,
    setNodeRef,
    transform,
    transition,
    isDragging,
  } = useSortable({ id: `list-${list.id}` })

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
    opacity: isDragging ? 0.5 : 1,
  }

  const listCards = cards
    .filter((card) => card.list_id === list.id)
    .sort((a, b) => (a.position ?? 0) - (b.position ?? 0))

  return (
    <Box
      ref={setNodeRef}
      style={style}
      bg="bg.subtle"
      borderRadius="lg"
      p={3}
      minW="280px"
      maxW="280px"
      maxH="calc(100vh - 200px)"
      display="flex"
      flexDirection="column"
    >
      <HStack justify="space-between" mb={3} {...attributes} {...listeners} cursor="grab">
        <Text fontWeight="bold" fontSize="sm">
          {list.name}
        </Text>
        <IconButton aria-label="List options" size="xs" variant="ghost">
          <FiMoreHorizontal />
        </IconButton>
      </HStack>

      <VStack
        align="stretch"
        gap={2}
        flex={1}
        overflowY="auto"
        minH="50px"
        css={{
          "&::-webkit-scrollbar": { width: "6px" },
          "&::-webkit-scrollbar-track": { background: "transparent" },
          "&::-webkit-scrollbar-thumb": { background: "gray.400", borderRadius: "3px" },
        }}
      >
        <SortableContext items={listCards.map((c) => c.id)} strategy={verticalListSortingStrategy}>
          {listCards.map((card) => (
            <SortableCard key={card.id} card={card} onClick={() => onCardClick(card)} />
          ))}
        </SortableContext>
      </VStack>

      {showAddCard ? (
        <AddCardForm listId={list.id} onClose={() => setShowAddCard(false)} />
      ) : (
        <Button
          variant="ghost"
          size="sm"
          mt={2}
          justifyContent="flex-start"
          onClick={() => setShowAddCard(true)}
        >
          <FiPlus />
          <Text ml={2}>Add a card</Text>
        </Button>
      )}
    </Box>
  )
}

const AddListForm = ({ boardId, onClose }: { boardId: string; onClose: () => void }) => {
  const [name, setName] = useState("")
  const queryClient = useQueryClient()
  const { showSuccessToast, showErrorToast } = useCustomToast()

  const mutation = useMutation({
    mutationFn: () =>
      ListsService.createBoardList({
        requestBody: {
          name,
          board_id: boardId,
        },
      }),
    onSuccess: () => {
      showSuccessToast("List created successfully.")
      setName("")
      onClose()
    },
    onError: (err: ApiError) => {
      showErrorToast(err.message || "Failed to create list")
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ["lists"] })
    },
  })

  return (
    <Box bg="bg.subtle" p={3} borderRadius="lg" minW="280px">
      <Input
        placeholder="Enter list name..."
        size="sm"
        value={name}
        onChange={(e) => setName(e.target.value)}
        autoFocus
        onKeyDown={(e) => {
          if (e.key === "Enter" && name.trim()) {
            mutation.mutate()
          }
        }}
      />
      <HStack mt={2}>
        <Button
          size="sm"
          colorPalette="blue"
          onClick={() => mutation.mutate()}
          loading={mutation.isPending}
          disabled={!name.trim()}
        >
          Add List
        </Button>
        <IconButton aria-label="Cancel" size="sm" variant="ghost" onClick={onClose}>
          <FiX />
        </IconButton>
      </HStack>
    </Box>
  )
}

const bgColors: Record<string, { gradient: string; preview: string }> = {
  purple: {
    gradient: "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
    preview: "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
  },
  blue: {
    gradient: "linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)",
    preview: "linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)",
  },
  green: {
    gradient: "linear-gradient(135deg, #43e97b 0%, #38f9d7 100%)",
    preview: "linear-gradient(135deg, #43e97b 0%, #38f9d7 100%)",
  },
  orange: {
    gradient: "linear-gradient(135deg, #fa709a 0%, #fee140 100%)",
    preview: "linear-gradient(135deg, #fa709a 0%, #fee140 100%)",
  },
  pink: {
    gradient: "linear-gradient(135deg, #a8edea 0%, #fed6e3 100%)",
    preview: "linear-gradient(135deg, #a8edea 0%, #fed6e3 100%)",
  },
  ocean: {
    gradient: "linear-gradient(135deg, #2E3192 0%, #1BFFFF 100%)",
    preview: "linear-gradient(135deg, #2E3192 0%, #1BFFFF 100%)",
  },
  sunset: {
    gradient: "linear-gradient(135deg, #ee9ca7 0%, #ffdde1 100%)",
    preview: "linear-gradient(135deg, #ee9ca7 0%, #ffdde1 100%)",
  },
  forest: {
    gradient: "linear-gradient(135deg, #134E5E 0%, #71B280 100%)",
    preview: "linear-gradient(135deg, #134E5E 0%, #71B280 100%)",
  },
  mountain: {
    gradient: "url('https://images.unsplash.com/photo-1506905925346-21bda4d32df4?w=1920&q=80') center/cover",
    preview: "url('https://images.unsplash.com/photo-1506905925346-21bda4d32df4?w=400&q=60') center/cover",
  },
  beach: {
    gradient: "url('https://images.unsplash.com/photo-1507525428034-b723cf961d3e?w=1920&q=80') center/cover",
    preview: "url('https://images.unsplash.com/photo-1507525428034-b723cf961d3e?w=400&q=60') center/cover",
  },
  city: {
    gradient: "url('https://images.unsplash.com/photo-1477959858617-67f85cf4f1df?w=1920&q=80') center/cover",
    preview: "url('https://images.unsplash.com/photo-1477959858617-67f85cf4f1df?w=400&q=60') center/cover",
  },
  space: {
    gradient: "url('https://images.unsplash.com/photo-1462332420958-a05d1e002413?w=1920&q=80') center/cover",
    preview: "url('https://images.unsplash.com/photo-1462332420958-a05d1e002413?w=400&q=60') center/cover",
  },
}

function BoardDetail() {
  const { boardId } = Route.useParams()
  const [showAddList, setShowAddList] = useState(false)
  const [activeCard, setActiveCard] = useState<CardPublic | null>(null)
  const [selectedCard, setSelectedCard] = useState<CardPublic | null>(null)
  const queryClient = useQueryClient()
  const { showSuccessToast, showErrorToast } = useCustomToast()

  const sensors = useSensors(
    useSensor(PointerSensor, {
      activationConstraint: {
        distance: 5,
      },
    }),
    useSensor(KeyboardSensor, {
      coordinateGetter: sortableKeyboardCoordinates,
    })
  )

  const { data: board, isLoading: boardLoading } = useQuery({
    queryKey: ["board", boardId],
    queryFn: () => BoardsService.readBoard({ id: boardId }),
  })

  const { data: listsData, isLoading: listsLoading } = useQuery({
    queryKey: ["lists", "board", boardId],
    queryFn: () => ListsService.readBoardLists({ limit: 100 }),
  })

  const { data: cardsData, isLoading: cardsLoading } = useQuery({
    queryKey: ["cards", "board", boardId],
    queryFn: () => CardsService.readCards({ limit: 500 }),
  })

  const updateCardMutation = useMutation({
    mutationFn: ({ cardId, listId, position }: { cardId: string; listId: string; position: number }) =>
      CardsService.updateCard({
        id: cardId,
        requestBody: { list_id: listId, position },
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["cards"] })
    },
    onError: (err: ApiError) => {
      showErrorToast(err.message || "Failed to move card")
      queryClient.invalidateQueries({ queryKey: ["cards"] })
    },
  })

  const updateBoardBg = useMutation({
    mutationFn: (background: string) =>
      BoardsService.updateBoard({
        id: boardId,
        requestBody: { background_image: background },
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["board", boardId] })
      showSuccessToast("Background updated")
    },
    onError: (err: ApiError) => {
      showErrorToast(err.message || "Failed to update background")
    },
  })

  const lists = useMemo(() => {
    return (listsData?.data ?? [])
      .filter((list) => list.board_id === boardId)
      .sort((a, b) => (a.position ?? 0) - (b.position ?? 0))
  }, [listsData, boardId])

  const cards = useMemo(() => {
    return cardsData?.data ?? []
  }, [cardsData])

  const handleDragStart = (event: DragStartEvent) => {
    const { active } = event
    const cardId = active.id as string

    if (!cardId.startsWith("list-")) {
      const card = cards.find((c) => c.id === cardId)
      if (card) {
        setActiveCard(card)
      }
    }
  }

  const handleDragOver = (_event: DragOverEvent) => {
  }

  const handleDragEnd = (event: DragEndEvent) => {
    const { active, over } = event
    setActiveCard(null)

    if (!over) return

    const activeId = active.id as string
    const overId = over.id as string

    if (activeId === overId) return

    if (!activeId.startsWith("list-")) {
      const activeCard = cards.find((c) => c.id === activeId)
      if (!activeCard) return

      let targetListId = activeCard.list_id
      let newPosition = activeCard.position ?? 65535

      if (overId.startsWith("list-")) {
        targetListId = overId.replace("list-", "")
        const listCards = cards.filter((c) => c.list_id === targetListId)
        newPosition = listCards.length > 0
          ? Math.max(...listCards.map((c) => c.position ?? 0)) + 65535
          : 65535
      } else {
        const overCard = cards.find((c) => c.id === overId)
        if (overCard) {
          targetListId = overCard.list_id

          const listCards = cards
            .filter((c) => c.list_id === targetListId)
            .sort((a, b) => (a.position ?? 0) - (b.position ?? 0))

          const overIndex = listCards.findIndex((c) => c.id === overId)
          const activeIndex = listCards.findIndex((c) => c.id === activeId)

          if (overIndex !== -1) {
            if (activeIndex === -1 || activeIndex > overIndex) {
              const prevPosition = overIndex > 0 ? (listCards[overIndex - 1].position ?? 0) : 0
              const overPosition = overCard.position ?? 65535
              newPosition = (prevPosition + overPosition) / 2
            } else {
              const overPosition = overCard.position ?? 65535
              const nextPosition = overIndex < listCards.length - 1
                ? (listCards[overIndex + 1].position ?? overPosition + 65535)
                : overPosition + 65535
              newPosition = (overPosition + nextPosition) / 2
            }
          }
        }
      }

      updateCardMutation.mutate({
        cardId: activeCard.id,
        listId: targetListId,
        position: newPosition,
      })
    }
  }

  if (boardLoading || listsLoading || cardsLoading) {
    return (
      <Flex justify="center" align="center" h="100vh">
        <Spinner size="xl" />
      </Flex>
    )
  }

  if (!board) {
    return (
      <Container maxW="full" py={8}>
        <Text>Board not found</Text>
      </Container>
    )
  }

  const boardBgConfig = bgColors[board.background_image || "purple"] || bgColors.purple
  const boardBg = boardBgConfig.gradient
  const isImageBg = boardBg.startsWith("url(")

  return (
    <Box
      minH="100vh"
      bgGradient={isImageBg ? undefined : boardBg}
      background={isImageBg ? boardBg : undefined}
      ml={{ base: 0, md: "-8" }}
      mr={{ base: 0, md: "-8" }}
      mt={{ base: 0, md: "-6" }}
      pt={4}
      px={4}
    >
      {/* Header */}
      <HStack mb={4} justify="space-between">
        <HStack>
          <RouterLink to="/boards" search={{ page: 1 }}>
            <IconButton aria-label="Back to boards" variant="ghost" colorPalette="whiteAlpha">
              <FiArrowLeft />
            </IconButton>
          </RouterLink>
          <Heading size="lg" color="white" textShadow={isImageBg ? "0 1px 3px rgba(0,0,0,0.5)" : undefined}>
            {board.name}
          </Heading>
        </HStack>
        <HStack>
          <DialogRoot size="sm">
            <DialogTrigger asChild>
              <Button
                variant="ghost"
                size="sm"
                bg="whiteAlpha.300"
                color="white"
                _hover={{ bg: "whiteAlpha.400" }}
              >
                <FiImage />
                <Text ml={2}>Background</Text>
              </Button>
            </DialogTrigger>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>Change Background</DialogTitle>
                <DialogCloseTrigger />
              </DialogHeader>
              <DialogBody pb={6}>
                <Text fontWeight="bold" mb={3}>Colors</Text>
                <SimpleGrid columns={4} gap={2} mb={4}>
                  {["purple", "blue", "green", "orange", "pink", "ocean", "sunset", "forest"].map((colorKey) => (
                    <Box
                      key={colorKey}
                      w="60px"
                      h="40px"
                      borderRadius="md"
                      background={bgColors[colorKey].preview}
                      cursor="pointer"
                      onClick={() => updateBoardBg.mutate(colorKey)}
                      border={board.background_image === colorKey ? "3px solid" : "none"}
                      borderColor="blue.500"
                      _hover={{ transform: "scale(1.05)", transition: "transform 0.2s" }}
                    />
                  ))}
                </SimpleGrid>
                <Text fontWeight="bold" mb={3}>Photos</Text>
                <SimpleGrid columns={2} gap={2}>
                  {["mountain", "beach", "city", "space"].map((imgKey) => (
                    <Box
                      key={imgKey}
                      w="100%"
                      h="60px"
                      borderRadius="md"
                      background={bgColors[imgKey].preview}
                      cursor="pointer"
                      onClick={() => updateBoardBg.mutate(imgKey)}
                      border={board.background_image === imgKey ? "3px solid" : "none"}
                      borderColor="blue.500"
                      _hover={{ transform: "scale(1.02)", transition: "transform 0.2s" }}
                    />
                  ))}
                </SimpleGrid>
              </DialogBody>
            </DialogContent>
          </DialogRoot>
          <Text fontSize="sm" color="whiteAlpha.800">
            {board.visibility}
          </Text>
        </HStack>
      </HStack>

      {/* Board with DnD */}
      <DndContext
        sensors={sensors}
        collisionDetection={closestCorners}
        onDragStart={handleDragStart}
        onDragOver={handleDragOver}
        onDragEnd={handleDragEnd}
      >
        <Flex gap={4} overflowX="auto" pb={4} align="flex-start">
          <SortableContext items={lists.map((l) => `list-${l.id}`)} strategy={horizontalListSortingStrategy}>
            {lists.map((list) => (
              <SortableListColumn
                key={list.id}
                list={list}
                cards={cards}
                onCardClick={setSelectedCard}
              />
            ))}
          </SortableContext>

          {showAddList ? (
            <AddListForm boardId={boardId} onClose={() => setShowAddList(false)} />
          ) : (
            <Button
              variant="ghost"
              bg="whiteAlpha.300"
              color="white"
              _hover={{ bg: "whiteAlpha.400" }}
              minW="280px"
              justifyContent="flex-start"
              onClick={() => setShowAddList(true)}
            >
              <FiPlus />
              <Text ml={2}>Add another list</Text>
            </Button>
          )}
        </Flex>

        <DragOverlay>
          {activeCard ? <CardDragOverlay card={activeCard} /> : null}
        </DragOverlay>
      </DndContext>

      {selectedCard && (
        <CardDetailModal
          card={selectedCard}
          isOpen={!!selectedCard}
          onClose={() => setSelectedCard(null)}
          workspaceId={board.workspace_id}
        />
      )}
    </Box>
  )
}

export default BoardDetail
