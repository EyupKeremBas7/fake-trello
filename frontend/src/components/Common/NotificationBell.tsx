import {
  Box,
  Button,
  Flex,
  Text,
  Icon,
  Badge,
  Spinner,
  VStack,
  HStack,
  IconButton,
} from "@chakra-ui/react"
import {
  DrawerRoot,
  DrawerTrigger,
  DrawerContent,
  DrawerBody,
  DrawerHeader,
  DrawerCloseTrigger,
  DrawerTitle,
  DrawerBackdrop,
} from "@chakra-ui/react"
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { FiBell, FiCheck, FiX, FiMail, FiMessageSquare, FiUserPlus } from "react-icons/fi"
import { useState } from "react"

import {
  NotificationsService,
  InvitationsService,
  type NotificationPublic,
  type WorkspaceInvitationWithDetails,
} from "@/client"

function NotificationBell() {
  const queryClient = useQueryClient()
  const [isOpen, setIsOpen] = useState(false)

  // Get notifications
  const { data: notifications, isLoading: notificationsLoading } = useQuery({
    queryKey: ["notifications"],
    queryFn: () => NotificationsService.readNotifications({ limit: 20 }),
    refetchInterval: 30000, // Refetch every 30 seconds
  })

  // Get pending invitations
  const { data: invitations, isLoading: invitationsLoading } = useQuery({
    queryKey: ["invitations"],
    queryFn: () => InvitationsService.readMyInvitations({}),
    refetchInterval: 30000,
  })

  // Mark notification as read
  const markAsReadMutation = useMutation({
    mutationFn: (id: string) => NotificationsService.markAsRead({ id }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["notifications"] })
    },
  })

  // Mark all as read
  const markAllAsReadMutation = useMutation({
    mutationFn: () => NotificationsService.markAllAsRead(),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["notifications"] })
    },
  })

  // Accept/reject invitation
  const respondInvitationMutation = useMutation({
    mutationFn: ({ id, accept }: { id: string; accept: boolean }) =>
      InvitationsService.respondToInvitation({ id, requestBody: { accept } }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["invitations"] })
      queryClient.invalidateQueries({ queryKey: ["notifications"] })
      queryClient.invalidateQueries({ queryKey: ["workspaces"] })
    },
  })

  const unreadCount = notifications?.unread_count || 0
  const pendingInvitations = invitations?.filter(
    (inv: WorkspaceInvitationWithDetails) => inv.status === "pending"
  ) || []
  const totalBadge = unreadCount + pendingInvitations.length

  const getNotificationIcon = (type: string) => {
    switch (type) {
      case "workspace_invitation":
        return FiUserPlus
      case "comment_added":
        return FiMessageSquare
      case "invitation_accepted":
      case "invitation_rejected":
        return FiMail
      default:
        return FiBell
    }
  }

  const formatTime = (date: string) => {
    const now = new Date()
    const notifDate = new Date(date)
    const diffMs = now.getTime() - notifDate.getTime()
    const diffMins = Math.floor(diffMs / 60000)
    const diffHours = Math.floor(diffMs / 3600000)
    const diffDays = Math.floor(diffMs / 86400000)

    if (diffMins < 1) return "just now"
    if (diffMins < 60) return `${diffMins}m ago`
    if (diffHours < 24) return `${diffHours}h ago`
    return `${diffDays}d ago`
  }

  return (
    <DrawerRoot
      placement="end"
      open={isOpen}
      onOpenChange={({ open }) => setIsOpen(open)}
    >
      <DrawerBackdrop />
      <DrawerTrigger asChild>
        <IconButton
          variant="ghost"
          size="sm"
          position="relative"
          aria-label="Notifications"
        >
          <Icon as={FiBell} boxSize={5} />
          {totalBadge > 0 && (
            <Badge
              position="absolute"
              top="-1"
              right="-1"
              colorPalette="red"
              borderRadius="full"
              fontSize="xs"
              minW="18px"
              h="18px"
              display="flex"
              alignItems="center"
              justifyContent="center"
            >
              {totalBadge > 99 ? "99+" : totalBadge}
            </Badge>
          )}
        </IconButton>
      </DrawerTrigger>
      <DrawerContent>
        <DrawerHeader borderBottomWidth="1px">
          <Flex justify="space-between" align="center" w="full">
            <DrawerTitle>Notifications</DrawerTitle>
            {unreadCount > 0 && (
              <Button
                size="xs"
                variant="ghost"
                onClick={() => markAllAsReadMutation.mutate()}
                loading={markAllAsReadMutation.isPending}
              >
                Mark all read
              </Button>
            )}
          </Flex>
        </DrawerHeader>
        <DrawerCloseTrigger />
        <DrawerBody p={0}>
          {(notificationsLoading || invitationsLoading) ? (
            <Flex justify="center" p={4}>
              <Spinner size="sm" />
            </Flex>
          ) : (
            <VStack gap={0} align="stretch">
              {/* Pending Invitations */}
              {pendingInvitations.map((invitation: WorkspaceInvitationWithDetails) => (
                <Box
                  key={invitation.id}
                  p={3}
                  borderBottomWidth="1px"
                  bg="blue.50"
                  _dark={{ bg: "blue.900" }}
                >
                  <HStack gap={3}>
                    <Icon as={FiUserPlus} boxSize={5} color="blue.500" />
                    <Box flex={1}>
                      <Text fontSize="sm" fontWeight="medium">
                        Workspace Invitation
                      </Text>
                      <Text fontSize="xs" color="gray.600" _dark={{ color: "gray.400" }}>
                        {invitation.inviter_name} invited you to "{invitation.workspace_name}"
                      </Text>
                      {invitation.message && (
                        <Text fontSize="xs" color="gray.500" mt={1} fontStyle="italic">
                          "{invitation.message}"
                        </Text>
                      )}
                      <HStack mt={2} gap={2}>
                        <Button
                          size="xs"
                          colorPalette="green"
                          onClick={() =>
                            respondInvitationMutation.mutate({
                              id: invitation.id,
                              accept: true,
                            })
                          }
                          loading={respondInvitationMutation.isPending}
                        >
                          <Icon as={FiCheck} /> Accept
                        </Button>
                        <Button
                          size="xs"
                          colorPalette="red"
                          variant="outline"
                          onClick={() =>
                            respondInvitationMutation.mutate({
                              id: invitation.id,
                              accept: false,
                            })
                          }
                          loading={respondInvitationMutation.isPending}
                        >
                          <Icon as={FiX} /> Decline
                        </Button>
                      </HStack>
                    </Box>
                  </HStack>
                </Box>
              ))}

              {/* Other Notifications */}
              {notifications?.data?.map((notification: NotificationPublic) => (
                <Box
                  key={notification.id}
                  p={3}
                  borderBottomWidth="1px"
                  bg={notification.is_read ? "transparent" : "gray.50"}
                  _dark={{ bg: notification.is_read ? "transparent" : "gray.800" }}
                  cursor="pointer"
                  _hover={{ bg: "gray.100", _dark: { bg: "gray.700" } }}
                  onClick={() => {
                    if (!notification.is_read) {
                      markAsReadMutation.mutate(notification.id)
                    }
                  }}
                >
                  <HStack gap={3}>
                    <Icon
                      as={getNotificationIcon(notification.type)}
                      boxSize={5}
                      color={notification.is_read ? "gray.400" : "blue.500"}
                    />
                    <Box flex={1}>
                      <Text
                        fontSize="sm"
                        fontWeight={notification.is_read ? "normal" : "medium"}
                      >
                        {notification.title}
                      </Text>
                      <Text fontSize="xs" color="gray.600" _dark={{ color: "gray.400" }}>
                        {notification.message}
                      </Text>
                      <Text fontSize="xs" color="gray.400" mt={1}>
                        {formatTime(notification.created_at)}
                      </Text>
                    </Box>
                    {!notification.is_read && (
                      <Box w={2} h={2} borderRadius="full" bg="blue.500" />
                    )}
                  </HStack>
                </Box>
              ))}

              {/* Empty State */}
              {pendingInvitations.length === 0 && notifications?.data?.length === 0 && (
                <Flex justify="center" p={6} color="gray.500">
                  <VStack>
                    <Icon as={FiBell} boxSize={8} />
                    <Text>No notifications</Text>
                  </VStack>
                </Flex>
              )}
            </VStack>
          )}
        </DrawerBody>
      </DrawerContent>
    </DrawerRoot>
  )
}

export default NotificationBell
