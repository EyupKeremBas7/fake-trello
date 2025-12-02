import { Flex, Spinner, Text, VStack } from "@chakra-ui/react"

const PendingWorkspaces = () => {
  return (
    <Flex justify="center" align="center" py={24}>
      <VStack gap={4}>
        <Spinner size="lg" />
        <Text color="gray.500">Loading workspaces...</Text>
      </VStack>
    </Flex>
  )
}

export default PendingWorkspaces