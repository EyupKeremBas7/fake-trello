import { Box, Flex, Icon, Text, VStack, Spinner } from "@chakra-ui/react"
import { useQuery, useQueryClient } from "@tanstack/react-query"
import { Link as RouterLink } from "@tanstack/react-router"
import { FiBriefcase, FiHome, FiSettings, FiUsers, FiArchive, FiList, FiChevronDown, FiChevronRight } from "react-icons/fi"
import { FaRegStickyNote } from "react-icons/fa"
import type { IconType } from "react-icons/lib"
import { useState } from "react"

import { WorkspacesService, type UserPublic } from "@/client"

const items = [
  { icon: FiHome, title: "Dashboard", path: "/" },
  { icon: FiArchive, title: "Boards", path: "/boards" },
  { icon: FiList, title: "Lists", path: "/lists" },
  { icon: FaRegStickyNote, title: "Cards", path: "/cards" },
  { icon: FiSettings, title: "User Settings", path: "/settings" },
]

interface SidebarItemsProps {
  onClose?: () => void
}

interface Item {
  icon: IconType
  title: string
  path: string
}

const WorkspacesList = ({ onClose }: { onClose?: () => void }) => {
  const [isExpanded, setIsExpanded] = useState(true)
  
  const { data, isLoading } = useQuery({
    queryKey: ["workspaces"],
    queryFn: () => WorkspacesService.readWorkspaces({ limit: 10 }),
  })

  const workspaces = data?.data ?? []

  return (
    <Box>
      <Flex
        px={4}
        py={2}
        alignItems="center"
        justifyContent="space-between"
        cursor="pointer"
        _hover={{ bg: "gray.subtle" }}
        onClick={() => setIsExpanded(!isExpanded)}
      >
        <Flex alignItems="center" gap={2}>
          <Icon as={FiBriefcase} />
          <Text fontSize="sm" fontWeight="medium">Workspaces</Text>
        </Flex>
        <Icon as={isExpanded ? FiChevronDown : FiChevronRight} />
      </Flex>
      
      {isExpanded && (
        <VStack align="stretch" pl={6} gap={0}>
          {isLoading ? (
            <Flex px={4} py={2}><Spinner size="xs" /></Flex>
          ) : workspaces.length === 0 ? (
            <Text fontSize="xs" color="gray.500" px={4} py={2}>No workspaces</Text>
          ) : (
            workspaces.map((workspace) => (
              <RouterLink key={workspace.id} to="/workspaces" search={{ page: 1 }} onClick={onClose}>
                <Flex
                  px={4}
                  py={2}
                  alignItems="center"
                  gap={2}
                  _hover={{ bg: "gray.subtle" }}
                  fontSize="sm"
                >
                  <Box
                    w={5}
                    h={5}
                    bg="blue.500"
                    borderRadius="sm"
                    display="flex"
                    alignItems="center"
                    justifyContent="center"
                    color="white"
                    fontSize="xs"
                    fontWeight="bold"
                  >
                    {workspace.name.charAt(0).toUpperCase()}
                  </Box>
                  <Text>{workspace.name}</Text>
                </Flex>
              </RouterLink>
            ))
          )}
          <RouterLink to="/workspaces" search={{ page: 1 }} onClick={onClose}>
            <Flex
              px={4}
              py={2}
              alignItems="center"
              gap={2}
              _hover={{ bg: "gray.subtle" }}
              fontSize="sm"
              color="blue.500"
            >
              <Text>+ Add Workspace</Text>
            </Flex>
          </RouterLink>
        </VStack>
      )}
    </Box>
  )
}

const SidebarItems = ({ onClose }: SidebarItemsProps) => {
  const queryClient = useQueryClient()
  const currentUser = queryClient.getQueryData<UserPublic>(["currentUser"])

  const finalItems: Item[] = currentUser?.is_superuser
    ? [...items, { icon: FiUsers, title: "Admin", path: "/admin" }]
    : items

  const listItems = finalItems.map(({ icon, title, path }) => (
    <RouterLink key={title} to={path} search={path === "/" ? undefined : { page: 1 }} onClick={onClose}>
      <Flex
        gap={4}
        px={4}
        py={2}
        _hover={{ background: "gray.subtle" }}
        alignItems="center"
        fontSize="sm"
      >
        <Icon as={icon} alignSelf="center" />
        <Text ml={2}>{title}</Text>
      </Flex>
    </RouterLink>
  ))

  return (
    <>
      <Text fontSize="xs" px={4} py={2} fontWeight="bold">Menu</Text>
      <Box>{listItems}</Box>
      <Box mt={4}>
        <WorkspacesList onClose={onClose} />
      </Box>
    </>
  )
}

export default SidebarItems