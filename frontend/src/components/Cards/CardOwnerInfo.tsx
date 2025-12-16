import { Box, HStack, Spinner, Text } from "@chakra-ui/react"
import { useQuery } from "@tanstack/react-query"

import { UsersService } from "@/client"

interface CardOwnerInfoProps {
    createdBy: string | null | undefined
    showAvatar?: boolean
    showLabel?: boolean
}

export const CardOwnerInfo = ({ createdBy, showAvatar = true, showLabel = false }: CardOwnerInfoProps) => {
    const { data, isLoading, isError } = useQuery({
        queryKey: ["user", createdBy],
        queryFn: () => UsersService.readUserById({ userId: createdBy! }),
        enabled: !!createdBy,
        staleTime: 5 * 60 * 1000, // Cache for 5 minutes
    })

    if (!createdBy) return <Text fontSize="sm" color="fg.muted">-</Text>
    if (isLoading) return <Spinner size="xs" />
    if (isError || !data) return <Text fontSize="sm" color="fg.muted">-</Text>

    const displayName = data.full_name || data.email || "Unknown"

    if (!showAvatar) {
        return (
            <Text fontSize="sm">
                {showLabel && <strong>Owner: </strong>}
                {displayName}
            </Text>
        )
    }

    return (
        <HStack>
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
                {displayName.charAt(0).toUpperCase()}
            </Box>
            <Text fontSize="sm" color="fg.muted">
                {showLabel && "Owner: "}
                {displayName}
            </Text>
        </HStack>
    )
}

export default CardOwnerInfo
