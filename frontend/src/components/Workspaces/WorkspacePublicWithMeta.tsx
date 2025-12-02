import type { Visibility, WorkspacePublic } from "@/client"

export type WorkspacePublicWithMeta = WorkspacePublic & {
  visibility?: Visibility | null
  background_image?: string | null
}