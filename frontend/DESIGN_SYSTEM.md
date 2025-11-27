# EpiSPY Design System

## Design Philosophy

The EpiSPY design system is built with **healthcare-appropriate color psychology**, **accessibility-first principles**, and **modern 2025 visual trends**. Our goal is to create an interface that is both visually stunning and functionally superior for epidemic surveillance.

### Core Principles

1. **Trust & Calm**: Medical blue primary colors inspire confidence and professionalism
2. **Clarity Over Decoration**: Data-driven design that prioritizes information clarity
3. **Progressive Disclosure**: Don't overwhelm users - reveal information progressively
4. **Accessibility**: WCAG 2.1 AA compliant, color-blind friendly, keyboard navigable
5. **Performance**: Fast perceived performance with smooth 60fps animations
6. **Mobile-First**: Responsive design that works beautifully on all devices

## Color System

### Primary Colors
- **Medical Blue (#2196F3)**: Trust, professionalism, calm
- **Teal (#00BCD4)**: Health, growth, recovery

### Risk Level Colors (Semantic)
- **Minimal** (Green): Safe, low risk
- **Low** (Light Green): Minimal concern
- **Moderate** (Amber): Requires attention
- **High** (Orange): Significant risk
- **Critical** (Red): Immediate action required

### Health Status Colors
- **Healthy**: Bright green
- **Exposed**: Amber
- **Infected**: Red
- **Recovered**: Cyan
- **Vaccinated**: Purple

## Typography

- **Primary Font**: Inter (clean, modern, highly readable)
- **Display Font**: Poppins (for headings, adds personality)
- **Mono Font**: Fira Code (for code/data)

## Spacing System

Based on 8px grid system for consistent spacing:
- 4px, 8px, 12px, 16px, 24px, 32px, 48px, 64px, 96px

## Component Showcase

### Button
```tsx
<Button variant="primary" size="md" loading={false}>
  Analyze Data
</Button>
```

Variants: `primary`, `secondary`, `outline`, `ghost`, `danger`, `success`, `warning`
Sizes: `xs`, `sm`, `md`, `lg`, `xl`, `icon`

### Card
```tsx
<Card variant="elevated" hover glow>
  <CardHeader>
    <CardTitle>Risk Assessment</CardTitle>
    <CardDescription>Current outbreak status</CardDescription>
  </CardHeader>
  <CardContent>...</CardContent>
</Card>
```

Variants: `default`, `elevated`, `glass`, `outlined`, `flat`

### Badge
```tsx
<Badge variant="critical" pulse>
  High Risk
</Badge>
```

Variants: Risk levels, health status, semantic colors

### Alert
```tsx
<Alert variant="warning" title="Outbreak Detected" dismissible>
  New cases reported in Mumbai
</Alert>
```

### Modal
```tsx
<Modal isOpen={open} onClose={handleClose} title="Confirm Action">
  <ModalContent>...</ModalContent>
</Modal>
```

## Animations

All components use Framer Motion for smooth animations:
- **Hover**: Subtle scale (1.02) and lift effects
- **Click**: Brief scale down (0.98) for tactile feedback
- **Enter**: Fade + slide up animations
- **Exit**: Smooth fade out

## Glassmorphism

Modern glassmorphism effects for elevated cards:
```tsx
<Card variant="glass">
  {/* Semi-transparent background with backdrop blur */}
</Card>
```

## Dark Mode

Full dark mode support with optimized colors:
- Deep navy backgrounds (#0A0E27)
- Elevated surfaces with subtle borders
- High contrast text for readability

## Accessibility Features

- ✅ Keyboard navigation (Tab, Arrow keys, Escape)
- ✅ Focus indicators (ring-2 ring-primary-500)
- ✅ ARIA labels and roles
- ✅ Screen reader support
- ✅ Color contrast ratios >4.5:1
- ✅ Reduced motion support

## Usage Example

```tsx
import { Button, Card, Badge, Alert } from '@/components/ui';

function Dashboard() {
  return (
    <div className="p-6">
      <Card variant="elevated" hover className="mb-4">
        <CardHeader>
          <CardTitle>Epidemic Overview</CardTitle>
          <div className="flex gap-2 mt-2">
            <Badge variant="critical">Critical</Badge>
            <Badge variant="high">High Risk</Badge>
          </div>
        </CardHeader>
        <CardContent>
          <Alert variant="warning" title="Alert">
            New outbreak detected
          </Alert>
        </CardContent>
        <CardFooter>
          <Button variant="primary">View Details</Button>
        </CardFooter>
      </Card>
    </div>
  );
}
```

## Next Steps

1. ✅ Design tokens and theme system
2. ✅ Core UI components (Button, Card, Badge, Alert, Modal)
3. ⏳ Data visualization components
4. ⏳ Layout components (AppShell, Sidebar, TopBar)
5. ⏳ Feature-specific dashboards
6. ⏳ Real-time WebSocket integration
7. ⏳ Mobile optimizations
8. ⏳ PWA features

