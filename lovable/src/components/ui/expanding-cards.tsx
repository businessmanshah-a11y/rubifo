"use client";

import * as React from "react";
import { cn } from "@/lib/utils";

export interface CardItem {
  id: string | number;
  title: string;
  description: string;
  imgSrc: string;
  icon: React.ReactNode;
  linkHref: string;
  meta?: string;
}

interface ExpandingCardsProps extends React.HTMLAttributes<HTMLUListElement> {
  items: CardItem[];
  defaultActiveIndex?: number;
  ctaLabel?: string;
}

export const ExpandingCards = React.forwardRef<HTMLUListElement, ExpandingCardsProps>(
  ({ className, items, defaultActiveIndex = 0, ctaLabel = "View", ...props }, ref) => {
    const [activeIndex, setActiveIndex] = React.useState(defaultActiveIndex);
    const [isDesktop, setIsDesktop] = React.useState(false);

    React.useEffect(() => {
      const handleResize = () => setIsDesktop(window.innerWidth >= 768);
      handleResize();
      window.addEventListener("resize", handleResize);
      return () => window.removeEventListener("resize", handleResize);
    }, []);

    const gridStyle = React.useMemo(() => {
      const tracks = items
        .map((_, index) => (index === activeIndex ? "5fr" : "1fr"))
        .join(" ");
      return isDesktop
        ? { gridTemplateColumns: tracks, gridTemplateRows: "1fr" }
        : { gridTemplateRows: tracks, gridTemplateColumns: "1fr" };
    }, [activeIndex, items, isDesktop]);

    const handleInteraction = (index: number) => setActiveIndex(index);

    return (
      <ul
        ref={ref}
        className={cn(
          "grid w-full gap-3 transition-[grid-template-columns,grid-template-rows] duration-700 ease-[cubic-bezier(0.22,1,0.36,1)]",
          "h-[520px] md:h-[460px]",
          className,
        )}
        style={gridStyle}
        {...props}
      >
        {items.map((item, index) => {
          const isActive = activeIndex === index;
          return (
            <li
              key={item.id}
              onMouseEnter={() => handleInteraction(index)}
              onFocus={() => handleInteraction(index)}
              onClick={() => handleInteraction(index)}
              tabIndex={0}
              data-active={isActive}
              className={cn(
                "group relative cursor-pointer overflow-hidden rounded-3xl border border-border bg-card outline-none",
                "transition-all duration-700 ease-[cubic-bezier(0.22,1,0.36,1)]",
                "focus-visible:ring-2 focus-visible:ring-gold/60",
                isActive ? "border-gold/50" : "hover:border-gold/30",
              )}
            >
              <img
                src={item.imgSrc}
                alt={item.title}
                loading="lazy"
                className={cn(
                  "absolute inset-0 h-full w-full object-cover transition-all duration-1000 ease-[cubic-bezier(0.22,1,0.36,1)]",
                  isActive ? "scale-105 opacity-100" : "scale-100 opacity-70",
                )}
              />
              <div
                className={cn(
                  "absolute inset-0 transition-opacity duration-700",
                  isActive
                    ? "bg-gradient-to-t from-background/90 via-background/40 to-background/10"
                    : "bg-gradient-to-t from-background/95 via-background/70 to-background/30",
                )}
              />

              {/* Collapsed label */}
              <div
                className={cn(
                  "absolute inset-0 flex items-end justify-center p-4 transition-opacity duration-300",
                  isActive ? "opacity-0" : "opacity-100",
                )}
              >
                <div className="flex items-center gap-2 text-foreground">
                  <span className="text-gold">{item.icon}</span>
                  <span className="hidden text-sm font-medium md:[writing-mode:vertical-rl] md:rotate-180 md:block">
                    {item.title}
                  </span>
                  <span className="text-sm font-medium md:hidden">{item.title}</span>
                </div>
              </div>

              {/* Expanded content */}
              <div
                className={cn(
                  "absolute inset-0 flex flex-col justify-end p-6 transition-all duration-500",
                  isActive
                    ? "translate-y-0 opacity-100 delay-200"
                    : "translate-y-4 opacity-0",
                )}
              >
                {item.meta && (
                  <span className="text-xs uppercase tracking-[0.2em] text-gold">
                    {item.meta}
                  </span>
                )}
                <div className="mt-2 flex items-center gap-2">
                  <span className="text-gold">{item.icon}</span>
                  <h3 className="text-xl font-semibold text-foreground md:text-2xl">
                    {item.title}
                  </h3>
                </div>
                <p className="mt-2 max-w-xl text-sm leading-relaxed text-muted-foreground">
                  {item.description}
                </p>
                <a
                  href={item.linkHref}
                  className="mt-4 inline-flex w-fit items-center gap-1.5 rounded-full border border-gold/40 bg-gold/10 px-4 py-1.5 text-xs font-medium text-gold transition hover:bg-gold hover:text-gold-foreground"
                >
                  {ctaLabel}
                </a>
              </div>
            </li>
          );
        })}
      </ul>
    );
  },
);
ExpandingCards.displayName = "ExpandingCards";
