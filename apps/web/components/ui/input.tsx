import * as React from "react";
import { cn } from "@/lib/utils";

export const Input = React.forwardRef<HTMLInputElement, React.InputHTMLAttributes<HTMLInputElement>>(({ className, ...props }, ref) => (
  <input
    ref={ref}
    className={cn(
      "flex h-12 w-full rounded-2xl border border-app bg-input-app px-4 py-2 text-sm text-texto placeholder:text-muted-app shadow-[inset_0_1px_0_var(--surface-inset)] transition-colors hover:border-app-strong hover:shadow-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primaria focus-visible:ring-offset-2 focus-visible:ring-offset-fundo disabled:cursor-not-allowed disabled:opacity-40",
      className
    )}
    {...props}
  />
));
Input.displayName = "Input";
