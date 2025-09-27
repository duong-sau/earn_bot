# Cryptocurrency Trading Dashboard Design Guidelines

## Design Approach
**Reference-Based Approach**: Drawing inspiration from professional trading platforms like Coinbase Pro, Binance, and TradingView. The interface prioritizes data density, real-time updates, and operational efficiency over aesthetic flourishes.

## Core Design Elements

### Color Palette
**Dark Mode Primary** (professional trading aesthetic):
- Background: 220 15% 8% (deep charcoal)
- Surface: 220 15% 12% (elevated panels)
- Border: 220 10% 20% (subtle dividers)
- Text Primary: 0 0% 95% (high contrast white)
- Text Secondary: 220 5% 65% (muted gray)

**Status Colors**:
- Success/Profit: 142 70% 45% (trading green)
- Error/Loss: 0 70% 50% (trading red)
- Warning: 45 90% 55% (alert amber)
- Info/Neutral: 220 70% 60% (cool blue)

### Typography
- **Primary Font**: Inter via Google Fonts CDN
- **Monospace**: JetBrains Mono for numerical data, timestamps, and IDs
- **Hierarchy**: Large titles (text-2xl), section headers (text-lg), body text (text-sm), data labels (text-xs)

### Layout System
**Tailwind Spacing Units**: Consistent use of 2, 4, 6, and 8 units
- Micro spacing: p-2, gap-2 for tight layouts
- Standard spacing: p-4, m-4 for component padding
- Section spacing: p-6, gap-6 for card layouts
- Major spacing: p-8, gap-8 for page-level separation

### Component Library

**Navigation**: 
- Fixed sidebar with microservice status indicators
- Top navigation bar with config reload and alert test buttons
- Breadcrumb navigation for deep sections

**Data Tables**:
- Dense, scannable rows with alternating backgrounds
- Sortable headers with subtle hover states
- Inline action buttons (start/stop, open/close)
- Status badges with appropriate colors

**Cards & Panels**:
- Elevated surfaces with subtle borders
- Header sections with action buttons
- Real-time updating content areas
- Collapsible sections for detailed views

**Forms & Controls**:
- Compact input fields for trading parameters
- Toggle switches for manual/auto modes
- Slider controls for leverage settings
- Filter dropdowns for symbol and exchange selection

**Status Indicators**:
- Dot indicators for microservice health
- Progress bars for loading states
- Real-time timestamp displays
- Connection status indicators

### Specific Interface Sections

**Microservices Dashboard**:
- Grid layout of service cards with status lights
- Quick start/stop toggle buttons
- Service health metrics and uptime displays

**Position Management**:
- Trading pair selection with search
- Leverage slider with visual feedback
- Manual/Auto mode toggle switches
- Position summary table with P&L indicators

**Opportunities Browser**:
- Filterable table with basis point sorting
- Real-time price update indicators
- Symbol search with autocomplete
- Minimum threshold slider controls

**Funding Snapshots**:
- Exchange comparison grid
- Historical rate charts (simple line graphs)
- Symbol filtering with multi-select
- Export functionality buttons

### Visual Hierarchy
- **Primary Actions**: Prominent buttons with brand colors
- **Secondary Actions**: Outline buttons with muted styling
- **Data Priority**: Larger text for critical metrics (P&L, prices)
- **Status Communication**: Color-coded backgrounds and borders

### Animations
Minimal and functional only:
- Smooth transitions for status changes (200ms)
- Loading states for data fetching
- Subtle hover feedback on interactive elements
- No decorative animations or distracting effects

This design prioritizes information density, operational efficiency, and professional aesthetics suitable for financial trading applications while maintaining excellent usability for rapid decision-making.