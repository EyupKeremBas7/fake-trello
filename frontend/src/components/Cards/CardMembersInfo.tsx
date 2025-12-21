import { Box, HStack, Text, VStack } from "@chakra-ui/react"
import { FiUser, FiUsers } from "react-icons/fi"

import type { CardPublic } from "@/client"

interface CardMembersInfoProps {
    card: CardPublic
    showLabels?: boolean
}

export const CardMembersInfo = ({ card, showLabels = true }: CardMembersInfoProps) => {
    const ownerName = card.owner_full_name || card.owner_email
    const assigneeName = card.assignee_full_name || card.assignee_email

    // If same person is both owner and assignee, show only once
    const samePersonOwnedAndAssigned = card.created_by === card.assigned_to && card.assigned_to

    if (samePersonOwnedAndAssigned) {
        return (
            <HStack>
                <Box
                    w={7}
                    h={7}
                    bg="purple.500"
                    borderRadius="full"
                    display="flex"
                    alignItems="center"
                    justifyContent="center"
                    color="white"
                    fontSize="xs"
                    fontWeight="bold"
                >
                    {(ownerName || "U").charAt(0).toUpperCase()}
                </Box>
                <VStack align="start" gap={0}>
                    <Text fontSize="sm" fontWeight="medium">{ownerName}</Text>
                    {showLabels && (
                        <Text fontSize="xs" color="fg.muted">Owner & Assigned</Text>
                    )}
                </VStack>
            </HStack>
        )
    }

    return (
        <VStack align="stretch" gap={3}>
            {/* Owner */}
            {ownerName && (
                <HStack>
                    <FiUser size={14} />
                    <Box
                        w={6}
                        h={6}
                        bg="purple.500"
                        borderRadius="full"
                        display="flex"
                        alignItems="center"
                        justifyContent="center"
                        color="white"
                        fontSize="xs"
                        fontWeight="bold"
                    >
                        {ownerName.charAt(0).toUpperCase()}
                    </Box>
                    <VStack align="start" gap={0}>
                        <Text fontSize="sm">{ownerName}</Text>
                        {showLabels && (
                            <Text fontSize="xs" color="fg.muted">Created by</Text>
                        )}
                    </VStack>
                </HStack>
            )}

            {/* Assignee - only show if different from owner */}
            {assigneeName && card.assigned_to !== card.created_by && (
                <HStack>
                    <FiUsers size={14} />
                    <Box
                        w={6}
                        h={6}
                        bg="green.500"
                        borderRadius="full"
                        display="flex"
                        alignItems="center"
                        justifyContent="center"
                        color="white"
                        fontSize="xs"
                        fontWeight="bold"
                    >
                        {assigneeName.charAt(0).toUpperCase()}
                    </Box>
                    <VStack align="start" gap={0}>
                        <Text fontSize="sm">{assigneeName}</Text>
                        {showLabels && (
                            <Text fontSize="xs" color="fg.muted">Assigned to</Text>
                        )}
                    </VStack>
                </HStack>
            )}

            {/* Not assigned */}
            {!assigneeName && (
                <HStack color="fg.muted">
                    <FiUsers size={14} />
                    <Text fontSize="sm">No one assigned</Text>
                </HStack>
            )}
        </VStack>
    )
}

export default CardMembersInfo
