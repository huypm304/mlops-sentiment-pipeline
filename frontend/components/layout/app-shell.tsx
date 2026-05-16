"use client"

import Link from "next/link"
import { Sparkles } from "lucide-react"

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
            "--sidebar-width": "14rem",
            "--sidebar-width-icon": "3rem",
          } as React.CSSProperties
        }
      >
        <Sidebar className="border-r border-white/[0.06] bg-sidebar/90 backdrop-blur-xl">
          <SidebarHeader className="border-b border-white/[0.06] p-2">
            <SidebarMenu>
              <SidebarMenuItem>
                <SidebarMenuButton size="lg" asChild className="h-10">
                  <Link href={brand.href}>
                    <div className="flex size-7 items-center justify-center rounded-md bg-primary/15">
                      <Sparkles className="size-3.5 text-primary" />
                    </div>
                    <div className="grid leading-tight group-data-[collapsible=icon]:hidden">
                      <span className="text-sm font-semibold">{brand.title}</span>
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
            <SidebarFooter className="border-t border-white/[0.06] p-2 text-[11px] text-muted-foreground group-data-[collapsible=icon]:hidden">
              {footer}
            </SidebarFooter>
          ) : null}
          <SidebarRail />
        </Sidebar>
        <SidebarInset>
          <header className="flex h-11 shrink-0 items-center gap-2 border-b border-white/[0.06] bg-background/80 px-4 backdrop-blur-md">
            <SidebarTrigger className="-ml-1 size-7" />
            <Separator orientation="vertical" className="h-4" />
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
          <main className="flex flex-1 flex-col gap-5 p-4 md:p-6">{children}</main>
        </SidebarInset>
      </SidebarProvider>
    </TooltipProvider>
  )
}
