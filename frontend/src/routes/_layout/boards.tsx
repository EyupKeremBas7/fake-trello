import {
  Container,
  EmptyState,
  Flex,
  Heading,
  Table,
  VStack,
} from "@chakra-ui/react"
import { useQuery } from "@tanstack/react-query"
import { createFileRoute, useNavigate } from "@tanstack/react-router"
import { FiSearch } from "react-icons/fi"
import { z } from "zod"

import { BoardsService } from "@/client"
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

export const Route = createFileRoute("/_layout/boards")({
  component: Boards,
  validateSearch: (search) => BoardsSearchSchema.parse(search),
})

function BoardsTable() {
  const navigate = useNavigate({ from: Route.fullPath })
  const { page } = Route.useSearch()

  const { data, isLoading, isPlaceholderData } = useQuery({
    ...getBoardsQueryOptions({ page }),
    placeholderData: (prevData) => prevData,
  })

  const setPage = (page: number) => {
    navigate({
      to: "/boards",
      search: (prev) => ({ ...prev, page }),
    })
  }

  const Boards = data?.data.slice(0, PER_PAGE) ?? []
  const count = data?.count ?? 0

  if (isLoading) {
    return <PendingBoards />
  }

  if (Boards.length === 0) {
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
            <Table.ColumnHeader w="sm">ID</Table.ColumnHeader>
            <Table.ColumnHeader w="sm">Name</Table.ColumnHeader>
            <Table.ColumnHeader w="sm">Visibility</Table.ColumnHeader>
            <Table.ColumnHeader w="sm">Workspace ID</Table.ColumnHeader>
            <Table.ColumnHeader w="sm">Owner ID</Table.ColumnHeader>
            <Table.ColumnHeader w="sm">Actions</Table.ColumnHeader>
          </Table.Row>
        </Table.Header>
        <Table.Body>
          {Boards?.map((Board) => (
            <Table.Row key={Board.id} opacity={isPlaceholderData ? 0.5 : 1}>

              <Table.Cell truncate maxW="sm">
                {Board.id}
              </Table.Cell>

              <Table.Cell truncate maxW="sm">
                {Board.name}
              </Table.Cell>

              <Table.Cell>
                {Board.visibility || "N/A"}
              </Table.Cell>

              <Table.Cell>
                {Board.workspace_id || "N/A"}
              </Table.Cell>

              <Table.Cell>
                {Board.owner_id}
              </Table.Cell>

              <Table.Cell>
                <BoardActionsMenu Board={Board} />
              </Table.Cell>

            </Table.Row>
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