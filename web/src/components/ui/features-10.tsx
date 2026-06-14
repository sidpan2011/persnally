import { Card } from "@/components/ui/card";
import { HubGraphic, ProvenanceGraphic } from "@/components/ui/feature-graphics";
import { cn } from "@/lib/utils";
import { Network, ScanSearch, type LucideIcon } from "lucide-react";
import { ReactNode } from "react";

export function Features() {
  return (
    <section className="py-16 md:py-28">
      <div className="mx-auto max-w-6xl px-6">
        <div className="mx-auto max-w-2xl text-center">
          <span className="font-mono text-[11px] uppercase tracking-[0.18em] text-volt">
            Under the hood
          </span>
          <h2 className="mt-5 text-3xl font-semibold tracking-tight text-foreground sm:text-5xl">
            More than memory. An engine.
          </h2>
          <p className="mt-5 text-lg leading-relaxed text-muted-foreground">
            Structured events, derived views, and a walkable provenance graph — explainable,
            decay-aware, and entirely your own.
          </p>
        </div>

        <div className="mx-auto mt-14 grid gap-4 lg:grid-cols-2">
          <FeatureCard>
            <CardHeading
              icon={Network}
              title="Cross-vendor · MCP"
              description="One context, every tool reads it."
            />
            <div className="relative mb-6 border-t border-dashed sm:mb-0">
              <div className="absolute inset-0 [background:radial-gradient(125%_125%_at_50%_0%,transparent_40%,hsl(var(--primary)/0.10),transparent_125%)]" />
              <div className="px-6 py-5">
                <HubGraphic />
              </div>
            </div>
          </FeatureCard>

          <FeatureCard>
            <CardHeading
              icon={ScanSearch}
              title="Provenance"
              description="Every claim cites its evidence."
            />
            <div className="relative mb-6 border-t border-dashed sm:mb-0">
              <div className="absolute inset-0 [background:radial-gradient(125%_125%_at_50%_0%,transparent_40%,hsl(var(--primary)/0.10),transparent_125%)]" />
              <div className="px-6 py-5">
                <ProvenanceGraphic />
              </div>
            </div>
          </FeatureCard>

          <FeatureCard className="p-6 lg:col-span-2">
            <p className="mx-auto my-6 max-w-md text-balance text-center text-2xl font-semibold text-foreground">
              Per-client scopes — decide exactly what each AI can see.
            </p>

            <div className="flex justify-center gap-6 overflow-hidden">
              <CircularUI label="Allowed" circles={[{ pattern: "border" }, { pattern: "border" }]} />
              <CircularUI label="Shared" circles={[{ pattern: "none" }, { pattern: "primary" }]} />
              <CircularUI label="Scoped" circles={[{ pattern: "primary" }, { pattern: "none" }]} />
              <CircularUI
                label="Hidden"
                circles={[{ pattern: "primary" }, { pattern: "none" }]}
                className="hidden sm:block"
              />
            </div>
          </FeatureCard>
        </div>
      </div>
    </section>
  );
}

interface FeatureCardProps {
  children: ReactNode;
  className?: string;
}

const FeatureCard = ({ children, className }: FeatureCardProps) => (
  <Card className={cn("group relative rounded-none shadow-zinc-950/5", className)}>
    <CardDecorator />
    {children}
  </Card>
);

const CardDecorator = () => (
  <>
    <span className="absolute -left-px -top-px block size-2 border-l-2 border-t-2 border-primary" />
    <span className="absolute -right-px -top-px block size-2 border-r-2 border-t-2 border-primary" />
    <span className="absolute -bottom-px -left-px block size-2 border-b-2 border-l-2 border-primary" />
    <span className="absolute -bottom-px -right-px block size-2 border-b-2 border-r-2 border-primary" />
  </>
);

interface CardHeadingProps {
  icon: LucideIcon;
  title: string;
  description: string;
}

const CardHeading = ({ icon: Icon, title, description }: CardHeadingProps) => (
  <div className="p-6">
    <span className="flex items-center gap-2 font-mono text-[11px] uppercase tracking-[0.16em] text-volt">
      <Icon className="size-4" />
      {title}
    </span>
    <p className="mt-6 text-xl font-semibold text-foreground">{description}</p>
  </div>
);

interface CircleConfig {
  pattern: "none" | "border" | "primary";
}

interface CircularUIProps {
  label: string;
  circles: CircleConfig[];
  className?: string;
}

const CircularUI = ({ label, circles, className }: CircularUIProps) => (
  <div className={className}>
    <div className="size-fit rounded-2xl bg-gradient-to-b from-border to-transparent p-px">
      <div className="relative flex aspect-square w-fit items-center -space-x-4 rounded-[15px] bg-gradient-to-b from-background to-muted/25 p-4">
        {circles.map((circle, i) => (
          <div
            key={i}
            className={cn("size-7 rounded-full border border-primary sm:size-8", {
              "bg-[repeating-linear-gradient(-45deg,hsl(var(--border)),hsl(var(--border))_1px,transparent_1px,transparent_4px)]":
                circle.pattern === "border",
              "bg-background bg-[repeating-linear-gradient(-45deg,hsl(var(--primary)),hsl(var(--primary))_1px,transparent_1px,transparent_4px)]":
                circle.pattern === "primary",
            })}
          />
        ))}
      </div>
    </div>
    <span className="mt-1.5 block text-center text-sm text-muted-foreground">{label}</span>
  </div>
);
