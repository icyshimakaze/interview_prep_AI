import { useId, type ComponentProps, type ReactNode } from "react";
import { cn } from "@/lib/utils";

type FieldProps = { label: string; hint?: string; error?: string };

export function InputField({
  label,
  hint,
  error,
  id: suppliedId,
  className,
  ...props
}: ComponentProps<"input"> & FieldProps) {
  const generated = useId();
  const id = suppliedId ?? generated;
  return (
    <div className="field">
      <label htmlFor={id}>{label}</label>
      <input
        id={id}
        className={cn("input", className)}
        aria-invalid={error ? true : undefined}
        aria-describedby={error || hint ? `${id}-help` : undefined}
        {...props}
      />
      {(error || hint) && (
        <p id={`${id}-help`} className={error ? "field-error" : "field-hint"}>
          {error ?? hint}
        </p>
      )}
    </div>
  );
}

export function SelectField({
  label,
  hint,
  error,
  id: suppliedId,
  className,
  ...props
}: ComponentProps<"select"> & FieldProps) {
  const generated = useId();
  const id = suppliedId ?? generated;
  return (
    <div className="field">
      <label htmlFor={id}>{label}</label>
      <select
        id={id}
        className={cn("input", className)}
        aria-invalid={error ? true : undefined}
        aria-describedby={error || hint ? `${id}-help` : undefined}
        {...props}
      />
      {(error || hint) && (
        <p id={`${id}-help`} className={error ? "field-error" : "field-hint"}>
          {error ?? hint}
        </p>
      )}
    </div>
  );
}

export function FormSection({
  title,
  description,
  children,
}: {
  title: string;
  description: string;
  children: ReactNode;
}) {
  return (
    <section className="form-section">
      <div>
        <h2 className="section-title">{title}</h2>
        <p className="mt-2 text-sm leading-6 text-muted">{description}</p>
      </div>
      <div className="grid min-w-0 gap-5 sm:grid-cols-2">{children}</div>
    </section>
  );
}
