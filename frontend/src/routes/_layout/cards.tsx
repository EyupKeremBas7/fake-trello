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

import { CardsService, ListsService, type CardPublic } from "@/client"
import AddCard from "@/components/Cards/AddCard"
import CardOwnerInfo from "@/components/Cards/CardOwnerInfo"
import CardActionsMenu from "@/components/Common/CardActionsMenu"
import PendingCards from "@/components/Pending/PendingCards"
import {
  PaginationItems,
  PaginationNextTrigger,
  PaginationPrevTrigger,
  PaginationRoot,
} from "@/components/ui/pagination.tsx"

const CardsSearchSchema = z.object({
  page: z.number().catch(1),
})

const PER_PAGE = 10

function getCardsQueryOptions({ page }: { page: number }) {
  return {
    queryFn: () =>
      CardsService.readCards({ skip: (page - 1) * PER_PAGE, limit: PER_PAGE }),
    queryKey: ["Cards", { page }],
  }
}

export const Route = createFileRoute("/_layout/cards")({
  component: Cards,
  validateSearch: (search) => CardsSearchSchema.parse(search),
})

const CardListInfo = ({ listId }: { listId: string }) => {
  const { data, isLoading } = useQuery({
    queryKey: ["boardList", listId],
    queryFn: () => ListsService.readBoardList({ id: listId }),
  })

  if (isLoading) return <Spinner size="xs" />

  return <Text fontSize="sm">{data?.name ?? "Unknown List"}</Text>
}

const CardRow = ({ card }: { card: CardPublic }) => {
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
          {card.id}
        </Table.Cell>
        <Table.Cell truncate maxW="sm" fontWeight="medium">
          {card.title}
        </Table.Cell>
        <Table.Cell>
          <CardListInfo listId={card.list_id} />
        </Table.Cell>
        <Table.Cell>
          <CardOwnerInfo createdBy={card.created_by} showAvatar={false} />
        </Table.Cell>
        <Table.Cell>{card.is_archived ? "Yes" : "No"}</Table.Cell>
        <Table.Cell>
          <CardActionsMenu card={card} />
        </Table.Cell>
      </Table.Row>

      {isExpanded && (
        <Table.Row>
          <Table.Cell colSpan={7} p={0}>
            <Box p={4} bg="bg.subtle" borderBottomWidth="1px" borderColor="border.subtle">
              <VStack align="start" gap={2}>
                <Text fontSize="sm">
                  <strong>Description:</strong> {card.description ?? "No description"}
                </Text>
                <Text fontSize="sm">
                  <strong>Due Date:</strong> {card.due_date ?? "Not set"}
                </Text>
                <Text fontSize="sm">
                  <strong>Position:</strong> {card.position}
                </Text>
                <Text fontSize="sm">
                  <strong>Created:</strong> {card.created_at}
                </Text>
                <Text fontSize="sm">
                  <strong>Updated:</strong> {card.updated_at}
                </Text>
              </VStack>
            </Box>
          </Table.Cell>
        </Table.Row>
      )}
    </>
  )
}

function CardsTable() {
  const navigate = useNavigate({ from: Route.fullPath })
  const { page } = Route.useSearch()

  const { data, isLoading } = useQuery({
    ...getCardsQueryOptions({ page }),
    placeholderData: (prevData) => prevData,
  })

  const setPage = (page: number) => {
    navigate({
      to: "/cards",
      search: (prev) => ({ ...prev, page }),
    })
  }

  const cards = data?.data ?? []
  const count = data?.count ?? 0

  if (isLoading) {
    return <PendingCards />
  }

  if (cards.length === 0) {
    return (
      <EmptyState.Root>
        <EmptyState.Content>
          <EmptyState.Indicator>
            <FiSearch />
          </EmptyState.Indicator>
          <VStack textAlign="center">
            <EmptyState.Title>You don't have any Cards yet</EmptyState.Title>
            <EmptyState.Description>Add a new Card to get started</EmptyState.Description>
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
            <Table.ColumnHeader w="sm">Title</Table.ColumnHeader>
            <Table.ColumnHeader w="sm">List</Table.ColumnHeader>
            <Table.ColumnHeader w="sm">Owner</Table.ColumnHeader>
            <Table.ColumnHeader w="sm">Archived</Table.ColumnHeader>
            <Table.ColumnHeader w="sm">Actions</Table.ColumnHeader>
          </Table.Row>
        </Table.Header>
        <Table.Body>
          {cards.slice(0, PER_PAGE).map((card) => (
            <CardRow key={card.id} card={card} />
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

function Cards() {
  return (
    <Container maxW="full">
      <Heading size="lg" pt={12}>
        Cards Management
      </Heading>
      <AddCard />
      <CardsTable />
    </Container>
  )
}

export default Cards