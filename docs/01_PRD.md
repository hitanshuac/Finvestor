# Product Requirements Document (PRD)

## 1. Project Overview
**Name:** Finvestor — Digital Wealth Advisory Avatar
**Description:** A Digital Wealth Advisory Avatar built for the IDBI Bank Hackathon (Track 1) to provide personalized, conversational investment advice to customers based on their 90-day transaction history and age-based risk profile.

## 2. Target Audience
IDBI Bank Retail Customers, specifically:
- **Young Salaried Professionals (Age 28):** High risk appetite, high transaction volume.
- **Pre-Retirement Customers (Age 55):** Conservative risk appetite, focused on wealth preservation.

## 3. Core Features (MVP)
1. **Mock Data Engine:** Deterministically generate 90 days of INR transactions (CR/DR) based on customer personas.
2. **Customer 360 Analytics:** Compute total 90-day inflows, outflows, and current balance using DuckDB aggregation.
3. **Conversational AI Avatar:** Stream real-time financial advice using OpenAI, factoring in the computed Customer 360 profile.
4. **Hybrid RM Handoff Protocol:** If the user requests highly specific or restricted financial instruments (e.g., F&O, direct stock tips), the Avatar gracefully degrades and hands off the conversation to a human Relationship Manager.
5. **Multi-Language Support:** Allow users to request advice in English, Hindi, or Marathi.

## 4. Non-Goals (Out of Scope for MVP)
- Real IDBI banking API integration.
- Voice-based interaction (text-only for MVP).
- Authentication/SSO integration.
