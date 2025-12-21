import { Box, HStack, Text, VStack, Spinner } from "@chakra-ui/react"
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { FiUserPlus, FiX } from "react-icons/fi"

import { CardsService, WorkspacesService, type CardPublic, type WorkspaceMemberPublic, UsersService } from "@/client"
import type { ApiError } from "@/client/core/ApiError"
import useCustomToast from "@/hooks/useCustomToast"
import { handleError } from "@/utils"

interface CardAssigneeSelectorProps {
    card: CardPublic
    workspaceId: string
}

const MemberOption = ({
    member,
    onSelect,
    isSelected
}: {
    member: WorkspaceMemberPublic & { user_name?: string }
    onSelect: (id: string | null) => void
    isSelected?: boolean
}) => {
    const { data: user } = useQuery({
        queryKey: ["user", member.user_id],
        queryFn: () => UsersService.readUserById({ userId: member.user_id }),
        staleTime: 5 * 60 * 1000,
    })

    const displayName = user?.full_name || user?.email || "Loading..."

    return (
        <HStack
            p={2}
            cursor="pointer"
            borderRadius="md"
            bg={isSelected ? "blue.50" : "transparent"}
            _hover={{ bg: isSelected ? "blue.100" : "bg.subtle" }}
            onClick={() => onSelect(isSelected ? null : member.user_id)}
        >
            <Box
                w={6}
                h={6}
                bg={isSelected ? "green.500" : "gray.400"}
                borderRadius="full"
                display="flex"
                alignItems="center"
                justifyContent="center"
                color="white"
                fontSize="xs"
                fontWeight="bold"
            >
                {displayName.charAt(0).toUpperCase()}
            </Box>
            <Text fontSize="sm">{displayName}</Text>
            {isSelected && <FiX size={14} />}
        </HStack>
    )
}

export const CardAssigneeSelector = ({ card, workspaceId }: CardAssigneeSelectorProps) => {
    const queryClient = useQueryClient()
    const { showSuccessToast } = useCustomToast()

    const { data: membersData, isLoading } = useQuery({
        queryKey: ["workspace-members", workspaceId],
        queryFn: () => WorkspacesService.readWorkspaceMembers({ id: workspaceId }),
        enabled: !!workspaceId,
    })

    const assignMutation = useMutation({
        mutationFn: (assigneeId: string | null) =>
            CardsService.updateCard({
                id: card.id,
                requestBody: { assigned_to: assigneeId },
            }),
        onSuccess: (_, assigneeId) => {
            showSuccessToast(assigneeId ? "Card assigned" : "Assignment removed")
        },
        onError: (err: ApiError) => handleError(err),
        onSettled: () => {
            queryClient.invalidateQueries({ queryKey: ["cards"] })
        },
    })

    if (isLoading) return <Spinner size="sm" />

    const members = membersData?.data ?? []

    return (
        <Box>
            <HStack mb={2}>
                <FiUserPlus />
                <Text fontSize="sm" fontWeight="medium">Assign to</Text>
            </HStack>
            <VStack align="stretch" gap={1} maxH="200px" overflowY="auto">
                {members.length === 0 ? (
                    <Text fontSize="sm" color="fg.muted">No workspace members</Text>
                ) : (
                    members.map((member) => (
                        <MemberOption
                            key={member.id}
                            member={member}
                            isSelected={card.assigned_to === member.user_id}
                            onSelect={(id) => assignMutation.mutate(id)}
                        />
                    ))
                )}
            </VStack>
        </Box>
    )
}

export default CardAssigneeSelector
