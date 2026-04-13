import * as React from "react";
import { cn } from "@/lib/utils";

export const Textarea = React.forwardRef<HTMLTextAreaElement, React.TextareaHTMLAttributes<HTMLTextAreaElement>>(({ className, ...props }, ref) => (
  <textarea
    ref={ref}
    className={cn(
      "min-h-[180px] w-full rounded-[24px] border border-dashed border-app bg-input-app px-5 py-4 text-sm text-texto shadow-[inset_0_1px_0_var(--surface-inset)] placeholder:text-muted-app transition-colors hover:border-app-strong focus-visible:border-solid focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primaria focus-visible:ring-offset-2 focus-visible:ring-offset-fundo disabled:cursor-not-allowed disabled:opacity-40",
      className
    )}
    {...props}
  />
));
Textarea.displayName = "Textarea";
