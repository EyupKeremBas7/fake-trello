import { IconButton } from "@chakra-ui/react"
import { BsThreeDotsVertical } from "react-icons/bs"
import type { BoardPublic } from "@/client"
import DeleteBoard from "../Boards/DeleteBoard"
import EditBoard from "../Boards/EditBoard"
import { MenuContent, MenuRoot, MenuTrigger } from "../ui/menu"

interface BoardActionsMenuProps {
  Board: BoardPublic
}

export const BoardActionsMenu = ({ Board }: BoardActionsMenuProps) => {
  return (
    <MenuRoot>
      <MenuTrigger asChild>
        <IconButton variant="ghost" color="inherit">
          <BsThreeDotsVertical />
        </IconButton>
      </MenuTrigger>
      <MenuContent>
        <EditBoard Board={Board} />
        <DeleteBoard id={Board.id} />
      </MenuContent>
    </MenuRoot>
  )
}
