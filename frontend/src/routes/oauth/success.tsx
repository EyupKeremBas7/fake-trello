import { Container, Spinner, Text, VStack } from "@chakra-ui/react"
import { createFileRoute, useNavigate } from "@tanstack/react-router"
import { useEffect } from "react"

export const Route = createFileRoute("/oauth/success")({
    component: OAuthSuccess,
})

function OAuthSuccess() {
    const navigate = useNavigate()

    useEffect(() => {
        const urlParams = new URLSearchParams(window.location.search)
        const token = urlParams.get("token")

        if (token) {
            localStorage.setItem("access_token", token)
            navigate({ to: "/" })
        } else {
            navigate({ to: "/login" })
        }
    }, [navigate])

    return (
        <Container h="100vh" centerContent justifyContent="center">
            <VStack gap={4}>
                <Spinner size="xl" color="blue.500" />
                <Text>Logging you in...</Text>
            </VStack>
        </Container>
    )
}
