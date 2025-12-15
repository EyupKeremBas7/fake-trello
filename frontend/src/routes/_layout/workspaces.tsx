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
} from "@chakra-ui/react"
import { useQuery } from "@tanstack/react-query"
import { createFileRoute, useNavigate } from "@tanstack/react-router"
import { useState } from "react"
import { FiChevronDown, FiChevronRight, FiSearch } from "react-icons/fi"
import { z } from "zod"

import { BoardsService, WorkspacesService, UsersService } from "@/client"
import WorkspaceActionsMenu from "@/components/Common/WorkspaceActionsMenu"
import PendingWorkspaces from "@/components/Pending/PendingWorkspaces"
import AddWorkspace from "@/components/Workspaces/AddWorkspace"
import WorkspaceMembers from "@/components/Workspaces/WorkspaceMembers"
import type { WorkspacePublicWithMeta } from "@/components/Workspaces/WorkspacePublicWithMeta"
import {
  PaginationItems,
  PaginationNextTrigger,
  PaginationPrevTrigger,
  PaginationRoot,
} from "@/components/ui/pagination.tsx"

const WorkspacesSearchSchema = z.object({
  page: z.number().catch(1),
})

const PER_PAGE = 5

function getWorkspacesQueryOptions({ page }: { page: number }) {
  return {
    queryFn: () =>
      WorkspacesService.readWorkspaces({ skip: (page - 1) * PER_PAGE, limit: PER_PAGE }),
    queryKey: ["Workspaces", { page }],
  }
}

export const Route = createFileRoute("/_layout/workspaces")({
  component: Workspaces,
  validateSearch: (search) => WorkspacesSearchSchema.parse(search),
})

const WorkspaceBoardsList = ({ workspaceId }: { workspaceId: string }) => {
  const { data, isLoading } = useQuery({
    queryKey: ["boards", "all"],
    queryFn: () => BoardsService.readBoards({ limit: 100 }),
  })

  if (isLoading) return <Spinner size="sm" />

  const workspaceBoards = (data?.data ?? []).filter((b) => b.workspace_id === workspaceId)

  if (workspaceBoards.length === 0) {
    return (
      <Text fontSize="sm" color="fg.muted" py={2}>
        No boards found in this workspace.
      </Text>
    )
  }

  return (
    <Box>
      <Text fontWeight="bold" fontSize="sm" mb={2}>
        Boards ({workspaceBoards.length})
      </Text>
      <Table.Root size="sm" variant="outline">
        <Table.Header>
          <Table.Row>
            <Table.ColumnHeader>Name</Table.ColumnHeader>
            <Table.ColumnHeader>Visibility</Table.ColumnHeader>
          </Table.Row>
        </Table.Header>
        <Table.Body>
          {workspaceBoards.map((board) => (
            <Table.Row key={board.id}>
              <Table.Cell>{board.name}</Table.Cell>
              <Table.Cell>{board.visibility ?? "private"}</Table.Cell>
            </Table.Row>
          ))}
        </Table.Body>
      </Table.Root>
    </Box>
  )
}

const WorkspaceOwnerInfo = ({ ownerId }: { ownerId: string }) => {
  const { data, isLoading } = useQuery({
    queryKey: ["user", ownerId],
    queryFn: () => UsersService.readUserById({ userId: ownerId }),
    enabled: !!ownerId,
  })

  if (isLoading) return <Spinner size="xs" />

  return <Text fontSize="sm">{data?.full_name || data?.email || "Unknown User"}</Text>
}

const WorkspaceRow = ({ workspace }: { workspace: WorkspacePublicWithMeta }) => {
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
          {workspace.id}
        </Table.Cell>
        <Table.Cell truncate maxW="sm" fontWeight="medium">
          {workspace.name}
        </Table.Cell>
        <Table.Cell>{workspace.visibility ?? "private"}</Table.Cell>
        <Table.Cell><WorkspaceOwnerInfo ownerId={workspace.owner_id} /></Table.Cell>
        <Table.Cell>
          <WorkspaceActionsMenu workspace={workspace} />
        </Table.Cell>
      </Table.Row>

      {isExpanded && (
        <Table.Row>
          <Table.Cell colSpan={6} p={0}>
            <Box p={4} bg="bg.subtle" borderBottomWidth="1px" borderColor="border.subtle">
              <VStack align="stretch" gap={6}>
                <WorkspaceBoardsList workspaceId={workspace.id} />
                <WorkspaceMembers workspaceId={workspace.id} ownerId={workspace.owner_id} />
              </VStack>
            </Box>
          </Table.Cell>
        </Table.Row>
      )}
    </>
  )
}

function WorkspacesTable() {
  const navigate = useNavigate({ from: Route.fullPath })
  const { page } = Route.useSearch()

  const { data, isLoading } = useQuery({
    ...getWorkspacesQueryOptions({ page }),
    placeholderData: (prevData) => prevData,
  })

  const setPage = (page: number) => {
    navigate({
      to: "/workspaces",
      search: (prev) => ({ ...prev, page }),
    })
  }

  const workspaces = (data?.data ?? []) as WorkspacePublicWithMeta[]
  const count = data?.count ?? 0

  if (isLoading) {
    return <PendingWorkspaces />
  }

  if (workspaces.length === 0) {
    return (
      <EmptyState.Root>
        <EmptyState.Content>
          <EmptyState.Indicator>
            <FiSearch />
          </EmptyState.Indicator>
          <VStack textAlign="center">
            <EmptyState.Title>You don't have any Workspaces yet</EmptyState.Title>
            <EmptyState.Description>Add a new Workspace to get started</EmptyState.Description>
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
            <Table.ColumnHeader w="sm">Owner</Table.ColumnHeader>
            <Table.ColumnHeader w="sm">Actions</Table.ColumnHeader>
          </Table.Row>
        </Table.Header>
        <Table.Body>
          {workspaces.slice(0, PER_PAGE).map((workspace) => (
            <WorkspaceRow key={workspace.id} workspace={workspace} />
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

function Workspaces() {
  return (
    <Container maxW="full">
      <Heading size="lg" pt={12}>
        Workspaces Management
      </Heading>
      <AddWorkspace />
      <WorkspacesTable />
    </Container>
  )
}

export default Workspaces