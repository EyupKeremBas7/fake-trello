import { Button, ButtonGroup } from "@chakra-ui/react"

import type { WorkspacePublicWithMeta } from "../Workspaces/WorkspacePublicWithMeta"

interface WorkspaceActionsMenuProps {
  workspace: WorkspacePublicWithMeta
}

const WorkspaceActionsMenu = ({ workspace }: WorkspaceActionsMenuProps) => {
  return (
    <ButtonGroup size="xs" variant="ghost" data-workspace-id={workspace.id}>
      <Button>Edit</Button>
      <Button colorPalette="red">Delete</Button>
    </ButtonGroup>
  )
}

export default WorkspaceActionsMenu