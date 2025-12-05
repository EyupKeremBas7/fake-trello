import { BsThreeDotsVertical } from "react-icons/bs"
import { IconButton } from "@chakra-ui/react"
import { MenuContent, MenuRoot, MenuTrigger } from "../ui/menu"
import type { WorkspacePublicWithMeta } from "../Workspaces/WorkspacePublicWithMeta"
import EditWorkspace from "../Workspaces/EditWorkspace"
import DeleteWorkspace from "../Workspaces/DeleteWorkspace"


interface WorkspaceActionsMenuProps {
  workspace: WorkspacePublicWithMeta
}

const WorkspaceActionsMenu = ({ workspace }: WorkspaceActionsMenuProps) => {
  return (
    <MenuRoot>
      <MenuTrigger asChild>
        <IconButton variant="ghost" color="inherit">
          <BsThreeDotsVertical />
        </IconButton>
      </MenuTrigger>
      <MenuContent>
        <EditWorkspace Workspace={workspace} />
        <DeleteWorkspace id={workspace.id} />
      </MenuContent>
    </MenuRoot>
  )
}

export default WorkspaceActionsMenu