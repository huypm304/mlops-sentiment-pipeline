"use client"

import Link from "next/link"
import { LayoutGrid } from "lucide-react"

import { NavMain } from "@/components/layout/nav-main"
import { ThemeToggle } from "@/components/layout/theme-toggle"
import { Button } from "@/components/ui/button"
import { Separator } from "@/components/ui/separator"
import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarHeader,
  SidebarInset,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  SidebarProvider,
  SidebarRail,
  SidebarTrigger,
} from "@/components/ui/sidebar"
import { TooltipProvider } from "@/components/ui/tooltip"
import type { NavGroup } from "@/types/navigation"

type AppShellProps = {
  children: React.ReactNode
  navGroups: NavGroup[]
  brand: { title: string; subtitle: string; href: string }
  footer?: React.ReactNode
  headerExtra?: React.ReactNode
  switchLink?: { href: string; label: string }
}

export function AppShell({
  children,
  navGroups,
  brand,
  footer,
  headerExtra,
  switchLink,
}: AppShellProps) {
  return (
    <TooltipProvider delayDuration={0}>
      <SidebarProvider
        style={
          {
            "--sidebar-width": "14.5rem",
            "--sidebar-width-icon": "3rem",
          } as React.CSSProperties
        }
      >
        <Sidebar className="border-r border-border bg-sidebar">
          <SidebarHeader className="border-b border-border/60 p-2">
            <SidebarMenu>
              <SidebarMenuItem>
                <SidebarMenuButton size="lg" asChild className="h-9">
                  <Link href={brand.href}>
                    <div className="flex size-6 items-center justify-center rounded border border-border/80 bg-background">
                      <LayoutGrid className="size-3 text-muted-foreground" />
                    </div>
                    <div className="grid leading-tight group-data-[collapsible=icon]:hidden">
                      <span className="text-[13px] font-semibold tracking-tight">
                        {brand.title}
                      </span>
                      <span className="text-[10px] text-muted-foreground">
                        {brand.subtitle}
                      </span>
                    </div>
                  </Link>
                </SidebarMenuButton>
              </SidebarMenuItem>
            </SidebarMenu>
          </SidebarHeader>
          <SidebarContent className="px-1 py-2">
            <NavMain groups={navGroups} />
          </SidebarContent>
          {footer ? (
            <SidebarFooter className="border-t border-border/60 p-2 group-data-[collapsible=icon]:hidden">
              {footer}
            </SidebarFooter>
          ) : null}
          <SidebarRail />
        </Sidebar>
        <SidebarInset>
          <header className="flex h-11 shrink-0 items-center gap-2 border-b border-border bg-background px-4">
            <SidebarTrigger className="-ml-1 size-7" />
            <Separator orientation="vertical" className="h-4 opacity-50" />
            {headerExtra}
            <div className="ml-auto flex items-center gap-2">
              {switchLink ? (
                <Button variant="ghost" size="sm" className="h-7 text-xs" asChild>
                  <Link href={switchLink.href}>{switchLink.label}</Link>
                </Button>
              ) : null}
              <ThemeToggle />
            </div>
          </header>
          <main className="flex flex-1 flex-col gap-6 p-6">{children}</main>
        </SidebarInset>
      </SidebarProvider>
    </TooltipProvider>
  )
}
