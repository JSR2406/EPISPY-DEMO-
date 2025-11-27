# Resource Marketplace & Personalized Risk System - Architecture

## Overview

This document describes the architecture and implementation of two major EpiSPY features:

1. **Resource Marketplace**: Automated resource matching and allocation system
2. **Personalized Risk Assessment**: Privacy-preserving individual risk calculation

## Resource Marketplace

### Database Schema

#### Core Models

1. **ResourceProvider**: Organizations/individuals providing resources
   - Types: Hospital, Clinic, Supplier, NGO, Government, Individual
   - Verification status, ratings, transaction history

2. **ResourceInventory**: Available resources
   - Resource types (ventilators, beds, PPE, medicine, staff)
   - Quantity, pricing, quality grades, expiry dates
   - Certifications (FDA, WHO standards)

3. **ResourceRequest**: Requests for resources
   - Urgency levels: Routine, Urgent, Critical, Emergency
   - Priority scoring based on multiple factors
   - Deadline tracking

4. **ResourceMatch**: Matches between requests and inventory
   - Match score (0-100) based on optimization algorithm
   - Status: Pending, Accepted, Rejected, Fulfilled

5. **ResourceTransfer**: Logistics tracking
   - Status: Scheduled, In Transit, Delivered
   - Tracking information, ETAs
   - Cost tracking

6. **VolunteerStaff**: Medical volunteer management
   - Specializations, certifications
   - Availability, location preferences

7. **StaffDeployment**: Volunteer deployment tracking
   - Facility assignments
   - Hours worked, ratings

### Matching Algorithm

**ResourceMatchingEngine** uses multi-criteria decision analysis:

#### Scoring Factors (Weighted)

1. **Geographic Proximity (25%)**
   - Haversine distance calculation
   - Exponential decay: 100 at 0km, 0 at 1000km+
   - Closer = higher score

2. **Urgency (30%)**
   - Emergency: 100, Critical: 75, Urgent: 50, Routine: 25
   - Deadline proximity boost
   - Highest weight due to life-saving priority

3. **Quality (15%)**
   - Grade A: 100, B: 75, C: 50, D: 25
   - Certification verification

4. **Cost (10%)**
   - Lower price = higher score
   - Normalized to 0-100

5. **Reliability (15%)**
   - Provider rating (0-5 → 0-100)
   - Verification bonus (+20)
   - Transaction history bonus

6. **Availability (5%)**
   - Can fulfill completely: 100
   - Partial fulfillment: ratio * 100

#### Optimization Approach

- **Greedy Algorithm**: Sort matches by score, select top matches
- **Multi-Request Optimization**: Consider all open requests simultaneously
- **Quantity Matching**: Match maximum available quantity
- **Auto-Accept**: High-scoring matches (>80) auto-accepted

#### Future Enhancements

- Linear Programming (PuLP/OR-Tools) for global optimization
- Multi-resource bundle matching
- Route optimization for logistics
- Predictive demand forecasting

### API Endpoints

#### Provider Endpoints
- `POST /marketplace/inventory/add` - List resources
- `PUT /marketplace/inventory/update/{id}` - Update inventory
- `GET /marketplace/inventory/my-listings` - View listings
- `GET /marketplace/requests/matching` - Requests I can fulfill

#### Requester Endpoints
- `POST /marketplace/request/create` - Create request
- `GET /marketplace/request/matches/{id}` - Get matches
- `POST /marketplace/request/accept-match` - Accept match
- `GET /marketplace/request/status/{id}` - Check status

#### Admin Endpoints
- `GET /marketplace/dashboard/overview` - Dashboard
- `GET /marketplace/analytics/supply-demand` - Analytics
- `POST /marketplace/admin/prioritize-request` - Manual prioritization
- `GET /marketplace/predictions/resource-needs` - Forecasts

## Personalized Risk Assessment

### Database Schema

#### Core Models

1. **UserProfile**: User health information
   - Age group, comorbidities
   - Vaccination status
   - Occupation, household size
   - Privacy level settings

2. **UserLocation**: Location history (privacy-preserving)
   - Coordinates, timestamps
   - Optional hashing for privacy
   - Current location flag

3. **ExposureEvent**: Contact tracing events
   - Exposure date, risk level
   - Notification status
   - User acknowledgment

4. **RiskHistory**: Historical risk scores
   - Daily risk assessments
   - Contributing factors
   - Location at time of assessment

5. **NotificationPreferences**: User notification settings
   - Channels (push, SMS, email)
   - Quiet hours
   - Sensitivity level
   - Daily limits

### Risk Calculation Algorithm

**PersonalizedRiskCalculator** uses weighted multi-factor analysis:

#### Risk Factors (Weighted)

1. **Location Risk (30%)**
   - Current area outbreak severity
   - Case growth rate
   - Normalized severity score (0-100)

2. **Travel Risk (15%)**
   - Locations visited in last 14 days
   - Average risk of visited locations
   - Time decay factor

3. **Exposure Risk (25%)**
   - Recent exposure events
   - Risk level of exposures
   - Time since exposure (decay)

4. **Vulnerability (15%)**
   - Age group multipliers (65+: 1.5x)
   - Comorbidity count
   - Vaccination status (reduces risk)

5. **Behavior (5%)**
   - Mask compliance
   - Social distancing
   - Up to 50% risk reduction

6. **Occupation (5%)**
   - Healthcare: 1.5x
   - Essential: 1.2x
   - Remote: 0.7x

7. **Household (5%)**
   - Household size factor
   - More members = higher risk

#### Risk Levels

- **LOW**: < 30
- **MODERATE**: 30-50
- **HIGH**: 50-75
- **CRITICAL**: > 75

#### Recommendations Engine

Generates personalized advice based on:
- Risk level
- Contributing factors
- User profile (age, health conditions)
- Local resources

### Privacy Architecture

#### Privacy Principles

1. **Data Minimization**: Collect only necessary data
2. **Local Processing**: Risk calculation on device when possible
3. **Anonymization**: Hash locations for analytics
4. **Retention Limits**: 30-day data retention
5. **User Control**: Privacy level settings (MINIMAL, STANDARD, FULL)
6. **Encryption**: At rest and in transit
7. **GDPR Compliance**: Right to deletion, consent management

#### Location Privacy

- Optional location hashing
- Differential privacy for aggregated data
- No centralized location tracking
- Device-side geofencing

### Notification System

**NotificationManager** handles:

#### Notification Types

1. Risk level change
2. Exposure alerts
3. Location warnings
4. Policy changes
5. Testing recommendations
6. Vaccination reminders

#### Smart Delivery

- **Quiet Hours**: No notifications 10 PM - 7 AM (unless critical)
- **Rate Limiting**: Max 3 notifications/day (configurable)
- **Priority Override**: Critical alerts bypass limits
- **Channel Selection**: Based on notification type and user preferences

#### Channels

- Push notifications (Firebase Cloud Messaging)
- SMS (Twilio)
- Email (SendGrid/SES)
- In-app notifications

## Integration Points

### With Existing Systems

1. **Outbreak Prediction Models**: For resource demand forecasting
2. **Location Data**: For geographic matching and risk calculation
3. **Policy System**: For location-based policy notifications
4. **Alert System**: For critical resource shortages

### Background Tasks

1. **Auto-matching**: Run every 5 minutes
2. **Risk Recalculation**: Daily for all users
3. **Notification Delivery**: Real-time
4. **Analytics Generation**: Daily reports
5. **Data Cleanup**: Expire old data (privacy compliance)

## Performance Considerations

### Scalability

- **Caching**: Redis for real-time risk calculations
- **Indexing**: Comprehensive database indexes
- **Batch Processing**: Bulk operations for efficiency
- **Async Operations**: Non-blocking I/O

### Optimization

- **Geographic Queries**: PostGIS for spatial queries
- **Match Caching**: Cache match scores
- **Lazy Loading**: Load relationships on demand
- **Connection Pooling**: Efficient database connections

## Security

- **Authentication**: JWT tokens
- **Authorization**: Role-based access control
- **Data Encryption**: AES-256 at rest
- **TLS**: All API communications
- **Audit Logging**: All transactions logged

## Future Enhancements

1. **Blockchain**: Supply chain transparency
2. **AI Matching**: ML-based match recommendations
3. **Predictive Analytics**: Advanced demand forecasting
4. **Mobile Apps**: React Native/Flutter
5. **Offline Mode**: PWA with service workers
6. **Multi-language**: i18n support

## Testing Strategy

1. **Unit Tests**: Algorithm correctness
2. **Integration Tests**: API endpoints
3. **Performance Tests**: Load testing
4. **Privacy Audits**: Data handling verification
5. **Security Tests**: Penetration testing

