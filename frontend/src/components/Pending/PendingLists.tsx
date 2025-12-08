import { Flex, Spinner, Text, VStack } from "@chakra-ui/react"

const PendingLists = () => {
  return (
    <Flex justify="center" align="center" py={24}>
      <VStack gap={4}>
        <Spinner size="lg" />
        <Text color="fg.muted">Loading lists...</Text>
      </VStack>
    </Flex>
  )
}

export default PendingLists