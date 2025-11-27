# EpiSPY Frontend

Modern, production-ready React frontend for the EpiSPY epidemic surveillance system.

## 🎨 Design System

Built with a comprehensive design system featuring:
- Healthcare-optimized color psychology
- Glassmorphism and modern visual effects
- Smooth animations with Framer Motion
- Full dark/light mode support
- WCAG 2.1 AA accessibility compliance

## 🚀 Quick Start

### Prerequisites
- Node.js 18+ 
- npm or yarn

### Installation

```bash
# Install dependencies
npm install

# Start development server
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview
```

## 📁 Project Structure

```
frontend/
├── src/
│   ├── components/
│   │   └── ui/          # Core UI components
│   ├── design/          # Design tokens and theme
│   ├── lib/             # Utilities
│   ├── examples/        # Component showcases
│   └── ...
├── public/              # Static assets
└── package.json
```

## 🎯 Core Components

### Button
Multiple variants: primary, secondary, outline, ghost, danger, success, warning
```tsx
<Button variant="primary" size="md">Click Me</Button>
```

### Card
Elevated cards with hover effects and glassmorphism
```tsx
<Card variant="elevated" hover>
  <CardHeader>
    <CardTitle>Title</CardTitle>
  </CardHeader>
  <CardContent>Content</CardContent>
</Card>
```

### Badge
Risk levels and status indicators
```tsx
<Badge variant="critical" pulse>High Risk</Badge>
```

### Alert
System notifications with icons
```tsx
<Alert variant="warning" title="Alert">Message</Alert>
```

### Modal
Smooth animated dialogs
```tsx
<Modal isOpen={open} onClose={handleClose} title="Modal">
  Content
</Modal>
```

## 🎨 Theme System

The design system uses a comprehensive theme with:
- Color palette (primary, risk levels, health status)
- Typography scale
- Spacing system (8px grid)
- Shadows and elevations
- Transitions and animations

See `src/design/theme.ts` for full details.

## 🌙 Dark Mode

Dark mode is fully supported. Toggle using:
```tsx
// Add dark class to html element
document.documentElement.classList.toggle('dark');
```

## ♿ Accessibility

- Keyboard navigation (Tab, Arrow keys, Escape)
- Focus indicators
- ARIA labels and roles
- Screen reader support
- Color contrast ratios >4.5:1
- Reduced motion support

## 📱 Responsive Design

Mobile-first approach with breakpoints:
- Mobile: < 640px
- Tablet: 640px - 1024px
- Desktop: > 1024px

## 🛠️ Tech Stack

- **React 18** with TypeScript
- **Vite** for build tooling
- **TailwindCSS** for styling
- **Framer Motion** for animations
- **class-variance-authority** for component variants
- **lucide-react** for icons

## 📚 Documentation

See `DESIGN_SYSTEM.md` for detailed design system documentation.

## 🎯 Next Steps

1. ✅ Design tokens and theme system
2. ✅ Core UI components
3. ⏳ Data visualization components
4. ⏳ Layout components
5. ⏳ Feature dashboards
6. ⏳ Real-time WebSocket integration

## 📝 License

Part of the EpiSPY project.

