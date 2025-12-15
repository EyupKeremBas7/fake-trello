import {
  Container,
  EmptyState,
  Flex,
  Heading,
  Table,
  VStack,
  Box,
  Text,
  Spinner,
  HStack,
  Badge,
  IconButton,
} from "@chakra-ui/react"
import { useQuery } from "@tanstack/react-query"
import { createFileRoute, useNavigate, Link as RouterLink } from "@tanstack/react-router"
import { useState } from "react"
import { FiChevronDown, FiChevronRight, FiSearch, FiExternalLink } from "react-icons/fi"
import { z } from "zod"

import { BoardsService, ListsService, WorkspacesService, UsersService, type BoardPublic } from "@/client"
import { BoardActionsMenu } from "@/components/Common/BoardActionsMenu"
import AddBoard from "@/components/Boards/AddBoard"
import PendingBoards from "@/components/Pending/PendingBoards"
import {
  PaginationItems,
  PaginationNextTrigger,
  PaginationPrevTrigger,
  PaginationRoot,
} from "@/components/ui/pagination.tsx"

const BoardsSearchSchema = z.object({
  page: z.number().catch(1),
})

const PER_PAGE = 5

function getBoardsQueryOptions({ page }: { page: number }) {
  return {
    queryFn: () =>
      BoardsService.readBoards({ skip: (page - 1) * PER_PAGE, limit: PER_PAGE }),
    queryKey: ["boards", { page }],
  }
}

const ListLists = ({ boardId }: { boardId: string }) => {
  const { data, isLoading } = useQuery({
    queryKey: ["lists", "all"],
    queryFn: () => ListsService.readBoardLists({ limit: 100 }),
  })

  if (isLoading) return <Spinner size="sm" />

  const lists = (data?.data ?? []).filter((list) => list.board_id === boardId)

  if (lists.length === 0) {
    return <Text fontSize="sm" color="fg.muted">No lists in this board</Text>
  }

  return (
    <VStack align="stretch" gap={2}>
      <Text fontSize="sm" fontWeight="bold" mb={2}>
        Lists ({lists.length})
      </Text>
      {lists.map((list) => (
        <Box
          key={list.id}
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
                {list.name}
              </Text>
              <Text fontSize="xs" color="fg.muted">
                Position: {list.position}
              </Text>
            </VStack>
            <Badge colorPalette="blue" size="sm">
              {list.position}
            </Badge>
          </HStack>
        </Box>
      ))}
    </VStack>
  )
}

const WorkspaceInfo = ({ workspaceId }: { workspaceId: string | null | undefined }) => {
  const { data, isLoading } = useQuery({
    queryKey: ["workspace", workspaceId],
    queryFn: () => WorkspacesService.readWorkspace({ id: workspaceId as string }),
    enabled: !!workspaceId,
  })

  if (!workspaceId) return <Text fontSize="sm">N/A</Text>
  if (isLoading) return <Spinner size="xs" />

  return <Text fontSize="sm">{data?.name ?? "Unknown Workspace"}</Text>
}

const OwnerInfo = ({ ownerId }: { ownerId: string }) => {
  const { data, isLoading } = useQuery({
    queryKey: ["user", ownerId],
    queryFn: () => UsersService.readUserById({ userId: ownerId }),
    enabled: !!ownerId,
  })

  if (isLoading) return <Spinner size="xs" />

  return <Text fontSize="sm">{data?.full_name || data?.email || "Unknown User"}</Text>
}

const BoardRow = ({ board }: { board: BoardPublic }) => {
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
          {board.id}
        </Table.Cell>
        <Table.Cell truncate maxW="sm" fontWeight="medium">
          <HStack>
            <RouterLink to="/board/$boardId" params={{ boardId: board.id }} search={{ page: 1 }}>
              <Text
                color="blue.500"
                _hover={{ textDecoration: "underline" }}
                cursor="pointer"
              >
                {board.name}
              </Text>
            </RouterLink>
            <RouterLink to="/board/$boardId" params={{ boardId: board.id }} search={{ page: 1 }}>
              <FiExternalLink size={12} />
            </RouterLink>
          </HStack>
        </Table.Cell>
        <Table.Cell>
          {board.visibility || "N/A"}
        </Table.Cell>
        <Table.Cell truncate maxW="sm">
          <WorkspaceInfo workspaceId={board.workspace_id} />
        </Table.Cell>
        <Table.Cell truncate maxW="sm">
          <OwnerInfo ownerId={board.owner_id} />
        </Table.Cell>
        <Table.Cell>
          <BoardActionsMenu Board={board} />
        </Table.Cell>
      </Table.Row>

      {isExpanded && (
        <Table.Row>
          <Table.Cell colSpan={7} p={0}>
            <Box p={4} bg="bg.subtle" borderBottomWidth="1px" borderColor="border.subtle">
              <ListLists boardId={board.id} />
            </Box>
          </Table.Cell>
        </Table.Row>
      )}
    </>
  )
}

export const Route = createFileRoute("/_layout/boards")({
  component: Boards,
  validateSearch: (search) => BoardsSearchSchema.parse(search),
})

function BoardsTable() {
  const navigate = useNavigate({ from: Route.fullPath })
  const { page } = Route.useSearch()

  const { data, isLoading } = useQuery({
    ...getBoardsQueryOptions({ page }),
    placeholderData: (prevData) => prevData,
  })

  const setPage = (page: number) => {
    navigate({
      to: "/boards",
      search: (prev) => ({ ...prev, page }),
    })
  }

  const boards = data?.data.slice(0, PER_PAGE) ?? []
  const count = data?.count ?? 0

  if (isLoading) {
    return <PendingBoards />
  }

  if (boards.length === 0) {
    return (
      <EmptyState.Root>
        <EmptyState.Content>
          <EmptyState.Indicator>
            <FiSearch />
          </EmptyState.Indicator>
          <VStack textAlign="center">
            <EmptyState.Title>You don't have any Boards yet</EmptyState.Title>
            <EmptyState.Description>
              Add a new Board to get started
            </EmptyState.Description>
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
            <Table.ColumnHeader w="sm">Visibility</Table.ColumnHeader>
            <Table.ColumnHeader w="sm">Workspace</Table.ColumnHeader>
            <Table.ColumnHeader w="sm">Owner</Table.ColumnHeader>
            <Table.ColumnHeader w="sm">Actions</Table.ColumnHeader>
          </Table.Row>
        </Table.Header>
        <Table.Body>
          {boards.map((board) => (
            <BoardRow key={board.id} board={board} />
          ))}
        </Table.Body>
      </Table.Root>
      <Flex justifyContent="flex-end" mt={4}>
        <PaginationRoot
          count={count}
          pageSize={PER_PAGE}
          onPageChange={({ page }) => setPage(page)}
        >
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

function Boards() {
  return (
    <Container maxW="full">
      <Heading size="lg" pt={12}>
        Boards Management
      </Heading>
      <AddBoard />
      <BoardsTable />
    </Container>
  )
}