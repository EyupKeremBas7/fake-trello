import {
  Box,
  Container,
  Flex,
  Heading,
  Text,
  VStack,
  HStack,
  Spinner,
  Button,
  SimpleGrid,
} from "@chakra-ui/react"
import { useQuery } from "@tanstack/react-query"
import { createFileRoute, Link as RouterLink } from "@tanstack/react-router"
import { FiPlus, FiClock, FiGrid } from "react-icons/fi"

import { WorkspacesService, BoardsService } from "@/client"
import AddBoard from "@/components/Boards/AddBoard"

export const Route = createFileRoute("/_layout/")({
  component: Dashboard,
})

const RecentBoards = () => {
  const { data, isLoading } = useQuery({
    queryKey: ["boards", "recent"],
    queryFn: () => BoardsService.readBoards({ limit: 5 }),
  })

  if (isLoading) return <Spinner size="sm" />

  const boards = data?.data ?? []

  if (boards.length === 0) {
    return <Text fontSize="sm" color="fg.muted">Henüz board yok</Text>
  }

  const bgColors: Record<string, string> = {
    purple: "purple.500",
    blue: "blue.500",
    green: "green.500",
    orange: "orange.500",
    pink: "pink.500",
  }

  return (
    <VStack align="stretch" gap={2}>
      {boards.map((board) => {
        const boardBg = bgColors[board.background_image || "purple"] || "purple.500"
        return (
          <RouterLink key={board.id} to="/board/$boardId" params={{ boardId: board.id }} search={{ page: 1 }}>
            <Flex
              px={3}
              py={2}
              borderRadius="md"
              bg="bg.subtle"
              _hover={{ bg: "bg.muted" }}
              cursor="pointer"
              alignItems="center"
              gap={3}
            >
              <Box w={10} h={8} bg={boardBg} borderRadius="sm" />
              <VStack align="start" gap={0}>
                <Text fontSize="sm" fontWeight="medium">{board.name}</Text>
                <Text fontSize="xs" color="fg.muted">{board.visibility}</Text>
              </VStack>
            </Flex>
          </RouterLink>
        )
      })}
    </VStack>
  )
}

const BoardCard = ({ board }: { board: { id: string; name: string; background_image?: string | null } }) => {
  const bgColors: Record<string, string> = {
    purple: "purple.500",
    blue: "blue.500",
    green: "green.500",
    orange: "orange.500",
    pink: "pink.500",
  }
  const boardBg = bgColors[board.background_image || "purple"] || "purple.500"

  return (
    <RouterLink to="/board/$boardId" params={{ boardId: board.id }} search={{ page: 1 }}>
      <Box
        bg={boardBg}
        borderRadius="md"
        p={4}
        h="100px"
        cursor="pointer"
        _hover={{ opacity: 0.9 }}
      >
        <Text color="white" fontWeight="bold" fontSize="md">{board.name}</Text>
      </Box>
    </RouterLink>
  )
}

const WorkspaceBoardsSection = () => {
  const { data: workspacesData, isLoading: workspacesLoading } = useQuery({
    queryKey: ["workspaces"],
    queryFn: () => WorkspacesService.readWorkspaces({ limit: 10 }),
  })

  const { data: boardsData, isLoading: boardsLoading } = useQuery({
    queryKey: ["boards", "all"],
    queryFn: () => BoardsService.readBoards({ limit: 100 }),
  })

  if (workspacesLoading || boardsLoading) return <Spinner />

  const workspaces = workspacesData?.data ?? []
  const boards = boardsData?.data ?? []

  return (
    <VStack align="stretch" gap={6}>
      {workspaces.map((workspace) => {
        const workspaceBoards = boards.filter((b) => b.workspace_id === workspace.id)
        
        return (
          <Box key={workspace.id}>
            <HStack mb={3}>
              <Box
                w={8}
                h={8}
                bg="blue.500"
                borderRadius="sm"
                display="flex"
                alignItems="center"
                justifyContent="center"
                color="white"
                fontSize="sm"
                fontWeight="bold"
              >
                {workspace.name.charAt(0).toUpperCase()}
              </Box>
              <Text fontWeight="bold">{workspace.name}</Text>
            </HStack>
            
            {workspaceBoards.length > 0 ? (
              <SimpleGrid columns={{ base: 1, sm: 2, md: 3, lg: 4 }} gap={4}>
                {workspaceBoards.map((board) => (
                  <BoardCard key={board.id} board={board} />
                ))}
                <Flex
                  bg="bg.subtle"
                  borderRadius="md"
                  p={4}
                  h="100px"
                  cursor="pointer"
                  alignItems="center"
                  justifyContent="center"
                  _hover={{ bg: "bg.muted" }}
                >
                  <AddBoard />
                </Flex>
              </SimpleGrid>
            ) : (
              <Flex bg="bg.subtle" borderRadius="md" p={6} alignItems="center" justifyContent="center">
                <VStack>
                  <FiGrid size={24} />
                  <Text color="fg.muted" fontSize="sm">Bu workspace'te henüz board yok</Text>
                  <AddBoard />
                </VStack>
              </Flex>
            )}
          </Box>
        )
      })}
    </VStack>
  )
}

const WelcomeSection = () => {
  return (
    <Box bg="purple.500/20" borderRadius="lg" p={8} mb={8} textAlign="center">
      <Box
        w="200px"
        h="150px"
        bg="purple.500/30"
        borderRadius="md"
        mx="auto"
        display="flex"
        alignItems="center"
        justifyContent="center"
        mb={4}
      >
        <FiGrid size={48} />
      </Box>
      <Heading size="lg" mb={2}>Her Şeyi Organize Edin</Heading>
      <Text color="fg.muted" mb={4}>
        İlk Trello panonuzla her şeyi tek bir yere koyun ve işlerinizi ilerletmeye başlayın!
      </Text>
      <HStack justify="center" gap={4}>
        <AddBoard />
        <Button variant="ghost">Anladım! Bunu iptal ediyorum.</Button>
      </HStack>
    </Box>
  )
}

function Dashboard() {
  const { data: workspacesData } = useQuery({
    queryKey: ["workspaces"],
    queryFn: () => WorkspacesService.readWorkspaces({ limit: 10 }),
  })

  const hasWorkspaces = (workspacesData?.data ?? []).length > 0

  return (
    <Container maxW="full" p={0}>
      <Flex>
        <Box flex={1} p={6}>
          <Heading size="lg" mb={6}>Dashboard</Heading>
          {!hasWorkspaces ? <WelcomeSection /> : <WorkspaceBoardsSection />}
        </Box>

        <Box
          display={{ base: "none", xl: "block" }}
          w="300px"
          minH="calc(100vh - 60px)"
          borderLeftWidth="1px"
          borderColor="border.subtle"
          p={4}
        >
          <VStack align="stretch" gap={4}>
            <HStack>
              <FiClock />
              <Text fontSize="sm" fontWeight="bold">Son Görüntülenenler</Text>
            </HStack>
            <RecentBoards />
            <Box mt={4}>
              <Text fontSize="sm" fontWeight="bold" mb={2}>Bağlantılar</Text>
              <RouterLink to="/boards" search={{ page: 1 }}>
                <Flex px={3} py={2} borderRadius="md" _hover={{ bg: "bg.subtle" }} alignItems="center" gap={2}>
                  <FiPlus />
                  <Text fontSize="sm">Yeni pano oluştur</Text>
                </Flex>
              </RouterLink>
            </Box>
          </VStack>
        </Box>
      </Flex>
    </Container>
  )
}

export default Dashboard