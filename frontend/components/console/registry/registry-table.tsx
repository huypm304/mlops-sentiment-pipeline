import { cn } from "@/lib/utils"

export function RegistryTable({
  className,
  ...props
}: React.ComponentProps<"table">) {
  return (
    <table
      className={cn("w-full border-collapse text-[13px]", className)}
      {...props}
    />
  )
}

export function RegistryThead({
  className,
  ...props
}: React.ComponentProps<"thead">) {
  return (
    <thead
      className={cn(
        "sticky top-0 z-10 border-b border-border bg-registry-stripe text-left text-[12px] font-medium text-muted-foreground",
        className,
      )}
      {...props}
    />
  )
}

export function RegistryTh({
  align = "left",
  className,
  ...props
}: React.ComponentProps<"th"> & { align?: "left" | "right" | "center" }) {
  return (
    <th
      className={cn(
        "px-3 py-2 font-medium whitespace-nowrap",
        align === "right" && "text-right",
        align === "center" && "text-center",
        className,
      )}
      {...props}
    />
  )
}

export function RegistryTr({
  className,
  ...props
}: React.ComponentProps<"tr">) {
  return (
    <tr
      className={cn("border-b border-border/80 last:border-b-0 hover:bg-muted/30", className)}
      {...props}
    />
  )
}

export function RegistryTd({
  align = "left",
  muted,
  mono,
  numeric,
  className,
  ...props
}: React.ComponentProps<"td"> & {
  align?: "left" | "right" | "center"
  muted?: boolean
  mono?: boolean
  numeric?: boolean
}) {
  return (
    <td
      className={cn(
        "px-3 py-2 align-middle",
        align === "right" && "text-right",
        align === "center" && "text-center",
        muted && "text-muted-foreground",
        mono && "font-mono text-[12px]",
        numeric && "tabular-nums",
        className,
      )}
      {...props}
    />
  )
}
