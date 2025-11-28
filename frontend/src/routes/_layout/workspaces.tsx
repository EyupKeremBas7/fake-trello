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

import { BoardsService, type WorkspacePublic, WorkspacesService } from "@/client"
import { WorkspaceActionsMenu } from "@/components/Common/WorkspaceActionsMenu"
import PendingWorkspaces from "@/components/Pending/PendingWorkspaces"
import AddWorkspace from "@/components/Workspaces/AddWorkspace"
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

// --- Alt Bileşen: Workspace'e ait Boardları Listeler ---
const WorkspaceBoardsList = ({ workspaceId }: { workspaceId: string }) => {
  // Not: Gerçek uygulamada backend'de "readBoards({ workspace_id: ... })" gibi bir filtre olmalı.
  // Şimdilik tüm boardları çekip burada filtreliyoruz.
  const { data, isLoading } = useQuery({
    queryKey: ["boards", "all"], 
    queryFn: () => BoardsService.readBoards({ limit: 100 }), // Limit artırıldı
  })

  if (isLoading) return <Spinner size="sm" />

  // Client-side filtering
  const workspaceBoards = data?.data.filter(b => b.workspace_id === workspaceId) || []

  if (workspaceBoards.length === 0) {
    return <Text fontSize="sm" color="gray.500" py={2}>No boards found in this workspace.</Text>
  }

  return (
    <Box py={2} px={4} bg="gray.50" borderRadius="md">
      <Text fontWeight="bold" fontSize="sm" mb={2}>Boards in this Workspace:</Text>
      <Table.Root size="sm" variant="outline" bg="white">
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
              <Table.Cell>{board.visibility}</Table.Cell>
            </Table.Row>
          ))}
        </Table.Body>
      </Table.Root>
    </Box>
  )
}

// --- Alt Bileşen: Tekil Workspace Satırı (Genişletme Mantığı Burada) ---
const WorkspaceRow = ({ workspace }: { workspace: WorkspacePublic }) => {
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
        <Table.Cell truncate maxW="sm">{workspace.id}</Table.Cell>
        <Table.Cell truncate maxW="sm" fontWeight="medium">{workspace.name}</Table.Cell>
        <Table.Cell>{workspace.visibility || "private"}</Table.Cell>
        <Table.Cell>{workspace.owner_id}</Table.Cell>
        <Table.Cell>
          <WorkspaceActionsMenu Workspace={workspace} />
        </Table.Cell>
      </Table.Row>
      
      {/* Genişletilmiş İçerik */}
      {isExpanded && (
        <Table.Row>
          <Table.Cell colSpan={6} p={0}>
            <Box p={4} bg="gray.50" borderBottomWidth="1px">
               <WorkspaceBoardsList workspaceId={workspace.id} />
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

  const Workspaces = data?.data.slice(0, PER_PAGE) ?? []
  const count = data?.count ?? 0

  if (isLoading) {
    return <PendingWorkspaces />
  }

  if (Workspaces.length === 0) {
    return (
      <EmptyState.Root>
        <EmptyState.Content>
          <EmptyState.Indicator>
            <FiSearch />
          </EmptyState.Indicator>
          <VStack textAlign="center">
            <EmptyState.Title>You don't have any Workspaces yet</EmptyState.Title>
            <EmptyState.Description>
              Add a new Workspace to get started
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
            <Table.ColumnHeader w="10"></Table.ColumnHeader> {/* Ok işareti için boş sütun */}
            <Table.ColumnHeader w="sm">ID</Table.ColumnHeader>
            <Table.ColumnHeader w="sm">Name</Table.ColumnHeader>
            <Table.ColumnHeader w="sm">Visibility</Table.ColumnHeader>
            <Table.ColumnHeader w="sm">Owner ID</Table.ColumnHeader>
            <Table.ColumnHeader w="sm">Actions</Table.ColumnHeader>
          </Table.Row>
        </Table.Header>
        <Table.Body>
          {Workspaces.map((workspace) => (
            <WorkspaceRow key={workspace.id} workspace={workspace} />
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