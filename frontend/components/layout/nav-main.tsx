"use client"

import Link from "next/link"
import { usePathname } from "next/navigation"

import {
  SidebarGroup,
  SidebarGroupContent,
  SidebarGroupLabel,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
} from "@/components/ui/sidebar"
import type { NavGroup } from "@/types/navigation"
import { cn } from "@/lib/utils"

type NavMainProps = {
  groups: NavGroup[]
}

export function NavMain({ groups }: NavMainProps) {
  const pathname = usePathname()

  return (
    <>
      {groups.map((group) => (
        <SidebarGroup key={group.title} className="py-0">
          <SidebarGroupLabel className="px-2 text-[10px] font-semibold uppercase tracking-wider text-muted-foreground/80">
            {group.title}
          </SidebarGroupLabel>
          <SidebarGroupContent>
            <SidebarMenu className="gap-0.5">
              {group.items.map((item) => {
                const isActive =
                  pathname === item.href ||
                  pathname.startsWith(`${item.href}/`)

                return (
                  <SidebarMenuItem key={item.href}>
                    <SidebarMenuButton
                      asChild
                      isActive={isActive}
                      tooltip={item.title}
                      className={cn(
                        "h-8 rounded-md text-[13px]",
                        isActive && "bg-primary/10 text-primary"
                      )}
                    >
                      <Link href={item.href}>
                        <item.icon className="size-4" />
                        <span>{item.title}</span>
                      </Link>
                    </SidebarMenuButton>
                  </SidebarMenuItem>
                )
              })}
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>
      ))}
    </>
  )
}
