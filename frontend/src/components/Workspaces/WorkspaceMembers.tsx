import {
  Badge,
  Box,
  Button,
  Flex,
  Spinner,
  Table,
  Text,
  VStack,
} from "@chakra-ui/react"
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { FiTrash2 } from "react-icons/fi"

import { UsersService, WorkspacesService } from "@/client"
import type { ApiError } from "@/client/core/ApiError"
import useCustomToast from "@/hooks/useCustomToast"
import { handleError } from "@/utils"
import AddWorkspaceMember from "./AddWorkspaceMember"

interface WorkspaceMembersProps {
  workspaceId: string
  ownerId: string
}

const getRoleBadgeColor = (role: string) => {
  switch (role) {
    case "admin":
      return "purple"
    case "member":
      return "blue"
    case "observer":
      return "gray"
    default:
      return "gray"
  }
}

const MemberRow = ({ member, workspaceId }: { member: any; workspaceId: string; ownerId: string }) => {
  const queryClient = useQueryClient()
  const { showSuccessToast } = useCustomToast()

  const { data: userData } = useQuery({
    queryKey: ["user", member.user_id],
    queryFn: () => UsersService.readUserById({ userId: member.user_id }),
  })

  const removeMutation = useMutation({
    mutationFn: () =>
      WorkspacesService.removeWorkspaceMember({
        id: workspaceId,
        memberId: member.id,
      }),
    onSuccess: () => {
      showSuccessToast("Member removed successfully.")
    },
    onError: (err: ApiError) => {
      handleError(err)
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ["workspaceMembers", workspaceId] })
    },
  })

  return (
    <Table.Row>
      <Table.Cell>
        <VStack align="start" gap={0}>
          <Text fontWeight="medium">{userData?.full_name || "Loading..."}</Text>
          <Text fontSize="xs" color="fg.muted">{userData?.email}</Text>
        </VStack>
      </Table.Cell>
      <Table.Cell>
        <Badge colorPalette={getRoleBadgeColor(member.role)}>{member.role}</Badge>
      </Table.Cell>
      <Table.Cell>
        <Text fontSize="sm" color="fg.muted">
          {new Date(member.created_at).toLocaleDateString()}
        </Text>
      </Table.Cell>
      <Table.Cell>
        <Button
          size="xs"
          variant="ghost"
          colorPalette="red"
          onClick={() => removeMutation.mutate()}
          loading={removeMutation.isPending}
        >
          <FiTrash2 />
        </Button>
      </Table.Cell>
    </Table.Row>
  )
}

const WorkspaceMembers = ({ workspaceId, ownerId }: WorkspaceMembersProps) => {
  const { data, isLoading } = useQuery({
    queryKey: ["workspaceMembers", workspaceId],
    queryFn: () => WorkspacesService.readWorkspaceMembers({ id: workspaceId }),
  })

  const { data: ownerData } = useQuery({
    queryKey: ["user", ownerId],
    queryFn: () => UsersService.readUserById({ userId: ownerId }),
  })

  if (isLoading) return <Spinner size="sm" />

  const members = data?.data ?? []

  return (
    <Box>
      <Flex justify="space-between" align="center" mb={4}>
        <Text fontWeight="bold">Members ({members.length + 1})</Text>
        <AddWorkspaceMember workspaceId={workspaceId} />
      </Flex>

      <Table.Root size="sm">
        <Table.Header>
          <Table.Row>
            <Table.ColumnHeader>User</Table.ColumnHeader>
            <Table.ColumnHeader>Role</Table.ColumnHeader>
            <Table.ColumnHeader>Joined</Table.ColumnHeader>
            <Table.ColumnHeader>Actions</Table.ColumnHeader>
          </Table.Row>
        </Table.Header>
        <Table.Body>
          <Table.Row>
            <Table.Cell>
              <VStack align="start" gap={0}>
                <Text fontWeight="medium">{ownerData?.full_name || "Loading..."}</Text>
                <Text fontSize="xs" color="fg.muted">{ownerData?.email}</Text>
              </VStack>
            </Table.Cell>
            <Table.Cell>
              <Badge colorPalette="green">Owner</Badge>
            </Table.Cell>
            <Table.Cell>
              <Text fontSize="sm" color="fg.muted">-</Text>
            </Table.Cell>
            <Table.Cell>
              <Text fontSize="xs" color="fg.muted">Cannot remove</Text>
            </Table.Cell>
          </Table.Row>
          {members.map((member) => (
            <MemberRow
              key={member.id}
              member={member}
              workspaceId={workspaceId}
              ownerId={ownerId}
            />
          ))}
        </Table.Body>
      </Table.Root>

      {members.length === 0 && (
        <Text fontSize="sm" color="fg.muted" mt={4} textAlign="center">
          No members added yet. Click "Add Member" to invite someone.
        </Text>
      )}
    </Box>
  )
}

export default WorkspaceMembers