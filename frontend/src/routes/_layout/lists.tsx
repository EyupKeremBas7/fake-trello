import {
  Box,
  Container,
  EmptyState,
  Flex,
  Heading,
  IconButton,
  Spinner,
  Table,
  Text,
  VStack,
  Badge,
  HStack,
} from "@chakra-ui/react"
import { useQuery } from "@tanstack/react-query"
import { createFileRoute, useNavigate } from "@tanstack/react-router"
import { useState } from "react"
import { FiChevronDown, FiChevronRight, FiSearch } from "react-icons/fi"
import { z } from "zod"

import { ListsService, BoardsService, CardsService, type ListPublic } from "@/client"
import AddList from "@/components/Lists/AddList"
import ListActionsMenu from "@/components/Common/ListActionsMenu"
import PendingLists from "@/components/Pending/PendingLists"
import {
  PaginationItems,
  PaginationNextTrigger,
  PaginationPrevTrigger,
  PaginationRoot,
} from "@/components/ui/pagination.tsx"

const ListsSearchSchema = z.object({
  page: z.number().catch(1),
})

const PER_PAGE = 10

function getListsQueryOptions({ page }: { page: number }) {
  return {
    queryFn: () =>
      ListsService.readBoardLists({ skip: (page - 1) * PER_PAGE, limit: PER_PAGE }),
    queryKey: ["Lists", { page }],
  }
}

export const Route = createFileRoute("/_layout/lists")({
  component: Lists,
  validateSearch: (search) => ListsSearchSchema.parse(search),
})

const ListBoardInfo = ({ boardId }: { boardId: string }) => {
  const { data, isLoading } = useQuery({
    queryKey: ["board", boardId],
    queryFn: () => BoardsService.readBoard({ id: boardId }),
  })

  if (isLoading) return <Spinner size="xs" />

  return <Text fontSize="sm">{data?.name ?? "Unknown Board"}</Text>
}

const ListCards = ({ listId }: { listId: string }) => {
  const { data, isLoading } = useQuery({
    queryKey: ["cards", "byList", listId],
    queryFn: () => CardsService.readCards({ limit: 100 }),
  })

  if (isLoading) return <Spinner size="sm" />

  const listCards = (data?.data ?? []).filter((card) => card.list_id === listId)

  if (listCards.length === 0) {
    return <Text fontSize="sm" color="fg.muted">No cards in this list</Text>
  }

  return (
    <VStack align="stretch" gap={2}>
      <Text fontSize="sm" fontWeight="bold" mb={2}>
        Cards ({listCards.length})
      </Text>
      {listCards.map((card) => (
        <Box
          key={card.id}
          p={3}
          bg="bg.panel"
          borderRadius="md"
          borderWidth="1px"
          borderColor="border.subtle"
          _hover={{ bg: "bg.subtle" }}
        >
          <HStack justify="space-between">
            <VStack align="start" gap={1}>
              <Text fontSize="sm" fontWeight="medium">
                {card.title}
              </Text>
              {card.description && (
                <Text fontSize="xs" color="fg.muted" lineClamp={1}>
                  {card.description}
                </Text>
              )}
            </VStack>
            <HStack gap={2}>
              {card.is_archived && (
                <Badge colorPalette="orange" size="sm">Archived</Badge>
              )}
              {card.due_date && (
                <Badge colorPalette="blue" size="sm">
                  {new Date(card.due_date).toLocaleDateString()}
                </Badge>
              )}
            </HStack>
          </HStack>
        </Box>
      ))}
    </VStack>
  )
}

const ListRow = ({ list }: { list: ListPublic }) => {
  const [isExpanded, setIsExpanded] = useState(false)

  return (
    <>
      <Table.Row>
        <Table.Cell>
          <IconButton
            aria-label="Expand row"
            variant="ghost"
            size="xs"
            onClick={() => setIsExpanded(!isExpanded)}
          >
            {isExpanded ? <FiChevronDown /> : <FiChevronRight />}
          </IconButton>
        </Table.Cell>
        <Table.Cell truncate maxW="sm">
          {list.id}
        </Table.Cell>
        <Table.Cell truncate maxW="sm" fontWeight="medium">
          {list.name}
        </Table.Cell>
        <Table.Cell>
          <ListBoardInfo boardId={list.board_id} />
        </Table.Cell>
        <Table.Cell>{list.position}</Table.Cell>
        <Table.Cell>
          <ListActionsMenu list={list} />
        </Table.Cell>
      </Table.Row>

      {isExpanded && (
        <Table.Row>
          <Table.Cell colSpan={6} p={0}>
            <Box p={4} bg="bg.subtle" borderBottomWidth="1px" borderColor="border.subtle">
              <VStack align="stretch" gap={4}>
                <HStack gap={4}>
                  <Text fontSize="sm">
                    <strong>Board ID:</strong> {list.board_id}
                  </Text>
                  <Text fontSize="sm">
                    <strong>Position:</strong> {list.position}
                  </Text>
                </HStack>
                <Box>
                  <ListCards listId={list.id} />
                </Box>
              </VStack>
            </Box>
          </Table.Cell>
        </Table.Row>
      )}
    </>
  )
}

function ListsTable() {
  const navigate = useNavigate({ from: Route.fullPath })
  const { page } = Route.useSearch()

  const { data, isLoading } = useQuery({
    ...getListsQueryOptions({ page }),
    placeholderData: (prevData) => prevData,
  })

  const setPage = (page: number) => {
    navigate({
      to: "/lists",
      search: (prev) => ({ ...prev, page }),
    })
  }

  const lists = data?.data ?? []
  const count = data?.count ?? 0

  if (isLoading) {
    return <PendingLists />
  }

  if (lists.length === 0) {
    return (
      <EmptyState.Root>
        <EmptyState.Content>
          <EmptyState.Indicator>
            <FiSearch />
          </EmptyState.Indicator>
          <VStack textAlign="center">
            <EmptyState.Title>You don't have any Lists yet</EmptyState.Title>
            <EmptyState.Description>Add a new List to get started</EmptyState.Description>
          </VStack>
        </EmptyState.Content>
      </EmptyState.Root>
    )
  }

  return (
    <>
      <Table.Root size={{ base: "sm", md: "md" }}>
        <Table.Header>
          <Table.Row>
            <Table.ColumnHeader w="10" />
            <Table.ColumnHeader w="sm">ID</Table.ColumnHeader>
            <Table.ColumnHeader w="sm">Name</Table.ColumnHeader>
            <Table.ColumnHeader w="sm">Board</Table.ColumnHeader>
            <Table.ColumnHeader w="sm">Position</Table.ColumnHeader>
            <Table.ColumnHeader w="sm">Actions</Table.ColumnHeader>
          </Table.Row>
        </Table.Header>
        <Table.Body>
          {lists.slice(0, PER_PAGE).map((list) => (
            <ListRow key={list.id} list={list} />
          ))}
        </Table.Body>
      </Table.Root>
      <Flex justifyContent="flex-end" mt={4}>
        <PaginationRoot count={count} pageSize={PER_PAGE} onPageChange={({ page }) => setPage(page)}>
          <Flex>
            <PaginationPrevTrigger />
            <PaginationItems />
            <PaginationNextTrigger />
          </Flex>
        </PaginationRoot>
      </Flex>
    </>
  )
}

function Lists() {
  return (
    <Container maxW="full">
      <Heading size="lg" pt={12}>
        Lists Management
      </Heading>
      <AddList />
      <ListsTable />
    </Container>
  )
}

export default Lists