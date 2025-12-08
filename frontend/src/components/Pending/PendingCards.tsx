import { Flex, Spinner, Text, VStack } from "@chakra-ui/react"

const PendingCards = () => {
  return (
    <Flex justify="center" align="center" py={24}>
      <VStack gap={4}>
        <Spinner size="lg" />
        <Text color="fg.muted">Loading cards...</Text>
      </VStack>
    </Flex>
  )
}

export default PendingCards